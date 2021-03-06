import math
import random
import time

from spg_overlay.map_abstract import MapAbstract

from simple_playgrounds.playground import LineRooms

from spg_overlay.sensor_disablers import EnvironmentType


class MyMapRandom(MapAbstract):
    environment_series = [EnvironmentType.EASY, EnvironmentType.NO_COM_ZONE]

    def __init__(self, environment_type: EnvironmentType = EnvironmentType.EASY):
        super().__init__(environment_type)
        self.number_drones = 20
        self.time_step_limit = 480
        self.real_time_limit = 22  # In seconds

        self.drones = []

        # BUILD MAP
        self.size_area = (1500, 700)
        self.playground = None
        self.build_map()

    def set_drones(self, drones):
        self.drones = drones

        # POSITIONS OF THE DRONES
        for i in range(0, self.number_drones):
            self.playground.add_agent(self.drones[i], (
                (random.uniform(0, self.size_area[0]), random.uniform(0, self.size_area[1])),
                random.uniform(-math.pi, math.pi)))

    def build_map(self):
        random.seed(time.time())
        self.playground = LineRooms(size=self.size_area, number_rooms=3, random_doorstep_position=True,
                                    doorstep_size=250, wall_type='light')
        self.explored_map.initialize_walls(self.playground)
