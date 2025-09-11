""" Contains the base class for entities.

Entity classes should be used to create body parts of
an agent, scene entities, spawners, timers, etc.

Entity is the generic building block of physical and interactive
objects in simple-playgrounds.

"""
from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from swarm_rescue.simulation.gui_map.playground import Playground


class Entity(ABC):
    """
    Base class that defines the entities that composing a Playground.
    Entities can be: SceneElement, Agent, Spawner, Timer, ...
    """

    def __init__(
            self,
            name: Optional[str] = None,
            temporary: bool = False,
            **_,
    ):
        """
        Initialize an Entity.

        Args:
            name (Optional[str]): Name of the entity.
            temporary (bool): Whether the entity is temporary.
            **_: Additional keyword arguments.
        """
        # Unique identifiers
        self._uid = None
        self._name = name

        self._temporary = temporary
        self._removed = False
        self._playground = None

    @property
    def uid(self) -> Optional[int]:
        """
        Returns the unique identifier of the entity.
        """
        return self._uid

    @uid.setter
    def uid(self, uid: int) -> None:
        """
        Set the unique identifier of the entity.

        Args:
            uid (int): Unique identifier.
        """
        self._uid = uid

    @property
    def name(self) -> Optional[str]:
        """
        Returns the name of the entity.
        """
        return self._name

    @name.setter
    def name(self, name: str) -> None:
        """
        Set the name of the entity.

        Args:
            name (str): Name of the entity.
        """
        self._name = name

    @property
    def removed(self) -> bool:
        """
        Returns whether the entity has been removed.
        """
        return self._removed

    @removed.setter
    def removed(self, rem: bool) -> None:
        """
        Set the removed state of the entity.

        Args:
            rem (bool): Removed state.
        """
        self._removed = rem

    @property
    def temporary(self) -> bool:
        """
        Returns whether the entity is temporary.
        """
        return self._temporary

    @property
    def playground(self) -> Optional["Playground"]:
        """
        Returns the playground the entity belongs to.
        """
        return self._playground

    @playground.setter
    def playground(self, playground: Optional[Playground]) -> None:
        """
        Set the playground for the entity.

        Args:
            playground (Optional[Playground]): Playground instance.
        """
        self._playground = playground

    @property
    def rng(self):
        """
        Returns the random number generator from the playground, if available.
        """
        if self._playground:
            return self._playground.rng

        return None

    def reset(self) -> None:
        """
        Upon reset of the Playground,
        revert the entity back to its original state.
        """

    def pre_step(self) -> None:
        """
        Preliminary calculations before the pymunk engine steps.
        """

    def post_step(self) -> None:
        """
        Updates the entity state after pymunk engine steps.
        """
