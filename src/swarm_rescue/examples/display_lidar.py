"""
This program can be launched directly.
To move the drone, you have to click on the map, then use the arrows on the keyboard
"""

import os
import sys

from spg.utils.definitions import CollisionTypes

# This line add, to sys.path, the path to parent path of this file
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from maps.walls_complete_map_2 import add_walls, add_boxes
from spg_overlay.entities.drone_abstract import DroneAbstract
from spg_overlay.entities.rescue_center import RescueCenter, wounded_rescue_center_collision
from spg_overlay.gui_map.closed_playground import ClosedPlayground
from spg_overlay.gui_map.gui_sr import GuiSR
from spg_overlay.gui_map.map_abstract import MapAbstract


class MyDroneLidar(DroneAbstract):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def define_message_for_all(self):
        """
        Here, we don't need communication...
        """
        pass

    def control(self):
        """
        We only send a command to do nothing
        """
        command = {"forward": 0.0,
                   "lateral": 0.0,
                   "rotation": 0.0,
                   "grasper": 0}
        return command


class MyMapLidar(MapAbstract):

    def __init__(self):
        super().__init__()
        self._size_area = (1122, 750)
        self._number_drones = 1

    def construct_playground(self):
        playground = ClosedPlayground(size=self._size_area)

        # RESCUE CENTER
        playground.add_interaction(CollisionTypes.GEM,
                                   CollisionTypes.ACTIVABLE_BY_GEM,
                                   wounded_rescue_center_collision)
        rescue_center = RescueCenter(size=(210, 90))
        playground.add(rescue_center, ((440, 315), 0))

        add_walls(playground)
        add_boxes(playground)

        # WOUNDED PERSONS
        playground.add(self._drones[0], ((-50, 0), 0))

        return playground


def main():
    my_map = MyMapLidar()
    my_drone = MyDroneLidar(should_display_lidar=True,
                            should_display_touch=False)
    my_map.set_drones([my_drone])
    playground = my_map.construct_playground()

    # draw_lidar : enable the visualization of the lidar rays
    # enable_visu_noises : to enable the visualization. It will show also a demonstration of the integration
    # of odometer values, by drawing the estimated path in red. The green circle shows the position of drone according
    # to the gps sensor and the compass
    gui = GuiSR(playground=playground,
                the_map=my_map,
                drones=[my_drone],
                draw_lidar=True,
                use_keyboard=True,
                enable_visu_noises=True,
                )
    gui.run()


if __name__ == '__main__':
    main()
