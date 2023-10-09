import math
from collections import namedtuple

import arcade
import numpy as np
from enum import Enum, auto

from spg.agent import Agent
from spg.agent.sensor import DistanceSensor, SemanticSensor
from spg.element import ColorWall
from spg.playground import Playground

from spg_overlay.entities.drone_base import DroneBase
from spg_overlay.entities.normal_wall import NormalWall, NormalBox
from spg_overlay.entities.rescue_center import RescueCenter
from spg_overlay.utils.constants import RESOLUTION_SEMANTIC_SENSOR, MAX_RANGE_SEMANTIC_SENSOR, FOV_SEMANTIC_SENSOR, \
    RESOLUTION_LIDAR_SENSOR, FOV_LIDAR_SENSOR, MAX_RANGE_LIDAR_SENSOR
from spg_overlay.utils.utils_noise import GaussianNoise
from spg_overlay.entities.wounded_person import WoundedPerson


def compute_ray_angles(fov_rad: float, nb_rays: int) -> np.ndarray:
    """
    The compute_ray_angles function calculates the angles of the laser rays of a sensor based on the field of view and
    the number of rays.

    Example Usage
        fov_rad = math.pi / 2
        nb_rays = 5
        ray_angles = compute_ray_angles(fov_rad, nb_rays)
        print(ray_angles)

        Output:
        [-0.78539816, -0.39269908, 0.0, 0.39269908, 0.78539816]

    Inputs
        fov_rad (float): The field of view in radians.
        nb_rays (int): The number of rays of the sensor.
    """

    if not isinstance(fov_rad, float) or fov_rad <= 0:
        raise ValueError("fov_rad must be a positive float.")

    if nb_rays == 1:
        ray_angles = [0.]
    else:
        ray_angles = np.linspace(-fov_rad / 2, fov_rad / 2, nb_rays)

    # 'ray_angles' is an array which contains the angles of the laser rays of the sensor
    return np.array(ray_angles)


class DroneDistanceSensor(DistanceSensor):
    """
    The DroneDistanceSensor class is a subclass of the DistanceSensor class and represents a distance sensor for a
    drone. It emulates a lidar sensor, which measures distances using a laser in different directions. The class
    provides methods to calculate the field of view in radians and degrees, get the sensor values, check if the sensor
    is disabled, apply noise to the sensor values, and draw the lidar sensor.
    """

    def __init__(self, noise=True, **kwargs):
        super().__init__(invisible_when_grasped=True, **kwargs)

        self._noise = noise
        self._std_dev_noise = 2.5
        self._noise_model = GaussianNoise(mean_noise=0, std_dev_noise=self._std_dev_noise)

        # 'ray_angles' is an array which contains the angles of the laser rays of the sensor
        self.ray_angles = compute_ray_angles(fov_rad=self.fov_rad(), nb_rays=self.resolution)

        self._null_sensor = np.empty(self.shape)
        self._null_sensor[:] = np.nan

        self._values = self._default_value

    def fov_rad(self):
        """Field of view in radians"""
        return self._fov

    def fov_deg(self):
        """ Field of view in degrees"""
        return math.degrees(self._fov)

    def get_sensor_values(self):
        """Get values of the lidar as a numpy array"""
        if not self._disabled:
            return self._values
        else:
            return None

    def is_disabled(self):
        """Returns a boolean indicating if the sensor is disabled."""
        return self._disabled

    def _apply_noise(self):
        self._values = self._noise_model.add_noise(self._values)

    def draw(self):
        """Draws the rays of lidar sensor."""
        hitpoints_ok = not isinstance(self._hitpoints, int)
        if hitpoints_ok:
            super().draw()

    @property
    def _default_value(self):
        return self._null_sensor

    @property
    def shape(self):
        return self._resolution,


