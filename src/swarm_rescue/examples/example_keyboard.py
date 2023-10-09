"""
This program can be launched directly.
To move the drone, you have to click on the map, then use the arrows on the keyboard
"""

import os
import sys
from typing import List, Type

from spg.utils.definitions import CollisionTypes

# This line add, to sys.path, the path to parent path of this file
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from spg_overlay.entities.drone_abstract import DroneAbstract
from spg_overlay.entities.rescue_center import RescueCenter, wounded_rescue_center_collision
from spg_overlay.entities.wounded_person import WoundedPerson
from spg_overlay.gui_map.closed_playground import ClosedPlayground
from spg_overlay.gui_map.gui_sr import GuiSR
from spg_overlay.gui_map.map_abstract import MapAbstract
from spg_overlay.utils.misc_data import MiscData


class MyDroneKeyboard(DroneAbstract):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def define_message_for_all(self):
        """
        Here, we don't need communication...
        """
        pass

    def control(self):
        command = {"forward": 0.0,
                   "lateral": 0.0,
                   "rotation": 0.0,
                   "grasper": 0}
        return command


class MyMapKeyboard(MapAbstract):

    def __init__(self):
        super().__init__()

        # PARAMETERS MAP
        self._size_area = (600, 600)

        self._rescue_center = RescueCenter(size=(100, 100))
        self._rescue_center_pos = ((0, 100), 0)

        self._wounded_persons_pos = [(200, 0), (-200, 0), (200, -200), (-200, -200)]
        self._number_wounded_persons = len(self._wounded_persons_pos)
        self._wounded_persons: List[WoundedPerson] = []

        self._number_drones = 1
        self._drones_pos = [((0, 0), 0)]
        self._drones = []

    def construct_playground(self, drone_type: Type[DroneAbstract]):
        playground = ClosedPlayground(size=self._size_area)

        # RESCUE CENTER
        playground.add_interaction(CollisionTypes.GEM,
                                   CollisionTypes.ACTIVABLE_BY_GEM,
                                   wounded_rescue_center_collision)

        playground.add(self._rescue_center, self._rescue_center_pos)

        # POSITIONS OF THE WOUNDED PERSONS
        for i in range(self._number_wounded_persons):
            wounded_person = WoundedPerson(rescue_center=self._rescue_center)
            self._wounded_persons.append(wounded_person)
            pos = (self._wounded_persons_pos[i], 0)
            playground.add(wounded_person, pos)

        # POSITIONS OF THE DRONES
        misc_data = MiscData(size_area=self._size_area,
                             number_drones=self._number_drones)
        for i in range(self._number_drones):
            drone = drone_type(identifier=i, misc_data=misc_data)
            self._drones.append(drone)
            playground.add(drone, self._drones_pos[i])

        return playground


def print_keyboard_man():
    print("How to use the keyboard to direct the drone?")
    print("\t- up / down key : forward and backward")
    print("\t- left / right key : turn left / right")
    print("\t- shift + left/right key : left/right lateral movement")
    print("\t- G key : grasp objects")
    print("\t- L key : display (or not) the lidar sensor")
    print("\t- S key : display (or not) the semantic sensor")
    print("\t- P key : draw position from GPS sensor")
    print("\t- C key : draw communication between drones")
    print("\t- M key : print messages between drones")
    print("\t- Q key : exit the program")
    print("\t- R key : reset")


def main():
    print_keyboard_man()
    my_map = MyMapKeyboard()

    playground = my_map.construct_playground(drone_type=MyDroneKeyboard)

    # draw_lidar_rays : enable the visualization of the lidar rays
    # draw_semantic_rays : enable the visualization of the semantic rays
    gui = GuiSR(playground=playground,
                the_map=my_map,
                draw_lidar_rays=True,
                draw_semantic_rays=True,
                use_keyboard=True,
                )
    gui.run()


if __name__ == '__main__':
    main()
