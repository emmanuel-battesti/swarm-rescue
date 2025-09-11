from __future__ import annotations

import arcade
import numpy as np

from swarm_rescue.simulation.ray_sensors.ray_sensor import RaySensor
from swarm_rescue.simulation.utils.uid import id_to_pixel


class SemanticSensor(RaySensor):
    """
    Sensor that detects semantic information (entity IDs and distances) using rays.
    """

    def _compute_raw_sensor(self) -> None:
        """
        Compute the raw semantic sensor values from hitpoints.
        """
        self._values = self._hitpoints[:, 8:10]

    def draw(self) -> None:
        """
        Draws the semantic sensor rays using Arcade.
        """
        if self._disabled:
            return

        view_xy = self._hitpoints[:, :2]
        center_xy = self._hitpoints[:, 6:8]
        id_detection = self._hitpoints[:, 8].astype(int)

        for ind_pt in range(len(view_xy)):

            if id_detection[ind_pt] != 0:
                color = id_to_pixel(id_detection[ind_pt])

                arcade.draw_line(
                    center_xy[ind_pt, 0],
                    center_xy[ind_pt, 1],
                    view_xy[ind_pt, 0],
                    view_xy[ind_pt, 1],
                    color,
                )

    @property
    def shape(self) -> tuple:
        """
        Returns the shape of the sensor output.
        """
        return self._resolution, 2

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
        self._values = self._values / (1, self._range)
