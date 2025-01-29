"""
Le drone suit les murs
"""

from enum import Enum
from typing import Optional

import numpy as np

from spg_overlay.entities.drone_abstract import DroneAbstract
from spg_overlay.utils.misc_data import MiscData

from spg_overlay.utils.utils import normalize_angle


class MyDroneWall(DroneAbstract):
    class Activity(Enum):
        """
        All the states of the drone as a state machine
        """
        SEARCHING_WALL = 1
        FOLLOWING_WALL = 2

    def __init__(self,
                 identifier: Optional[int] = None,
                 misc_data: Optional[MiscData] = None,
                 **kwargs):
        super().__init__(identifier=identifier,
                         misc_data=misc_data,
                         **kwargs)
        # Initialisation de l'activité
        self.state  = self.Activity.SEARCHING_WALL

        # Initialisation des paramètres cinétiques
        self.prev_epsilon_wall_angle = 0

    def define_message_for_all(self):
        """
        Here, we don't need communication...
        """
        pass

    def control(self):
        found_wall,epsilon_wall_angle = self.process_lidar_sensor(self.lidar())

        #############
        # TRANSITIONS OF THE STATE MACHINE
        #############

        if self.state is self.Activity.SEARCHING_WALL and found_wall:
            self.state = self.Activity.FOLLOWING_WALL
        
        elif self.state is self.Activity.FOLLOWING_WALL and not found_wall:
            self.state = self.Activity.SEARCHING_WALL

        ##########
        # COMMANDS FOR EACH STATE
        ##########
        
        command = {"forward": 0.1,
                            "lateral": 0.0,
                            "rotation": 0.0,
                            "grasper": 0}

        if found_wall :

            epsilon_wall_angle = normalize_angle(epsilon_wall_angle)

            deriv_epsilon_wall_angle = normalize_angle(epsilon_wall_angle - self.prev_epsilon_wall_angle)
            Kp = 9.0
            Kd = 0.6
            rotation = Kp * epsilon_wall_angle + Kd * deriv_epsilon_wall_angle
            rotation = min( max(-1,rotation) , 1 )

            self.prev_epsilon_wall_angle = epsilon_wall_angle

            command["rotation"] = rotation
        
        else:

            self.prev_epsilon_wall_angle = 0.0

        return command
    
    def process_lidar_sensor(self,self_lidar):
        """
        -> ( bool near_obstacle , float epsilon_wall_angle )
        where epsilon_wall_angle is the (counter-clockwise convention) angle made
        between the drone and the nearest wall
        """
        lidar_values = self_lidar.get_sensor_values()

        if lidar_values is None:
            return (False,0)
        
        ray_angles = self_lidar.ray_angles
        size = self_lidar.resolution

        angle_nearest_obstacle = 0
        if size != 0:
            min_dist = min(lidar_values)
            angle_nearest_obstacle = ray_angles[np.argmin(lidar_values)]

        near_obstacle = False
        if min_dist < 40:
            near_obstacle = True

        epsilon_wall_angle = angle_nearest_obstacle - np.pi/2

        return (near_obstacle,epsilon_wall_angle)
