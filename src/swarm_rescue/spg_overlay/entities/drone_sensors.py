import math
from abc import ABC

import numpy as np

from spg.agent.sensor.internal import InternalSensor
from spg_overlay.utils.utils import deg2rad
from spg_overlay.utils.utils_noise import AutoregressiveModelNoise, GaussianNoise


class DroneGPS(InternalSensor, ABC):
    """
      DroneGPS Sensor returns a numpy array containing the position of the anchor.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._pg_size = None

        self._noise = True
        model_param = 0.80
        std_dev_noise = 5
        self._noiseModel = AutoregressiveModelNoise(model_param=model_param, std_dev_noise=std_dev_noise)

        self._values = self._default_value()

    def _compute_raw_sensor(self):
        self._values = np.array(self._anchor.position)

    def set_playground_size(self, size):
        self._pg_size = size

    def _apply_normalization(self):
        if self._pg_size:
            self._values /= (self._pg_size[0], self._pg_size[1])

    def _default_value(self):
        null_sensor = np.empty(self.shape)
        null_sensor[:] = np.nan
        return null_sensor

    def get_sensor_values(self):
        """Get values of the lidar as a numpy array"""
        return self._values

    def draw(self):
        pass

    @property
    def shape(self):
        return (2,)

    def _apply_noise(self):
        """
        Overload of an internal function of _apply_noise of the class InternalSensor
        We use a noise that follow an autoregressive model of order 1 : https://en.wikipedia.org/wiki/Autoregressive_model#AR(1)
        """
        self._values = self._noiseModel.add_noise(self._values)

    def is_disabled(self):
        return self._disabled


class DroneCompass(InternalSensor):
    """
      DroneCompass Sensor returns a numpy array containing the orientation of the anchor.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._noise = True
        model_param = 0.80
        std_dev_noise_angle = deg2rad(4)
        self._noiseModel = AutoregressiveModelNoise(model_param=model_param, std_dev_noise=std_dev_noise_angle)

        self._values = self._default_value()

    def _compute_raw_sensor(self):
        self._values = np.array([self._anchor.angle])

    def _apply_normalization(self):
        self._values /= 2 * math.pi

    def _default_value(self) -> np.ndarray:
        null_sensor = np.empty(self.shape)
        null_sensor[:] = np.nan
        return null_sensor

    def get_sensor_values(self):
        """Get values of the lidar as a numpy array"""
        return self._values

    def draw(self):
        pass

    @property
    def shape(self) -> tuple:
        return (1,)

    def _apply_noise(self):
        """
        Overload of an internal function of _apply_noise of the class InternalSensor
        We use a noise that follow an autoregressive model of order 1 : https://en.wikipedia.org/wiki/Autoregressive_model#AR(1)
        """
        self._values = self._noiseModel.add_noise(self._values)

    def is_disabled(self):
        return self._disabled


class DroneVelocity(InternalSensor):
    """
      DroneVelocity Sensor returns a numpy array containing the velocity of the anchor.
    """

    def __init__(self, **kwargs):
        super().__init__(name="DroneVelocity", **kwargs)

        self._noise = True
        std_dev_velocity = 0.08
        self._noiseModel = GaussianNoise(std_dev_noise=std_dev_velocity)

        self._values = self._default_value()

    def _compute_raw_sensor(self):
        # we should put here the velocity not the angle
        self._values = np.array([self._anchor.velocity])

    def _apply_normalization(self):
        pass

    def _default_value(self):
        null_sensor = np.empty(self.shape)
        null_sensor[:] = np.nan
        return null_sensor

    def get_sensor_values(self):
        """Get values of the lidar as a numpy array"""
        return self._values

    def draw(self):
        pass

    @property
    def shape(self):
        return (1,)

    def _apply_noise(self):
        """
        Overload of an internal function of _apply_noise of the class InternalSensor
        """
        self._values = self._noiseModel.add_noise(self._values)

    def is_disabled(self):
        return self._disabled
