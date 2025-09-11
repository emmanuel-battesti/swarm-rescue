from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, Optional

import arcade

from swarm_rescue.simulation.elements.embodied import EmbodiedEntity
from swarm_rescue.simulation.utils.definitions import (
    DEFAULT_INTERACTION_RANGE,
    INVISIBLE_ALPHA,
)

if TYPE_CHECKING:
    from swarm_rescue.simulation.elements.physical_entity import PhysicalEntity


class InteractiveAnchored(EmbodiedEntity, ABC):
    """
    Base class for interactive devices anchored to physical entities.
    """

    def __init__(
            self,
            anchor: Optional[PhysicalEntity] = None,
            interaction_range: float = DEFAULT_INTERACTION_RANGE,
            **kwargs,
    ):
        """
        Initialize the InteractiveAnchored device.

        Args:
            anchor (Optional[PhysicalEntity]): The entity to anchor to.
            interaction_range (float): The interaction range.
            **kwargs: Additional keyword arguments.
        """
        if anchor:
            # If an anchor is provided, adjust the texture and radius based on the interaction range
            texture = anchor.texture
            radius = anchor.radius + interaction_range
            super().__init__(texture=texture, radius=radius, **kwargs)
        else:
            super().__init__(**kwargs)

        # Mark all pymunk shapes as sensors (non-solid objects that detect collisions)
        for pm_shape in self._pm_shapes:
            pm_shape.sensor = True

        self._anchor = None

    def get_sprite(self, zoom: float = 1, use_color_uid: bool = None) -> arcade.Sprite:
        """
        Retrieve the sprite and set its transparency.

        Args:
            zoom (float): Zoom factor.
            use_color_uid (bool): Whether to use color UID.

        Returns:
            arcade.Sprite: The sprite with adjusted alpha.
        """
        sprite = super().get_sprite(zoom, use_color_uid)
        sprite.alpha = INVISIBLE_ALPHA
        return sprite

    @property
    def pm_body(self):
        """
        Returns the pymunk body of the entity.
        """
        return self._pm_body

    def set_pm_body(self, pm_body):
        """
        Set the pymunk body and update all shapes to reference it.

        Args:
            pm_body: The pymunk body to set.
        """
        self._pm_body = pm_body
        for pm_shape in self._pm_shapes:
            pm_shape.body = self._pm_body

    @property
    def anchor(self):
        """
        Returns the anchor entity.
        """
        return self._anchor

    def set_anchor(self, anchor: PhysicalEntity):
        """
        Set the anchor and update the pymunk body to match the anchor's body.

        Args:
            anchor (PhysicalEntity): The anchor entity.
        """
        self._anchor = anchor
        for pm_shape in self._pm_shapes:
            pm_shape.body = self._anchor.pm_body

        self._pm_body = self._anchor.pm_body

    def _get_pm_body(self):
        """
        Return None as interactive anchored devices do not have their own body.
        """
        return None

    @property
    def pm_elements(self):
        """
        Returns the pymunk shapes of the entity.
        """
        return self._pm_shapes

    @property
    def needs_sprite_update(self):
        """
        Returns whether the anchor requires a sprite update.
        """
        assert self._anchor
        return self._anchor.needs_sprite_update
