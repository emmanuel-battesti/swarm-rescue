from __future__ import annotations

import arcade
import numpy as np

from swarm_rescue.simulation.ray_sensors.ray_sensor import RaySensor


# Helper function that computes the angles of the laser rays of the sensor in radians
def compute_ray_angles(fov_rad: float, nb_rays: int) -> np.ndarray:
    """
    Calculates the angles of the laser rays of a sensor based on the field of view and the number of rays.
    Example Usage:
        fov_rad = math.pi / 2
        nb_rays = 5
        ray_angles = compute_ray_angles(fov_rad, nb_rays)
        print(ray_angles)

        Output:
        [-0.78539816, -0.39269908, 0.0, 0.39269908, 0.78539816]

    Args:
        fov_rad (float): The field of view in radians.
        nb_rays (int): The number of rays of the sensor.

    Returns:
        np.ndarray: Array of angles in radians.
    """

    if not isinstance(fov_rad, float) or fov_rad <= 0:
        raise ValueError("fov_rad must be a positive float.")

    if nb_rays == 1:
        ray_angles = [0.]
    else:
        ray_angles = np.linspace(-fov_rad / 2, fov_rad / 2, nb_rays)

    # 'ray_angles' is an array which contains the angles of the laser rays of
    # the sensor
    return np.array(ray_angles)


class DistanceSensor(RaySensor):
    """
    Sensor that measures distances using ray casting.
    """

    def _compute_raw_sensor(self) -> None:
        """
        Compute the raw sensor values from hitpoints.
        """
        self._values = self._hitpoints[:, 9]

    def draw(self) -> None:
        """
        Draws the distance sensor rays using Arcade.
        """
        if self._disabled:
            return
        view_xy = self._hitpoints[:, :2]
        center_xy = self._hitpoints[:, 6:8]
        dist = 1 - self._hitpoints[:, 9] / self._range

        point_list = []
        color_list = []

        for (view, center, d) in zip(view_xy, center_xy, dist):
            color_value = int(d * 255)
            color = (color_value, color_value, color_value)

            point_list.append((center[0], center[1]))
            point_list.append((view[0], view[1]))
            color_list.append(color)
            color_list.append(color)

        arcade.create_lines_with_colors(point_list, color_list).draw()

    @property
    def shape(self) -> tuple:
        """
        Returns the shape of the sensor output.
        """
        return self._resolution, 1

    @property
    def _default_value(self) -> np.ndarray:
        """
        Returns the default value for the sensor.
        """
        return np.zeros(self.shape)

    def _apply_normalization(self) -> None:
        """
        Normalizes the sensor values by the sensor range.
        """
        self._values = self._values / self._range
