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
from swarm_rescue.simulation.elements.rescue_center import RescueCenter
from swarm_rescue.simulation.elements.return_area import ReturnArea
from swarm_rescue.simulation.elements.sensor_disablers import (ZoneType, NoComZone,
                                                               NoGpsZone, KillZone)
from swarm_rescue.simulation.elements.wounded_person import WoundedPerson
from swarm_rescue.simulation.gui_map.closed_playground import ClosedPlayground
from swarm_rescue.simulation.gui_map.gui_sr import GuiSR
from swarm_rescue.simulation.gui_map.map_abstract import MapAbstract
from swarm_rescue.simulation.reporting.evaluation import ZonesConfig
from swarm_rescue.simulation.utils.misc_data import MiscData

from swarm_rescue.maps.walls_final_2022_23 import add_walls, add_boxes


class MapFinal2022_23(MapAbstract):

    def __init__(self, drone_type: Type[DroneAbstract], zones_config: ZonesConfig = ()):
        super().__init__(drone_type, zones_config)
        self._max_timestep_limit = 7200
        self._max_walltime_limit = 1440  # In seconds

        # PARAMETERS MAP
        self._size_area = (1819, 1350)

        self._return_area = ReturnArea(size=(293, 160))
        self._return_area_pos = ((-6, 217), 0)

        self._rescue_center = RescueCenter(size=(293, 140))
        self._rescue_center_pos = ((-6, 63), 0)

        self._no_com_zone = NoComZone(size=(377, 486))
        self._no_com_zone_pos = ((-697, 54), 0)

        self._no_gps_zone = NoGpsZone(size=(248, 544))
        self._no_gps_zone_pos = ((-282, -377), 0)

        self._kill_zone = KillZone(size=(96, 242))
        self._kill_zone_pos = ((-674, -68), 0)

        self._wounded_persons_pos = \
            [(-200, -200), (-838, 599), (-356, 555), (-304, 555), (38, 575),
             (316, 585), (852, 621), (-552, 453), (640, 215), (-860, 265),
             (-538, 265), (-450, -55), (850, -41), (-550, -365), (-370, -365),
             (840, -385), (840, -625), (320, -495), (-110, -615), (-202, -615),
             (-850, -615), ]
        self._number_wounded_persons = len(self._wounded_persons_pos)
        self._wounded_persons: List[WoundedPerson] = []

        # POSITIONS OF THE DRONES
        self._number_drones = 10
        # They are positioned in a square whose side size depends on the total number of drones.
        start_area_drones = (0, 217)
        nb_per_side = math.ceil(math.sqrt(float(self._number_drones)))
        dist_inter_drone = 40.0
        # print("nb_per_side", nb_per_side)
        # print("dist_inter_drone", dist_inter_drone)
        sx = start_area_drones[0] - (nb_per_side - 1) * 0.5 * dist_inter_drone
        sy = start_area_drones[1] - (nb_per_side - 1) * 0.5 * dist_inter_drone
        # print("sx", sx, "sy", sy)

        self._drones_pos = []
        for i in range(self._number_drones):
            x = sx + (float(i) % nb_per_side) * dist_inter_drone
            y = sy + math.floor(float(i) / nb_per_side) * dist_inter_drone
            angle = random.uniform(-math.pi, math.pi)
            self._drones_pos.append(((x, y), angle))

        self._drones: List[DroneAbstract] = []

        self._playground = ClosedPlayground(size=self._size_area)

        self._playground.add(self._return_area, self._return_area_pos)
        self._playground.add(self._rescue_center, self._rescue_center_pos)

        add_walls(self._playground)
        add_boxes(self._playground)

        self._explored_map.initialize_walls(self._playground)

        # DISABLER ZONES
        # self._kill_zone_pos = ((200, 217), 0)
        # self._playground.add(self._kill_zone, self._kill_zone_pos)

        if ZoneType.NO_COM_ZONE in self._zones_config:
            self._playground.add(self._no_com_zone, self._no_com_zone_pos)

        if ZoneType.NO_GPS_ZONE in self._zones_config:
            self._playground.add(self._no_gps_zone, self._no_gps_zone_pos)

        if ZoneType.KILL_ZONE in self._zones_config:
            self._playground.add(self._kill_zone, self._kill_zone_pos)

        # POSITIONS OF THE WOUNDED PERSONS
        for i in range(self._number_wounded_persons):
            wounded_person = WoundedPerson(rescue_center=self._rescue_center)
            self._wounded_persons.append(wounded_person)
            pos = (self._wounded_persons_pos[i], 0)
            self._playground.add(wounded_person, pos)

        # POSITIONS OF THE DRONES
        misc_data = MiscData(size_area=self._size_area,
                             number_drones=self._number_drones,
                             max_timestep_limit=self._max_timestep_limit,
                             max_walltime_limit=self._max_walltime_limit)
        for i in range(self._number_drones):
            drone = drone_type(identifier=i, misc_data=misc_data)
            self._drones.append(drone)
            self._playground.add(drone, self._drones_pos[i])


def main():
    the_map = MapFinal2022_23(drone_type=DroneMotionless)

    gui = GuiSR(the_map=the_map,
                use_mouse_measure=True,
                )
    gui.run()


if __name__ == '__main__':
    main()
