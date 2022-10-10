import math
import random

from spg.utils.definitions import CollisionTypes

from spg_overlay.gui_map.closed_playground import ClosedPlayground
from spg_overlay.entities.rescue_center import RescueCenter, wounded_rescue_center_collision
from spg_overlay.entities.sensor_disablers import EnvironmentType, NoComZone, NoGpsZone, KillZone, srdisabler_disables_device
from spg_overlay.entities.wounded_person import WoundedPerson
from spg_overlay.gui_map.map_abstract import MapAbstract

from .walls_complete_map_1 import add_walls, add_boxes


class MyMapComplete01(MapAbstract):
    environment_series = [EnvironmentType.EASY,
                          EnvironmentType.NO_COM_ZONE,
                          EnvironmentType.NO_GPS_ZONE,
                          EnvironmentType.KILL_ZONE]

    def __init__(self, environment_type: EnvironmentType = EnvironmentType.EASY):
        super().__init__(environment_type)
        self._number_drones = 10
        self._time_step_limit = 1200
        self._real_time_limit = 240  # In seconds
        self._number_wounded_persons = 0  # it will be filled in the function construct_playground()
        self._size_area = (1110, 750)
        self._wounded_persons = []

    def construct_playground(self):
        playground = ClosedPlayground(size=self._size_area)

        # RESCUE CENTER
        playground.add_interaction(CollisionTypes.GEM,
                                   CollisionTypes.ACTIVABLE_BY_GEM,
                                   wounded_rescue_center_collision)
        rescue_center = RescueCenter(size=(90, 170))
        playground.add(rescue_center, ((-505, -285), 0))

        add_walls(playground)
        add_boxes(playground)

        self._explored_map.initialize_walls(playground)

        # DISABLER ZONES
        playground.add_interaction(CollisionTypes.DISABLER,
                                   CollisionTypes.DEVICE,
                                   srdisabler_disables_device)

        if self._environment_type == EnvironmentType.NO_COM_ZONE:
            no_com_zone = NoComZone(size=(270, 500))
            playground.add(no_com_zone, ((-220, 46), 0))

        # no_com_zone_test = NoComZone(size=(300, 300))
        # playground.add(no_com_zone_test, ((900, 554), 0))

        if self._environment_type == EnvironmentType.NO_GPS_ZONE:
            no_gps_zone = NoGpsZone(size=(380, 252))
            playground.add(no_gps_zone, ((-360, 21), 0))

        # no_gps_zone_test = NoGpsZone(size=(400, 400))
        # playground.add(no_gps_zone_test, ((900, 554), 0))

        if self._environment_type == EnvironmentType.KILL_ZONE:
            kill_zone = KillZone(size=(55, 55))
            playground.add(kill_zone, ((-387, 75), 0))

        # sensor_disabler_test = KillZone(size=(300, 300))
        # playground.add(sensor_disabler_test, ((900, 554), 0))

        # POSITIONS OF THE WOUNDED PERSONS
        wounded_persons_pos = [(-516, 335), (-466, 335), (-226, 335),
                               (-481, 75), (-61, 325), (-311, 100),
                               (-171, -145), (-100, -155), (524, 325)]
        self._number_wounded_persons = len(wounded_persons_pos)

        for i in range(self._number_wounded_persons):
            wounded_person = WoundedPerson(rescue_center=rescue_center)
            pos = (wounded_persons_pos[i], 0)
            playground.add(wounded_person, pos)
            self._wounded_persons.append(wounded_person)

        # POSITIONS OF THE DRONES
        # They are positioned in a square whose side size depends on the total number of drones.
        start_area_drones = (-375, -300)
        nb_per_side = math.ceil(math.sqrt(float(self._number_drones)))
        dist_inter_drone = 30.0
        # print("nb_per_side", nb_per_side)
        # print("dist_inter_drone", dist_inter_drone)
        sx = start_area_drones[0] - (nb_per_side - 1) * 0.5 * dist_inter_drone
        sy = start_area_drones[1] - (nb_per_side - 1) * 0.5 * dist_inter_drone
        # print("sx", sx, "sy", sy)

        for i in range(self._number_drones):
            x = sx + (float(i) % nb_per_side) * dist_inter_drone
            y = sy + math.floor(float(i) / nb_per_side) * dist_inter_drone
            angle = random.uniform(-math.pi, math.pi)
            playground.add(self._drones[i], ((x, y), angle))

        return playground
