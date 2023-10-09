"""
This program can be launched directly.
Example of how to control one drone
"""

import math
import os
import sys
from typing import List, Type, Tuple

import arcade
import numpy as np

# This line add, to sys.path, the path to parent path of this file
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from spg_overlay.utils.path import Path
from spg_overlay.utils.pose import Pose
from spg_overlay.utils.utils import clamp
from spg_overlay.entities.drone_abstract import DroneAbstract
from spg_overlay.gui_map.closed_playground import ClosedPlayground
from spg_overlay.gui_map.gui_sr import GuiSR
from spg_overlay.gui_map.map_abstract import MapAbstract
from spg_overlay.utils.misc_data import MiscData


class MyDronePidTranslation(DroneAbstract):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.counter = 0
        self.distance = 150
        self.position_consigne = np.array([-self.distance, 0.0])
        self.counter_change_position = 100

        self.iter_path = 0
        self.path_done = Path()
        self.prev_diff_position = 0

        self.to_the_right = True

    def define_message_for_all(self):
        """
        Here, we don't need communication...
        """
        pass

    def control(self):
        """
        The Drone will move a fix distance
        """
        command = {"forward": 0,
                   "rotation": 0}

        self.iter_path += 1
        if self.iter_path % 3 == 0:
            position = np.array([self.true_position()[0], self.true_position()[1]])
            angle = self.true_angle()
            pose = Pose(position=position, orientation=angle)
            self.path_done.append(pose)

        self.counter += 1
        if self.counter % self.counter_change_position == 0:
            if self.to_the_right:
                self.position_consigne = np.array([self.distance, 0.0])
            else:
                self.position_consigne = np.array([-self.distance, 0.0])
            self.to_the_right = not self.to_the_right
            print("*******************************")

        diff_position = self.position_consigne - np.asarray(self.true_position())

        if self.identifier == 0:  # with PD
            deriv_diff_position = diff_position - self.prev_diff_position
            # PD filter 1 #########
            Ku = 25 / 100  # Gain debut oscillation maintenue en P pure
            Tu = 26  # Période d'oscillation
            Kp = 0.8 * Ku
            Kd = Ku * Tu / 10.0
            forward = Kp * diff_position[0] + Kd * deriv_diff_position[0]

            forward = clamp(forward, -1.0, 1.0)

            print("counter", self.counter,
                  ", diff_position", int(diff_position[0] * 1000), "forward=", forward)

            rotation = 0
            command = {"forward": forward,
                       "rotation": rotation}

            self.prev_diff_position = diff_position

        elif self.identifier == 1:  # with P with too much gain
            forward = 10 * diff_position[0]
            forward = clamp(forward, -1.0, 1.0)
            rotation = 0
            command = {"forward": forward,
                       "rotation": rotation}

        elif self.identifier == 2:  # with P with too little gain
            forward = 0.006 * diff_position[0]
            forward = clamp(forward, -1.0, 1.0)
            rotation = 0
            command = {"forward": forward,
                       "rotation": rotation}

        return command

    def draw_bottom_layer(self):
        self.draw_consigne()
        self.draw_path(path=self.path_done, color=(255, 0, 255))
        self.draw_antedirection()

    def draw_consigne(self):
        half_width = self._half_size_array[0]
        half_height = self._half_size_array[1]
        pt1 = self.position_consigne + np.array([half_width, 0])
        pt2 = self.position_consigne + np.array([half_width, 2 * half_height])
        arcade.draw_line(pt2[0], pt2[1], pt1[0], pt1[1], color=arcade.color.GRAY)

    def draw_path(self, path: Path(), color: Tuple[int, int, int]):
        length = path.length()
        # print(length)
        pt2 = None
        for ind_pt in range(length):
            pose = path.get(ind_pt)
            pt1 = pose.position + self._half_size_array
            # print(ind_pt, pt1, pt2)
            if ind_pt > 0:
                arcade.draw_line(pt2[0], pt2[1], pt1[0], pt1[1], color)
            pt2 = pt1

    def draw_antedirection(self):
        pt1 = np.array([self.true_position()[0], self.true_position()[1]])
        pt1 = pt1 + self._half_size_array
        pt2 = pt1 + 150 * np.array([math.cos(self.true_angle() + np.pi / 2),
                                    math.sin(self.true_angle() + np.pi / 2)])
        color = (255, 64, 0)
        arcade.draw_line(pt2[0], pt2[1], pt1[0], pt1[1], color)


class MyMapRandom(MapAbstract):
    def __init__(self):
        super().__init__()

        # PARAMETERS MAP
        self._size_area = (400, 400)

        # POSITIONS OF THE DRONES
        self._number_drones = 3
        self._drones_pos = []
        for i in range(self._number_drones):
            pos = ((0, 100 - i * 100), 0)
            self._drones_pos.append(pos)

        self._drones: List[DroneAbstract] = []

    def construct_playground(self, drone_type: Type[DroneAbstract]):
        playground = ClosedPlayground(size=self._size_area)

        # POSITIONS OF THE DRONES
        misc_data = MiscData(size_area=self._size_area,
                             number_drones=self._number_drones)
        for i in range(self._number_drones):
            drone = drone_type(identifier=i, misc_data=misc_data)
            self._drones.append(drone)
            playground.add(drone, self._drones_pos[i])

        return playground


def main():
    my_map = MyMapRandom()

    playground = my_map.construct_playground(drone_type=MyDronePidTranslation)

    gui = GuiSR(playground=playground,
                the_map=my_map,
                use_keyboard=False,
                use_mouse_measure=True,
                enable_visu_noises=False,
                )

    gui.run()


if __name__ == '__main__':
    main()
