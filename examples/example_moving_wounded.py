"""
This program can be launched directly.
To move the drone, you have to click on the map, then use the arrows on the keyboard
"""

import pathlib
import sys
from typing import List, Type

import numpy as np

# Insert the 'src' directory, located two levels up from the current script,
# into sys.path. This ensures Python can find project-specific modules
# (e.g., 'swarm_rescue') when the script is run from a subfolder like 'examples/'.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from swarm_rescue.simulation.drone.controller import CommandsDict
from swarm_rescue.simulation.reporting.result_path_creator import ResultPathCreator
from swarm_rescue.simulation.reporting.team_info import TeamInfo
from swarm_rescue.simulation.drone.drone_abstract import DroneAbstract
from swarm_rescue.simulation.elements.rescue_center import RescueCenter
from swarm_rescue.simulation.elements.wounded_person import WoundedPerson
from swarm_rescue.simulation.gui_map.closed_playground import ClosedPlayground
from swarm_rescue.simulation.gui_map.gui_sr import GuiSR
from swarm_rescue.simulation.gui_map.map_abstract import MapAbstract
from swarm_rescue.simulation.utils.misc_data import MiscData
from swarm_rescue.simulation.utils.pose import Pose


class MyDroneMovingWounded(DroneAbstract):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def define_message_for_all(self):
        """
        Here, we don't need communication...
        """
        msg_data = (self.identifier,
                    (self.measured_gps_position(), self.measured_compass_angle()))
        return msg_data

    def control(self) -> CommandsDict:
        """
        We only send a command to do nothing
        """
        command: CommandsDict = {"forward": 0.0,
                                 "lateral": 0.0,
                                 "rotation": 0.0,
                                 "grasper": 0}
        return command


class MyMapMovingWounded(MapAbstract):

    def __init__(self, drone_type: Type[DroneAbstract]):
        super().__init__(drone_type=drone_type)

        # PARAMETERS MAP
        self._size_area = (600, 600)

        self._rescue_center = RescueCenter(size=(100, 100))
        self._rescue_center_pos = ((0, 250), 0)

        self._wounded_persons_pos = [(200, 0), (-200, 0), (-200, -200), (150, -200)]
        self._wounded_persons_path = [[(250, 0), (250, 100)],
                                      [(-250, 0)],
                                      [],
                                      [(150, -200), (250, -200), (250, -100), (150, -100), (150, -100), (150, -200)],
                                      ]
        self._number_wounded_persons = len(self._wounded_persons_pos)
        self._wounded_persons: List[WoundedPerson] = []

        self._number_drones = 1
        self._drones_pos = [((0, 200), 0)]
        self._drones = []

        self._playground = ClosedPlayground(size=self._size_area)

        self._playground.add(self._rescue_center, self._rescue_center_pos)

        # POSITIONS OF THE WOUNDED PERSONS
        for i in range(self._number_wounded_persons):
            wounded_person = WoundedPerson(rescue_center=self._rescue_center)
            self._wounded_persons.append(wounded_person)
            init_pos = (self._wounded_persons_pos[i], 0)
            self._playground.add(wounded_person, init_pos)

            list_path = self._wounded_persons_path[i]
            wounded_person.add_pose_to_path(Pose(np.array(init_pos[0])))
            for pt in list_path:
                wounded_person.add_pose_to_path(Pose(np.array(list(pt))))

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
    the_map = MyMapMovingWounded(drone_type=MyDroneMovingWounded)

    # Set this value to True to generate a video of the mission
    video_capture_enabled = False
    if video_capture_enabled:
        team_info = TeamInfo()
        rpc = ResultPathCreator(team_info)
        filename_video_capture = rpc.path + "/example_movingWounded.avi"
    else:
        filename_video_capture = None

    # enable_visu_noises : to enable the visualization. It will show also a demonstration of the integration
    # of odometer values, by drawing the estimated path in red. The green circle shows the position of drone according
    # to the gps sensor and the compass.
    gui = GuiSR(the_map=the_map,
                print_messages=True,
                use_keyboard=True,
                enable_visu_noises=False,
                filename_video_capture=filename_video_capture
                )
    gui.run()


if __name__ == '__main__':
    main()
