import math
import random

from maps.map_abstract import MapAbstract

from simple_playgrounds.playgrounds.layouts import LineRooms


class MyMapFish(MapAbstract):

    def __init__(self):
        self.number_drones = 20
        self.time_limit = 10000
        self.max_reward = 950

        self.drones = []

        # BUILD MAP
        self.size_area = (800, 800)
        self.playground = None
        self.build_map()

    def set_drones(self, drones):
        self.drones = drones

        # POSITIONS OF THE DRONES
        for i in range(0, self.number_drones):
            self.playground.add_agent(self.drones[i],
                                      ((random.uniform(0, self.size_area[0]), random.uniform(0, self.size_area[1])),
                                       random.uniform(-math.pi, math.pi)))

    def build_map(self):
        self.playground = LineRooms(size=self.size_area, number_rooms=1, random_doorstep_position=True,
                                    doorstep_size=150)
