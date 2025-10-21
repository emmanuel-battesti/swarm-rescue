import math
from typing import Optional

import numpy as np

from swarm_rescue.simulation.ray_sensors.distance_sensor import DistanceSensor, compute_ray_angles
from swarm_rescue.simulation.utils.constants import RESOLUTION_LIDAR_SENSOR, FOV_LIDAR_SENSOR, MAX_RANGE_LIDAR_SENSOR
from swarm_rescue.simulation.utils.utils_noise import GaussianNoise


class DroneDistanceSensor(DistanceSensor):
    """
    The DroneDistanceSensor class is a subclass of the DistanceSensor class and
    represents a distance sensor for a drone. It emulates a lidar sensor, which
    measures distances using a laser in different directions. The class provides
    methods to calculate the field of view in radians and degrees, get the
    sensor values, check if the sensor is disabled, apply noise to the sensor
    values, and draw the lidar sensor.
    """

    def __init__(self, noise: bool = True, **kwargs):
        """
        Initialize the DroneDistanceSensor.

        Args:
            noise (bool): Whether to apply noise to the sensor.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(invisible_when_grasped=True, **kwargs)

        self._noise = noise
        self._std_dev_noise = 2.5
        self._noise_model = (
            GaussianNoise(mean_noise=0, std_dev_noise=self._std_dev_noise))

        # 'ray_angles' is an array which contains the angles of the laser rays
        # of the sensor
        self.ray_angles = (
            compute_ray_angles(fov_rad=self.fov_rad(), nb_rays=self.resolution))

        self._null_sensor = np.empty(self.shape)
        self._null_sensor[:] = np.nan

        self._values = self._default_value

    def fov_rad(self) -> float:
        """
        Returns the field of view in radians.
        """
        return self._fov

    def fov_deg(self) -> float:
        """
        Returns the field of view in degrees.
        """
        return math.degrees(self._fov)

    def get_sensor_values(self) -> Optional[np.ndarray]:
        """
        Get values of the lidar as a numpy array.

        Returns:
            np.ndarray or None: Sensor values or None if disabled.
        """
        if not self._disabled:
            return self._values
        else:
            return None

    def is_disabled(self) -> bool:
        """
        Returns a boolean indicating if the sensor is disabled.

        Returns:
            bool: True if disabled, False otherwise.
        """
        return self._disabled

    def _apply_noise(self) -> None:
        """
        Applies noise to the sensor values.
        """
        self._values = self._noise_model.add_noise(self._values)

    def draw(self) -> None:
        """
        Draws the rays of lidar sensor.
        """
        if self._hitpoints is not None:
            super().draw()

    @property
    def _default_value(self) -> np.ndarray:
        """
        Returns the default value for the sensor.
        """
        return self._null_sensor

    @property
    def shape(self) -> tuple:
        """
        Returns the shape of the sensor output.
        """
        return self._resolution,


class DroneLidar(DroneDistanceSensor):
    """
    It emulates a lidar.
    The DroneLidar class is a subclass of the DroneDistanceSensor class and
    represents a lidar sensor for a drone.
    It emulates a real lidar sensor ("light detection and ranging") that
    measures distances using a laser in different directions. The class provides
     methods to calculate the field of view in radians and degrees, get the
     sensor values, check if the sensor is disabled, apply noise to the sensor
     values, and draw the lidar sensor.

    It is a real sensor that measures distances with a laser in different
    directions.
    - fov (field of view): 360 degrees
    - resolution (number of rays): 181
    - max range (maximum range of the sensor): 300 pix
    """

    def __init__(self, noise: bool = True, invisible_elements=None, **kwargs):
        """
        Initialize the DroneLidar.

        Args:
            noise (bool): Whether to apply noise.
            invisible_elements: Elements invisible to the lidar.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(normalize=False,
                         fov=FOV_LIDAR_SENSOR,
                         resolution=RESOLUTION_LIDAR_SENSOR,
                         max_range=MAX_RANGE_LIDAR_SENSOR,
                         invisible_elements=invisible_elements,
                         noise=noise,
                         **kwargs)
