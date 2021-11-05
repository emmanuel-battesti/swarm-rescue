import math
import random
import time

from spg_overlay.rescue_center import RescueCenter
from spg_overlay.wounded_person import WoundedPerson
from spg_overlay.map_abstract import MapAbstract

from simple_playgrounds.playground import SingleRoom

from .walls_01 import add_walls, add_boxes


class MyMapCompet01(MapAbstract):

    def __init__(self):
        super().__init__()
        self.number_drones = 10
        self.time_step_limit = 100000
        self.real_time_limit = 3600  # In seconds
        self.number_wounded_persons = 0  # it will be filled in the function build_map()

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

        self.playground = SingleRoom(size=self.size_area, wall_type='light')

        # RESCUE CENTER
        rescue_center = RescueCenter(size=[90, 170])
        self.playground.add_element(rescue_center, ((50, 660), 0))

        add_walls(self.playground)
        add_boxes(self.playground)

        self.explored_map.initialize_walls(self.playground)

        wounded_persons_pos = [(40, 40), (90, 40), (330, 40),
                               (35, 300), (495, 50), (245, 275),
                               (385, 520), (460, 530), (1080, 50)]
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
        start_area = (300, 660)

        for i in range(0, self.number_drones):
            self.playground.add_agent(self.drones[i], (
                (random.uniform(start_area[0] - 200, start_area[0] + 200),
                 random.uniform(start_area[1] - 70, start_area[1] + 70)),
                random.uniform(-math.pi, math.pi)))
