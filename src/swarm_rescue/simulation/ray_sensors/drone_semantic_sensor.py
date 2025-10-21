import math
import os
import sys
from collections import namedtuple
from enum import Enum, auto
from typing import Union

import arcade
import numpy as np

from swarm_rescue.simulation.drone.agent import Agent
from swarm_rescue.simulation.drone.drone_base import DroneBase
from swarm_rescue.simulation.ray_sensors.distance_sensor import compute_ray_angles
from swarm_rescue.simulation.ray_sensors.semantic_sensor import SemanticSensor
from swarm_rescue.simulation.elements.normal_wall import NormalWall, NormalBox
from swarm_rescue.simulation.elements.rescue_center import RescueCenter
from swarm_rescue.simulation.elements.wounded_person import WoundedPerson
from swarm_rescue.simulation.gui_map.playground import Playground
from swarm_rescue.simulation.utils.constants import RESOLUTION_SEMANTIC_SENSOR, MAX_RANGE_SEMANTIC_SENSOR, \
    FOV_SEMANTIC_SENSOR


class DroneSemanticSensor(SemanticSensor):
    """
    Semantic sensors allow to determine the nature of an object, without data
    processing, around the drone.

    - fov (field of view): 360 degrees
    - resolution (number of rays): 35
    - range (maximum range of the sensor): 200 pix
    """

    # noinspection PyArgumentList
    class TypeEntity(Enum):
        """
        Type of the entity detected.
        """
        WALL = auto()
        WOUNDED_PERSON = auto()
        RESCUE_CENTER = auto()
        DRONE = auto()
        OTHER = auto()

    Data = namedtuple("Data",
                      "distance angle entity_type grasped")

    def __init__(self, playground: Playground, noise: bool = True,
                 invisible_elements=None, **kwargs):
        """
        Initialize the DroneSemanticSensor.

        Args:
            playground (Playground): The playground environment.
            noise (bool): Whether to apply noise.
            invisible_elements: Elements invisible to the sensor.
            **kwargs: Additional keyword arguments.
        """
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

        # 'ray_angles' is an array which contains the angles of the laser rays
        # of the sensor
        self.ray_angles = compute_ray_angles(fov_rad=self.fov_rad(),
                                             nb_rays=self.resolution)

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

    def _compute_raw_sensor(self, *_) -> None:
        """
        Compute the raw sensor values and classify detected entities.
        """
        super()._compute_raw_sensor()

        # id_detections is the first column of self._values
        id_detections = self._values[:, 0].astype(int)
        # distances is the second column of self._values
        distances = self._values[:, 1]

        new_values = []

        for index, id_detection in enumerate(id_detections):
            if id_detection == 0:
                continue
            try:
                entity = self._playground.get_entity_from_uid(id_detection)
            except KeyError:
                # Skip invalid entity IDs (e.g., background colors in xvfb)
                continue

            if isinstance(entity, NormalWall):
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
            if (hasattr(entity, 'graspable') and
                    entity.graspable and
                    entity.grasped_by):
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

    def get_sensor_values(self) -> Union[list, None]:
        """
        Get values of the semantic sensor.

        Returns:
            list or None: Sensor values or None if disabled.
        """
        if not self._disabled:
            return self._values
        else:
            return None

    @property
    def max_range(self) -> float:
        """
        Returns the maximum range of the sensor.
        """
        return self._range

    def is_disabled(self) -> bool:
        """
        Returns a boolean indicating if the sensor is disabled.

        Returns:
            bool: True if disabled, False otherwise.
        """
        return self._disabled

    def _apply_noise(self) -> None:
        """
        Applies noise to the semantic sensor values.
        """
        for index, data in enumerate(self._values):
            new_data = self.Data(
                distance=max(0.0, data.distance +
                             np.random.normal(self._std_dev_noise)),
                angle=data.angle,
                entity_type=data.entity_type,
                grasped=data.grasped)

            self._values[index] = new_data

    def draw(self) -> None:
        """
        Draws the lidar sensor rays.
        """
        # If hitpoints are defined, call the draw_details method
        if self._hitpoints is not None:
            self.draw_details()

    def draw_details(self) -> None:
        """
        Draws the lidar sensor rays and colors them based on the type of entity detected.
        """
        if self._disabled:
            return

        # view_xy corresponds to the first two columns (:2) of the
        # self._hitpoints array.
        view_xy = self._hitpoints[:, :2]
        center_xy = self._hitpoints[:, 6:8]
        #  id_detection corresponds to the ninth column (8) of the
        #  self._hitpoints array.
        id_detection = self._hitpoints[:, 8].astype(int)

        point_list = []
        color_list = []

        for (view, center, id_detect) in zip(view_xy, center_xy, id_detection):
            if id_detect != 0:
                try:
                    entity = self._playground.get_entity_from_uid(id_detect)
                except KeyError as error:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print(f"KeyError in file {fname} at line {exc_tb.tb_lineno}")
                    print("Wrong Key for detected entity:", error)
                    continue
                color = self.entity_colors.get(type(entity), [204, 204, 204])
            else:
                color = [204, 204, 204]

            point_list.append((center[0], center[1]))
            point_list.append((view[0], view[1]))
            color_list.append(color)
            color_list.append(color)

        arcade.create_lines_with_colors(point_list, color_list).draw()

    @property
    def _default_value(self) -> list:
        """
        Returns the default value for the sensor.
        """
        return self._null_sensor
