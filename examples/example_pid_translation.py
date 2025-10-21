"""
This program can be launched directly.
"""

import math
import pathlib
import sys
from typing import List, Type, Tuple

import arcade
import numpy as np

# Insert the 'src' directory, located two levels up from the current script,
# into sys.path. This ensures Python can find project-specific modules
# (e.g., 'swarm_rescue') when the script is run from a subfolder like 'examples/'.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from swarm_rescue.simulation.drone.controller import CommandsDict
from swarm_rescue.simulation.utils.path import Path
from swarm_rescue.simulation.utils.pose import Pose
from swarm_rescue.simulation.utils.utils import clamp
from swarm_rescue.simulation.drone.drone_abstract import DroneAbstract
from swarm_rescue.simulation.gui_map.closed_playground import ClosedPlayground
from swarm_rescue.simulation.gui_map.gui_sr import GuiSR
from swarm_rescue.simulation.gui_map.map_abstract import MapAbstract
from swarm_rescue.simulation.utils.misc_data import MiscData


class MyDronePidTranslation(DroneAbstract):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.counter = 0
        self.distance = 150.0
        self.position_setpoint = np.array([-self.distance, 0.0])
        self.counter_change_setpoint = 180

        self.iter_path = 0
        self.path_done = Path()
        self.prev_diff_position = 0

        self.to_the_right = True

    def define_message_for_all(self):
        """
        Here, we don't need communication...
        """
        pass

    def control(self) -> CommandsDict:
        """
        The Drone will move a fix distance
        """
        command: CommandsDict = {"forward": 0.0,
                                 "rotation": 0.0}

        self.iter_path += 1
        if self.iter_path % 3 == 0:
            position = np.array([self.true_position()[0],
                                 self.true_position()[1]])
            angle = self.true_angle()
            pose = Pose(position=position, orientation=angle)
            self.path_done.append(pose)

        self.counter += 1
        if self.counter % self.counter_change_setpoint == 0:
            if self.to_the_right:
                self.position_setpoint = np.array([self.distance, 0.0])
            else:
                self.position_setpoint = np.array([-self.distance, 0.0])
            self.to_the_right = not self.to_the_right
            print("*******************************")

        diff_position = (self.position_setpoint -
                         np.asarray(self.true_position()))

        if self.identifier == 0:  # with PD
            deriv_diff_position = diff_position - self.prev_diff_position
            Kp = 1.6
            Kd = 11.0

            forward = (Kp * float(diff_position[0]) +
                       Kd * float(deriv_diff_position[0]))

            forward = clamp(forward, -1.0, 1.0)

            print("counter", self.counter,
                  ", diff_position", int(diff_position[0] * 10),
                  "forward=", forward)

            rotation = 0.0
            command = {"forward": forward,
                       "rotation": rotation}

            self.prev_diff_position = diff_position

        elif self.identifier == 1:  # with P with too much gain
            forward = 2.0 * float(diff_position[0])
            forward = clamp(forward, -1.0, 1.0)
            rotation = 0.0
            command = {"forward": forward,
                       "rotation": rotation}

        elif self.identifier == 2:  # with P with too little gain
            forward = 0.0015 * float(diff_position[0])
            forward = clamp(forward, -1.0, 1.0)
            rotation = 0
            command = {"forward": forward,
                       "rotation": rotation}

        return command

    def draw_bottom_layer(self):
        self.draw_setpoint()
        self.draw_path(path=self.path_done, color=(255, 0, 255))
        self.draw_antedirection()

    def draw_setpoint(self):
        half_width = self._half_size_array[0]
        half_height = self._half_size_array[1]
        pt1 = self.position_setpoint + np.array([half_width, 0])
        pt2 = self.position_setpoint + np.array([half_width, 2 * half_height])
        arcade.draw_line(float(pt2[0]),
                         float(pt2[1]),
                         float(pt1[0]),
                         float(pt1[1]),
                         color=arcade.color.GRAY)

    def draw_path(self, path: Path(), color: Tuple[int, int, int]):
        length = path.length()
        # print(length)
        pt2 = None
        for ind_pt in range(length):
            pose = path.get(ind_pt)
            pt1 = pose.position + self._half_size_array
            # print(ind_pt, pt1, pt2)
            if ind_pt > 0:
                arcade.draw_line(float(pt2[0]),
                                 float(pt2[1]),
                                 float(pt1[0]),
                                 float(pt1[1]), color)
            pt2 = pt1

    def draw_antedirection(self):
        pt1 = np.array([self.true_position()[0], self.true_position()[1]])
        pt1 = pt1 + self._half_size_array
        pt2 = pt1 + 150 * np.array([math.cos(self.true_angle() + np.pi / 2),
                                    math.sin(self.true_angle() + np.pi / 2)])
        color = (255, 64, 0)
        arcade.draw_line(float(pt2[0]),
                         float(pt2[1]),
                         float(pt1[0]),
                         float(pt1[1]),
                         color)


class MyMap(MapAbstract):
    def __init__(self, drone_type: Type[DroneAbstract]):
        super().__init__(drone_type=drone_type)

        # PARAMETERS MAP
        self._size_area = (600, 400)

        # POSITIONS OF THE DRONES
        self._number_drones = 3
        self._drones_pos = []
        for i in range(self._number_drones):
            pos = ((0, 100 - i * 100), 0)
            self._drones_pos.append(pos)

        self._drones: List[DroneAbstract] = []

        self._playground = ClosedPlayground(size=self._size_area)

        # POSITIONS OF THE DRONES
        misc_data = MiscData(size_area=self._size_area,
                             number_drones=self._number_drones,
                             max_timestep_limit=self._max_timestep_limit,
                             max_walltime_limit=self._max_walltime_limit)
        for i in range(self._number_drones):
            drone = drone_type(identifier=i, misc_data=misc_data)
            self._drones.append(drone)
            self._playground.add(drone, self._drones_pos[i])


def main():
    the_map = MyMap(drone_type=MyDronePidTranslation)

    gui = GuiSR(the_map=the_map,
                use_keyboard=False,
                use_mouse_measure=True,
                enable_visu_noises=False,
                )

    gui.run()

    score_health_returned = the_map.compute_score_health_returned()
    print("score_health_returned = ", score_health_returned)


if __name__ == '__main__':
    main()
