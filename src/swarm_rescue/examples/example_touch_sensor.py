"""
This program can be launched directly.
Example of how to use the touch sensor
"""

import os
import random
import sys
from typing import Type

# This line add, to sys.path, the path to parent path of this file
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from spg_overlay.entities.drone_abstract import DroneAbstract
from spg_overlay.gui_map.closed_playground import ClosedPlayground
from spg_overlay.gui_map.gui_sr import GuiSR
from spg_overlay.gui_map.map_abstract import MapAbstract
from spg_overlay.utils.constants import FRAME_RATE
from spg_overlay.utils.misc_data import MiscData


class MyDroneTouch(DroneAbstract):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def define_message_for_all(self):
        """
        Here, we don't need communication...
        """
        pass

    def control(self):
        the_touch_sensor = self.touch()
        if the_touch_sensor.get_sensor_values() is None:
            return None

        max_value = max(the_touch_sensor.get_sensor_values())
        print("max value touch sensor :", max_value)
        # indices will contain indices with max values of the sensor
        indices = [i for i, x in enumerate(the_touch_sensor.get_sensor_values()) if
                   x == max(the_touch_sensor.get_sensor_values())]

        in_front = False
        size = len(the_touch_sensor.get_sensor_values())
        quarter = round(size / 4)
        middle = round(size / 2)
        for ind in indices:
            if middle - quarter <= ind < middle + quarter:
                in_front = True
                break

        touched = False
        if max_value > 0.5 and in_front:
            touched = True

        command_straight = {"forward": 1.0,
                            "rotation": random.uniform(-0.1, 0.1)}
        command_turn = {"forward": 0.0,
                        "rotation": 1.0}
        if touched:
            command = command_turn
        else:
            command = command_straight

        return command


class MyMapTouch(MapAbstract):
    def __init__(self):
        super().__init__()

        # PARAMETERS MAP
        self._size_area = (700, 700)

        self._number_drones = 1
        self._drones_pos = [((80, 100), 0)]
        self._drones = []

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
    my_map = MyMapTouch()
    playground = my_map.construct_playground(drone_type=MyDroneTouch)

    # draw_touch : enable the visualization of the touch sensor
    gui = GuiSR(playground=playground,
                the_map=my_map,
                draw_touch=True,
                use_keyboard=False,
                enable_visu_noises=False,
                )
    gui.run()


if __name__ == '__main__':
    main()
