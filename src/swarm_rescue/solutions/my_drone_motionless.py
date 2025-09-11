"""
The Drone will not move.
"""
from typing import Optional

from swarm_rescue.simulation.drone.controller import CommandsDict
from swarm_rescue.simulation.drone.drone_abstract import DroneAbstract
from swarm_rescue.simulation.utils.misc_data import MiscData


class MyDroneMotionless(DroneAbstract):
    """
    Drone controller that does not move.
    """
    def __init__(self,
                 identifier: Optional[int] = None,
                 misc_data: Optional[MiscData] = None,
                 **kwargs):
        """
        Initializes a motionless drone.

        Args:
            identifier (Optional[int]): Drone identifier.
            misc_data (Optional[MiscData]): Miscellaneous data.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(identifier=identifier,
                         misc_data=misc_data,
                         **kwargs)

    def define_message_for_all(self) -> None:
        """
        No communication needed for a motionless drone.
        """
        pass

    def control(self) -> CommandsDict:
        """
        Returns a command that keeps the drone motionless.

        Returns:
            CommandsDict: The motionless command.
        """
        command_motionless: CommandsDict = {"forward": 0.0,
                                            "lateral": 0.0,
                                            "rotation": 0.0,
                                            "grasper": 0}

        return command_motionless

