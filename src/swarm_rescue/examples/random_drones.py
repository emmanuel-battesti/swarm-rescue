"""
This program can be launched directly.
Example of how to control several drones
"""

import math
import os
import random
import sys

# This line add, to sys.path, the path to parent path of this file
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from spg_overlay.entities.drone_abstract import DroneAbstract
from spg_overlay.gui_map.closed_playground import ClosedPlayground
from spg_overlay.gui_map.gui_sr import GuiSR
from spg_overlay.gui_map.map_abstract import MapAbstract
from spg_overlay.utils.utils import normalize_angle


class MyDroneRandom(DroneAbstract):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.counterStraight = 0
        self.angleStopTurning = random.uniform(-math.pi, math.pi)
        self.counterStopStraight = random.uniform(10, 100)
        self.isTurningLeft = False
        self.isTurningRight = False

    def define_message_for_all(self):
        """
        Here, we don't need communication...
        """
        pass

    def control(self):
        """
        The Drone will move forward and turn for a random angle when an obstacle is hit
        """
        command_straight = {"forward": 1.0,
                            "rotation": 0.0}
        command_turn_left = {"forward": 0.0,
                             "rotation": 1.0}
        command_turn_right = {"forward": 0.0,
                              "rotation": -1.0}

        self.counterStraight += 1

        if not self._is_turning() and self.counterStraight > self.counterStopStraight:
            self.angleStopTurning = random.uniform(-math.pi, math.pi)
            diff_angle = normalize_angle(self.angleStopTurning - self.angle)
            if diff_angle > 0:
                self.isTurningLeft = True
            else:
                self.isTurningRight = True

        diff_angle = normalize_angle(self.angleStopTurning - self.angle)
        if self._is_turning() and abs(diff_angle) < 0.2:
            self.isTurningLeft = False
            self.isTurningRight = False
            self.counterStraight = 0
            self.counterStopStraight = random.uniform(10, 100)

        # print("\nself.isTurning : {}, abs(diff_angle) = {}".format(self.isTurning, abs(diff_angle)))
        # print("self.angleStopTurning = {}, self.angle = {}, diff_angle = {}".format(self.angleStopTurning, self.angle, diff_angle))
        if self.isTurningLeft:
            return command_turn_left
        elif self.isTurningRight:
            return command_turn_right
        else:
            return command_straight

    def _is_turning(self):
        return self.isTurningLeft or self.isTurningRight


class MyMapRandom(MapAbstract):
    def __init__(self):
        super().__init__()
        self._size_area = (900, 900)
        self._number_drones = 30

    def construct_playground(self):
        playground = ClosedPlayground(size=self._size_area)

        # POSITIONS OF THE DRONES
        for drone in self._drones:
            coordinate = ((random.uniform(-self._size_area[0] / 2, self._size_area[0] / 2),
                           random.uniform(-self._size_area[1] / 2, self._size_area[1] / 2)),
                          random.uniform(-math.pi, math.pi))
            playground.add(drone, coordinate)

        return playground


def main():
    my_map = MyMapRandom()
    drones = [MyDroneRandom() for _ in range(my_map.number_drones)]

    my_map.set_drones(drones)
    playground = my_map.construct_playground()

    gui = GuiSR(playground=playground,
                the_map=my_map,
                drones=drones,
                use_keyboard=False,
                use_mouse_measure=True)
    gui.run()


if __name__ == '__main__':
    main()
