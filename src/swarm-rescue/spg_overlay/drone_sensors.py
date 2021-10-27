import math
from typing import List, Optional, Union

import numpy as np

from simple_playgrounds.agents.sensors import Lidar, SemanticCones, Touch
from simple_playgrounds.common.entity import Entity


class DroneLidar(Lidar):
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

        self.ray_angles = np.array(self.ray_angles)

    def fov_rad(self):
        return self._fov

    def fov_deg(self):
        return self._fov * 180 / math.pi

    def get_sensor_values(self):
        self.sensor_values = np.reshape(self.sensor_values, (len(self.sensor_values),))
        return self.sensor_values

    @property
    def resolution(self):
        return self._resolution

    @property
    def min_range(self):
        return self._min_range

    @property
    def max_range(self):
        return self._max_range


class DroneTouch(Touch):
    def __init__(self, **kwargs):
        super().__init__(normalize=True,
                         fov=360,
                         max_range=5,
                         resolution=36,
                         **kwargs)


class DroneSemanticCones(SemanticCones):
    def __init__(self, **kwargs):
        super().__init__(normalize=False,
                         n_cones=36,
                         rays_per_cone=4,
                         max_range=200,
                         fov=360,
                         **kwargs)
