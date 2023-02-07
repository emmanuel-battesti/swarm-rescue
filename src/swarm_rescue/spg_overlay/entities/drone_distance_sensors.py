import math
from collections import namedtuple

import numpy as np
from enum import Enum, auto

from spg.agent import Agent
from spg.agent.sensor import DistanceSensor, SemanticSensor
from spg.element import ColorWall
from spg.playground import Playground

from spg_overlay.entities.drone_base import DroneBase
from spg_overlay.entities.normal_wall import NormalWall, NormalBox
from spg_overlay.entities.rescue_center import RescueCenter
from spg_overlay.utils.utils_noise import GaussianNoise
from spg_overlay.entities.wounded_person import WoundedPerson


def compute_ray_angles(fov_rad: float, nb_rays: int) -> np.ndarray:
    a = fov_rad / (nb_rays - 1)
    b = fov_rad / 2
    if nb_rays == 1:
        ray_angles = [0.]
    else:
        ray_angles = [n * a - b for n in range(nb_rays)]

    # 'ray_angles' is an array which contains the angles of the laser rays of the sensor
    return np.array(ray_angles)


class DroneDistanceSensor(DistanceSensor):
    def __init__(self, noise=True, **kwargs):
        super().__init__(invisible_when_grasped=True, **kwargs)

        self._noise = noise
        self._std_dev_noise = 2.5
        self._noise_model = GaussianNoise(mean_noise=0, std_dev_noise=self._std_dev_noise)

        self._values = self._default_value

        # 'ray_angles' is an array which contains the angles of the laser rays of the sensor
        self.ray_angles = compute_ray_angles(fov_rad=self.fov_rad(), nb_rays=self.resolution)

    def fov_rad(self):
        """Field of view in radians"""
        return self._fov

    def fov_deg(self):
        """ Field of view in degrees"""
        return self._fov * 180 / math.pi

    def get_sensor_values(self):
        """Get values of the lidar as a numpy array"""
        return self._values

    def is_disabled(self):
        return self._disabled

    def _apply_noise(self):
        self._values = self._noise_model.add_noise(self._values)

    def draw(self):
        hitpoints_ok = not isinstance(self._hitpoints, int)
        if hitpoints_ok:
            super().draw()

    @property
    def _default_value(self):
        null_sensor = np.empty(self.shape)
        null_sensor[:] = np.nan
        return null_sensor

    @property
    def shape(self):
        return self._resolution,


class DroneLidar(DroneDistanceSensor):
    """
    It emulates a lidar.
    Lidar is an acronym of "light detection and ranging".
    It is a real sensor that measures distances with a laser in different directions.
    - fov (field of view): 360 degrees
    - resolution (number of rays): 90
    - max range (maximum range of the sensor): 300 pix
    """

    def __init__(self, noise=True, invisible_elements=None, **kwargs):
        super().__init__(normalize=False,
                         fov=360,
                         resolution=181,
                         max_range=300,
                         invisible_elements=invisible_elements,
                         noise=noise,
                         **kwargs)


class DroneTouch(DroneDistanceSensor):
    """
    Touch sensor detects close proximity of entities (objects or walls) near the drone.

    It emulates artificial skin,

    - *fov* (field of view): 360 degrees
    - *resolution* (number of rays): 36
    - *max range* (maximum range of the sensor): 5 pix

    The return value is between 0 and 1.
    """

    def __init__(self, noise=True, invisible_elements=None, **kwargs):
        super().__init__(normalize=False,
                         fov=360,
                         resolution=13,
                         max_range=25,
                         invisible_elements=invisible_elements,
                         noise=noise,
                         **kwargs)

        self._noise = noise
        std_dev_noise = 0.05
        self._noise_model = GaussianNoise(mean_noise=0, std_dev_noise=std_dev_noise)

    def _apply_noise(self):
        self._values = self._noise_model.add_noise(self._values)
        self._values = np.clip(self._values, a_min=0.0, a_max=1.0)

    def _compute_raw_sensor(self, *_):
        super()._compute_raw_sensor()

        # self._values = np.minimum(self.range + 15 - self._values, np.ones_like(self._values) * self.range)
        val = np.zeros_like(self._values)
        val[self._values < 20] = 1.0
        self._values = val


