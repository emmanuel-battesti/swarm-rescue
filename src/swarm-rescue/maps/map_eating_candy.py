import math
import random
import time

from .map_abstract import MapAbstract

from simple_playgrounds.common.position_utils import CoordinateSampler
from simple_playgrounds.elements.collection.contact import Candy
from simple_playgrounds.playgrounds.layouts import LineRooms


class MyMapEatingCandy(MapAbstract):

    def __init__(self):
        self.number_drones = 20
        self.time_limit = 10000
        self.number_candies = 400
        self.max_reward = self.number_candies * 5 * 95 / 100

        self.drones = []

        # BUILD MAP
        self.size_area = (1500, 700)
        self.playground = self.build_map()

    def set_drones(self, drones):
        self.drones = drones

        # POSITIONS OF THE DRONES
        for i in range(0, self.number_drones):
            self.playground.add_agent(self.drones[i], (
                (random.uniform(0, self.size_area[0]), random.uniform(0, self.size_area[1])),
                random.uniform(-math.pi, math.pi)))

    def build_map(self):
        random.seed(time.time())

        center_area = (self.size_area[0] / 2, self.size_area[1] / 2)
        # my_playground = GridRooms(size=size_area, room_layout=(3, 3), random_doorstep_position=False, doorstep_size=90)
        playground = LineRooms(size=self.size_area, number_rooms=3, random_doorstep_position=True,
                               doorstep_size=250)

        area_all = CoordinateSampler(center=center_area, area_shape='rectangle', size=self.size_area)
        for i in range(self.number_candies):
            candy = Candy()
            try:
                playground.add_element(candy, area_all, allow_overlapping=True)
            except:
                print('Failed to place object')

        return playground
