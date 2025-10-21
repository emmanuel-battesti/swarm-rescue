"""
Module that defines DisappearingWall class - walls that disappear after a specified time
"""
from typing import Tuple

from swarm_rescue.simulation.elements.normal_wall import NormalWall, NormalBox


class DisappearingWall(NormalWall):
    """
    A wall that disappears after a specified duration (in timesteps).

    After the wall disappears, drones can pass through the area where it was.

    Example Usage:
        # Create a wall that disappears after 150 timesteps
        wall = DisappearingWall(pos_start=(0, 0), pos_end=(100, 0), disappear_after_timesteps=150)
    """

    def __init__(
        self,
        pos_start: Tuple[float, float],
        pos_end: Tuple[float, float],
        disappear_after_timesteps: int = 900,  # Default to 900 timesteps (30 seconds at 30 FPS)
        wall_thickness: int = 6,
        **kwargs
    ):
        """
        Initialize a DisappearingWall.

        Args:
            pos_start (Tuple[float, float]): Start position of the wall.
            pos_end (Tuple[float, float]): End position of the wall.
            disappear_after_timesteps (int): Timesteps before the wall disappears.
            wall_thickness (int): Thickness of the wall.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(pos_start=pos_start, pos_end=pos_end, wall_thickness=wall_thickness, **kwargs)

        self._disappear_after_timesteps = disappear_after_timesteps
        self._disappeared = False
        self._creation_timestep = None

    @property
    def disappear_after_timesteps(self) -> int:
        """Returns the timesteps before disappearing."""
        return self._disappear_after_timesteps

    @property
    def disappeared(self) -> bool:
        """Returns whether the wall has disappeared."""
        return self._disappeared

    def pre_step(self):
        """
        Called before each physics step. Checks if it's time to disappear.
        """
        super().pre_step()

        # Record creation timestep on first step
        if self._creation_timestep is None and self._playground:
            self._creation_timestep = self._playground.timestep

        # Check if it's time to disappear
        if not self._disappeared and self._playground and self._creation_timestep is not None:
            elapsed_timesteps = self._playground.timestep - self._creation_timestep

            if elapsed_timesteps >= self._disappear_after_timesteps:
                self._disappear()

    def _disappear(self):
        """Make the wall disappear by removing it from the playground."""
        if self._disappeared or not self._playground:
            return

        self._disappeared = True
        # Remove the wall from the playground (definitive removal)
        self._playground.remove(self, definitive=True)


class DisappearingBox(NormalBox):
    """
    A box that disappears after a specified duration (in timesteps).

    After the box disappears, drones can pass through the area where it was.

    Example Usage:
        # Create a box that disappears after 1350 timesteps
        box = DisappearingBox(up_left_point=(0, 0), width=50, height=50, disappear_after_timesteps=1350)
    """

    def __init__(
        self,
        up_left_point: Tuple[float, float],
        width: float,
        height: float,
        disappear_after_timesteps: int = 900,  # Default to 900 timesteps (30 seconds at 30 FPS)
        **kwargs
    ):
        """
        Initialize a DisappearingBox.

        Args:
            up_left_point (Tuple[float, float]): Upper left point of the box.
            width (float): Width of the box.
            height (float): Height of the box.
            disappear_after_timesteps (int): Timesteps before the box disappears.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(up_left_point=up_left_point, width=width, height=height, **kwargs)

        self._disappear_after_timesteps = disappear_after_timesteps
        self._disappeared = False
        self._creation_timestep = None

    @property
    def disappear_after_timesteps(self) -> int:
        """Returns the timesteps before disappearing."""
        return self._disappear_after_timesteps

    @property
    def disappeared(self) -> bool:
        """Returns whether the box has disappeared."""
        return self._disappeared

    def pre_step(self):
        """
        Called before each physics step. Checks if it's time to disappear.
        """
        super().pre_step()

        # Record creation timestep on first step
        if self._creation_timestep is None and self._playground:
            self._creation_timestep = self._playground.timestep

        # Check if it's time to disappear
        if not self._disappeared and self._playground and self._creation_timestep is not None:
            elapsed_timesteps = self._playground.timestep - self._creation_timestep

            if elapsed_timesteps >= self._disappear_after_timesteps:
                self._disappear()

    def _disappear(self):
        """Make the box disappear by removing it from the playground."""
        if self._disappeared or not self._playground:
            return

        self._disappeared = True
        # Remove the box from the playground (definitive removal)
        self._playground.remove(self, definitive=True)

