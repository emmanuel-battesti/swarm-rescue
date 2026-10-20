import math
from typing import Optional

import numpy as np

from swarm_rescue.simulation.drone.sensor import Sensor
from swarm_rescue.simulation.utils.utils import deg2rad, normalize_angle
from swarm_rescue.simulation.utils.utils_noise import AutoregressiveModelNoise, GaussianNoise, RNG


class DroneGPS(Sensor):
    """
    The DroneGPS class is a subclass of Sensor that represents a GPS
    sensor for a drone. It returns the position of the drone as a numpy
    array, with a noise that follows an autoregressive model of order 1.
    """

    def __init__(self, rng: RNG = None, **kwargs):
        """
        Initialize the DroneGPS sensor.

        Args:
            rng (np.random.Generator): Optional generator for the sensor
            noise. None (the default) comes from the global numpy RNG.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(**kwargs)

        self._pg_size = None

        self._noise = True
        model_param = 0.98
        self.std_dev_noise = 5
        self._noise_model = AutoregressiveModelNoise(model_param=model_param,
                                                     std_dev_noise=self.std_dev_noise,
                                                     rng=rng)

        self._null_sensor = np.empty(self.shape)
        self._null_sensor[:] = np.nan

        self._values = self._default_value

    def set_noise_rng(self, rng: RNG) -> None:
        """
        Set the generator the sensor noise comes from.

        Called by the playground when it claims the drone: None leaves the
        noise on the global numpy RNG.

        Args:
            rng (np.random.Generator): The generator to draw noise from.
        """
        self._noise_model.set_rng(rng)

    def _compute_raw_sensor(self) -> None:
        """
        Compute the raw GPS sensor value (position).
        """
        self._values = np.array(self.anchor.position)

    def set_playground_size(self, size: tuple) -> None:
        """
        Set the size of the playground for normalization.

        Args:
            size (tuple): Tuple of two positive numbers (width, height).
        """
        if (isinstance(size, tuple) and len(size) == 2 and
                all(isinstance(num, (int, float)) and num > 0 for num in size)):
            self._pg_size = size
        else:
            raise ValueError("Invalid playground size. Size should be a tuple "
                             "of two positive numbers.")

    def _apply_normalization(self) -> None:
        """
        Normalize the GPS values by the playground size.
        """
        if self._pg_size:
            self._values /= (self._pg_size[0], self._pg_size[1])

    @property
    def _default_value(self) -> np.ndarray:
        """
        Returns the default value for the sensor.
        """
        return self._null_sensor

    def get_sensor_values(self) -> Optional[np.ndarray]:
        """
        Get the GPS sensor values.

        Returns:
            np.ndarray or None: Sensor values or None if disabled.
        """
        if not self._disabled:
            return self._values
        else:
            return None

    def draw(self) -> None:
        """
        Draws the GPS sensor (no-op).
        """
        pass

    @property
    def shape(self) -> tuple:
        """
        Returns the shape of the sensor output.
        """
        return 2,

    def _apply_noise(self):
        """
        Overload of an internal function of _apply_noise of the class
        Sensor.
        We use a noise that follow an autoregressive model of order 1 :
         https://en.wikipedia.org/wiki/Autoregressive_model#AR(1)
        """
        self._values = self._noise_model.add_noise(self._values)

    def is_disabled(self) -> bool:
        """
        Returns whether the sensor is disabled.

        Returns:
            bool: True if disabled, False otherwise.
        """
        return self._disabled


class DroneCompass(Sensor):
    """
    DroneCompass sensor returns the orientation of the drone as a float.
    """

    def __init__(self, rng: RNG = None, **kwargs):
        """
        Initialize the DroneCompass sensor.

        Args:
            rng (np.random.Generator): Optional generator for the sensor
            noise. None (the default) comes from the global numpy RNG.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(**kwargs)

        self._noise = True
        model_param = 0.98
        self.std_dev_noise_angle = deg2rad(4.0)
        self._noise_model = (
            AutoregressiveModelNoise(model_param=model_param,
                                     std_dev_noise=self.std_dev_noise_angle,
                                     rng=rng))

        self._null_sensor = np.nan

        self._values = self._default_value

    def set_noise_rng(self, rng: RNG) -> None:
        """
        Set the generator the sensor noise comes from.

        Called by the playground when it claims the drone: None leaves the
        noise on the global numpy RNG.

        Args:
            rng (np.random.Generator): The generator to draw noise from.
        """
        self._noise_model.set_rng(rng)

    def _compute_raw_sensor(self) -> None:
        """
        Compute the raw compass sensor value (orientation).
        """
        self._values = normalize_angle(self.anchor.angle)

    def _apply_normalization(self) -> None:
        """
        Normalize the compass value by pi.
        """
        self._values /= math.pi

    @property
    def _default_value(self) -> float:
        """
        Returns the default value for the sensor.
        """
        return self._null_sensor

    def get_sensor_values(self) -> Optional[float]:
        """
        Get the compass sensor value.

        Returns:
            float or None: Sensor value or None if disabled.
        """
        if not self._disabled:
            return self._values
        else:
            return None

    def draw(self) -> None:
        """
        Draws the compass sensor (no-op).
        """
        pass

    @property
    def shape(self) -> tuple:
        """
        Returns the shape of the sensor output.
        """
        return 1,

    def _apply_noise(self) -> None:
        """
        Overload of an internal function of _apply_noise of the class
        Sensor
        We use a noise that follow an autoregressive model of order 1 :
        https://en.wikipedia.org/wiki/Autoregressive_model#AR(1)
        """
        angle = self._noise_model.add_noise(self._values)
        self._values = normalize_angle(angle)

    def is_disabled(self) -> bool:
        """
        Returns whether the sensor is disabled.

        Returns:
            bool: True if disabled, False otherwise.
        """
        return self._disabled


