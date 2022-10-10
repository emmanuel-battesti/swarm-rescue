"""
This program can be launched directly.
Example of how to use the touch sensor
"""

import os
import random
import sys

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
        self._size_area = (700, 700)
        self._number_drones = 1

    def construct_playground(self):
        playground = ClosedPlayground(size=self._size_area)

        # POSITIONS OF THE DRONES
        playground.add(self._drones[0], ((80, 100), 0))

        return playground


def main():
    my_map = MyMapTouch()
    misc_data = MiscData(size_area=my_map.size_area, number_drones=1)
    my_drone = MyDroneTouch(misc_data=misc_data)

    my_map.set_drones([my_drone])
    playground = my_map.construct_playground()

    gui = GuiSR(playground=playground,
                the_map=my_map,
                drones=[my_drone],
                draw_touch=True,
                use_keyboard=False)
    gui.run()


if __name__ == '__main__':
    main()
