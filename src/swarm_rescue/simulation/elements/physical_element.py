"""
Module that defines Base Class PhysicalElement
"""
from __future__ import annotations

from typing import Optional

from swarm_rescue.simulation.drone.interactive_anchored import InteractiveAnchored
from swarm_rescue.simulation.elements.entity import Entity
from swarm_rescue.simulation.elements.physical_entity import PhysicalEntity
from swarm_rescue.simulation.elements.scene_element import SceneElement
from swarm_rescue.simulation.utils.definitions import CollisionTypes


class PhysicalElement(PhysicalEntity, SceneElement):
    """
    Base class for physical elements in the playground.
    """

    def __init__(self, **entity_params):
        """
        Initialize the PhysicalElement.

        Args:
            **entity_params: Additional keyword arguments.
        """
        super().__init__(**entity_params)

        self._interactives = []
        self._grasped_by = []
        self._graspable = False
        self._produced_by: Optional[Entity] = None

    @property
    def graspable(self) -> bool:
        """
        Returns whether the element is graspable.
        """
        return bool(self._graspable)

    @graspable.setter
    def graspable(self, graspable: bool) -> None:
        """
        Set whether the element is graspable.

        Args:
            graspable (bool): Graspable state.
        """
        self._graspable = graspable

    @property
    def grasped_by(self):
        """
        Returns the list of entities grasping this element.
        """
        return self._grasped_by

    @property
    def produced_by(self) -> Optional[Entity]:
        """
        Returns the entity that produced this element, if any.
        """
        return self._produced_by

    @property
    def interactives(self):
        """
        Returns the list of interactive devices attached to this element.
        """
        return self._interactives

    def add_device(self, interactive: InteractiveAnchored) -> None:
        """
        Add an interactive device to this element.

        Args:
            interactive (InteractiveAnchored): The device to add.
        """
        self._interactives.append(interactive)
        interactive.set_pm_body(self._pm_body)
        interactive.set_anchor(self)

        if self._playground:
            self._playground.add(interactive)

    @property
    def _collision_type(self):
        """
        Returns the collision type for the physical element.
        """
        return CollisionTypes.ELEMENT
