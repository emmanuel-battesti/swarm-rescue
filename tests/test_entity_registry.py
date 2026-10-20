"""
Tests for `EntityRegistry`, the "who exists and how do I find it again" part.

The registry was extracted from `Playground` for one reason: answering "which
entities are in the world, and what is their uid" has nothing to do with the
window `Playground` also owns. These tests demonstrate that -- they build
entities and resolve uids without ever creating an OpenGL context.

The uid rules are the load-bearing part, because the ray sensors identify
entities by uid: a uid that collides, or that equals the background, silently
makes a drone invisible.
"""

import pathlib
import sys

import numpy as np
import pytest

# Insert the 'src' directory into sys.path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from swarm_rescue.simulation.elements.normal_wall import ColorWall
from swarm_rescue.simulation.entity_registry import EntityRegistry

# The sensors recombine the uid as b0 + 256 * b1 + 256 * 256 * b2 from the three
# image channels, so it has to stay under 2**24.
MAX_UID = 2**24


@pytest.fixture
def registry():
    return EntityRegistry()


@pytest.fixture
def rng():
    return np.random.default_rng(42)


def _wall(**kwargs):
    kwargs.setdefault("pos_start", (0, 0))
    kwargs.setdefault("pos_end", (100, 0))
    kwargs.setdefault("color", (200, 0, 0))
    return ColorWall(**kwargs)


def _drone(playground):
    """A drone that does nothing, for the cache tests only."""
    from swarm_rescue.simulation.drone.drone_abstract import DroneAbstract

    class _Drone(DroneAbstract):
        def define_message_for_all(self):
            return None

        def control(self):
            return {"forward": 0.0, "lateral": 0.0,
                    "rotation": 0.0, "grasper": 0}

    return _Drone(playground)


class TestUidDrawing:
    def test_a_registered_entity_gets_a_uid(self, registry, rng):
        wall = _wall()
        registry.register(wall, rng, background_uid=-1)

        assert wall.uid is not None

    def test_the_uid_fits_in_three_bytes(self, registry, rng):
        """
        The sensors read the uid out of a 3-channel image.

        A uid above 2**24 cannot be encoded, and the entity would read back as
        something else entirely.
        """
        wall = _wall()
        registry.register(wall, rng, background_uid=-1)

        assert 0 <= wall.uid < MAX_UID

    def test_the_uid_comes_from_the_generator(self, registry, rng):
        """
        This is what makes a seeded round replayable.

        Two registries fed the same generator and the same entity must hand out
        the same uid; otherwise the lidar of a replayed round identifies
        different objects.
        """
        wall = _wall()
        registry.register(wall, rng, background_uid=-1)

        replay = EntityRegistry()
        replayed = _wall()
        replay.register(replayed, np.random.default_rng(42), background_uid=-1)

        assert wall.uid == replayed.uid

    def test_a_different_seed_gives_a_different_uid(self):
        """Otherwise the seed would not actually control the round."""
        first = EntityRegistry()
        first_wall = _wall(color=(1, 1, 1))
        first.register(first_wall, np.random.default_rng(1), background_uid=-1)

        second = EntityRegistry()
        second_wall = _wall(color=(1, 1, 1))
        second.register(second_wall, np.random.default_rng(2), background_uid=-1)

        assert first_wall.uid != second_wall.uid

class TestUidCollisions:
    def test_the_background_uid_is_never_handed_out(self, registry):
        """
        The uid image is cleared with the background color.

        An entity carrying that uid would be perfectly addressable and yet
        invisible to every sensor -- the worst kind of bug, because nothing
        would report an error.
        """
        background_uid = 5

        class CollidesWithTheBackgroundOnce:
            """
            Returns the forbidden uid first, then a usable one.

            A generator that only ever returns the background uid would make
            the rejection loop spin forever, which is the correct behavior but
            useless as a fixture.
            """

            def __init__(self):
                self.calls = 0

            def integers(self, *args, **kwargs):
                self.calls += 1
                return background_uid if self.calls == 1 else background_uid + 1

        wall = _wall()
        registry.register(wall, CollidesWithTheBackgroundOnce(),
                          background_uid=background_uid)

        assert wall.uid == background_uid + 1

    def test_a_uid_already_in_use_is_not_handed_out_twice(self, registry, rng):
        """Two entities sharing a uid would make every sensor hit ambiguous."""
        first = _wall()
        second = _wall(pos_end=(0, 100))

        registry.register(first, rng, background_uid=-1)
        registry.register(second, rng, background_uid=-1)

        assert first.uid != second.uid


