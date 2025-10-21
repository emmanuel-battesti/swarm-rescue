from __future__ import annotations

from abc import abstractmethod
from typing import Union, Dict

import numpy as np

from swarm_rescue.simulation.drone.pocket_device import PocketDevice

CommandName = str
Command = Union[float, int, bool]
CommandsDict = Dict[CommandName, Command]

CONTROLLER_COLOR = (123, 234, 213)


class Controller(PocketDevice):
    """
    Command classes define how parts can be controlled.
    It is used to control parts of an agent:
        - physical actions (movements)
        - interactive actions (eat, grasp, ...)
    """

    def __init__(self, name: str, hard_check: bool = True, **_):
        """
        Initialize the controller.

        Args:
            name (str): Name of the controller.
            hard_check (bool): If True, raise error on invalid command.
            **_: Additional keyword arguments.
        """
        super().__init__(name=name, color=CONTROLLER_COLOR)

        self._command = self.default
        self._hard_check = hard_check
        self._currently_disabled = False

    @property
    def _rng(self):
        """
        Returns the random number generator for the playground.
        """
        if self._playground:
            return self._playground.rng

        return np.random.default_rng()

    @property
    @abstractmethod
    def default(self) -> Command:
        """
        Returns the default command value.
        """
        ...

    @abstractmethod
    def get_random_commands(self) -> Command:
        """
        Returns a random valid command.
        """
        ...

    @property
    def command(self) -> Command:
        """
        Returns the current command value.
        """
        return self._command

    @command.setter
    def command(self, command: Command):
        """
        Set the command value, checking validity.

        Args:
            command (Command): The command to set.

        Raises:
            ValueError: If the command is invalid and hard_check is True.
        """
        check_passed = self._check(command)

        if not check_passed and self._hard_check:
            raise ValueError(f"Invalid command '{command}' for controller '{self.name}'. Expected type: {type(self.default).__name__}")

        # Maybe replace by closest later?
        if not check_passed or self._currently_disabled:
            command = self.default

        self._command = command

    def pre_step(self):
        """
        Reset the command to default before each simulation step.
        """
        super().pre_step()
        self._command = self.default

    def post_step(self):
        """
        Update the disabled state after each simulation step.
        """
        self._currently_disabled = self._disabled

    def reset(self):
        """
        Reset the controller state.
        """
        self.pre_step()

    @abstractmethod
    def _check(self, command: Command) -> bool:
        """
        Check if a command is valid.

        Args:
            command (Command): The command to check.

        Returns:
            bool: True if valid, False otherwise.
        """
        ...

    @property
    def command_value(self) -> Command:
        """
        Returns the current command value.
        """
        return self._command


class GrasperController(Controller):
    """
    Grasper Commands.
    Command values can take a number within a list of integers.
    0 is always the default command, even if not given at initialization.
    """

    def __init__(
            self,
            name: str,
            **kwargs,
    ):
        """
        Initialize the GrasperController.

        Args:
            name (str): Name of the controller.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(name=name, **kwargs)

        self._valid_command_values = [0, 1]

    def _check(self, command: Command) -> bool:
        """
        Check if the command is valid for the grasper.

        Args:
            command (Command): The command to check.

        Returns:
            bool: True if valid, False otherwise.
        """
        return command in self._valid_command_values

    @property
    def default(self) -> int:
        """
        Returns the default command value (0).
        """
        return 0

    @property
    def valid_commands(self):
        """
        Returns the list of valid command values.
        """
        return self._valid_command_values

    def get_random_commands(self) -> int:
        """
        Returns a random valid command value.
        """
        return self._playground.rng.choice(self._valid_command_values)


class CenteredContinuousController(Controller):
    """
    Controller for continuous commands in the range [-1, 1].
    """

    def __init__(self, name: str, **kwargs):
        """
        Initialize the CenteredContinuousController.

        Args:
            name (str): Name of the controller.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(name=name, **kwargs)

        self._min = -1
        self._max = 1

    def _check(self, command: Command) -> bool:
        """
        Check if the command is within the allowed range.

        Args:
            command (Command): The command to check.

        Returns:
            bool: True if valid, False otherwise.
        """
        return self._min <= command <= self._max

    @property
    def default(self) -> float:
        """
        Returns the default command value (0.0).
        """
        return 0

    @property
    def min(self) -> float:
        """
        Returns the minimum allowed command value.
        """
        return self._min

    @property
    def max(self) -> float:
        """
        Returns the maximum allowed command value.
        """
        return self._max

    def get_random_commands(self) -> float:
        """
        Returns a random command value in the allowed range.
        """
        return self._playground.rng.uniform(self._min, self._max)
