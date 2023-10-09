import math
import random
from typing import List, Type

from spg.playground import Playground
from spg.utils.definitions import CollisionTypes

from spg_overlay.entities.drone_abstract import DroneAbstract
from spg_overlay.entities.rescue_center import RescueCenter, wounded_rescue_center_collision
from spg_overlay.entities.sensor_disablers import ZoneType, NoComZone, KillZone, srdisabler_disables_device
from spg_overlay.entities.wounded_person import WoundedPerson
from spg_overlay.gui_map.closed_playground import ClosedPlayground
from spg_overlay.gui_map.map_abstract import MapAbstract
from spg_overlay.reporting.evaluation import ZonesConfig
from spg_overlay.utils.misc_data import MiscData


class MyMapIntermediate02(MapAbstract):

    def __init__(self, zones_config: ZonesConfig = ()):
        super().__init__(zones_config)
        self._time_step_limit = 3000
        self._real_time_limit = 120

        # PARAMETERS MAP
        self._size_area = (1200, 500)

        self._rescue_center = RescueCenter(size=(200, 80))
        self._rescue_center_pos = ((496, 206), 0)

        self._no_com_zone = NoComZone(size=(330, 500))
        self._no_com_zone_pos = ((-159, 0), 0)

        self._kill_zone = KillZone(size=(68, 360))
        self._kill_zone_pos = ((-484, 0), 0)

        self._wounded_persons_pos = [(-555, 188), (-420, 188), (-285, 188), (-150, 188), (-15, 188), (120, 188),
                                     (255, 188), (-555, 63), (-420, 63), (-285, 63), (-150, 63), (-15, 63), (120, 63),
                                     (255, 63), (-555, -62), (-420, -62), (-285, -62), (-150, -62), (-15, -62),
                                     (120, -62), (255, -62), (-555, -187), (-420, -187), (-285, -187), (-150, -187),
                                     (-15, -187), (120, -187), (255, -187)]
        self._number_wounded_persons = len(self._wounded_persons_pos)
        self._wounded_persons: List[WoundedPerson] = []

        self._number_drones = 10
        # They are positioned in a square whose side size depends on the total number of drones.
        start_area_drones = (496, 100)
        nb_per_side = math.ceil(math.sqrt(float(self._number_drones)))
        dist_inter_drone = 50.0
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

        self._explored_map.initialize_walls(playground)

        # DISABLER ZONES
        playground.add_interaction(CollisionTypes.DISABLER,
                                   CollisionTypes.DEVICE,
                                   srdisabler_disables_device)

        if ZoneType.NO_COM_ZONE in self._zones_config:
            playground.add(self._no_com_zone, self._no_com_zone_pos)

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
                             number_drones=self._number_drones)
        for i in range(self._number_drones):
            drone = drone_type(identifier=i, misc_data=misc_data)
            self._drones.append(drone)
            playground.add(drone, self._drones_pos[i])

        return playground
