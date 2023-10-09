"""
This program can be launched directly.
To move the drone, you have to click on the map, then use the arrows on the keyboard
"""

import os
import sys
from typing import Type

from spg.playground import Playground
from spg.utils.definitions import CollisionTypes

# This line add, to sys.path, the path to parent path of this file
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from maps.walls_medium_02 import add_walls, add_boxes
from spg_overlay.entities.drone_abstract import DroneAbstract
from spg_overlay.entities.rescue_center import RescueCenter, wounded_rescue_center_collision
from spg_overlay.gui_map.closed_playground import ClosedPlayground
from spg_overlay.gui_map.gui_sr import GuiSR
from spg_overlay.gui_map.map_abstract import MapAbstract
from spg_overlay.utils.misc_data import MiscData


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

        # PARAMETERS MAP
        self._size_area = (1113, 750)

        self._rescue_center = RescueCenter(size=(210, 90))
        self._rescue_center_pos = ((440, 315), 0)

        self._number_drones = 1
        self._drones_pos = [((-50, 0), 0)]
        self._drones = []

    def construct_playground(self, drone_type: Type[DroneAbstract]) -> Playground:
        playground = ClosedPlayground(size=self._size_area)

        # RESCUE CENTER
        playground.add_interaction(CollisionTypes.GEM,
                                   CollisionTypes.ACTIVABLE_BY_GEM,
                                   wounded_rescue_center_collision)

        playground.add(self._rescue_center, self._rescue_center_pos)

        add_walls(playground)
        add_boxes(playground)

        # POSITIONS OF THE DRONES
        misc_data = MiscData(size_area=self._size_area,
                             number_drones=self._number_drones)
        for i in range(self._number_drones):
            drone = drone_type(identifier=i, misc_data=misc_data,
                               display_lidar_graph=True)
            self._drones.append(drone)
            playground.add(drone, self._drones_pos[i])

        return playground


def main():
    my_map = MyMapLidar()
    playground = my_map.construct_playground(drone_type=MyDroneLidar)

    # draw_lidar_rays : enable the visualization of the lidar rays
    # enable_visu_noises : to enable the visualization. It will show also a demonstration of the integration
    # of odometer values, by drawing the estimated path in red. The green circle shows the position of drone according
    # to the gps sensor and the compass
    gui = GuiSR(playground=playground,
                the_map=my_map,
                draw_lidar_rays=True,
                use_keyboard=True,
                enable_visu_noises=True,
                )
    gui.run()


if __name__ == '__main__':
    main()