class DroneLidar(DroneDistanceSensor):
    """
    It emulates a lidar.
    The DroneLidar class is a subclass of the DroneDistanceSensor class and represents a lidar sensor for a drone.
    It emulates a real lidar sensor ("light detection and ranging") that measures distances using a laser in different
    directions. The class provides
     methods to calculate the field of view in radians and degrees, get the sensor values, check if the sensor is
     disabled, apply noise to the sensor values, and draw the lidar sensor.

    It is a real sensor that measures distances with a laser in different directions.
    - fov (field of view): 360 degrees
    - resolution (number of rays): 181
    - max range (maximum range of the sensor): 300 pix
    """

    def __init__(self, noise=True, invisible_elements=None, **kwargs):
        super().__init__(normalize=False,
                         fov=FOV_LIDAR_SENSOR,
                         resolution=RESOLUTION_LIDAR_SENSOR,
                         max_range=MAX_RANGE_LIDAR_SENSOR,
                         invisible_elements=invisible_elements,
                         noise=noise,
                         **kwargs)


class DroneSemanticSensor(SemanticSensor):
    """
    Semantic sensors allow to determine the nature of an object, without data processing,
    around the drone.

    - fov (field of view): 360 degrees
    - resolution (number of rays): 35
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
                         resolution=RESOLUTION_SEMANTIC_SENSOR,
                         max_range=MAX_RANGE_SEMANTIC_SENSOR,
                         fov=FOV_SEMANTIC_SENSOR,
                         invisible_elements=invisible_elements,
                         invisible_when_grasped=True,
                         **kwargs)

        self._playground = playground
        self._noise = noise
        self._std_dev_noise = 2.5

        # 'ray_angles' is an array which contains the angles of the laser rays of the sensor
        self.ray_angles = compute_ray_angles(fov_rad=self.fov_rad(), nb_rays=self.resolution)

        self.entity_colors = {
            WoundedPerson: [179, 143, 0],
            RescueCenter: [255, 64, 64],
            Agent: [64, 64, 255],
            DroneBase: [64, 64, 255]
        }

        null_data = self.Data(distance=np.nan,
                              angle=np.nan,
                              entity_type=np.nan,
                              grasped=False)
        self._null_sensor = [null_data] * self.resolution

        self._values = self._default_value

    def _compute_raw_sensor(self, *_):
        super()._compute_raw_sensor()

        # id_detections is the first column of self._values
        id_detections = self._values[:, 0].astype(int)
        # distances is the second column of self._values
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
            if hasattr(entity, 'graspable') and entity.graspable and entity.grasped_by:
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
        """Get values of the lidar as a numpy array"""
        if not self._disabled:
            return self._values
        else:
            return None

    @property
    def max_range(self):
        """max_range : max distance given by the lidar """
        return self._range

    def is_disabled(self):
        """Returns a boolean indicating if the sensor is disabled."""
        return self._disabled

    def _apply_noise(self):
        """Applies noise to the lidar sensor values."""
        for index, data in enumerate(self._values):
            new_data = self.Data(
                distance=max(0.0, data.distance + np.random.normal(self._std_dev_noise)),
                angle=data.angle,
                entity_type=data.entity_type,
                grasped=data.grasped)

            self._values[index] = new_data

    def draw(self):
        """Draws the lidar sensor rays."""
        hitpoints_ok = not isinstance(self._hitpoints, int)
        if hitpoints_ok:
            self.draw_details()

    def draw_details(self):
        """The draw_details method is responsible for drawing the lidar sensor rays and coloring them based on the type
        of entity detected by the sensor."""

        if self._disabled:
            return

        # view_xy corresponds to the first two columns (:2) of the self._hitpoints array.
        view_xy = self._hitpoints[:, :2]
        center_xy = self._hitpoints[:, 6:8]
        #  id_detection corresponds to the ninth column (8) of the self._hitpoints array.
        id_detection = self._hitpoints[:, 8].astype(int)

        point_list = []
        color_list = []

        for (view, center, id_detect) in zip(view_xy, center_xy, id_detection):
            if id_detect != 0:
                entity = self._playground.get_entity_from_uid(id_detect)
                color = self.entity_colors.get(type(entity), [204, 204, 204])
            else:
                color = [204, 204, 204]

            point_list.append((center[0], center[1]))
            point_list.append((view[0], view[1]))
            color_list.append(color)
            color_list.append(color)

        arcade.create_lines_with_colors(point_list, color_list).draw()

    @property
    def _default_value(self):
        return self._null_sensor
