import math
import pathlib
import random
import sys
from typing import List, Type

# Insert the parent directory of the current file's directory into sys.path.
# This allows Python to locate modules that are one level above the current
# script, in this case simulation.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from swarm_rescue.simulation.drone.drone_abstract import DroneAbstract
from swarm_rescue.simulation.drone.drone_motionless import DroneMotionless
from swarm_rescue.simulation.elements.wounded_person import WoundedPerson
from swarm_rescue.simulation.gui_map.closed_playground import ClosedPlayground
from swarm_rescue.simulation.gui_map.gui_sr import GuiSR
from swarm_rescue.simulation.gui_map.map_abstract import MapAbstract
from swarm_rescue.simulation.reporting.evaluation import ZonesConfig
from swarm_rescue.simulation.utils.misc_data import MiscData


class MapRandom(MapAbstract):

    def __init__(self, drone_type: Type[DroneAbstract], zones_config: ZonesConfig = ()):
        super().__init__(drone_type, zones_config)
        self._number_drones = 10
        self._max_timestep_limit = 220
        self._max_walltime_limit = 22  # In seconds
        self._size_area = (1500, 700)
        self._wounded_persons: List[WoundedPerson] = []
        self._drones: List[DroneAbstract] = []

        self._playground = ClosedPlayground(size=self._size_area)

        self._explored_map.initialize_walls(self._playground)

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
            self._playground.add(drone, ((x, y), angle))


if __name__ == '__main__':
    the_map = MapRandom(drone_type=DroneMotionless)

    gui = GuiSR(the_map=the_map,
                use_mouse_measure=True,
                )
    gui.run()
