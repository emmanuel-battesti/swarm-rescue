import math
import random
from typing import List, Type

from spg.playground import Playground

from spg_overlay.entities.drone_abstract import DroneAbstract
from spg_overlay.entities.wounded_person import WoundedPerson
from spg_overlay.gui_map.closed_playground import ClosedPlayground
from spg_overlay.gui_map.map_abstract import MapAbstract
from spg_overlay.reporting.evaluation import ZonesConfig


class MyMapRandom(MapAbstract):

    def __init__(self, zones_config: ZonesConfig = ()):
        super().__init__(zones_config)
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
