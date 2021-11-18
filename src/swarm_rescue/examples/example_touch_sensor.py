"""
This program can be launched directly.
Example of how to use the touch sensor
"""

import random
import time

from simple_playgrounds.engine import Engine
from simple_playgrounds.playground import LineRooms
from simple_playgrounds.agent.controllers import External

import os
import sys

# This line add, to sys.path, the path to parent path of this file
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from spg_overlay.misc_data import MiscData
from spg_overlay.drone_abstract import DroneAbstract


class MyDrone(DroneAbstract):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def define_message(self):
        pass

    def control(self):
        pass


def my_control(drone):
    the_touch_sensor = drone.touch()
    max_value = max(the_touch_sensor.sensor_values)
    # indices will contain indices with max values of the sensor
    indices = [i for i, x in enumerate(the_touch_sensor.sensor_values) if x == max(the_touch_sensor.sensor_values)]

    in_front = False
    for ind in indices:
        if 9 <= ind < 27:
            in_front = True
            break

    touched = False
    if max_value > 0.5 and in_front:
        touched = True

    command_straight = {drone.longitudinal_force: 1.0,
                        drone.rotation_velocity: random.uniform(-0.1, 0.1)}
    command_turn = {drone.longitudinal_force: 0.0,
                    drone.rotation_velocity: 1}
    if touched:
        command = command_turn
    else:
        command = command_straight

    return command


size_area = (700, 700)
my_playground = LineRooms(size=size_area, number_rooms=2, random_doorstep_position=True, doorstep_size=200)

misc_data = MiscData(size_area=size_area)
my_drone = MyDrone(controller=External(), misc_data=misc_data)

my_playground.add_agent(my_drone, ((80, 100), 0))

engine = Engine(playground=my_playground, time_limit=10000, screen=True)

while engine.game_on:

    engine.update_screen()
    engine.update_observations(grasped_invisible=True)

    actions = {}
    for my_drone in engine.agents:
        actions[my_drone] = my_control(my_drone)

    terminate = engine.step(actions)

    time.sleep(0.002)

    if terminate:
        engine.terminate()

engine.terminate()
