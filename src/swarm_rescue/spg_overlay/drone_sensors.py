import math
import copy
from collections import namedtuple

import numpy as np
from enum import Enum, auto

from simple_playgrounds.agent.parts import MobilePlatform
from simple_playgrounds.common.definitions import Detection

from simple_playgrounds.device.sensors import Lidar, SemanticCones, Touch, Position
from simple_playgrounds.element.elements.activable import VendingMachine
from simple_playgrounds.element.elements.basic import Wall
from simple_playgrounds.element.elements.contact import Candy
from simple_playgrounds.element.elements.gem import Coin

from spg_overlay.normal_wall import NormalWall, NormalBox
from spg_overlay.rescue_center import RescueCenter
from spg_overlay.utils import deg2rad
from spg_overlay.wounded_person import WoundedPerson


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
        resolution = 90
        std_dev_noise = 2.5

        super().__init__(normalize=False,
                         resolution=resolution,
                         max_range=300,
                         fov=180,
                         noise_params={"type": "gaussian", "mean": 0, "scale": std_dev_noise},
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
        std_dev_noise = 0.01

        super().__init__(normalize=True,
                         fov=360,
                         max_range=5,
                         resolution=12,
                         noise_params={"type": "gaussian", "mean": 0, "scale": std_dev_noise},
                         **kwargs)


class DroneSemanticCones(SemanticCones):
    """
    Semantic Cones sensors allow to determine the nature of an object, without data processing, around the drone.

    - fov (field of view): 360 degrees
    - max range (maximum range of the sensor): 200 pix
    - n_cones, number of cones evenly spaced across the field of view: 36
    """

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

    def __init__(self, **kwargs):
        # We use a gaussian noise, but only for the distance. We need to declare noise_params
        # we will do our own computation for the noise in the overload function _apply_noise()
        noise_params = {"type": "gaussian",
                        "mean": 0,
                        "scale": 0}
        super().__init__(normalize=False,
                         n_cones=36,
                         rays_per_cone=4,
                         max_range=200,
                         fov=360,
                         noise_params=noise_params,
                         **kwargs)

    def _compute_raw_sensor(self, playground, *_):
        super()._compute_raw_sensor(playground)

        for index, detection in enumerate(self.sensor_values):
            if isinstance(detection.entity, Wall):
                entity_type = self.TypeEntity.WALL
            elif isinstance(detection.entity, NormalWall):
                entity_type = self.TypeEntity.WALL
            elif isinstance(detection.entity, NormalBox):
                entity_type = self.TypeEntity.WALL
            elif isinstance(detection.entity, WoundedPerson):
                entity_type = self.TypeEntity.WOUNDED_PERSON
            elif isinstance(detection.entity, RescueCenter):
                entity_type = self.TypeEntity.RESCUE_CENTER
            elif isinstance(detection.entity, Candy):
                entity_type = self.TypeEntity.CANDY
            elif isinstance(detection.entity, Coin):
                entity_type = self.TypeEntity.COIN
            elif isinstance(detection.entity, VendingMachine):
                entity_type = self.TypeEntity.VENDING_MACHINE
            elif isinstance(detection.entity, MobilePlatform):
                entity_type = self.TypeEntity.DRONE
            else:
                entity_type = self.TypeEntity.OTHER
                # print(__file__, type(detection.entity))

            grasped = False
            if detection.entity.graspable and len(detection.entity.held_by) > 0:
                grasped = True

            new_detection = self.Data(distance=detection.distance,
                                      angle=detection.angle,
                                      entity_type=entity_type,
                                      grasped=grasped)

            self.sensor_values[index] = new_detection

    def _apply_noise(self):
        std_dev_noise = 2.5
        for index, data in enumerate(self.sensor_values):
            new_data = self.Data(distance=max(0.0, data.distance + np.random.normal(std_dev_noise)),
                                 angle=data.angle,
                                 entity_type=data.entity_type,
                                 grasped=data.grasped)

            self.sensor_values[index] = new_data


class DronePosition(Position):
    def __init__(self, **kwargs):
        # In reality, we dont use a gaussian noise, for the moment we need to do this
        # to fool the system into using our own noise in the overload function _apply_noise().
        noise_params = {"type": "gaussian",
                        "mean": 0,
                        "scale": 0}
        super().__init__(noise_params=noise_params,
                         **kwargs)

        self.model_param = 0.95

        # std_dev is the real standard deviation of the resulted noise
        self.std_dev = 15
        # _std_dev_wn is the standard deviation of the white noise
        self._std_dev_wn = math.sqrt(self.std_dev ** 2 * (1 - self.model_param ** 2))

        # std_dev_angle is the real standard deviation of the resulted noise
        self.std_dev_angle = deg2rad(4)
        # _std_dev_angle_wn is the standard deviation of the white noise
        self._std_dev_angle_wn = math.sqrt(self.std_dev_angle ** 2 * (1 - self.model_param ** 2))

        self._last_noise = None

    def _apply_noise(self):
        """
        Overload of an internal function of _apply_noise of the class InternalSensor
        We use a noise that follow an autoregressive model of order 1 : https://en.wikipedia.org/wiki/Autoregressive_model#AR(1)
        """
        white_noise = np.random.normal(0,
                                       (self._std_dev_wn, self._std_dev_wn, self._std_dev_angle_wn),
                                       size=self.shape)

        if self._last_noise is None:
            self._last_noise = np.zeros(self.shape)

        additive_noise = self.model_param * self._last_noise + white_noise
        self._last_noise = additive_noise

        self.sensor_values += additive_noise
