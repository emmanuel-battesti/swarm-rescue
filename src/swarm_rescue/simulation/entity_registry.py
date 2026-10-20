"""
The registry of everything that lives in the playground, and how to find it.

This class owns the lists, the caches and the lookup tables, and keeps the
flags to itself: `agents` rebuilds its cache when it must, so no caller can
forget to invalidate anything. Answering "who is in the world, and what is
their uid" therefore needs no window and no rendering.

`pymunk` is used, because that is what the uid is encoded into -- but nothing
here knows about arcade, a window, or a view.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from swarm_rescue.simulation.drone.agent import Agent
from swarm_rescue.simulation.elements.embodied import EmbodiedEntity
from swarm_rescue.simulation.elements.entity import Entity
from swarm_rescue.simulation.elements.scene_element import SceneElement


class EntityRegistry:
    """
    Knows which entities exist, and resolves a uid or a shape back to one.

    The playground delegates to this; a solution never sees it, which is why
    it is not part of the participant API.
    """

    def __init__(self) -> None:
        self._agents: List[Agent] = []
        self._elements: List[Entity] = []

        # uid -> entity, and pymunk shape -> entity. The second is what the
        # collision handlers read: a pymunk collision gives shapes, not
        # entities, and something has to translate.
        self._uids_to_entities: Dict[int, Entity] = {}
        self._shapes_to_entities: Dict[object, Entity] = {}

        # `agents` and `elements` are read on every step by every sensor, so
        # they are cached. The flags live here rather than in the playground so
        # that nothing outside can invalidate the cache behind the registry's
        # back.
        self._cached_agents: List[Agent] = []
        self._cached_elements: List[Entity] = []
        self._agents_cache_needs_update = False
        self._elements_cache_needs_update = False

    @property
    def agents(self) -> List[Agent]:
        """
        The agents currently in the playground, removed ones excluded.

        Returns:
            List[Agent]: The live agents.
        """
        if self._agents_cache_needs_update:
            self._cached_agents = [
                agent for agent in self._agents if not agent.removed
            ]
            self._agents_cache_needs_update = False

        return self._cached_agents

    @property
    def elements(self) -> List[Entity]:
        """
        The elements currently in the playground, removed ones excluded.

        Returns:
            List[Entity]: The live elements.
        """
        if self._elements_cache_needs_update:
            self._cached_elements = [
                elem for elem in self._elements if not elem.removed
            ]
            self._elements_cache_needs_update = False

        return self._cached_elements

    @property
    def uids_to_entities(self) -> Dict[int, Entity]:
        """
        The uid lookup table.

        The uids are what the ray sensors report: a lidar hit means nothing
        without a way back to the entity that was hit.

        Returns:
            Dict[int, Entity]: uid -> entity.
        """
        return self._uids_to_entities

    @property
    def shapes_to_entities(self) -> Dict[object, Entity]:
        """
        The shape lookup table used by the collision handlers.

        Returns:
            Dict[object, Entity]: pymunk shape -> entity.
        """
        return self._shapes_to_entities

    def get_entity_from_uid(self, uid: int) -> Optional[Entity]:
        """
        Find the entity a sensor hit.

        Args:
            uid (int): The uid read from the uid image.

        Returns:
            Optional[Entity]: The entity, or None if it is gone -- a drone
            destroyed mid-step stays in the last sensor reading.
        """
        return self._uids_to_entities.get(uid, None)

    def get_entity_from_shape(self, pm_shape) -> Optional[Entity]:
        """
        Find the entity a pymunk shape belongs to.

        Args:
            pm_shape: The pymunk shape from the collision arbiter.

        Returns:
            Optional[Entity]: The owning entity, or None for a shape the
            playground does not know (one already removed).
        """
        return self._shapes_to_entities.get(pm_shape, None)

    # --- Naming ------------------------------------------------------------

    def _existing_names(self) -> set:
        """
        Every name already in use, so a duplicate can be rejected.

        Returns:
            set: The names of the live elements and agents.
        """
        names = {elem.name for elem in self.elements}
        names.update(agent.name for agent in self.agents)
        return names

    def _get_identifier(self, entity: Entity, rng, background_uid: int):
        """
        Draw a unique uid for an entity, and check its name is free.

        The uid is drawn from the playground's generator rather than from
        `pymunk.b2d_hash`. That is deliberate and load-bearing: the ray sensors
        identify entities by uid, so drawing it from the seeded generator is
        what makes a seeded round replayable. A hash of the pymunk handles
        would tie the uids to allocation order instead.

        The background color is excluded because the uid image clears with it:
        an entity carrying it would be invisible to every sensor.

        Args:
            entity (Entity): The entity to identify.
            rng: The playground generator, seeded when a seed was given.
            background_uid (int): The uid the background color encodes to.

        Returns:
            tuple: (uid, name)

        Raises:
            ValueError: If the entity's name is already used.
        """
        uid = None

        while True:
            new_uid = rng.integers(0, 2**24)

            if new_uid not in self._uids_to_entities and new_uid != background_uid:
                uid = new_uid
                break

        name = entity.name
        if not name:
            name = type(entity).__name__ + "_" + str(uid)

        if name in self._existing_names():
            raise ValueError(
                f"Entity with this name already in Playground: {name}"
            )

        return uid, name

    # --- Registration ------------------------------------------------------

    def register(self, entity: Entity, rng, background_uid: int) -> None:
        """
        Record a newly added entity, and give it a uid and a name.

        Args:
            entity (Entity): The entity to record.
            rng: The playground generator, for the uid.
            background_uid (int): The uid the background color encodes to.
        """
        entity.uid, entity.name = self._get_identifier(
            entity, rng, background_uid
        )

        self._uids_to_entities[entity.uid] = entity

        if isinstance(entity, Agent):
            self._agents.append(entity)
            self._agents_cache_needs_update = True

        elif isinstance(entity, SceneElement):
            self._elements.append(entity)
            self._elements_cache_needs_update = True

        if isinstance(entity, EmbodiedEntity):
            for pm_shape in entity.pm_shapes:
                self._shapes_to_entities[pm_shape] = entity

    def unregister(self, entity: Entity) -> None:
        """
        Forget an entity for good.

        Only called on a definitive removal. A non-definitive `remove()` keeps
        the mappings, so a sensor reading taken during the step can still be
        resolved: otherwise a drone destroyed mid-step would make the lidar
        report a uid that maps to nothing.

        Args:
            entity (Entity): The entity to forget.
        """
        assert entity.uid

        # Already gone: removing twice must not raise.
        if entity.uid not in self._uids_to_entities:
            return

        self._uids_to_entities.pop(entity.uid)

        if isinstance(entity, Agent):
            if entity in self._agents:
                self._agents.remove(entity)
                self._agents_cache_needs_update = True

        elif isinstance(entity, SceneElement):
            if entity in self._elements:
                self._elements.remove(entity)
                self._elements_cache_needs_update = True

        if not isinstance(entity, Agent):
            for pm_shape in getattr(entity, "pm_shapes", []):
                if pm_shape in self._shapes_to_entities:
                    self._shapes_to_entities.pop(pm_shape)

        entity.playground = None

    def mark_changed(self, entity: Entity) -> None:
        """
        Flag that an entity was added or removed, so the caches are rebuilt.

        The agent/element distinction is made here rather than in the
        caller, because `entity.removed` may have been set elsewhere.

        Args:
            entity (Entity): The entity whose list changed.
        """
        if isinstance(entity, Agent):
            self._agents_cache_needs_update = True
        elif isinstance(entity, SceneElement):
            self._elements_cache_needs_update = True

    def clear(self) -> None:
        """Drop everything. Used by `Playground.cleanup()`."""
        self._agents.clear()
        self._elements.clear()
        self._uids_to_entities.clear()
        self._shapes_to_entities.clear()
        self._cached_agents.clear()
        self._cached_elements.clear()
        self._agents_cache_needs_update = False
        self._elements_cache_needs_update = False
