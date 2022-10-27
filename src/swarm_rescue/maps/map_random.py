import math
import random
from typing import List, Type

from spg.playground import Playground

from spg_overlay.entities.drone_abstract import DroneAbstract
from spg_overlay.entities.wounded_person import WoundedPerson
from spg_overlay.gui_map.closed_playground import ClosedPlayground
from spg_overlay.entities.sensor_disablers import EnvironmentType
from spg_overlay.gui_map.map_abstract import MapAbstract


class MyMapRandom(MapAbstract):
    environment_series = [EnvironmentType.EASY, EnvironmentType.NO_COM_ZONE]

    def __init__(self, environment_type: EnvironmentType = EnvironmentType.EASY):
        super().__init__(environment_type)
        self._number_drones = 10
        self._time_step_limit = 480
        self._real_time_limit = 22  # In seconds
        self._size_area = (1500, 700)
        self._wounded_persons: List[WoundedPerson] = []

    def construct_playground(self, drone_type: Type[DroneAbstract]) -> Playground:
        playground = ClosedPlayground(size=self._size_area)

        self._explored_map.initialize_walls(playground)

        # POSITIONS OF THE DRONES
        for i in range(self._number_drones):
            x = random.uniform(-self._size_area[0]/2, self._size_area[0]/2)
            y = random.uniform(-self._size_area[1]/2, self._size_area[1]/2)
            angle = random.uniform(-math.pi, math.pi)
            playground.add(self._drones[i], ((x, y), angle))

        return playground