class DroneOdometer(Sensor):
    """
    DroneOdometer sensor returns a numpy array containing:
      - dist_travel: the distance of the travel of the drone during one step
      - alpha: the relative angle of the current position seen from the
        previous reference frame of the drone
      - theta: the variation of orientation (or rotation) of the drone during
        the last step in the reference frame
    """

    def __init__(self, rng: RNG = None, **kwargs):
        """
        Initialize the DroneOdometer sensor.

        Args:
            rng (np.random.Generator): Optional generator for the sensor
            noise. None (the default) comes from the global numpy RNG.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(**kwargs)
        self._noise = True

        self.std_dev_dist_travel = 0.2
        self._noise_dist_travel_model = GaussianNoise(std_dev_noise=self.std_dev_dist_travel,
                                                      rng=rng)

        self.std_dev_alpha = deg2rad(8.0)
        self._noise_alpha_model = GaussianNoise(std_dev_noise=self.std_dev_alpha,
                                                rng=rng)

        self.std_dev_theta = deg2rad(1.0)
        self._noise_theta_model = GaussianNoise(std_dev_noise=self.std_dev_theta,
                                                rng=rng)

        self._null_sensor = np.empty(self.shape)
        self._null_sensor[:] = np.nan

        self._values = self._default_value

        self.prev_angle = None
        self.prev_position = None

    def set_noise_rng(self, rng: RNG) -> None:
        """
        Set the generator the sensor noise comes from.

        Called by the playground when it claims the drone: None leaves the
        noise on the global numpy RNG.

        Args:
            rng (np.random.Generator): The generator to draw noise from.
        """
        self._noise_dist_travel_model.set_rng(rng)
        self._noise_alpha_model.set_rng(rng)
        self._noise_theta_model.set_rng(rng)

    def _compute_raw_sensor(self) -> None:
        """
        Compute the distance traveled, relative angle, and variation of orientation for the robot.
        """
        # DIST_TRAVEL
        if self.prev_position is None:
            self.prev_position = self.anchor.position

        travel_vector = self.anchor.position - self.prev_position
        dist_travel = math.sqrt(travel_vector[0] ** 2 + travel_vector[1] ** 2)
        self._values[0] = dist_travel

        # ALPHA
        if self.prev_angle is None:
            self.prev_angle = self.anchor.angle

        alpha = (math.atan2(travel_vector[1], travel_vector[0]) -
                 self.prev_angle)
        self._values[1] = normalize_angle(alpha)

        # THETA
        theta = self.anchor.angle - self.prev_angle
        self._values[2] = normalize_angle(theta)

        # UPDATE
        self.prev_position = self.anchor.position
        self.prev_angle = self.anchor.angle

    def _apply_normalization(self) -> None:
        """
        No normalization applied for odometer.
        """
        pass

    @property
    def _default_value(self) -> np.ndarray:
        """
        Returns the default value for the sensor.
        """
        return self._null_sensor

    def get_sensor_values(self) -> Optional[np.ndarray]:
        """
        Get the odometer sensor values.

        Returns:
            np.ndarray or None: Sensor values or None if disabled.
        """
        if not self._disabled:
            return self._values
        else:
            return None

    def draw(self) -> None:
        """
        Draws the odometer sensor (no-op).
        """
        pass

    @property
    def shape(self) -> tuple:
        """
        Returns the shape of the sensor output.
        """
        return 3,

    def _apply_noise(self) -> None:
        """
        Applies noise to the odometer sensor values.
        """
        noisy_dist_travel = (
            self._noise_dist_travel_model.add_noise(self._values[0]))
        # print("travel: {:2f}, noisy_dist_travel: {:2f}".format(dist_travel, noisy_dist_travel))

        noisy_alpha = self._noise_alpha_model.add_noise(self._values[1])
        noisy_alpha = normalize_angle(noisy_alpha)

        noisy_theta = self._noise_theta_model.add_noise(self._values[2])
        noisy_theta = normalize_angle(noisy_theta)

        self._values = np.array([noisy_dist_travel, noisy_alpha, noisy_theta])

    def is_disabled(self) -> bool:
        """
        Returns whether the sensor is disabled.

        Returns:
            bool: True if disabled, False otherwise.
        """
        return self._disabled
