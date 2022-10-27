import math
import random
from typing import List, Type

from spg.playground import Playground
from spg.utils.definitions import CollisionTypes

from spg_overlay.entities.drone_abstract import DroneAbstract
from spg_overlay.entities.rescue_center import RescueCenter, wounded_rescue_center_collision
from spg_overlay.entities.sensor_disablers import EnvironmentType, NoComZone, NoGpsZone, KillZone, \
    srdisabler_disables_device
from spg_overlay.entities.wounded_person import WoundedPerson
from spg_overlay.gui_map.closed_playground import ClosedPlayground
from spg_overlay.gui_map.map_abstract import MapAbstract
from spg_overlay.utils.misc_data import MiscData

from .walls_complete_map_2 import add_walls, add_boxes


class MyMapComplete02(MapAbstract):
    environment_series = [EnvironmentType.EASY,
                          EnvironmentType.NO_COM_ZONE,
                          EnvironmentType.NO_GPS_ZONE,
                          EnvironmentType.KILL_ZONE]

    def __init__(self, environment_type: EnvironmentType = EnvironmentType.EASY):
        super().__init__(environment_type)
        self._time_step_limit = 1200
        self._real_time_limit = 240  # In seconds

        # PARAMETERS MAP
        self._size_area = (1113, 750)

        self._rescue_center = RescueCenter(size=(210, 90))
        self._rescue_center_pos = ((440, 315), 0)

        self._no_com_zone = NoComZone(size=(405, 208))
        self._no_com_zone_pos = ((-336, 114), 0)

        self._no_gps_zone = NoGpsZone(size=(232, 330))
        self._no_gps_zone_pos = ((-424, 54), 0)

        self._kill_zone = KillZone(size=(80, 80))
        self._kill_zone_pos = ((-56, 45), 0)

        self._wounded_persons_pos = [(-481, 175), (-511, -185), (-261, -175),
                                     (-81, 305), (-61, -175), (189, 315)]
        self._number_wounded_persons = len(self._wounded_persons_pos)
        self._wounded_persons: List[WoundedPerson] = []

        # POSITIONS OF THE DRONES
        self._number_drones = 10
        # They are positioned in a square whose side size depends on the total number of drones.
        start_area_drones = (439.0, 195)
        nb_per_side = math.ceil(math.sqrt(float(self._number_drones)))
        dist_inter_drone = 30.0
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

    def construct_playground(self, drone_type: Type[DroneAbstract]) -> Playground:
        playground = ClosedPlayground(size=self._size_area)

        # RESCUE CENTER
        playground.add_interaction(CollisionTypes.GEM,
                                   CollisionTypes.ACTIVABLE_BY_GEM,
                                   wounded_rescue_center_collision)

        playground.add(self._rescue_center, self._rescue_center_pos)

        add_walls(playground)
        add_boxes(playground)

        self._explored_map.initialize_walls(playground)

        # DISABLER ZONES
        playground.add_interaction(CollisionTypes.DISABLER,
                                   CollisionTypes.DEVICE,
                                   srdisabler_disables_device)

        if self._environment_type == EnvironmentType.NO_COM_ZONE:
            playground.add(self._no_com_zone, self._no_com_zone_pos)

        if self._environment_type == EnvironmentType.NO_GPS_ZONE:
            playground.add(self._no_gps_zone, self._no_gps_zone_pos)

        if self._environment_type == EnvironmentType.KILL_ZONE:
            playground.add(self._kill_zone, self._kill_zone_pos)

        # POSITIONS OF THE WOUNDED PERSONS
        for i in range(self._number_wounded_persons):
            wounded_person = WoundedPerson(rescue_center=self._rescue_center)
            self._wounded_persons.append(wounded_person)
            pos = (self._wounded_persons_pos[i], 0)
            playground.add(wounded_person, pos)

        # POSITIONS OF THE DRONES
        misc_data = MiscData(size_area=self._size_area,
                             number_drones=self._number_drones)
        for i in range(self._number_drones):
            drone = drone_type(identifier=i, misc_data=misc_data)
            self._drones.append(drone)
            playground.add(drone, self._drones_pos[i])

        return playground