class TestNaming:
    def test_an_unnamed_entity_is_named_after_its_type_and_uid(self, registry, rng):
        wall = _wall()
        registry.register(wall, rng, background_uid=-1)

        assert wall.name == f"ColorWall_{wall.uid}"

    def test_an_explicit_name_is_kept(self, registry, rng):
        wall = _wall(name="my_wall")
        registry.register(wall, rng, background_uid=-1)

        assert wall.name == "my_wall"

    def test_a_duplicate_name_is_rejected(self, registry, rng):
        """
        A silent duplicate makes the reporting ambiguous: two entities answer
        to the same name in the CSV and in the PDF.
        """
        first = _wall(name="wall")
        second = _wall(name="wall", pos_end=(0, 100))

        registry.register(first, rng, background_uid=-1)

        with pytest.raises(ValueError, match="already in Playground"):
            registry.register(second, rng, background_uid=-1)


class TestLookups:
    def test_an_entity_is_found_from_its_uid(self, registry, rng):
        wall = _wall()
        registry.register(wall, rng, background_uid=-1)

        assert registry.get_entity_from_uid(wall.uid) is wall

    def test_an_unknown_uid_resolves_to_none(self, registry):
        """
        It must not raise: a drone destroyed mid-step stays in the last sensor
        reading for the rest of that step.
        """
        assert registry.get_entity_from_uid(123456) is None

    def test_an_embodied_entity_is_found_from_its_shape(self, registry, rng):
        """This is the lookup the collision handlers run on every arbiter."""
        wall = _wall()
        registry.register(wall, rng, background_uid=-1)

        for shape in wall.pm_shapes:
            assert registry.get_entity_from_shape(shape) is wall

    def test_a_shape_after_removal_resolves_to_none(self, registry, rng):
        wall = _wall()
        registry.register(wall, rng, background_uid=-1)
        shapes = list(wall.pm_shapes)

        registry.unregister(wall)

        for shape in shapes:
            assert registry.get_entity_from_shape(shape) is None

class TestCacheInvalidation:
    """
    `agents` and `elements` are cached, and the flag that invalidates them used
    to be set by hand from three different methods. A missed call means a
    destroyed drone keeps being stepped forever.
    """

    def test_a_removed_agent_disappears_from_the_list(self):
        from swarm_rescue.simulation.gui_map.closed_playground import ClosedPlayground

        playground = ClosedPlayground(size=(300, 200))
        try:
            registry = playground._registry
            drone = _drone(playground)
            playground.add(drone, initial_coordinates=((0.0, 0.0), 0.0))
            assert drone in registry.agents

            drone.removed = True
            registry.mark_changed(drone)

            assert drone not in registry.agents
        finally:
            playground.close_window()

    def test_the_cache_is_rebuilt_only_when_needed(self, registry):
        """
        `agents` is read by every sensor on every step; rebuilding it each time
        would be a real cost, so a plain read must reuse the cache.
        """
        assert registry._agents_cache_needs_update is False
        first = registry.agents
        second = registry.agents

        assert first is second, "the cache should have been reused"

    def test_marking_invalidates_the_cache(self, registry, rng):
        wall = _wall()
        registry.register(wall, rng, background_uid=-1)

        # Register already invalidated it; reading consumed the flag. Marking
        # again must put it back.
        assert registry.elements
        registry.mark_changed(wall)

        assert registry._elements_cache_needs_update is True


class TestUnregistration:
    def test_a_definitively_removed_entity_is_forgotten(self, registry, rng):
        wall = _wall()
        registry.register(wall, rng, background_uid=-1)

        registry.unregister(wall)

        assert registry.get_entity_from_uid(wall.uid) is None
        assert wall not in registry.elements

    def test_removing_twice_does_not_raise(self, registry, rng):
        """
        `Playground.cleanup()` removes everything, including parts that may
        already have removed themselves. A raise there would abort the cleanup
        halfway and leak the window.
        """
        wall = _wall()
        registry.register(wall, rng, background_uid=-1)
        registry.unregister(wall)

        registry.unregister(wall)  # must not raise

    def test_unregistering_detaches_the_entity_from_its_playground(self):
        from swarm_rescue.simulation.gui_map.closed_playground import ClosedPlayground

        playground = ClosedPlayground(size=(300, 200))
        try:
            wall = _wall(pos_end=(50, 0))
            playground.add(wall, wall.wall_coordinates)
            assert wall.playground is playground

            playground.remove(wall, definitive=True)

            assert wall.playground is None
        finally:
            playground.close_window()

    def test_clear_drops_everything(self, registry, rng):
        for i in range(3):
            registry.register(
                _wall(pos_end=(50, i * 10)), rng, background_uid=-1
            )

        registry.clear()

        assert registry.agents == []
        assert registry.elements == []
        assert registry.uids_to_entities == {}
        assert registry.shapes_to_entities == {}


class TestNoWindowNeeded:
    def test_the_registry_works_without_an_opengl_context(self, registry, rng):
        """
        The point of the extraction, stated as a test.

        Nothing in this file builds a playground, a window or a view, and the
        lookup round trip still works. That was not possible before.
        """
        wall = _wall()
        registry.register(wall, rng, background_uid=-1)

        assert registry.get_entity_from_uid(wall.uid) is wall
        assert wall in registry.elements
        assert registry.shapes_to_entities[wall.pm_shapes[0]] is wall
