from __future__ import annotations

from abc import ABC
from typing import Optional

import pymunk

from swarm_rescue.simulation.elements.embodied import EmbodiedEntity


class PhysicalEntity(EmbodiedEntity, ABC):
    """
    PhysicalEntity creates a physical object that can collide with
    other Physical Entities.
    It deals with physical properties such as the mass, visual texture,
     whether it is transparent or not.
    PhysicalEntity is visible by default.
    An agent is composed of multiple PhysicalEntity that are attached to each other.
    """

    def __init__(
            self,
            mass: Optional[float] = None,
            transparent: bool = False,
            **kwargs,
    ):
        """
        Initialize the PhysicalEntity.

        Args:
            mass (Optional[float]): Mass of the entity.
            transparent (bool): Whether the entity is transparent.
            **kwargs: Additional keyword arguments.
        """
        self._mass = mass
        self._transparent = transparent

        super().__init__(**kwargs)

    @property
    def transparent(self) -> bool:
        """
        Returns whether the entity is transparent.
        """
        return self._transparent

    @property
    def movable(self) -> bool:
        """
        Returns whether the entity is movable (has mass).
        """
        return bool(self._mass)

    @property
    def needs_sprite_update(self) -> bool:
        """
        Returns whether the sprite needs to be updated.
        """
        return self._moved or self.movable

    ########################
    # BODY AND SHAPE
    ########################

    def _get_pm_body(self) -> pymunk.Body:
        """
        Returns the pymunk body for the entity.

        Returns:
            pymunk.Body: The pymunk body.
        """
        if not self._mass:
            return pymunk.Body(body_type=pymunk.Body.STATIC)

        vertices = self._base_sprite.get_hit_box()
        moment = pymunk.moment_for_poly(self._mass, vertices)

        return pymunk.Body(self._mass, moment, body_type=pymunk.Body.DYNAMIC)
