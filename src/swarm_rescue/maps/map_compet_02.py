import math
import random
import time

from spg_overlay.kill_zone import KillZone
from spg_overlay.rescue_center import RescueCenter
from spg_overlay.sensor_disablers import NoComZone, NoGpsZone, EnvironmentType
from spg_overlay.wounded_person import WoundedPerson
from spg_overlay.map_abstract import MapAbstract

from simple_playgrounds.playground import SingleRoom

from .walls_02 import add_walls, add_boxes


class MyMapCompet02(MapAbstract):
    environment_series = [EnvironmentType.EASY, EnvironmentType.NO_COM_ZONE, EnvironmentType.NO_GPS_ZONE,
                          EnvironmentType.KILL_ZONE]

    def __init__(self, environment_type: EnvironmentType = EnvironmentType.EASY):
        super().__init__(environment_type)
        self.number_drones = 10
        self.time_step_limit = 1200
        self.real_time_limit = 240  # In seconds
        self.number_wounded_persons = 0  # it will be filled in the function build_map()

        self.drones = []

        # BUILD MAP
        self.size_area = (1122, 750)
        self.playground = None
        self.wounded_persons = list()
        self._build_map()

    def set_drones(self, drones):
        # BUILD DRONES
        self.drones = drones

        # POSITIONS OF THE DRONES
        self.positions_drones()

    def _build_map(self):
        random.seed(time.time())

        self.playground = SingleRoom(size=self.size_area, wall_type='light')

        # RESCUE CENTER
        rescue_center = RescueCenter(size=[210, 90])
        self.playground.add_element(rescue_center, ((995, 60), 0))

        add_walls(self.playground)
        add_boxes(self.playground)

        self.explored_map.initialize_walls(self.playground)

        if self.environment_type == EnvironmentType.NO_COM_ZONE:
            no_com_zone = NoComZone(size=(405, 208))
            self.playground.add_element(no_com_zone, ((220, 489), 0))

        # no_com_zone_test = NoComZone(size=(300, 300))
        # self.playground.add_element(no_com_zone_test, ((900, 554), 0))

        if self.environment_type == EnvironmentType.NO_GPS_ZONE:
            no_gps_zone = NoGpsZone(size=(232, 330))
            self.playground.add_element(no_gps_zone, ((132, 429), 0))

        # no_gps_zone_test = NoGpsZone(size=(400, 400))
        # self.playground.add_element(no_gps_zone_test, ((900, 554), 0))

        if self.environment_type == EnvironmentType.KILL_ZONE:
            kill_zone = KillZone(size=(80, 80))
            self.playground.add_element(kill_zone, ((500, 420), 0))

        # sensor_disabler_test = KillZone(size=(300, 300))
        # self.playground.add_element(sensor_disabler_test, ((900, 554), 0))

        wounded_persons_pos = [(80, 200), (50, 560), (300, 550),
                               (480, 70), (500, 550), (750, 60)]
        self.number_wounded_persons = len(wounded_persons_pos)

        for i in range(self.number_wounded_persons):
            wounded_person = WoundedPerson(graspable=True, rescue_center=rescue_center)
            try:
                pos = (wounded_persons_pos[i], 0)
                self.playground.add_element(wounded_person, pos)
                self.wounded_persons.append(wounded_person)
            except:
                print('Failed to place object')

    def positions_drones(self):
        """
        The drones are positioned in a square whose side size depends on the total number of drones.
        """
        start_area = (1000.0, 180.0)
        nb_per_side = math.ceil(math.sqrt(float(self.number_drones)))
        dist_inter_drone = 30.0
        # print("nb_per_side", nb_per_side)
        # print("dist_inter_drone", dist_inter_drone)
        sx = start_area[0] - (nb_per_side - 1) * 0.5 * dist_inter_drone
        sy = start_area[1] - (nb_per_side - 1) * 0.5 * dist_inter_drone
        # print("sx", sx, "sy", sy)

        for i in range(0, self.number_drones):
            x = sx + (float(i) % nb_per_side) * dist_inter_drone
            y = sy + math.floor(float(i) / nb_per_side) * dist_inter_drone
            self.playground.add_agent(self.drones[i], ((x, y), random.uniform(-math.pi, math.pi)))
