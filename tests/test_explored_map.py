import pathlib
import sys
from typing import List, Type

import numpy as np

# Insert the 'src' directory, located two levels up from the current script,
# into sys.path. This ensures Python can find project-specific modules
# (e.g., 'swarm_rescue') when the script is run from a subfolder like 'tests/'.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from swarm_rescue.simulation.drone.drone_abstract import DroneAbstract
from swarm_rescue.simulation.elements.normal_wall import NormalBox
from swarm_rescue.simulation.elements.wounded_person import WoundedPerson
from swarm_rescue.simulation.gui_map.closed_playground import ClosedPlayground
from swarm_rescue.simulation.gui_map.map_abstract import MapAbstract
from swarm_rescue.simulation.reporting.explored_map import ExploredMap
from swarm_rescue.simulation.utils.misc_data import MiscData


class MyDrone(DroneAbstract):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def define_message_for_all(self):
        pass

    def control(self):
        command = {"forward": 1.0,
                   "lateral": 0.0,
                   "rotation": 0.0,
                   "grasper": 0}
        return command


class MyMap(MapAbstract):
    def __init__(self, drone_type: Type[DroneAbstract]):
        super().__init__(drone_type=drone_type)

        # PARAMETERS MAP
        self._size_area = (200, 200)

        # POSITIONS OF THE DRONES
        self._number_drones = 1
        self._drones_pos = [((10, 10), 0)]
        self._drones = []

        self._drones: List[DroneAbstract] = []

        self._playground = ClosedPlayground(size=self._size_area)

        # POSITIONS OF THE DRONES
        misc_data = MiscData(size_area=self._size_area,
                             number_drones=self._number_drones,
                             max_timestep_limit=self._max_timestep_limit,
                             max_walltime_limit=self._max_walltime_limit)
        for i in range(self._number_drones):
            drone = drone_type(identifier=i, misc_data=misc_data)
            self._drones.append(drone)
            self._playground.add(drone, self._drones_pos[i])


def _make_test_map():
    return MyMap(drone_type=MyDrone)


class MyDroneFreeMap(MapAbstract):
    """A map with a playground and walls, and no drone at all."""

    def __init__(self, drone_type: Type[DroneAbstract]):
        super().__init__(drone_type=drone_type)

        self._size_area = (200, 200)
        self._number_drones = 0
        self._drones: List[DroneAbstract] = []

        self._playground = ClosedPlayground(size=self._size_area)
        self._playground.add(
            NormalBox(up_left_point=(40, 40), width=30, height=30),
            ((55.0, 55.0), 0),
        )
        self._number_wounded_persons = 0


def test_initialize_explored_map_with_default_values():
    the_map = _make_test_map()
    explored_map = ExploredMap()
    assert explored_map.initialized is False
    assert explored_map._img_playground.shape == (0, 0)
    assert explored_map._map_playground.shape == (0, 0)
    assert explored_map._map_explo_lines.shape == (0, 0)
    assert explored_map._map_explo_zones.shape == (0, 0)
    assert explored_map._explo_pts == {}
    assert explored_map._last_position == {}
    assert explored_map._count_explored_pixels == 0

    # `update_drones` initializes the walls by itself. It used to return
    # silently on a map that had not called `initialize_walls`, which made
    # every map carry that call by hand -- sixteen identical lines -- and made
    # the exploration score read 0.0% for anyone who forgot it.
    drones = the_map.playground.agents
    explored_map.update_drones(drones)
    assert explored_map.initialized is True
    assert explored_map._map_playground.shape != (0, 0)
    assert explored_map._map_explo_lines.shape != (0, 0)


