"""
Module defining the Base Classes for Sensors.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import List, Optional, Union, Any

import numpy as np

from swarm_rescue.simulation.drone.pocket_device import PocketDevice

SensorValue = Union[np.ndarray, List[np.ndarray]]

SENSOR_COLOR = (23, 24, 113)


class Sensor(PocketDevice):
    """Base class Sensor, used as an Interface for all sensors.

    Attributes:
        anchor: Part or Element to which the sensor is attached.
            Sensor is attached to the center of the anchor.
        sensor_values: current values of the sensor.
        name: Name of the sensor.

    Note:
        The anchor is always invisible to the sensor.

    """

    def __init__(
            self,
            normalize: Optional[bool] = False,
            **kwargs: Any,
    ):
        """
        Sensors are attached to an anchor.
        They can detect any visible Part of an Agent or Elements of the Playground.
        If the entity is in invisible elements, it is not detected.

        Args:
            anchor: Body Part or Scene Element on which the sensor will be attached.
            normalize: boolean. If True, sensor values are scaled between 0 and 1.
            noise_params: Dictionary of noise parameters.
                Noise is applied to the raw sensor, before normalization.
            name: name of the sensor. If not provided, a name will be set by default.

        Noise Parameters:
            type: 'gaussian', 'salt_pepper'
            mean: mean of gaussian noise (default 0)
            scale: scale (or std) of gaussian noise (default 1)
            salt_pepper_probability: probability for a pixel to be turned off or max

        """

        super().__init__(color=SENSOR_COLOR, **kwargs)

        self._values = None

        self._normalize = normalize

        self._noise = False

    def update(self) -> None:
        """
        Update the sensor values, applying noise and normalization if enabled.
        """
        if self._disabled:
            self._values = self._default_value

        else:
            self._compute_raw_sensor()

            if self._noise:
                self._apply_noise()

            if self._normalize:
                self._apply_normalization()

    @abstractmethod
    def _compute_raw_sensor(self) -> None:
        """
        Compute the raw sensor values.
        """
        ...

    @abstractmethod
    def _apply_normalization(self) -> None:
        """
        Apply normalization to the sensor values.
        """
        ...

    def _apply_noise(self) -> None:
        """
        Implement this method on custom sensors to add noise to the values.
        """

    @property
    @abstractmethod
    def _default_value(self) -> np.ndarray:
        """
        Returns the default value for the sensor.
        """
        ...

    @property
    @abstractmethod
    def shape(self) -> tuple:
        """
        Returns the shape of the numpy array, if applicable.
        """
        ...

    @abstractmethod
    def draw(self) -> None:
        """
        Draw the sensor visualization.
        """
        ...
