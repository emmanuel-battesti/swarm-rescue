"""
This program can be launched directly.
To move the drone, you have to click on the map, then use the arrows on the keyboard
"""

import os
import sys
from typing import Type

from spg.utils.definitions import CollisionTypes

# This line add, to sys.path, the path to parent path of this file
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from spg_overlay.reporting.data_saver import DataSaver
from spg_overlay.reporting.team_info import TeamInfo
from spg_overlay.entities.drone_abstract import DroneAbstract
from spg_overlay.entities.sensor_disablers import NoComZone, KillZone, srdisabler_disables_device
from spg_overlay.gui_map.closed_playground import ClosedPlayground
from spg_overlay.gui_map.gui_sr import GuiSR
from spg_overlay.gui_map.map_abstract import MapAbstract
from spg_overlay.utils.misc_data import MiscData


class MyDroneComDisabler(DroneAbstract):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def define_message_for_all(self):
        """
        Here, we don't need communication...
        """
        msg_data = (self.identifier,
                    (self.measured_gps_position(), self.measured_compass_angle()))
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


class MyMapComDisabler(MapAbstract):

    def __init__(self):
        super().__init__()

        # PARAMETERS MAP
        self._size_area = (1000, 600)

        self._no_com_zone = NoComZone(size=(150, 150))
        self._no_com_zone_pos = ((-350, 0), 0)

        self._kill_zone = KillZone(size=(150, 150))
        self._kill_zone_pos = ((-200, -200), 0)

        self._number_drones = 5
        self._drones_pos = [((450, 0), 3.1416), ((-350, 0), 0), ((-200, -200), 1.57), ((0, -200), 1.57),
                            ((-200, 200), -1.57)]
        self._drones = []

    def construct_playground(self, drone_type: Type[DroneAbstract]):
        playground = ClosedPlayground(size=self._size_area)

        # DISABLER ZONES
        playground.add_interaction(CollisionTypes.DISABLER,
                                   CollisionTypes.DEVICE,
                                   srdisabler_disables_device)

        playground.add(self._no_com_zone, self._no_com_zone_pos)
        playground.add(self._kill_zone, self._kill_zone_pos)

        # POSITIONS OF THE DRONES
        misc_data = MiscData(size_area=self._size_area,
                             number_drones=self._number_drones)
        for i in range(self._number_drones):
            drone = drone_type(identifier=i, misc_data=misc_data)
            self._drones.append(drone)
            playground.add(drone, self._drones_pos[i])

        return playground


def main():
    my_map = MyMapComDisabler()
    playground = my_map.construct_playground(drone_type=MyDroneComDisabler)

    team_info = TeamInfo()
    data_saver = DataSaver(team_info, enabled=True)
    video_capture_enabled = True
    video_capture_enabled &= data_saver.enabled
    if video_capture_enabled:
        filename_video_capture = data_saver.path + "/example_com_disabler.avi"
    else:
        filename_video_capture = None

    # enable_visu_noises : to enable the visualization. It will show also a demonstration of the integration
    # of odometer values, by drawing the estimated path in red. The green circle shows the position of drone according
    # to the gps sensor and the compass.
    gui = GuiSR(playground=playground,
                the_map=my_map,
                print_messages=True,
                draw_com=True,
                use_keyboard=True,
                enable_visu_noises=False,
                filename_video_capture=filename_video_capture
                )
    gui.run()


if __name__ == '__main__':
    main()
