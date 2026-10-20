"""
Module defining `DisappearingWall` and `DisappearingBox` classes.

These elements are walls or boxes that disappear from the simulation after a
specified number of physics timesteps, allowing agents to pass through their
original position afterward.
"""
from typing import Tuple

from swarm_rescue.simulation.elements.normal_wall import NormalWall, NormalBox


class DisappearingWall(NormalWall):
    """
    A wall that automatically disappears from the simulation after a
    predefined duration, measured in physics timesteps.

    Once the wall disappears, it is removed from the playground, and the space
    it previously occupied becomes traversable by drones.

    Example:
        # Create a wall that disappears after 150 timesteps
        wall = DisappearingWall(
            pos_start=(0, 0),
            pos_end=(100, 0),
            disappear_after_timesteps=150
        )
    """

    def __init__(
        self,
        pos_start: Tuple[float, float],
        pos_end: Tuple[float, float],
        disappear_after_timesteps: int = 900,
        wall_thickness: int = 6,
        **kwargs
    ):
        """
        Initializes a DisappearingWall.

        Args:
            pos_start: Starting coordinates of the wall (x, y).
            pos_end: Ending coordinates of the wall (x, y).
            disappear_after_timesteps: Number of timesteps to wait before
                making the wall disappear (default: 900, ~30s at 30 FPS).
            wall_thickness: Thickness of the wall.
            **kwargs: Additional keyword arguments for the base `NormalWall` class.
        """
        super().__init__(pos_start=pos_start, pos_end=pos_end, wall_thickness=wall_thickness, **kwargs)

        self._disappear_after_timesteps = disappear_after_timesteps
        self._disappeared = False
        self._creation_timestep = None

    @property
    def disappear_after_timesteps(self) -> int:
        """The number of timesteps before the wall disappears."""
        return self._disappear_after_timesteps

    @property
    def disappeared(self) -> bool:
        """Whether the wall has already disappeared."""
        return self._disappeared

    def pre_step(self):
        """
        Executes logic before the physics step.

        Tracks the creation time of the wall and checks if the elapsed
        time exceeds the disappearance threshold.
        """
        super().pre_step()

        # Record creation timestep on the first step, once in a playground
        if self._creation_timestep is None and self._playground:
            self._creation_timestep = self._playground.timestep

        # If not yet disappeared, check if the timeout has been reached
        if not self._disappeared and self._playground and self._creation_timestep is not None:
            elapsed_timesteps = self._playground.timestep - self._creation_timestep

            if elapsed_timesteps >= self._disappear_after_timesteps:
                self._disappear()

    def reset(self):
        """
        Resets the wall to its initial state.

        This makes the wall reappear and resets the disappearance timer.
        """
        super().reset()
        self._disappeared = False
        self._creation_timestep = None

    def _disappear(self):
        """
        Internal method to handle the wall's disappearance.

        Removes the wall from the playground if it hasn't already been removed.
        """
        if self._disappeared or not self._playground:
            return

        self._disappeared = True
        self._playground.remove(self)


class DisappearingBox(NormalBox):
    """
    A box that automatically disappears from the simulation after a
    predefined duration, measured in physics timesteps.

    Once the box disappears, it is removed from the playground, and the space
    it previously occupied becomes traversable by drones.

    Example:
        # Create a box that disappears after 1350 timesteps
        box = DisappearingBox(
            up_left_point=(0, 0),
            width=50,
            height=50,
            disappear_after_timesteps=1350
        )
    """

    def __init__(
        self,
        up_left_point: Tuple[float, float],
        width: float,
        height: float,
        disappear_after_timesteps: int = 900,
        **kwargs
    ):
        """
        Initializes a DisappearingBox.

        Args:
            up_left_point: Upper left coordinates of the box (x, y).
            width: Width of the box.
            height: Height of the box.
            disappear_after_timesteps: Number of timesteps to wait before
                making the box disappear (default: 900, ~30s at 30 FPS).
            **kwargs: Additional keyword arguments for the base `NormalBox` class.
        """
        super().__init__(up_left_point=up_left_point, width=width, height=height, **kwargs)

        self._disappear_after_timesteps = disappear_after_timesteps
        self._disappeared = False
        self._creation_timestep = None

    @property
    def disappear_after_timesteps(self) -> int:
        """The number of timesteps before the box disappears."""
        return self._disappear_after_timesteps

    @property
    def disappeared(self) -> bool:
        """Whether the box has already disappeared."""
        return self._disappeared

    def pre_step(self):
        """
        Executes logic before the physics step.

        Tracks the creation time of the box and checks if the elapsed
        time exceeds the disappearance threshold.
        """
        super().pre_step()

        # Record creation timestep on the first step, once in a playground
        if self._creation_timestep is None and self._playground:
            self._creation_timestep = self._playground.timestep

        # If not yet disappeared, check if the timeout has been reached
        if not self._disappeared and self._playground and self._creation_timestep is not None:
            elapsed_timesteps = self._playground.timestep - self._creation_timestep

            if elapsed_timesteps >= self._disappear_after_timesteps:
                self._disappear()

    def reset(self):
        """
        Resets the box to its initial state.

        This makes the box reappear and resets the disappearance timer.
        """
        super().reset()
        self._disappeared = False
        self._creation_timestep = None

    def _disappear(self):
        """
        Internal method to handle the box's disappearance.

        Removes the box from the playground if it hasn't already been removed.
        """
        if self._disappeared or not self._playground:
            return

        self._disappeared = True
        self._playground.remove(self)

