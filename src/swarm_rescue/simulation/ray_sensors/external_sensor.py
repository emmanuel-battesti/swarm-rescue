"""
Module defining the Base Classes for Sensors.
"""

from __future__ import annotations

import math
from abc import ABC
from typing import List, Optional, Union

from swarm_rescue.simulation.drone.sensor import Sensor
from swarm_rescue.simulation.elements.embodied import EmbodiedEntity


class ExternalSensor(Sensor, ABC):
    """
    Base class for external sensors with field of view, resolution, and range.
    """

    def __init__(
            self,
            fov: float,
            resolution: int,
            max_range: float,  # pylint: disable=redefined-builtin
            invisible_elements: Optional[
                Union[List[EmbodiedEntity], EmbodiedEntity]
            ] = None,
            invisible_when_grasped: bool = False,
            **kwargs,
    ):
        """
        Initialize the ExternalSensor.

        Args:
            fov (float): Field of view of the external_sensor (in degrees).
            resolution (int): Resolution of the external_sensor.
            max_range (float): Maximum range of the external_sensor.
            invisible_elements (Optional[List[EmbodiedEntity] or EmbodiedEntity]): Elements invisible to the external_sensor.
            invisible_when_grasped (bool): If True, external_sensor is invisible when grasped.
            **kwargs: Additional keyword arguments.
        """

        super().__init__(**kwargs)

        self._invisible_elements: List[EmbodiedEntity]

        # Invisible elements
        if not invisible_elements:
            self._invisible_elements = []
        elif isinstance(invisible_elements, EmbodiedEntity):
            self._invisible_elements = [invisible_elements]
        else:
            self._invisible_elements = invisible_elements

        self._range = max_range
        self._fov = math.radians(fov)
        self._resolution = resolution

        if self._resolution < 0:
            raise ValueError("resolution must be more than 1")
        if self._fov < 0:
            raise ValueError("field of view must be more than 1")
        if self._range < 0:
            raise ValueError("range must be more than 1")

        self._temporary_invisible: List[EmbodiedEntity] = []
        self._invisible_grasped = invisible_when_grasped
        self._require_invisible_update = False

    @property
    def max_range(self) -> float:
        """
        Returns the maximum range of the external_sensor.
        """
        return self._range

    @property
    def fov(self) -> float:
        """
        Returns the field of view of the external_sensor (in radians).
        """
        return self._fov

    @property
    def resolution(self) -> int:
        """
        Returns the resolution of the external_sensor.
        """
        return self._resolution

    @property
    def invisible_ids(self) -> list:
        """
        Returns a list of IDs of invisible entities for the external_sensor.
        """
        return [ent.uid for ent in self._temporary_invisible + self._invisible_elements]

    @property
    def invisible_grasped(self) -> bool:
        """
        Returns whether the external_sensor is invisible when grasped.
        """
        return self._invisible_grasped

    @property
    def require_invisible_update(self) -> bool:
        """
        Returns whether an update is required for invisible elements.
        """
        return self._require_invisible_update

    def add_to_temporary_invisible(self, elem: EmbodiedEntity) -> None:
        """
        Add an element to the temporary invisible list.

        Args:
            elem (EmbodiedEntity): The entity to add.
        """
        self._temporary_invisible.append(elem)
        self._require_invisible_update = True

    def remove_from_temporary_invisible(self, elem: EmbodiedEntity) -> None:
        """
        Remove an element from the temporary invisible list.

        Args:
            elem (EmbodiedEntity): The entity to remove.
        """
        self._temporary_invisible.remove(elem)
        self._require_invisible_update = True

    def pre_step(self) -> None:
        """
        Pre-step hook for the external_sensor.
        """
        super().pre_step()

    def post_step(self) -> None:
        """
        Post-step hook for the external_sensor.
        """
        super().post_step()
        self._require_invisible_update = False
