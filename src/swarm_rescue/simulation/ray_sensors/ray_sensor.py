from __future__ import annotations

from abc import ABC
from typing import Optional

import numpy as np

from swarm_rescue.simulation.ray_sensors.external_sensor import ExternalSensor


class RaySensor(ExternalSensor, ABC):
    """
    Base class for Ray Based sensors.
    Ray sensors use Arcade shaders.
    """

    def __init__(
            self,
            spatial_resolution: float = 1,
            **kwargs,
    ):
        """
        Initialize the RaySensor.

        Args:
            spatial_resolution (float): Spatial resolution of the sensor.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(**kwargs)

        self._spatial_resolution = spatial_resolution
        self._n_points = int(self._range / self._spatial_resolution)

        self._hitpoints : Optional[np.ndarray] = None

    @property
    def spatial_resolution(self) -> float:
        """
        Returns the spatial resolution of the sensor.
        """
        return self._spatial_resolution

    @property
    def n_points(self) -> int:
        """
        Returns the number of points along each ray.
        """
        return self._n_points

    def update_hitpoints(self, hitpoints: np.ndarray) -> None:
        """
        Update the hitpoints for the sensor.

        Args:
            hitpoints (np.ndarray): Array of hitpoints.
        """
        self._hitpoints = hitpoints

    @property
    def end_positions(self) -> np.ndarray:
        """
        Returns the end positions of the rays in the sensor's frame.

        Returns:
            np.ndarray: Array of end positions.
        """
        angles = np.linspace(self.angle - self.fov / 2, self.angle + self.fov / 2, self._resolution)

        x = self._range * np.cos(angles)
        y = self._range * np.sin(angles)
        return np.vstack((x, y))
