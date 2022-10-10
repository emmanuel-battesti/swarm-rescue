import math
import random

from spg.utils.definitions import CollisionTypes

from spg_overlay.gui_map.closed_playground import ClosedPlayground
from spg_overlay.entities.rescue_center import RescueCenter, wounded_rescue_center_collision
from spg_overlay.entities.sensor_disablers import EnvironmentType, NoComZone, NoGpsZone, KillZone, srdisabler_disables_device
from spg_overlay.entities.wounded_person import WoundedPerson
from spg_overlay.gui_map.map_abstract import MapAbstract

from .walls_complete_map_2 import add_walls, add_boxes


class MyMapComplete02(MapAbstract):
    environment_series = [EnvironmentType.EASY,
                          EnvironmentType.NO_COM_ZONE,
                          EnvironmentType.NO_GPS_ZONE,
                          EnvironmentType.KILL_ZONE]

    def __init__(self, environment_type: EnvironmentType = EnvironmentType.EASY):
        super().__init__(environment_type)
        self._number_drones = 10
        self._time_step_limit = 1200
        self._real_time_limit = 240  # In seconds
        self._number_wounded_persons = 0  # it will be filled in the function build_map()

        # BUILD MAP
        self._size_area = (1113, 750)
        self._wounded_persons = list()

    def construct_playground(self):
        playground = ClosedPlayground(size=self._size_area)

        # RESCUE CENTER
        playground.add_interaction(CollisionTypes.GEM,
                                   CollisionTypes.ACTIVABLE_BY_GEM,
                                   wounded_rescue_center_collision)
        rescue_center = RescueCenter(size=(210, 90))
        playground.add(rescue_center, ((440, 315), 0))

        add_walls(playground)
        add_boxes(playground)

        self._explored_map.initialize_walls(playground)

        # DISABLER ZONES
        playground.add_interaction(CollisionTypes.DISABLER,
                                   CollisionTypes.DEVICE,
                                   srdisabler_disables_device)

        if self._environment_type == EnvironmentType.NO_COM_ZONE:
            no_com_zone = NoComZone(size=(405, 208))
            playground.add(no_com_zone, ((-336, 114), 0))

        # no_com_zone_test = NoComZone(size=(300, 300))
        # playground.add(no_com_zone_test, ((900, 554), 0))

        if self._environment_type == EnvironmentType.NO_GPS_ZONE:
            no_gps_zone = NoGpsZone(size=(232, 330))
            playground.add(no_gps_zone, ((-424, 54), 0))

        # no_gps_zone_test = NoGpsZone(size=(400, 400))
        # playground.add(no_gps_zone_test, ((900, 554), 0))

        if self._environment_type == EnvironmentType.KILL_ZONE:
            kill_zone = KillZone(size=(80, 80))
            playground.add(kill_zone, ((-56, 45), 0))

        # sensor_disabler_test = KillZone(size=(300, 300))
        # playground.add(sensor_disabler_test, ((900, 554), 0))

        # POSITIONS OF THE WOUNDED PERSONS
        wounded_persons_pos = [(-481, 175), (-511, -185), (-261, -175),
                               (-81, 305), (-61, -175), (189, 315)]
        self._number_wounded_persons = len(wounded_persons_pos)

        for i in range(self._number_wounded_persons):
            wounded_person = WoundedPerson(rescue_center=rescue_center)
            pos = (wounded_persons_pos[i], 0)
            playground.add(wounded_person, pos)
            self._wounded_persons.append(wounded_person)

        # POSITIONS OF THE DRONES
        # They are positioned in a square whose side size depends on the total number of drones.
        start_area_drones = (439.0, 195)
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
            playground.add(self._drones[i], ((x, y), random.uniform(-math.pi, math.pi)))

        return playground

    @property
    def number_drones(self):
        return self._number_drones

    @property
    def time_step_limit(self):
        return self._time_step_limit
