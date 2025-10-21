from __future__ import annotations

from typing import Optional, Tuple

import pymunk

from swarm_rescue.simulation.drone.device import Device
from swarm_rescue.simulation.utils.sprite import get_texture_from_shape

DEVICE_RADIUS = 5


class PocketDevice(Device):
    """
    Base class for small, circular devices attached to drone parts.
    """

    def __init__(
            self,
            color: Optional[Tuple[int, int, int]] = None,
            **kwargs,
    ):
        """
        Initialize a PocketDevice.

        Args:
            color (Optional[Tuple[int, int, int]]): Color of the device.
            radius (float): Radius of the device.
            **kwargs: Additional keyword arguments.
        """
        pm_shape = pymunk.Circle(None, DEVICE_RADIUS)
        texture = get_texture_from_shape(
            pm_shape, color, f"Device_{DEVICE_RADIUS}_{color}"
        )
        shape_approximation = "circle"
        radius = DEVICE_RADIUS

        super().__init__(
            texture=texture,
            shape_approximation=shape_approximation,
            radius=radius,
            **kwargs,
        )
