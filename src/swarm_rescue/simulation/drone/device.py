from __future__ import annotations

from swarm_rescue.simulation.drone.interactive_anchored import InteractiveAnchored
from swarm_rescue.simulation.utils.definitions import CollisionTypes


class Device(InteractiveAnchored):
    """
    Base class for all devices attached to drone parts.
    """

    def __init__(
            self,
            **kwargs,
    ):
        """
        Initialize the Device.

        Args:
            **kwargs: Additional keyword arguments.
        """
        super().__init__(
            **kwargs,
        )
        self._disabled: bool = False

    @property
    def _collision_type(self) -> CollisionTypes:
        """
        Returns the collision type for the device.
        """
        return CollisionTypes.DEVICE

    def pre_step(self) -> None:
        """
        Reset the device's disabled state before each simulation step.
        """
        self._disabled = False

    def disable(self) -> None:
        """
        Disable the device for the current step.
        """
        self._disabled = True

    @property
    def agent(self):
        """
        Returns the agent to which this device is attached.
        """
        assert self._anchor
        return self._anchor.agent

