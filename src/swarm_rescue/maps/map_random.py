import math
import random
import sys
from pathlib import Path
from typing import List, Type

# Insert the parent directory of the current file's directory into sys.path.
# This allows Python to locate modules that are one level above the current
# script, in this case spg_overlay.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from spg.playground import Playground

from spg_overlay.entities.drone_abstract import DroneAbstract
from spg_overlay.entities.drone_motionless import DroneMotionless
from spg_overlay.entities.wounded_person import WoundedPerson
from spg_overlay.gui_map.closed_playground import ClosedPlayground
from spg_overlay.gui_map.gui_sr import GuiSR
from spg_overlay.gui_map.map_abstract import MapAbstract
from spg_overlay.reporting.evaluation import ZonesConfig
from spg_overlay.utils.misc_data import MiscData


class MyMapRandom(MapAbstract):

    def __init__(self, zones_config: ZonesConfig = ()):
        super().__init__(zones_config)
        self._number_drones = 10
        self._max_timestep_limit = 480
        self._max_walltime_limit = 22  # In seconds
        self._size_area = (1500, 700)
        self._wounded_persons: List[WoundedPerson] = []
        self._drones: List[DroneAbstract] = []

    def construct_playground(self, drone_type: Type[DroneAbstract]) -> Playground:
        playground = ClosedPlayground(size=self._size_area)

        self._explored_map.initialize_walls(playground)

        # POSITIONS OF THE DRONES
        misc_data = MiscData(size_area=self._size_area,
                             number_drones=self._number_drones,
                             max_timestep_limit=self._max_timestep_limit,
                             max_walltime_limit=self._max_walltime_limit)
        for i in range(self._number_drones):
            x = random.uniform(-self._size_area[0] / 2, self._size_area[0] / 2)
            y = random.uniform(-self._size_area[1] / 2, self._size_area[1] / 2)
            angle = random.uniform(-math.pi, math.pi)
            drone = drone_type(identifier=i, misc_data=misc_data)
            self._drones.append(drone)
            playground.add(drone, ((x, y), angle))

        return playground


if __name__ == '__main__':
    my_map = MyMapRandom()
    my_playground = my_map.construct_playground(drone_type=DroneMotionless)

    gui = GuiSR(playground=my_playground,
                the_map=my_map,
                use_mouse_measure=True,
                )
    gui.run()
