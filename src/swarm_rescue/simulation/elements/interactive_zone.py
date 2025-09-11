from __future__ import annotations

from abc import ABC

import arcade
import pymunk

from swarm_rescue.simulation.elements.embodied import EmbodiedEntity
from swarm_rescue.simulation.utils.definitions import (
    SPECIAL_ZONE_ALPHA,
)


class InteractiveZone(EmbodiedEntity, ABC):
    """
    Base class for interactive zones in the playground.
    Interactive zones are non-solid objects that detect collisions.
    """

    def __init__(self, **kwargs):
        """
        Initialize the InteractiveZone.

        Args:
            **kwargs: Additional keyword arguments.
        """
        super().__init__(**kwargs)

        # Mark all pymunk shapes as sensors (non-solid objects that detect collisions)
        for pm_shape in self._pm_shapes:
            pm_shape.sensor = True

    def get_sprite(self, zoom: float = 1, use_color_uid: bool = None) -> arcade.Sprite:
        """
        Retrieve the sprite for the interactive zone and set its transparency.

        Args:
            zoom (float): Zoom factor for the sprite.
            use_color_uid (bool): Whether to use color UID.

        Returns:
            arcade.Sprite: The sprite with adjusted alpha.
        """
        sprite = super().get_sprite(zoom, use_color_uid)
        sprite.alpha = SPECIAL_ZONE_ALPHA

        return sprite

    def _get_pm_body(self) -> pymunk.Body:
        """
        Interactive zones are static objects in pymunk.

        Returns:
            pymunk.Body: The static pymunk body.
        """
        return pymunk.Body(body_type=pymunk.Body.STATIC)
