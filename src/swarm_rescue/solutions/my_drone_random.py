"""
Simple random controller
The Drone will move forward and turn for a random angle when an obstacle is hit
"""
import math
import random
from typing import Optional

from swarm_rescue.simulation.drone.controller import CommandsDict
from swarm_rescue.simulation.drone.drone_abstract import DroneAbstract
from swarm_rescue.simulation.utils.misc_data import MiscData
from swarm_rescue.simulation.utils.utils import normalize_angle


class MyDroneRandom(DroneAbstract):
    """
    Drone controller that moves randomly and turns when hitting obstacles.

    Attributes:
        counterStraight (int): Counter for straight movement.
        angleStopTurning (float): Angle to stop turning.
        distStopStraight (float): Distance to stop moving straight.
        isTurning (bool): Whether the drone is currently turning.
    """
    counterStraight: int
    angleStopTurning: float
    distStopStraight: float
    isTurning: bool

    def __init__(self,
                 identifier: Optional[int] = None,
                 misc_data: Optional[MiscData] = None,
                 **kwargs):
        """
        Initializes the random drone controller.

        Args:
            identifier (Optional[int]): Drone identifier.
            misc_data (Optional[MiscData]): Miscellaneous data.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(identifier=identifier,
                         misc_data=misc_data,
                         display_lidar_graph=False,
                         **kwargs)
        self.counterStraight = 0
        self.angleStopTurning = random.uniform(-math.pi, math.pi)
        self.distStopStraight = random.uniform(10, 50)
        self.isTurning = False

    def define_message_for_all(self) -> None:
        """
        No communication needed for a random drone.
        """
        pass

    def process_lidar_sensor(self) -> bool:
        """
        Returns True if the drone collided with an obstacle.

        Returns:
            bool: True if collision detected, False otherwise.
        """
        if self.lidar_values() is None:
            return False

        collided = False
        dist = min(self.lidar_values())

        if dist < 40:
            collided = True

        return collided

    def control(self) -> CommandsDict:
        """
        The Drone will move forward and turn for a random angle when an obstacle is hit.

        Returns:
            CommandsDict: The control command for the drone.
        """
        command_straight: CommandsDict = {"forward": 1.0,
                                          "lateral": 0.0,
                                          "rotation": 0.0,
                                          "grasper": 0}

        command_turn: CommandsDict = {"forward": 0.0,
                                      "lateral": 0.0,
                                      "rotation": 1.0,
                                      "grasper": 0}

        collided = self.process_lidar_sensor()

        self.counterStraight += 1

        if collided and not self.isTurning and self.counterStraight > self.distStopStraight:
            self.isTurning = True
            self.angleStopTurning = random.uniform(-math.pi, math.pi)

        measured_angle = 0
        if self.measured_compass_angle() is not None:
            measured_angle = self.measured_compass_angle()

        diff_angle = normalize_angle(self.angleStopTurning - measured_angle)
        if self.isTurning and abs(diff_angle) < 0.2:
            self.isTurning = False
            self.counterStraight = 0
            self.distStopStraight = random.uniform(10, 50)

        if self.isTurning:
            return command_turn
        else:
            return command_straight

