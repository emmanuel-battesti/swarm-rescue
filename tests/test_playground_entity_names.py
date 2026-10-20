"""
Tests for the entity name uniqueness in `Playground`.

Every entity gets a name, used by the reporting.
`_get_identifier` used to check for duplicates only in `self.elements`,
while the agents live in `self.agents`. A collision was therefore detected in
one order only: an entity added after an agent of the same name slipped
through and ended up with a duplicate name.
"""

import pathlib
import sys

import pytest

# Insert the 'src' directory into sys.path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from swarm_rescue.simulation.drone.drone_abstract import DroneAbstract
from swarm_rescue.simulation.elements.normal_wall import ColorWall
from swarm_rescue.simulation.gui_map.closed_playground import ClosedPlayground


class NamedDrone(DroneAbstract):
    def define_message_for_all(self):
        pass

    def control(self):
        return {"forward": 0.0, "lateral": 0.0, "rotation": 0.0, "grasper": 0}


@pytest.fixture
def playground():
    pg = ClosedPlayground(size=(1200, 800))
    try:
        yield pg
    finally:
        pg.close_window()


def _add_wall(pg, name, at=(300, 300)):
    wall = ColorWall(
        pos_start=at, pos_end=(at[0] + 50, at[1]), color=(1, 2, 3), name=name
    )
    pg.add(wall, initial_coordinates=wall.wall_coordinates)
    return wall


def _add_drone(pg, name, at=(0, 0)):
    drone = NamedDrone(pg, name=name, angle=0.0)
    pg.add(drone, initial_coordinates=(at, 0.0))
    return drone


class TestDuplicateNamesAreRejected:
    """A name must be unique across the whole playground."""

    def test_entity_after_agent_is_rejected(self, playground):
        """The order that used to slip through."""
        _add_drone(playground, "dup")

        with pytest.raises(ValueError, match="dup"):
            _add_wall(playground, "dup")

    def test_agent_after_entity_is_rejected(self, playground):
        """The order that already worked."""
        _add_wall(playground, "dup")

        with pytest.raises(ValueError, match="dup"):
            _add_drone(playground, "dup")

    def test_two_entities_are_rejected(self, playground):
        _add_wall(playground, "dup")

        with pytest.raises(ValueError, match="dup"):
            _add_wall(playground, "dup", at=(400, 400))

    def test_two_agents_are_rejected(self, playground):
        _add_drone(playground, "dup")

        with pytest.raises(ValueError, match="dup"):
            _add_drone(playground, "dup", at=(50, 0))

    def test_the_error_names_the_offending_name(self, playground):
        """The message must say which name is taken, not just that one is."""
        _add_drone(playground, "wilfried")

        with pytest.raises(ValueError) as excinfo:
            _add_wall(playground, "wilfried")

        assert "wilfried" in str(excinfo.value)


class TestDistinctNamesAreAccepted:
    """The uniqueness check must not produce false positives."""

    def test_distinct_names_coexist(self, playground):
        drone = _add_drone(playground, "alice")
        wall = _add_wall(playground, "bob")

        assert drone.name == "alice"
        assert wall.name == "bob"

    def test_an_unnamed_entity_gets_a_generated_name(self, playground):
        """Entities without a name get a unique generated one."""
        first = _add_wall(playground, None, at=(300, 300))
        second = _add_wall(playground, None, at=(400, 400))

        assert first.name
        assert second.name
        assert first.name != second.name

    def test_several_unnamed_agents_get_distinct_names(self, playground):
        first = _add_drone(playground, None)
        second = _add_drone(playground, None, at=(50, 0))

        assert first.name != second.name

    def test_a_removed_entity_frees_its_name(self, playground):
        """Once removed, the name is available again."""
        wall = _add_wall(playground, "dup")
        playground.remove(wall, definitive=True)

        # Must not raise.
        _add_wall(playground, "dup", at=(400, 400))
