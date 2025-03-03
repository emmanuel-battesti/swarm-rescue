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
from spg_overlay.entities.rescue_center import RescueCenter
from spg_overlay.entities.return_area import ReturnArea
from spg_overlay.entities.sensor_disablers import ZoneType, NoComZone, NoGpsZone, KillZone
from spg_overlay.entities.wounded_person import WoundedPerson
from spg_overlay.gui_map.closed_playground import ClosedPlayground
from spg_overlay.gui_map.gui_sr import GuiSR
from spg_overlay.gui_map.map_abstract import MapAbstract
from spg_overlay.reporting.evaluation import ZonesConfig
from spg_overlay.utils.misc_data import MiscData
from spg_overlay.utils.pose import Pose

from map_editor.walls_box import add_walls, add_boxes, dimensions


class MyMapbox(MapAbstract):

    def __init__(self, zones_config: ZonesConfig = ()):
        super().__init__(zones_config)
        self._max_timestep_limit = 2000
        self._max_walltime_limit = 120

        # PARAMETERS MAP
        self._size_area = dimensions()

        self._rescue_center = RescueCenter(size=(127, 52))
        self._rescue_center_pos = ((-320, 256), 0)

        self._return_area = ReturnArea(size=(197, 92))
        self._return_area_pos = ((-296, 248), 0)

        self._wounded_persons_pos = [(374, 290), (383, -282), (-309, -230)]
        self._number_wounded_persons = len(self._wounded_persons_pos)
        self._wounded_persons: List[WoundedPerson] = []

        self._drones_pos = [(pos, random.uniform(-math.pi, math.pi)) for pos in [(-320, 215)]]
        self._number_drones = len(self._drones_pos)
        self._drones: List[DroneAbstract] = []

    def construct_playground(self, drone_type: Type[DroneAbstract]) -> Playground:
        playground = ClosedPlayground(size=self._size_area)

        playground.add(self._return_area, self._return_area_pos)
        playground.add(self._rescue_center, self._rescue_center_pos)

        add_walls(playground)
        add_boxes(playground)

        self._explored_map.initialize_walls(playground)

        # DISABLER ZONES
        if ZoneType.NO_COM_ZONE in self._zones_config:
            playground.add(self._no_com_zone, self._no_com_zone_pos)

        if ZoneType.NO_GPS_ZONE in self._zones_config:
            playground.add(self._no_gps_zone, self._no_gps_zone_pos)

        if ZoneType.KILL_ZONE in self._zones_config:
            playground.add(self._kill_zone, self._kill_zone_pos)

        # POSITIONS OF THE WOUNDED PERSONS
        for i in range(self._number_wounded_persons):
            wounded_person = WoundedPerson(rescue_center=self._rescue_center)
            self._wounded_persons.append(wounded_person)
            pos = (self._wounded_persons_pos[i], 0)
            playground.add(wounded_person, pos)

        # POSITIONS OF THE DRONES
        misc_data = MiscData(size_area=self._size_area,
                             number_drones=self._number_drones,
                             max_timestep_limit=self._max_timestep_limit,
                             max_walltime_limit=self._max_walltime_limit)
        for i in range(self._number_drones):
            drone = drone_type(identifier=i, misc_data=misc_data)
            self._drones.append(drone)
            playground.add(drone, self._drones_pos[i])

        return playground


if __name__ == '__main__':
        my_map = MyMapbox()
        my_playground = my_map.construct_playground(drone_type=DroneMotionless)

        gui = GuiSR(playground=my_playground, the_map=my_map, use_mouse_measure=True)
        gui.run()