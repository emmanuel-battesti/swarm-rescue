from typing import List, Type

from spg.playground import Playground

from spg_overlay.entities.drone_abstract import DroneAbstract
from spg_overlay.gui_map.closed_playground import ClosedPlayground
from spg_overlay.gui_map.map_abstract import MapAbstract
from spg_overlay.reporting.explored_map import ExploredMap
from spg_overlay.utils.misc_data import MiscData


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
    def __init__(self):
        super().__init__()

        # PARAMETERS MAP
        self._size_area = (200, 200)

        # POSITIONS OF THE DRONES
        self._number_drones = 1
        self._drones_pos = [((10, 10), 0)]
        self._drones = []

        self._drones: List[DroneAbstract] = []

    def construct_playground(self, drone_type: Type[DroneAbstract]):
        playground = ClosedPlayground(size=self._size_area)

        # POSITIONS OF THE DRONES
        misc_data = MiscData(size_area=self._size_area,
                             number_drones=self._number_drones)
        for i in range(self._number_drones):
            drone = drone_type(identifier=i, misc_data=misc_data)
            self._drones.append(drone)
            playground.add(drone, self._drones_pos[i])

        return playground


def test_initialize_explored_map_with_default_values():
    my_map = MyMap()
    playground = my_map.construct_playground(drone_type=MyDrone)
    explored_map = ExploredMap()
    assert explored_map.initialized == False
    assert explored_map._img_playground.shape == (0, 0)
    assert explored_map._map_playground.shape == (0, 0)
    assert explored_map._map_explo_lines.shape == (0, 0)
    assert explored_map._map_explo_zones.shape == (0, 0)
    assert explored_map._explo_pts == {}
    assert explored_map._last_position == {}
    assert explored_map._count_pixel_walls == 0
    # assert explored_map._count_pixel_explored == 0
    assert explored_map._count_pixel_total == 0

    drones = [playground.agents]
    explored_map.update_drones(drones)
    assert explored_map.initialized == False


def test_reset_explored_map():
    my_map = MyMap()
    playground = my_map.construct_playground(drone_type=MyDrone)

    for _ in range(1):
        playground.step()

    explored_map = ExploredMap()
    drones = my_map.drones
    explored_map.initialize_walls(playground)
    explored_map.update_drones(drones)
    explored_map.score()
    assert explored_map._explo_pts != {}
    assert explored_map._last_position != {}
    # assert explored_map._count_pixel_explored != 0
    assert explored_map._count_pixel_total != 0

    explored_map.reset()
    assert explored_map._explo_pts == {}
    assert explored_map._last_position == {}
    assert explored_map._count_pixel_explored == 0
    assert explored_map._count_pixel_total == 0
