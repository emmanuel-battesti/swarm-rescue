"""
This program can be launched directly.
"""

import sys
from pathlib import Path
from typing import List, Type, Tuple

import numpy as np

# Insert the parent directory of the current file's directory into sys.path.
# This allows Python to locate modules that are one level above the current
# script, in this case spg_overlay.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from spg_overlay.utils.utils import clamp
from spg_overlay.entities.drone_abstract import DroneAbstract
from spg_overlay.entities.return_area import ReturnArea
from spg_overlay.gui_map.closed_playground import ClosedPlayground
from spg_overlay.gui_map.gui_sr import GuiSR
from spg_overlay.gui_map.map_abstract import MapAbstract
from spg_overlay.utils.misc_data import MiscData


class MyDrone(DroneAbstract):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.counter = 0
        self.counter_change_direction = 100
        self.to_the_right = True

        self.last_is_inside_return_area = False

    def define_message_for_all(self):
        """
        Here, we don't need communication...
        """
        pass

    def control(self):
        command = {"forward": 0.0,
                   "rotation": 0.0}

        self.counter += 1
        if self.counter % self.counter_change_direction == 0:
            self.to_the_right = not self.to_the_right

        if self.to_the_right:
            forward = 0.8
        else:
            forward = -0.8
        rotation = 0.0
        command = {"forward": forward,
                   "rotation": rotation}

        if self.is_inside_return_area != self.last_is_inside_return_area:
            print("is_inside_return_area : ", self.is_inside_return_area)
            self.last_is_inside_return_area = self.is_inside_return_area

        return command


class MyMap(MapAbstract):
    def __init__(self):
        super().__init__()

        # PARAMETERS MAP
        self._size_area = (400, 400)

        self._return_area = ReturnArea(size=(150, 350))
        self._return_area_pos = ((0, 0), 0)

        # POSITIONS OF THE DRONES
        self._number_drones = 3
        self._drones_pos = []
        for i in range(self._number_drones):
            pos = ((-150+i*100, 100 - i * 100), 0)
            self._drones_pos.append(pos)

        self._drones: List[DroneAbstract] = []

    def construct_playground(self, drone_type: Type[DroneAbstract]):
        playground = ClosedPlayground(size=self._size_area)

        playground.add(self._return_area, self._return_area_pos)

        # POSITIONS OF THE DRONES
        misc_data = MiscData(size_area=self._size_area,
                             number_drones=self._number_drones,
                             max_timestep_limit=self._max_timestep_limit,
                             max_walltime_limit=self._max_walltime_limit)
        for i in range(self._number_drones):
            drone = drone_type(identifier=i, misc_data=misc_data)
            self._drones.append(drone)
            playground.add(drone, self._drones_pos[i])

        return playground


def main():
    my_map = MyMap()
    my_playground = my_map.construct_playground(drone_type=MyDrone)

    gui = GuiSR(playground=my_playground,
                the_map=my_map,
                use_keyboard=False,
                use_mouse_measure=True,
                enable_visu_noises=False,
                )

    gui.run()

    score_health_returned = my_map.compute_score_health_returned()
    print("score_health_returned = ", score_health_returned)


if __name__ == '__main__':
    main()
