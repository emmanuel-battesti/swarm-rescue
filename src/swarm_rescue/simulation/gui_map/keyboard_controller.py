import arcade

from swarm_rescue.simulation.drone.controller import CommandsDict


class KeyboardController:
    """
    The KeyboardController class is responsible for handling keyboard input and
    converting it into commands for controlling a robot. It keeps track of the
    current command values for forward movement, lateral movement,
    rotation, and the grasper.
    """

    def __init__(self):
        """
        Initialize the KeyboardController.
        """
        # A dictionary that stores the current command values for forward movement,
        # lateral movement, rotation, and the grasper.
        self._command: CommandsDict = {"forward": 0.0,
                                       "lateral": 0.0,
                                       "rotation": 0.0,
                                       "grasper": 0}

    def on_key_press(self, key: int, modifiers: int) -> None:
        """
        Called whenever a key is pressed. Updates the command values based
        on the pressed key.

        Args:
            key (int): The key code pressed.
            modifiers (int): Bitwise OR of all modifier keys currently pressed.
        """
        if self._command:

            if key == arcade.key.UP:
                self._command["forward"] = 1.0
            elif key == arcade.key.DOWN:
                self._command["forward"] = -1.0

            if key == arcade.key.LEFT or key == arcade.key.RIGHT:
                # Both lateral and rotation are driven by the same two keys:
                # the plain key turns, Shift + key strafes. Both values are
                # therefore reset before re-evaluating the modifiers, so that
                # releasing (or pressing) Shift while the key is still held
                # switches mode instead of leaving the previous one active.
                self._command["lateral"] = 0.0
                self._command["rotation"] = 0.0

                if not modifiers & arcade.key.MOD_SHIFT:
                    if key == arcade.key.LEFT:
                        self._command["rotation"] = 1.0
                    else:
                        self._command["rotation"] = -1.0
                else:
                    if key == arcade.key.LEFT:
                        self._command["lateral"] = 1.0
                    else:
                        self._command["lateral"] = -1.0

            if key == arcade.key.W:
                self._command["grasper"] = 1

    def on_key_release(self, key: int, _: int) -> None:
        """
        Called whenever a key is released. Resets the command values based
        on the released key.

        Args:
            key (int): The key code released.
            _ (int): Bitwise OR of all modifier keys currently pressed.
        """
        if self._command:

            if key == arcade.key.UP:
                self._command["forward"] = 0
            elif key == arcade.key.DOWN:
                self._command["forward"] = 0

            if key == arcade.key.LEFT:
                self._command["lateral"] = 0
                self._command["rotation"] = 0
            elif key == arcade.key.RIGHT:
                self._command["lateral"] = 0
                self._command["rotation"] = 0

            if key == arcade.key.W:
                self._command["grasper"] = 0

    def control(self) -> CommandsDict:
        """
        Returns the current command values.

        Returns:
            CommandsDict: The current command dictionary.
        """
        return self._command
