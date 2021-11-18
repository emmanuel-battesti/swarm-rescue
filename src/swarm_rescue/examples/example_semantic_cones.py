"""
This program can be launched directly.
Example of how to use semantic cones, grasping and dropping
"""

import random
import time
import math
from typing import Optional

import numpy as np
from enum import Enum

from simple_playgrounds.common.position_utils import CoordinateSampler
from simple_playgrounds.engine import Engine
from simple_playgrounds.playground import SingleRoom

import os
import sys

# This line add, to sys.path, the path to parent path of this file
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from spg_overlay.drone_sensors import DroneSemanticCones
from spg_overlay.misc_data import MiscData
from spg_overlay.rescue_center import RescueCenter
from spg_overlay.wounded_person import WoundedPerson
from spg_overlay.drone_abstract import DroneAbstract
from spg_overlay.utils import sign, normalize_angle


class MyDrone(DroneAbstract):
    class Activity(Enum):
        """
        All the states of the drone as a state machine
        """
        SEARCHING_WOUNDED = 1
        GRASPING_WOUNDED = 2
        SEARCHING_RESCUE_CENTER = 3
        DROPPING_AT_RESCUE_CENTER = 4

    def __init__(self,
                 identifier: Optional[int] = None, **kwargs):
        super().__init__(identifier=identifier,
                         should_display_lidar=False,
                         **kwargs)
        # The state is initialize to searching wounded person
        self.state = self.Activity.SEARCHING_WOUNDED

        # Those values are used by the random control function
        self.counterStraight = 0
        self.angleStopTurning = 0
        self.isTurning = False

    def define_message(self):
        """
        Here, we don't need communication...
        """
        pass

    def control(self):
        command = {self.longitudinal_force: 0.0,
                   self.lateral_force: 0.0,
                   self.rotation_velocity: 0.0,
                   self.grasp: 0,
                   self.activate: 0}

        found_wounded, found_rescue_center, command_semantic = self.process_semantic_sensor(self.semantic_cones())

        #############
        # TRANSITIONS OF THE STATE MACHINE
        #############

        if self.state is self.Activity.SEARCHING_WOUNDED and found_wounded:
            self.state = self.Activity.GRASPING_WOUNDED

        elif self.state is self.Activity.GRASPING_WOUNDED and self.grasp.grasped_element:
            self.state = self.state.SEARCHING_RESCUE_CENTER

        elif self.state is self.Activity.GRASPING_WOUNDED and not found_wounded:
            self.state = self.state.SEARCHING_WOUNDED

        elif self.state is self.Activity.SEARCHING_RESCUE_CENTER and found_rescue_center:
            self.state = self.Activity.DROPPING_AT_RESCUE_CENTER

        elif self.state is self.Activity.DROPPING_AT_RESCUE_CENTER and not self.grasp.grasped_element:
            self.state = self.Activity.SEARCHING_WOUNDED

        elif self.state is self.Activity.DROPPING_AT_RESCUE_CENTER and not found_rescue_center:
            self.state = self.Activity.SEARCHING_RESCUE_CENTER

        ##########
        # COMMANDS FOR EACH STATE
        # Searching randomly, but when a rescue center or wounded person is detected, we use a special command
        ##########
        if self.state is self.Activity.SEARCHING_WOUNDED:
            command = self.control_random()
            command[self.grasp] = 0

        elif self.state is self.Activity.GRASPING_WOUNDED:
            command = command_semantic
            command[self.grasp] = 1

        elif self.state is self.Activity.SEARCHING_RESCUE_CENTER:
            command = self.control_random()
            command[self.grasp] = 1

        elif self.state is self.Activity.DROPPING_AT_RESCUE_CENTER:
            command = command_semantic
            command[self.grasp] = 1

        return command

    def process_touch_sensor(self):
        """
        Returns True if the drone hits an obstacle
        """
        touched = False
        detection = max(self.touch().sensor_values)

        if detection > 0.5:
            touched = True

        return touched

    def control_random(self):
        """
        The Drone will move forward and turn for a random angle when an obstacle is hit
        """
        command_straight = {self.longitudinal_force: 1.0,
                            self.rotation_velocity: 0.0}

        command_turn = {self.longitudinal_force: 0.0,
                        self.rotation_velocity: 1.0}

        touched = self.process_touch_sensor()

        self.counterStraight += 1

        if touched and not self.isTurning and self.counterStraight > 10:
            self.isTurning = True
            self.angleStopTurning = random.uniform(-math.pi, math.pi)

        diff_angle = normalize_angle(self.angleStopTurning - self.measured_angle())
        if self.isTurning and abs(diff_angle) < 0.2:
            self.isTurning = False
            self.counterStraight = 0

        if self.isTurning:
            return command_turn
        else:
            return command_straight

    def process_semantic_sensor(self, the_semantic_sensor):
        """
        According his state in the state machine, the Drone will move towards a wound person or the rescue center
        """
        command = {self.longitudinal_force: 1.0,
                   self.lateral_force: 0.0,
                   self.rotation_velocity: 0.0}
        rotation_velocity_max = 0.6

        detection_semantic = the_semantic_sensor.sensor_values
        best_angle = 1000

        found_wounded = False
        if (self.state is self.Activity.SEARCHING_WOUNDED
            or self.state is self.Activity.GRASPING_WOUNDED) \
                and detection_semantic:
            scores = []
            for data in detection_semantic:
                # If the wounded person detected is held by nobody
                if data.entity_type == DroneSemanticCones.TypeEntity.WOUNDED_PERSON and not data.grasped:
                    found_wounded = True
                    v = (data.angle * data.angle) + (data.distance * data.distance / 10 ** 5)
                    scores.append((v, data.angle, data.distance))

            # Select the best one among wounded persons detected
            best_score = 10000
            for score in scores:
                if score[0] < best_score:
                    best_score = score[0]
                    best_angle = score[1]

        found_rescue_center = False
        if (self.state is self.Activity.SEARCHING_RESCUE_CENTER
            or self.state is self.Activity.DROPPING_AT_RESCUE_CENTER) \
                and detection_semantic:
            for data in detection_semantic:
                if data.entity_type == DroneSemanticCones.TypeEntity.RESCUE_CENTER:
                    found_rescue_center = True
                    best_angle = data.angle

        if found_rescue_center or found_wounded:
            a = sign(best_angle)
            # The robot will turn until best_angle is 0
            command[self.rotation_velocity] = a * rotation_velocity_max

        return found_wounded, found_rescue_center, command


