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

        A device is anchored either to a drone part, which knows its agent, or
        to a wounded person, which has none. `getattr` keeps that duck-typed
        rather than importing `DronePart` here, which would be circular.
        """
        anchor = self.anchor
        agent = getattr(anchor, "agent", None)
        assert agent is not None, f"{anchor!r} belongs to no agent."
        return agent

    @property
    def is_switched_off(self) -> bool:
        """
        Whether this device must currently be treated as switched off.

        Two separate reasons, and they are not the same:

        - a disabler zone switched it off for the current step. `_disabled` is
          reset at every `pre_step`, so it says nothing beyond that step.
        - its drone was destroyed. That is permanent until the drone is reset,
          and it is what stops a wreck from still reading, or drawing, the world.

        Not named `is_disabled`, because `DroneGPS`, `DroneCompass` and
        `DroneOdometry` already define an `is_disabled()` *method*, which
        `DroneAbstract.gps_is_disabled()` and friends call. A property here would
        be shadowed by those, so the two would quietly disagree about the same
        device.

        Note that `_disabled` is deliberately not enough on its own: a dead
        drone's devices are re-enabled by the next `pre_step` like everyone
        else's, so a sensor drawing on `_disabled` alone would come back to life
        one step after its drone died.
        """
        if self._disabled:
            return True

        agent = self.agent
        return agent is not None and agent.is_dead

