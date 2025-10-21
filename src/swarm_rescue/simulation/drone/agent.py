# pylint: disable=too-many-public-methods

""" Contains the base class for agents.

Agent class should be inherited to create agents.
It is possible to define custom Agent with
body parts, sensors and corresponding Keyboard controllers.

Examples can be found in spg/agents/agents.py

"""
from __future__ import annotations

from swarm_rescue.simulation.drone.communicator import Communicator
from swarm_rescue.simulation.drone.controller import Controller, CommandsDict
from swarm_rescue.simulation.drone.drone_base import DroneBase
from swarm_rescue.simulation.ray_sensors.external_sensor import ExternalSensor
from swarm_rescue.simulation.drone.sensor import Sensor
from swarm_rescue.simulation.elements.embodied import EmbodiedEntity
from swarm_rescue.simulation.elements.entity import Entity
from swarm_rescue.simulation.utils.position import Coordinate

_BORDER_IMAGE = 3


class Agent(Entity):
    """
    Base class for building agents.
    Agents are composed of a base and parts which are attached to the base
    or to each other.
    Each part has actuators allowing for control of the agent.
    The base has no actuator.

    Attributes:
        name: name of the agent.
            Either provided by the user or generated using internal counter.
        base: Main part of the agent. Can be mobile or fixed.
        parts: Different parts attached to the base or to other parts.
        actuators:
        sensors:
        initial_coordinates:
    """

    _index_agent: int = 0

    def __init__(
            self,
            **kwargs,
    ):
        """
        Initialize the Agent.

        Args:
            **kwargs: Additional keyword arguments.
        """
        super().__init__(**kwargs)

        # Body parts
        self._base: DroneBase | None = None

        # Reward
        self._reward: float = 0

        self._initial_coordinates = None
        self._allow_overlapping = False

    def add_base(self, base: DroneBase) -> None:
        """
        Attach a base to the agent.

        Args:
            base (DroneBase): The base to attach.
        """
        base.agent = self
        self._base = base

    ################
    # Properties
    ################

    @property
    def base(self) -> DroneBase:
        """Return the base of the agent."""
        return self._base

    @property
    def initial_coordinates(self):
        """Return the initial coordinates of the agent."""
        return self._initial_coordinates

    @initial_coordinates.setter
    def initial_coordinates(self, init_coord):
        """Set the initial coordinates of the agent and its base."""
        self._initial_coordinates = init_coord
        self.base.initial_coordinates = init_coord

    @property
    def allow_overlapping(self):
        """Return whether the agent allows overlapping."""
        return self._allow_overlapping

    @allow_overlapping.setter
    def allow_overlapping(self, allow):
        """Set whether the agent allows overlapping."""
        self._allow_overlapping = allow
        self.base.allow_overlapping = allow

    @property
    def position(self):
        """Return the position of the agent (delegated to base)."""
        return self.base.position

    @property
    def angle(self):
        """Return the angle of the agent (delegated to base)."""
        return self.base.angle

    ################
    # Observations
    ################

    @property
    def observations(self) -> dict:
        """Return a dictionary of sensor names to their current values."""
        return {
            sens: sens.sensor_values
            for sens in self.base.devices
            if isinstance(sens, Sensor)
        }

    @property
    def controllers(self) -> list[Controller]:
        """Return a list of controllers attached to the agent."""
        return [
            contr
            for contr in self.base.devices
            if isinstance(contr, Controller)
        ]

    @property
    def _name_to_controller(self) -> dict:
        """Return a mapping from controller names to controller objects."""
        return {contr.name: contr for contr in self.controllers}

    @property
    def communicators(self) -> list[Communicator]:
        """Return a list of communicators attached to the agent."""
        return [
            comm
            for comm in self.base.devices
            if isinstance(comm, Communicator)
        ]

    @property
    def sensors(self) -> list[Sensor]:
        """Return a list of sensors attached to the agent."""
        return [
            sensor
            for sensor in self.base.devices
            if isinstance(sensor, Sensor)
        ]

    @property
    def external_sensors(self) -> list[ExternalSensor]:
        """Return a list of external sensors attached to the agent."""
        return [sensor for sensor in self.sensors if isinstance(sensor, ExternalSensor)]

    def compute_observations(self) -> None:
        """Update all sensors' values."""
        for sensor in self.sensors:
            sensor.update()

    ################
    # Commands
    ################

    @property
    def default_commands(self) -> CommandsDict:
        """Return a dictionary of default commands for each controller."""
        return {controller.name: controller.default for controller in self.controllers}

    def receive_commands(self, commands: CommandsDict) -> None:
        """
        Receive and apply commands to the agent's controllers.

        Args:
            commands (CommandsDict): Dictionary of controller names to commands.
        """
        if commands is None:
            return

        for controller_name, command in commands.items():
            controller = self._name_to_controller[controller_name]
            assert controller.agent is self
            controller.command = command

    def apply_commands(self) -> None:
        """Apply commands to the base (and thus to the playground physics)."""
        self.base.apply_commands()

    def get_random_commands(self) -> dict:
        """Return a dictionary of random commands for each controller."""
        return {contr.name: contr.get_random_commands() for contr in self.controllers}

    ################
    # Rewards
    ################

    @property
    def reward(self) -> float:
        """Return the current reward of the agent."""
        return self._reward

    @reward.setter
    def reward(self, rew: float):
        """Set the reward of the agent."""
        self._reward = rew

    ##############
    # CONTROL
    ##############

    def pre_step(self) -> None:
        """
        Reset actuators and reward to 0 before a new step of the environment.
        """
        self._reward = 0
        self.base.pre_step()

    def reset(self) -> None:
        """Reset the agent's base."""
        self.base.reset()

    def post_step(self) -> None:
        """Call post_step on the agent's base."""
        self.base.post_step()

    ###############
    # PLAYGROUND INTERACTIONS
    ###############

    def move_to(self, coord: Coordinate, **kwargs) -> None:
        """
        Move the agent to a given coordinate.

        After moving, the agent body is back in its original configuration.
        Default angle, etc.

        Args:
            coord (Coordinate): The coordinate to move to.
        """
        self.base.move_to(coordinates=coord, move_anchors=True, **kwargs)

    def _overlaps(
            self,
            entity: EmbodiedEntity,
    ) -> bool:
        """
        Check if the agent overlaps with another embodied entity.

        Args:
            entity (EmbodiedEntity): The entity to check overlap with.

        Returns:
            bool: True if overlapping, False otherwise.
        """
        assert self._playground

        if self._playground.overlaps(self.base, entity):
            return True

        return False
