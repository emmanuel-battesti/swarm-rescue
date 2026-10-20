"""
Tests for `Playground.reset()` repositioning the scene elements.

`reset()` puts back in place anything that may have drifted. Two distinct
conditions trigger this, and they used to be written as two duplicated
branches:

- `element.movable`  a PhysicalElement, i.e. one that has a mass
- `element.moved`    any EmbodiedEntity that actually moved

They are not the same set: `moved` also covers embodied entities that are
not `PhysicalElement` (a Grasper, a RaySensor, a zone), and those have no
`movable` attribute at all. These tests pin the behavior of both, so that
merging the two branches cannot silently change what gets repositioned.
"""

import pathlib
import sys

import numpy as np
import pytest

# Insert the 'src' directory into sys.path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from swarm_rescue.simulation.elements.normal_wall import ColorWall
from swarm_rescue.simulation.elements.wounded_person import WoundedPerson
from swarm_rescue.simulation.elements.rescue_center import RescueCenter
from swarm_rescue.simulation.gui_map.closed_playground import ClosedPlayground


@pytest.fixture
def playground():
    pg = ClosedPlayground(size=(1200, 800))
    try:
        yield pg
    finally:
        pg.close_window()


def _add_wall(pg, pos_start, pos_end, mass=None):
    """Add a ColorWall; `mass` makes it movable when set."""
    wall = ColorWall(
        pos_start=pos_start,
        pos_end=pos_end,
        color=(200, 0, 0),
        mass=mass,
    )
    coordinates = wall.wall_coordinates
    pg.add(wall, initial_coordinates=coordinates)
    return wall


class TestResetRepositionsElements:
    """reset() must bring the scene back to its initial state."""

    def test_movable_element_is_put_back_in_place(self, playground):
        """A movable element that drifted must return to its initial spot."""
        wall = _add_wall(playground, (100, 100), (200, 100), mass=10)
        start = wall.position
        assert wall.movable, "the wall should be movable (it has a mass)"

        wall.move_to(((300.0, 200.0), 0.0))
        assert not np.allclose(wall.position, start)

        playground.reset()

        assert np.allclose(wall.position, start)

    def test_static_element_is_not_moved(self, playground):
        """An element that cannot move and did not move must be left alone.

        Guards against the repositioning being applied too broadly.
        """
        wall = _add_wall(playground, (-400, -300), (-300, -300), mass=0)
        assert not wall.movable
        start = wall.position

        playground.reset()

        assert np.allclose(wall.position, start)

    def test_wounded_person_is_put_back_in_place(self, playground):
        """A heavy element (a wounded person) that drifted goes back home.

        This one is covered by `moved` *and* by `movable`, so it exercises the
        merging of the two branches.
        """
        center = RescueCenter(size=(100, 100))
        playground.add(center, initial_coordinates=((0.0, 0.0), 0.0))

        person = WoundedPerson(center)
        playground.add(person, initial_coordinates=((50.0, 50.0), 0.0))
        start = person.position

        person.move_to(((-200.0, 150.0), 0.0))
        assert not np.allclose(person.position, start)

        playground.reset()

        assert np.allclose(person.position, start)

    def test_reset_is_idempotent(self, playground):
        """Calling reset() twice must not move elements further."""
        wall = _add_wall(playground, (100, 100), (200, 100), mass=10)
        wall.move_to(((250.0, -150.0), 0.0))

        playground.reset()
        first = wall.position
        playground.reset()

        assert np.allclose(wall.position, first)
