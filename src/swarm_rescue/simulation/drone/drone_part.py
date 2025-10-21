""" Module that defines the base class Part and Actuator.

Part inherits from Entity, and is used to create different body parts
of an agent. Parts are visible and movable by default.

"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict, List, Optional, Union

from swarm_rescue.simulation.drone.controller import Command
from swarm_rescue.simulation.drone.device import Device
from swarm_rescue.simulation.drone.grasper import Grasper
from swarm_rescue.simulation.elements.physical_entity import PhysicalEntity

if TYPE_CHECKING:
    from swarm_rescue.simulation.utils.position import Coordinate
    from swarm_rescue.simulation.drone.agent import Agent

CommandDict = Dict[Command, Union[float, int]]


class DronePart(PhysicalEntity, ABC):
    """
    Base class for drone body parts. Inherits from PhysicalEntity.
    """

    def __init__(self, **kwargs):
        """
        Initialize a DronePart.

        Args:
            **kwargs: Additional keyword arguments.
        """
        super().__init__(
            **kwargs,
        )

        # Add physical motors if needed
        self._devices: List[Device] = []

        self._agent: Optional[Agent] = None

    @property
    def agent(self) -> Optional["Agent"]:
        """
        Returns the agent to which this part belongs.
        """
        return self._agent

    @agent.setter
    def agent(self, agent: "Agent") -> None:
        """
        Set the agent for this part.

        Args:
            agent (Agent): The agent to set.
        """
        self._agent = agent

    @property
    def devices(self) -> List[Device]:
        """
        Returns the list of devices attached to this part.
        """
        return self._devices

    def add_device(self, device: Device) -> None:
        """
        Attach a device to this part.

        Args:
            device (Device): The device to add.
        """
        device.set_anchor(self)

        if isinstance(device, Device):
            self._devices.append(device)
        else:
            raise ValueError("Not implemented")

    def move_to(  # pylint: disable=arguments-differ
            self,
            coordinates: Coordinate,
            move_anchors: bool = False,
            **kwargs,
    ) -> None:
        """
        Move the part to the given coordinates.

        Args:
            coordinates (Coordinate): The coordinates to move to.
            move_anchors (bool): Whether to move anchors as well.
            **kwargs: Additional keyword arguments.
        """
        super().move_to(coordinates=coordinates, **kwargs)

    def apply_commands(self, **kwargs) -> None:
        """
        Apply commands to the part and its devices.

        Args:
            **kwargs: Additional keyword arguments.
        """
        self._apply_commands(**kwargs)

        for device in self.devices:
            if isinstance(device, Grasper):
                device.apply_commands()

    @abstractmethod
    def _apply_commands(self, **kwargs) -> None:
        """
        Abstract method to apply commands to the part.

        Args:
            **kwargs: Additional keyword arguments.
        """
        ...

    def pre_step(self) -> None:
        """
        Prepare the part and its devices for a new simulation step.
        """
        super().pre_step()
        for device in self._devices:
            device.pre_step()

    def post_step(self) -> None:
        """
        Finalize the part and its devices after a simulation step.
        """
        super().post_step()
        for device in self._devices:
            device.post_step()

    def reset(self) -> None:
        """
        Reset the part and its devices to their initial state.
        """
        super().reset()

        self._pm_body.velocity = (0, 0)
        self._pm_body.angular_velocity = 0

        for device in self._devices:
            device.reset()
