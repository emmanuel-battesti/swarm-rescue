import math
import random
import time

from spg_overlay.rescue_center import RescueCenter
from spg_overlay.wounded_person import WoundedPerson

from simple_playgrounds.elements.collection.basic import Traversable
from .map_abstract import MapAbstract

from simple_playgrounds.common.position_utils import CoordinateSampler
from simple_playgrounds.playgrounds.layouts import LineRooms


class MyMapRescueWoundedPersons(MapAbstract):

    def __init__(self):
        self.number_drones = 5
        self.time_limit = 100000
        self.number_wounded_persons = 30
        self.max_reward = (self.number_wounded_persons - 1) * 5

        self.drones = []

        # BUILD MAP
        self.size_area = (1500, 700)
        self.playground = None
        self.wounded_persons = list()
        self.build_map()

    def set_drones(self, drones):
        self.drones = drones

        # POSITIONS OF THE DRONES
        self.positions_drones()

    def build_map(self):
        random.seed(time.time())

        center_area = (self.size_area[0] / 2, self.size_area[1] / 2)
        # my_playground = GridRooms(size=size_area, room_layout=(3, 3), random_doorstep_position=False, doorstep_size=90)
        self.playground = LineRooms(size=self.size_area, number_rooms=3, random_doorstep_position=True,
                                    doorstep_size=250)

        rescue_center = RescueCenter(reward=5, size=[90, 90])
        self.playground.add_element(rescue_center, ((50, 50), 0))

        area_all = CoordinateSampler(center=center_area, area_shape='rectangle', size=self.size_area)
        for i in range(self.number_wounded_persons):
            wounded_person = WoundedPerson(graspable=True, rescue_center=rescue_center)
            try:
                self.playground.add_element(wounded_person, area_all, allow_overlapping=True)
                self.wounded_persons.append(wounded_person)
            except:
                print('Failed to place object')

    def positions_drones(self):
        start_area = (150, 100)

        for i in range(0, self.number_drones):
            self.playground.add_agent(self.drones[i], (
                (random.uniform(100, 0), random.uniform(100 + start_area[0], 0 + start_area[1])),
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