class DroneSemanticSensor(SemanticSensor):
    """
    Semantic sensors allow to determine the nature of an object, without data processing,
    around the drone.

    - fov (field of view): 360 degrees
    - resolution (number of rays): 36
    - range (maximum range of the sensor): 200 pix
    """

    # noinspection PyArgumentList
    class TypeEntity(Enum):
        """
        Type of the entity detected
        """
        WALL = auto()
        WOUNDED_PERSON = auto()
        GRASPED_WOUNDED_PERSON = auto()
        RESCUE_CENTER = auto()
        CANDY = auto()
        DRONE = auto()
        COIN = auto()
        VENDING_MACHINE = auto()
        OTHER = auto()

    Data = namedtuple("Data", "distance angle entity_type grasped")

    def __init__(self, playground: Playground, noise=True, invisible_elements=None, **kwargs):
        super().__init__(normalize=False,
                         resolution=35,
                         max_range=200,
                         fov=360,
                         invisible_elements=invisible_elements,
                         invisible_when_grasped=True,
                         **kwargs)

        self._playground = playground
        self._noise = noise
        self._std_dev_noise = 2.5

        self._values = self._default_value

        # 'ray_angles' is an array which contains the angles of the laser rays of the sensor
        self.ray_angles = compute_ray_angles(fov_rad=self.fov_rad(), nb_rays=self.resolution)

    def _compute_raw_sensor(self, *_):
        super()._compute_raw_sensor()

        id_detections = self._values[:, 0].astype(int)
        distances = self._values[:, 1]

        new_values = []

        for index, id_detection in enumerate(id_detections):
            if id_detection == 0:
                continue
            entity = self._playground.get_entity_from_uid(id_detection)
            if isinstance(entity, ColorWall):
                entity_type = self.TypeEntity.WALL
            elif isinstance(entity, NormalWall):
                entity_type = self.TypeEntity.WALL
            elif isinstance(entity, NormalBox):
                entity_type = self.TypeEntity.WALL
            elif isinstance(entity, WoundedPerson):
                entity_type = self.TypeEntity.WOUNDED_PERSON
            elif isinstance(entity, RescueCenter):
                entity_type = self.TypeEntity.RESCUE_CENTER
            elif isinstance(entity, Agent) or isinstance(entity, DroneBase):
                entity_type = self.TypeEntity.DRONE
            else:
                entity_type = self.TypeEntity.OTHER
                # print(__file__, type(entity))

            grasped = False
            if hasattr(entity, 'graspable') and entity.graspable and len(entity.grasped_by) > 0:
                grasped = True

            distance = distances[index]
            angle = self.ray_angles[index]

            # We remove the walls, so that it is not too easy
            if entity_type == self.TypeEntity.WALL:
                continue

            new_detection = self.Data(distance=distance,
                                      angle=angle,
                                      entity_type=entity_type,
                                      grasped=grasped)
            new_values.append(new_detection)

        self._values = new_values

    def fov_rad(self):
        """Field of view in radians"""
        return self._fov

    def fov_deg(self):
        """ Field of view in degrees"""
        return self._fov * 180 / math.pi

    def get_sensor_values(self):
        """Get values of the lidar as a list"""
        return self._values

    @property
    def max_range(self):
        """max_range : max distance given by the lidar """
        return self._range

    def is_disabled(self):
        return self._disabled

    def _apply_noise(self):
        for index, data in enumerate(self._values):
            new_data = self.Data(
                distance=max(0.0, data.distance + np.random.normal(self._std_dev_noise)),
                angle=data.angle,
                entity_type=data.entity_type,
                grasped=data.grasped)

            self._values[index] = new_data

    def draw(self):
        hitpoints_ok = not isinstance(self._hitpoints, int)
        if hitpoints_ok:
            super().draw()

    @property
    def _default_value(self):
        null_data = self.Data(distance=np.nan,
                              angle=np.nan,
                              entity_type=np.nan,
                              grasped=False)
        null_sensor = [null_data] * self.resolution
        return null_sensor
