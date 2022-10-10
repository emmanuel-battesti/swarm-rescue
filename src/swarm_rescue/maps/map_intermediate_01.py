import math
import random

from spg.utils.definitions import CollisionTypes

from spg_overlay.gui_map.closed_playground import ClosedPlayground
from spg_overlay.entities.rescue_center import RescueCenter, wounded_rescue_center_collision
from spg_overlay.entities.sensor_disablers import EnvironmentType, NoGpsZone, srdisabler_disables_device
from spg_overlay.entities.wounded_person import WoundedPerson
from spg_overlay.gui_map.map_abstract import MapAbstract

from .walls_intermediate_map_1 import add_walls, add_boxes


class MyMapIntermediate01(MapAbstract):
    environment_series = [EnvironmentType.EASY,
                          EnvironmentType.NO_GPS_ZONE]

    def __init__(self, environment_type: EnvironmentType = EnvironmentType.EASY):
        super().__init__(environment_type)
        self._number_drones = 1
        self._time_step_limit = 36000
        self._real_time_limit = 600  # In seconds
        self._number_wounded_persons = 0  # it will be filled in the function build_map()

        # BUILD MAP
        self._size_area = (800, 500)
        self._wounded_persons = list()

    def construct_playground(self):
        playground = ClosedPlayground(size=self._size_area)

        # RESCUE CENTER
        playground.add_interaction(CollisionTypes.GEM,
                                   CollisionTypes.ACTIVABLE_BY_GEM,
                                   wounded_rescue_center_collision)
        rescue_center = RescueCenter(size=(200, 80))
        playground.add(rescue_center, ((295, 205), 0))

        add_walls(playground)
        add_boxes(playground)

        self._explored_map.initialize_walls(playground)

        # DISABLER ZONES
        playground.add_interaction(CollisionTypes.DISABLER,
                                   CollisionTypes.DEVICE,
                                   srdisabler_disables_device)

        if self._environment_type == EnvironmentType.NO_GPS_ZONE:
            no_gps_zone = NoGpsZone(size=(400, 500))
            playground.add(no_gps_zone, ((-190, 0), 0))

        # POSITIONS OF THE WOUNDED PERSONS
        wounded_persons_pos = [(-310, -180)]
        self._number_wounded_persons = len(wounded_persons_pos)

        for i in range(self._number_wounded_persons):
            wounded_person = WoundedPerson(rescue_center=rescue_center)
            pos = (wounded_persons_pos[i], 0)
            playground.add(wounded_person, pos)
            self._wounded_persons.append(wounded_person)

        # POSITIONS OF THE DRONES
        orient = random.uniform(-math.pi, math.pi)
        playground.add(self._drones[0], ((295, 118), orient))

        return playground

    @property
    def number_drones(self):
        return self._number_drones

    @property
    def time_step_limit(self):
        return self._time_step_limit