def test_the_walls_do_not_depend_on_what_stands_on_the_map():
    """
    The reason `initialize_walls` renders the static geometry only.

    A map used to have to be initialized *before* its drones and wounded
    persons were added, because those sprites were baked into the walls. The
    call was therefore order-sensitive, with no error to point at it: the same
    map produced a different wall image -- hence a different exploration score
    -- depending on where the author had put the line. Adding a drone to a map
    that initialized its explored map late silently cost it reachable pixels.

    Rendering the map for its own sake removes the constraint, so putting the
    entities on the map must leave the walls untouched.

    Both renders happen on the *same* playground on purpose. Two separate
    playgrounds are not a valid reference here: they do not render
    bit-identically (measured: ~27k differing pixels on the raw image, from the
    GL state each one inherits), and the wall map is a threshold of that image,
    so an unrelated pixel can land on either side of the cut.
    """
    playground = ClosedPlayground(size=(400, 300))
    playground.add(NormalBox(up_left_point=(100, 60), width=30, height=30),
                   ((115.0, 75.0), 0))
    try:
        before = ExploredMap()
        before.initialize_walls(playground)

        # Sanity: the render is not simply blank.
        assert np.count_nonzero(before._map_playground == 0) > 0

        playground.add(WoundedPerson(rescue_center=None), ((200.0, 120.0), 0))
        playground.add(MyDrone(), ((-100.0, -80.0), 0))

        after = ExploredMap()
        after.initialize_walls(playground)

        assert np.array_equal(before._map_playground, after._map_playground), (
            "the walls changed after drones and wounded persons were added to "
            "the playground, so a map that initializes its explored map after "
            "placing them is measured differently from one that does not"
        )
    finally:
        playground.close_window()


def test_a_map_needs_no_manual_initialization_to_be_scored():
    """The user-facing point: a map that never calls `initialize_walls` scores."""
    the_map = _make_test_map()
    explored_map = the_map.explored_map

    # MyMap never calls `initialize_walls`.
    for _ in range(10):
        the_map.playground.step()
        explored_map.update_drones(the_map.drones)

    assert explored_map.score() > 0.0


def test_a_map_without_drones_still_reports_its_walls():
    """
    A map with no drone at all.

    The explored map used to find its playground by looking at the drones, so a
    map with none of them was never initialized: `score()` returned 0.0 as if
    nothing had been explored, and -- worse -- `get_pretty_map_explo_lines` and
    `get_pretty_map_explo_zones` returned (0, 0) arrays, which is what the
    launcher feeds to the PDF report. The map now learns its playground when it
    is assigned one, so the walls exist whatever the fleet size.

    No drone means no exploration, so 0.0 is the right score; what must not
    happen is an unmeasured map, whose report images have no size at all.
    """
    the_map = MyDroneFreeMap(drone_type=MyDrone)
    explored_map = the_map.explored_map

    assert the_map.number_drones == 0

    explored_map.update_drones(the_map.drones)

    assert explored_map.initialized is True
    assert explored_map.score() == 0.0

    # The report needs real images even though nothing was explored.
    lines = explored_map.get_pretty_map_explo_lines()
    zones = explored_map.get_pretty_map_explo_zones()
    assert lines.shape == explored_map._map_playground.shape
    assert zones.shape == explored_map._map_playground.shape
    assert lines.shape != (0, 0)


def test_reset_explored_map():
    the_map = _make_test_map()

    explored_map = ExploredMap()
    drones = the_map.drones
    explored_map.initialize_walls(the_map.playground)
    score = explored_map.score()
    assert score == 0.0
    assert explored_map.initialized is True
    assert explored_map._img_playground.shape != (0, 0)
    assert explored_map._map_playground.shape != (0, 0)
    assert explored_map._map_explo_lines.shape != (0, 0)
    assert explored_map._map_explo_zones.shape != (0, 0)

    for _ in range(10):
        the_map.playground.step()
        explored_map.update_drones(drones)
    assert explored_map._explo_pts != {}
    assert explored_map._last_position != {}

    score = explored_map.score()
    assert score > 0.0
    assert explored_map._explo_pts != {}
    assert explored_map._last_position != {}
    assert explored_map._count_explored_pixels != 0

    explored_map.reset()
    score = explored_map.score()
    assert float(score) == 0.0
    assert explored_map._explo_pts == {}
    assert explored_map._last_position == {}
    assert explored_map._count_explored_pixels == 0


def test_texture_deprecation_warning():
    from PIL import Image

    img = Image.new("RGBA", (1, 1))
    t1 = img.transpose(Image.Transpose.TRANSPOSE)
    t2 = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    assert t1.size == (1, 1)
    assert t2.size == (1, 1)
