"""
This program can be launched directly.
To move the drone, you have to click on the map, then use the arrows on the keyboard
"""

import os
import sys

from spg.utils.definitions import CollisionTypes

# This line add, to sys.path, the path to parent path of this file
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from spg_overlay.entities.drone_abstract import DroneAbstract
from spg_overlay.entities.rescue_center import RescueCenter, wounded_rescue_center_collision
from spg_overlay.entities.sensor_disablers import NoGpsZone, NoComZone, KillZone, srdisabler_disables_device
from spg_overlay.entities.wounded_person import WoundedPerson
from spg_overlay.gui_map.closed_playground import ClosedPlayground
from spg_overlay.gui_map.gui_sr import GuiSR
from spg_overlay.gui_map.map_abstract import MapAbstract


class MyDroneDisablers(DroneAbstract):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def define_message_for_all(self):
        """
        Here, we don't need communication...
        """
        msg_data = (self.identifier,
                    (self.measured_position(), self.measured_angle()))
        return msg_data

    def control(self):
        """
        We only send a command to do nothing
        """
        command = {"forward": 0.0,
                   "lateral": 0.0,
                   "rotation": 0.0,
                   "grasper": 0}
        return command


class MyMapDisablers(MapAbstract):

    def __init__(self):
        super().__init__()
        self._size_area = (600, 600)
        self._number_drones = 1

    def construct_playground(self):
        playground = ClosedPlayground(size=self._size_area)

        # RESCUE CENTER
        playground.add_interaction(CollisionTypes.GEM,
                                   CollisionTypes.ACTIVABLE_BY_GEM,
                                   wounded_rescue_center_collision)
        rescue_center = RescueCenter(size=(100, 100))
        playground.add(rescue_center, ((0, 100), 0))

        # WOUNDED PERSONS
        wounded_persons_pos = [(200, 0), (-200, 0), (200, -200), (-200, -200)]
        self._number_wounded_persons = len(wounded_persons_pos)

        for i in range(self._number_wounded_persons):
            wounded_person = WoundedPerson(rescue_center=rescue_center)
            pos = (wounded_persons_pos[i], 0)
            playground.add(wounded_person, pos)

        # DISABLERS
        playground.add_interaction(CollisionTypes.DISABLER,
                                   CollisionTypes.DEVICE,
                                   srdisabler_disables_device)

        no_gps_disabler = NoGpsZone(size=(150, 150))
        playground.add(no_gps_disabler, ((150, 0), 0))

        no_com_disabler = NoComZone(size=(150, 150))
        playground.add(no_com_disabler, ((-150, 0), 0))

        kill_disabler = KillZone(size=(150, 150))
        playground.add(kill_disabler, ((0, -200), 0))

        # POSITIONS OF THE DRONES
        playground.add(self._drones[0], ((0, 0), 0))

        return playground


def main():
    my_map = MyMapDisablers()
    my_drone = MyDroneDisablers()
    my_map.set_drones([my_drone])
    playground = my_map.construct_playground()

    gui = GuiSR(playground=playground,
                the_map=my_map,
                drones=[my_drone],
                print_messages=True,
                use_keyboard=True)
    gui.run()


if __name__ == '__main__':
    main()
