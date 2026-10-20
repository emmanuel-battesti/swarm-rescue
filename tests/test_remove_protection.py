#!/usr/bin/env python3
"""
Protection against repeated removal in Playground.remove().

`remove()` is written so that it can be called again on an entity that is
already gone: the `if not entity.removed:` guard skips `_remove_from_space()`
(whose pymunk `space.remove()` raises "shape not in space" otherwise), and
`_remove_from_mappings()` returns early when the uid is no longer mapped.
These tests lock that behavior in.

Semantics verified against the implementation:
  - `definitive=False` -> `entity.removed` is True, the entity is still listed
    in `_elements` and its uid is still in `_uids_to_entities`.
  - `definitive=True`  -> additionally dropped from `_elements` and
    `_uids_to_entities`.
"""
import pathlib
import sys
from typing import List, Type

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from swarm_rescue.simulation.gui_map.closed_playground import ClosedPlayground
from swarm_rescue.simulation.gui_map.map_abstract import MapAbstract
from swarm_rescue.simulation.elements.wounded_person import WoundedPerson
from swarm_rescue.simulation.elements.rescue_center import RescueCenter
from swarm_rescue.simulation.drone.drone_abstract import DroneAbstract


class DummyDrone(DroneAbstract):
    """Simple drone for testing"""
    def define_message_for_all(self):
        pass

    def control(self):
        pass


class MyMapTest(MapAbstract):
    """Test map with basic playground setup"""
    def __init__(
        self, drone_type: Type[DroneAbstract] = DummyDrone, with_rescue_center: bool = True
    ):
        super().__init__(drone_type=drone_type)

        # PARAMETERS MAP
        self._size_area = (1000, 1000)
        self._number_drones = 0
        self._drones: List[DroneAbstract] = []

        self._playground = ClosedPlayground(size=self._size_area)

        # Add rescue center if needed
        if with_rescue_center:
            self.rescue_center = RescueCenter(size=(100, 100))
            self._playground.add(self.rescue_center, ((0, 0), 0))
        else:
            self.rescue_center = None


def test_1_single_remove():
    """A non-definitive remove marks the entity and keeps it in _elements."""
    the_map = MyMapTest()
    playground = the_map.playground

    wp = WoundedPerson(rescue_center=the_map.rescue_center)
    playground.add(wp, ((100, 100), 0))
    elements_before = len(playground._elements)
    uids_before = len(playground._uids_to_entities)

    playground.remove(wp, definitive=False)

    assert wp.removed is True, "The entity must be marked as removed"
    # A non-definitive removal is reversible-looking: the entity stays
    # registered, only its pymunk shapes are detached.
    assert wp in playground._elements, "Non-definitive removal keeps the entity in _elements"
    assert len(playground._elements) == elements_before, "_elements size must not change"
    assert wp.uid in playground._uids_to_entities, "Non-definitive removal keeps the uid mapping"
    assert len(playground._uids_to_entities) == uids_before
    # It is no longer part of the visible set.
    assert wp not in [e for e in playground._elements if not e.removed]


def test_2_double_remove_same_entity():
    """Removing an already-removed entity is a no-op, not a pymunk crash.

    This is the regression test for the `if not entity.removed:` guard: without
    it, the second call reaches `space.remove()` on shapes that are gone and
    pymunk raises `AssertionError: shape not in space`.
    """
    the_map = MyMapTest()
    playground = the_map.playground

    wp = WoundedPerson(rescue_center=the_map.rescue_center)
    playground.add(wp, ((100, 100), 0))

    playground.remove(wp, definitive=False)
    elements_before = len(playground._elements)

    # Must not raise.
    playground.remove(wp, definitive=False)

    assert wp.removed is True
    assert len(playground._elements) == elements_before, \
        "A second remove() must not drop the entity a second time"
    assert wp in playground._elements
    assert wp.uid in playground._uids_to_entities


