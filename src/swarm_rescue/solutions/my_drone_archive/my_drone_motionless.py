"""
The Drone will not move.
"""
from typing import Optional

from spg_overlay.entities.drone_abstract import DroneAbstract
from spg_overlay.utils.misc_data import MiscData


class MyDroneMotionless(DroneAbstract):
    def __init__(self,
                 identifier: Optional[int] = None,
                 misc_data: Optional[MiscData] = None,
                 **kwargs):
        super().__init__(identifier=identifier,
                         misc_data=misc_data,
                         **kwargs)


    def define_message_for_all(self):
        """
        Here, we don't need communication...
        """
        pass

    def control(self):
        """
        The Drone will not move
        """
        command_motionless = {"forward": 0.0,
                            "lateral": 0.0,
                            "rotation": 0.0,
                            "grasper": 0}

        return command_motionless
