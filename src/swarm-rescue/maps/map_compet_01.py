import math
import random
import time

from spg_overlay.rescue_center import RescueCenter
from spg_overlay.wounded_person import WoundedPerson
from simple_playgrounds.elements.collection.basic import Traversable
from .map_abstract import MapAbstract

from simple_playgrounds.common.position_utils import CoordinateSampler
from simple_playgrounds.playgrounds.layouts import SingleRoom

# If we want to use another version of our drone, just change MyDrone01 by MyDrone02 for example
from .walls_01 import add_walls


class MyMapCompet01(MapAbstract):

    def __init__(self):
        self.number_drones = 10
        self.time_limit = 100000
        self.number_wounded_persons = 30
        self.max_reward = (self.number_wounded_persons - 1) * 5

        self.drones = []

        # BUILD MAP
        self.size_area = (1112, 750)
        self.playground = None
        self.wounded_persons = list()
        self.build_map()

    def set_drones(self, drones):
        # BUILD DRONES
        self.drones = drones

        # POSITIONS OF THE DRONES
        self.positions_drones()

    def build_map(self):
        random.seed(time.time())

        center_area = (self.size_area[0] / 2, self.size_area[1] / 2)
        self.playground = SingleRoom(size=self.size_area)

        # RESCUE CENTER
        rescue_center = RescueCenter(reward=5, size=[90, 170])
        self.playground.add_element(rescue_center, ((50, 660), 0))

        add_walls(self.playground)

        area_all = CoordinateSampler(center=center_area, area_shape='rectangle', size=self.size_area)
        for i in range(self.number_wounded_persons):
            wounded_person = WoundedPerson(graspable=True, rescue_center=rescue_center)
            try:
                self.playground.add_element(wounded_person, area_all, allow_overlapping=True)
                self.wounded_persons.append(wounded_person)
            except:
                print('Failed to place object')

    def positions_drones(self):
        start_area = (300, 660)

        for i in range(0, self.number_drones):
            self.playground.add_agent(self.drones[i], (
                (random.uniform(start_area[0] - 200, start_area[0] + 200),
                 random.uniform(start_area[1] - 70, start_area[1] + 70)),
                random.uniform(-math.pi, math.pi)))

    def draw_stuff(self):
        circle_cli = Traversable(config_key='circle',
                                 movable=False,
                                 texture=[150, 100, 150],
                                 radius=10)

        drone = self.drones[0]

        # print(drone.all_positions)
        for pt in drone.all_positions:
            self.playground.add_element(circle_cli, initial_coordinates=[[pt[0], pt[1]], 0])

        # self.playground.add_element(circle_cli, (
        #     (random.uniform(0, self.playground.size[0]), random.uniform(0, self.playground.size[1])), 1.8))