def test_3_cleanup_after_rescue():
    """cleanup() must cope with entities already removed non-definitively.

    This is the real-world case: a wounded person is picked up (removed
    non-definitively), then the round ends and cleanup() removes everything
    definitively. Removing an already-removed entity must not raise.
    """
    the_map = MyMapTest()
    playground = the_map.playground

    wounded_persons = []
    for i in range(3):
        wp = WoundedPerson(rescue_center=the_map.rescue_center)
        wounded_persons.append(wp)
        playground.add(wp, ((100 * (i + 1), 100), 0))

    elements_before = len(playground._elements)
    uids_before = len(playground._uids_to_entities)

    # Two rescued: removed, but still registered.
    playground.remove(wounded_persons[0], definitive=False)
    playground.remove(wounded_persons[1], definitive=False)

    assert all(p.removed for p in wounded_persons[:2])
    assert len(playground._elements) == elements_before

    # Must not raise.
    playground.cleanup()

    # The two rescued ones are gone for good; the third was never touched.
    assert wounded_persons[0] not in playground._elements
    assert wounded_persons[1] not in playground._elements
    assert wounded_persons[0].uid not in playground._uids_to_entities
    assert wounded_persons[1].uid not in playground._uids_to_entities
    assert len(playground._uids_to_entities) < uids_before


def test_4_drone_collision_scenario():
    """cleanup() after an entity was already removed definitively."""
    the_map = MyMapTest()
    playground = the_map.playground

    wp = WoundedPerson(rescue_center=the_map.rescue_center)
    playground.add(wp, ((100, 100), 0))

    # Simulate a destroyed entity.
    playground.remove(wp, definitive=True)

    assert wp.removed is True
    assert wp not in playground._elements, "A definitive removal drops the entity"
    assert wp.uid not in playground._uids_to_entities

    # Must not raise: cleanup() will try to remove it again.
    playground.cleanup()

    assert wp.uid not in playground._uids_to_entities


def test_5_mixed_scenario():
    """cleanup() on a playground holding both removed and active entities."""
    the_map = MyMapTest()
    playground = the_map.playground

    wounded_persons = []
    for i in range(5):
        wp = WoundedPerson(rescue_center=the_map.rescue_center)
        wounded_persons.append(wp)
        playground.add(wp, ((100 * (i + 1), 100), 0))

    # 2 rescued (non-definitive), 1 destroyed (definitive), 2 untouched.
    playground.remove(wounded_persons[0], definitive=False)
    playground.remove(wounded_persons[2], definitive=False)
    playground.remove(wounded_persons[4], definitive=True)

    assert wounded_persons[4] not in playground._elements
    assert wounded_persons[0] in playground._elements
    assert wounded_persons[2] in playground._elements

    # Must not raise on the mixed state.
    playground.cleanup()

    # Every wounded person is now definitively gone, whatever its prior state.
    for wp in wounded_persons:
        assert wp not in playground._elements, \
            "cleanup() must definitively remove every wounded person"
        assert wp.uid not in playground._uids_to_entities


def test_6_triple_remove_attempt():
    """Removing the same entity three times is idempotent."""
    the_map = MyMapTest()
    playground = the_map.playground

    wp = WoundedPerson(rescue_center=the_map.rescue_center)
    playground.add(wp, ((100, 100), 0))

    elements_before = len(playground._elements)

    for _ in range(3):
        playground.remove(wp, definitive=False)

    assert wp.removed is True
    assert len(playground._elements) == elements_before
    assert wp in playground._elements
    assert wp.uid in playground._uids_to_entities


def test_13_removal_and_cleanup():
    """Removal immediately followed by cleanup leaves no dangling entity."""
    the_map = MyMapTest()
    playground = the_map.playground

    wounded_persons = []
    for i in range(3):
        wp = WoundedPerson(rescue_center=the_map.rescue_center)
        wounded_persons.append(wp)
        playground.add(wp, ((100 * (i + 1), 100), 0))

    playground.remove(wounded_persons[0], definitive=False)
    playground.remove(wounded_persons[1], definitive=False)

    playground.cleanup()

    for wp in wounded_persons:
        assert wp.uid not in playground._uids_to_entities
        assert wp not in playground._elements
