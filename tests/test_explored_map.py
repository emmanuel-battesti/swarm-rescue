import pathlib
import sys
from typing import List, Type

# Insert the 'src' directory, located two levels up from the current script,
# into sys.path. This ensures Python can find project-specific modules
# (e.g., 'swarm_rescue') when the script is run from a subfolder like 'tests/'.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from swarm_rescue.simulation.drone.drone_abstract import DroneAbstract
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


def test_initialize_explored_map_with_default_values():
    the_map = MyMap(drone_type=MyDrone)
    explored_map = ExploredMap()
    assert explored_map.initialized is False
    assert explored_map._img_playground.shape == (0, 0)
    assert explored_map._map_playground.shape == (0, 0)
    assert explored_map._map_explo_lines.shape == (0, 0)
    assert explored_map._map_explo_zones.shape == (0, 0)
    assert explored_map._explo_pts == {}
    assert explored_map._last_position == {}
    assert explored_map._count_explored_pixels == 0

    drones = the_map.playground.agents
    explored_map.update_drones(drones)
    assert explored_map.initialized is False


def test_reset_explored_map():
    the_map = MyMap(drone_type=MyDrone)

    explored_map = ExploredMap()
    drones = the_map.drones
    explored_map.initialize_walls(the_map.playground)
    score = explored_map.score()
    assert score == 0
    assert explored_map.initialized == True
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
    assert score > 0
    assert explored_map._explo_pts != {}
    assert explored_map._last_position != {}
    assert explored_map._count_explored_pixels != 0

    explored_map.reset()
    score = explored_map.score()
    assert score == 0
    assert explored_map._explo_pts == {}
    assert explored_map._last_position == {}
    assert explored_map._count_explored_pixels == 0