class MyMap:
    def __init__(self):

        # BUILD MAP
        self.size_area = (200, 200)
        self.playground = SingleRoom(size=self.size_area, wall_type='light')

        # RESCUE CENTER
        rescue_center = RescueCenter(size=[30, 30])
        self.playground.add_element(rescue_center, ((20, 20), 0))

        # WOUNDED PERSONS
        self.number_wounded_persons = 5
        center_area = (self.size_area[0] * 3 / 4, self.size_area[1] * 3 / 4)
        area_all = CoordinateSampler(center=center_area, area_shape='rectangle',
                                     size=(self.size_area[0], self.size_area[1]))

        for i in range(self.number_wounded_persons):
            wounded_person = WoundedPerson(graspable=True, rescue_center=rescue_center)
            try:
                self.playground.add_element(wounded_person, area_all, allow_overlapping=False)
            except:
                print("Failed to place object 'wounded_person'")

        # DRONE
        misc_data = MiscData(size_area=self.size_area)
        self.my_drone = MyDrone(misc_data=misc_data)
        self.playground.add_agent(self.my_drone, ((40, 40), 0))


my_map = MyMap()
engine = Engine(playground=my_map.playground, time_limit=10000, screen=True)

while engine.game_on:
    engine.update_screen()
    engine.update_observations(grasped_invisible=True)
    actions = {my_map.my_drone: my_map.my_drone.control()}
    terminate = engine.step(actions)
    time.sleep(0.002)

    if terminate:
        engine.terminate()

engine.terminate()
