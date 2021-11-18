"""
Simple random controller
The Drone will move forward and turn for a random angle when an obstacle is hit
"""

import random
import math
from typing import Optional

from spg_overlay.drone_abstract import DroneAbstract
from spg_overlay.misc_data import MiscData
from spg_overlay.utils import normalize_angle


class MyDroneRandom(DroneAbstract):
    def __init__(self,
                 identifier: Optional[int] = None,
                 misc_data: Optional[MiscData] = None,
                 **kwargs):
        super().__init__(identifier=identifier,
                         misc_data=misc_data,
                         should_display_lidar=False,
                         **kwargs)
        self.counterStraight = 0
        self.angleStopTurning = 0
        self.isTurning = False

    def define_message(self):
        """
        Here, we don't need communication...
        """
        pass

    def process_touch_sensor(self):
        """
        Returns True if the drone hits an obstacle
        """
        touched = False
        detection = max(self.touch().sensor_values)

        if detection > 0.5:
            touched = True

        return touched

    def control(self):
        """
        The Drone will move forward and turn for a random angle when an obstacle is hit
        """
        command_straight = {self.longitudinal_force: 1.0,
                            self.lateral_force: 0.0,
                            self.rotation_velocity: 0.0,
                            self.grasp: 0,
                            self.activate: 0}

        command_turn = {self.longitudinal_force: 0.0,
                        self.lateral_force: 0.0,
                        self.rotation_velocity: 1.0,
                        self.grasp: 0,
                        self.activate: 0}

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
