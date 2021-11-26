"""
This program can be launched directly.
To move the drone, you have to click on the map, then use the arrows on the keyboard
"""

import math
import os
import sys

# This line add, to sys.path, the path to parent path of this file
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from spg_overlay.misc_data import MiscData
from spg_overlay.drone_abstract import DroneAbstract

from simple_playgrounds.agent.controllers import Keyboard
from simple_playgrounds.playground import SingleRoom
from simple_playgrounds.engine import Engine
from simple_playgrounds.element.elements.basic import Physical

# to display the sensors
import cv2


class MyDrone(DroneAbstract):
    def __init__(self, controller=Keyboard(), **kwargs):
        super().__init__(controller=controller, **kwargs)

    def define_message(self):
        pass

    def control(self):
        command = {self.longitudinal_force: 0.0,
                   self.lateral_force: 0.0,
                   self.rotation_velocity: 0.0,
                   self.grasp: 0,
                   self.activate: 0}
        return command


class Basics2(SingleRoom):
    def __init__(self, size=(200, 400), **playground_params):
        super().__init__(size=size, **playground_params)

        square_01 = Physical(config_key='square', name='test')
        self.add_element(square_01,
                         initial_coordinates=((160, 150), math.pi / 4))

        square_02 = Physical(config_key='square')
        self.add_element(square_02, ((60, 150), 0))

        square_03 = Physical(config_key='square', radius=15)
        self.add_element(square_03, ((160, 50), math.pi / 2))

        square_04 = Physical(config_key='square', movable=False, mass=5)
        self.add_element(square_04, ((100, 100), math.pi / 4))

        square_05 = Physical(config_key='square',
                             radius=20)
        self.add_element(square_05, ((66, 300), 0))

        square_06 = Physical(config_key='square',
                             radius=20)
        self.add_element(square_06, ((133, 300), math.pi / 3))


my_playground = Basics2()

misc_data = MiscData(size_area=my_playground.size, number_drones=1)
my_drone = MyDrone(misc_data=misc_data, should_display_lidar=False)

my_playground.add_agent(my_drone)

engine = Engine(time_limit=10000, playground=my_playground, screen=True)

print(my_drone.base_platform.position, my_drone.base_platform.angle)
# my_drone.base_platform.position = Vec2d(107.40581356827045, 290.98786189924715)
# my_drone.base_platform.angle = 4.1516577389231086

while engine.game_on:

    engine.update_screen()

    actions = {my_drone: my_drone.controller.generate_actions()}

    terminate = engine.step(actions)
    engine.update_observations(grasped_invisible=True)

    cv2.imshow('control panel',
               engine.generate_agent_image(agent=my_drone,
                                           max_size_pg=400,
                                           width_sensors=300,
                                           height_sensor=40,
                                           layout=('playground', 'sensors')))
    cv2.waitKey(2)

    if terminate:
        engine.terminate()

engine.terminate()
cv2.destroyAllWindows()
