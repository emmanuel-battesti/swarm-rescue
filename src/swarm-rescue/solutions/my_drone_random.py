import random
import math
from copy import deepcopy
from typing import Optional

import numpy as np

from spg_overlay.drone import DroneAbstract
from spg_overlay.utils import normalize_angle


class MyDroneRandom(DroneAbstract):
    def __init__(self, identifier: Optional[int] = None, **kwargs):
        super().__init__(identifier=identifier,
                         should_display_lidar=False,
                         **kwargs)
        self.counterStraight = 0
        self.angleStopTurning = 0
        self.isTurning = False

    def define_message(self):
        msg_data = (self.identifier, self.coordinates)
        return msg_data

    def process_touch_sensor(self):
        touched = False
        detection = max(self.touch().sensor_values)

        if detection > 0.5:
            touched = True

        return touched

    def control(self):
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

        diff_angle = normalize_angle(self.angleStopTurning - self.angle)
        if self.isTurning and abs(diff_angle) < 0.2:
            self.isTurning = False
            self.counterStraight = 0

        if self.isTurning:
            return command_turn
        else:
            return command_straight
