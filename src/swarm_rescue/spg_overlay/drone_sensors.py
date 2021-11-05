import math

import numpy as np

from simple_playgrounds.device.sensors import Lidar, SemanticCones, Touch, Position


class DroneLidar(Lidar):
    """
    It emulates a lidar.
    Lidar is an acronym of "light detection and ranging".
    It is a real sensor that measures distances with a laser in different directions.
    - fov (field of view): 180 degrees
    - resolution (number of rays): 180
    - max range (maximum range of the sensor): 300 pix
    """
    def __init__(self, **kwargs):
        resolution = 180

        super().__init__(normalize=False,
                         resolution=resolution,
                         max_range=300,
                         fov=180,
                         **kwargs)

        self.size = resolution
        a = self.fov_rad() / (self.size - 1)
        b = self.fov_rad() / 2
        if self.size == 1:
            self.ray_angles = [0.]
        else:
            self.ray_angles = [n * a - b for n in range(self.size)]

        # 'ray_angles' is an array which contains the angles of the laser rays of the lidar
        self.ray_angles = np.array(self.ray_angles)

    def fov_rad(self):
        """Field of view in radians"""
        return self._fov

    def fov_deg(self):
        """ Field of view in degrees"""
        return self._fov * 180 / math.pi

    def get_sensor_values(self):
        """Get values of the lidar as a numpy array"""
        self.sensor_values = np.reshape(self.sensor_values, (len(self.sensor_values),))
        return self.sensor_values

    @property
    def resolution(self):
        """resolution : number of rays """
        return self._resolution

    @property
    def min_range(self):
        """min_range : min distance given by the lidar """
        return self._min_range

    @property
    def max_range(self):
        """min_range : max distance given by the lidar """
        return self._max_range


class DroneTouch(Touch):
    """
    Touch sensor detects close proximity of entities (objects or walls) near the drone.

    It emulates artificial skin,

    - *fov* (field of view): 360 degrees
    - *resolution* (number of rays): 36
    - *max range* (maximum range of the sensor): 5 pix

    The return value is between 0 and 1.
    """
    def __init__(self, **kwargs):
        super().__init__(normalize=True,
                         fov=360,
                         max_range=5,
                         resolution=36,
                         **kwargs)


class DroneSemanticCones(SemanticCones):
    """
    Semantic Cones sensors allow to determine the nature of an object, without data processing, around the drone.

    - fov (field of view): 360 degrees
    - max range (maximum range of the sensor): 200 pix
    - n_cones, number of cones evenly spaced across the field of view: 36
    """
    def __init__(self, **kwargs):
        super().__init__(normalize=False,
                         n_cones=36,
                         rays_per_cone=4,
                         max_range=200,
                         fov=360,
                         **kwargs)


class DronePosition(Position):
    def __init__(self, **kwargs):
        noise_params = {"type": "gaussian",
                        "mean": 0,
                        "scale": 0}
        super().__init__(noise_params=noise_params,
                         **kwargs)
