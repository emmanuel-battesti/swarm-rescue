""" Contains the base class for Playgrounds.

Playground class should be inherited to create environments
where agents can play.
Playground defines the physics and mechanics of the game, and manages
how elements interact with each other.

Examples can be found in :
    - spg/playgrounds/empty.py
    - spg/playgrounds/collection
"""
# pylint: disable=too-many-public-methods

from __future__ import annotations

from typing import Dict, List, Optional, Tuple, Union

import arcade
import matplotlib.pyplot as plt
import numpy as np
import pymunk
import pymunk.matplotlib_util

from swarm_rescue.simulation.drone.agent import Agent
from swarm_rescue.simulation.drone.communicator import Communicator, Message
from swarm_rescue.simulation.drone.controller import CommandsDict
from swarm_rescue.simulation.drone.drone_part import DronePart
from swarm_rescue.simulation.drone.interactive_anchored import InteractiveAnchored
from swarm_rescue.simulation.ray_sensors.ray_compute import RayCompute
from swarm_rescue.simulation.ray_sensors.ray_sensor import RaySensor
from swarm_rescue.simulation.drone.sensor import Sensor, SensorValue
from swarm_rescue.simulation.elements.embodied import EmbodiedEntity
from swarm_rescue.simulation.elements.entity import Entity
from swarm_rescue.simulation.elements.physical_element import PhysicalElement
from swarm_rescue.simulation.elements.scene_element import SceneElement
from swarm_rescue.simulation.utils.definitions import (
    PYMUNK_STEPS,
    SPACE_DAMPING,
    CollisionTypes,
)
from swarm_rescue.simulation.utils.position import Coordinate

# pylint: disable=unused-argument
# pylint: disable=line-too-long

AllCommandsDict = Dict[Agent, CommandsDict]
TargetCommunicator = Optional[Union[Communicator, List[Communicator]]]
AllSentMessagesDict = Dict[Agent, Dict[Communicator, Tuple[TargetCommunicator, Message]]]

ObservationsDict = Dict[Agent, Dict[Sensor, SensorValue]]
ReceivedMessagesDict = Dict[Agent, Dict[Communicator, Tuple[Communicator, Message]]]
RewardsDict = Dict[Agent, float]


class Playground:
    """Playground is a Base Class that manages the physical simulation.

    Playground manages the interactions between Agents and Scene Elements.

    Notes:
          In the case of multi-agent setting,
          individual initial positions can be defined when
          instantiating the playground.

          Always reset the playground before starting a run.
    """

    # pylint: disable=too-many-instance-attributes

    time_limit = None
    time_limit_reached_reward = None

    def __init__(
            self,
            size: Optional[Tuple[int, int]] = None,
            seed: Optional[int] = None,
            background: Optional[
                Union[Tuple[int, int, int], List[int], Tuple[int, int, int, int]]
            ] = None,
            use_shaders: bool = True,
    ):
        """
        Initialize the Playground.

        Args:
            size (Optional[Tuple[int, int]]): Size of the playground (width, height).
            seed (Optional[int]): Seed for the random number generator.
            background (Optional[Tuple[int, int, int] or List[int] or Tuple[int, int, int, int]]): Background color.
            use_shaders (bool): Whether to use shaders for rendering.
        """

        # Random number generator for replication, rewind, etc.
        self._rng = np.random.default_rng(seed)

        # By default, size is infinite and center is at (0,0)
        self._center = (0, 0)
        self._size = size

        # Background color
        if not background:
            background = (0, 0, 0, 0)

        self._background = background

        # Initialization of the pymunk space, modelling all the physics
        self._space = self._initialize_space()

        # Lists containing elements in the playground
        self._elements: List[SceneElement] = []
        self._agents: List[Agent] = []

        # Cache variables for performance optimization
        self._cached_agents: List[Agent] = []
        self._cached_elements: List[SceneElement] = []
        self._agents_cache_needs_update = True
        self._elements_cache_needs_update = True

        # Private attributes for managing interactions in playground
        self._timestep: int = 0

        # Mappings
        self._shapes_to_entities: Dict[pymunk.Shape, EmbodiedEntity] = {}
        self._name_to_agents: Dict[str, Agent] = {}
        self._uids_to_entities: Dict[int, Entity] = {}

        self._handle_interactions()
        self._views = []

        # Arcade window necessary to create contexts, views, sensors and gui
        self._window = arcade.Window(width=1, height=1, visible=False, antialiasing=True)  # type: ignore
        self._window.ctx.blend_func = self._window.ctx.ONE, self._window.ctx.ZERO

        self._ray_compute = None
        self._use_shaders = use_shaders

    def debug_draw(self, plt_width: int = 10, center: Optional[Tuple[float, float]] = None, size: Optional[Tuple[int, int]] = None) -> None:
        """
        Draw the playground using matplotlib for debugging.

        Args:
            plt_width (int): Width of the plot.
            center (Optional[Tuple[float, float]]): Center of the plot.
            size (Optional[Tuple[int, int]]): Size of the plot.
        """
        if not center:
            center = self._center

        if not size:
            if not self._size:
                raise ValueError("Size must be set for display")
            size = self._size

        fig_size = (plt_width, plt_width / size[0] * size[1])

        fig = plt.figure(figsize=fig_size)

        ax = plt.axes(
            xlim=(center[0] - size[0] / 2, center[0] + size[0] / 2),
            ylim=(center[1] - size[1] / 2, center[1] + size[1] / 2),
        )
        ax.set_aspect("equal")

        options = pymunk.matplotlib_util.DrawOptions(ax)
        options.collision_point_color = (10, 20, 30, 40)
        self._space.debug_draw(options)
        # ax.invert_yaxis()
        plt.show()
        del fig

    @property
    def window(self) -> arcade.Window:
        """
        Returns the Arcade window associated with the playground.

        Returns:
            arcade.Window: The window.
        """
        return self._window

    @property
    def ctx(self):
        """
        Returns the OpenGL context of the window.
        """
        return self._window.ctx

    @property
    def ray_compute(self) -> RayCompute:
        """
        Returns the RayCompute object for ray-based sensors.

        Returns:
            RayCompute: The RayCompute instance.
        """
        if not self._ray_compute:
            assert self._size
            self._ray_compute = RayCompute(
                self, self._size, self._center, zoom=1, use_shader=self._use_shaders
            )

        return self._ray_compute

    @property
    def background(self):
        """
        Returns the background color of the playground.
        """
        return self._background

    @property
    def rng(self):
        """
        Returns the random number generator.
        """
        return self._rng

    @property
    def size(self) -> Optional[Tuple[int, int]]:
        """
        Returns the size of the playground.

        Returns:
            Optional[Tuple[int, int]]: The size.
        """
        return self._size

    @property
    def center(self) -> Tuple[float, float]:
        """
        Returns the center of the playground.

        Returns:
            Tuple[float, float]: The center.
        """
        return self._center

    @property
    def timestep(self) -> int:
        """
        Returns the current timestep of the simulation.

        Returns:
            int: The timestep.
        """
        return self._timestep

    #################
    # Pymunk space
    #################

    @property
    def space(self) -> pymunk.Space:
        """
        Returns the pymunk Space object for physics simulation.

        Returns:
            pymunk.Space: The pymunk space.
        """
        return self._space

    @staticmethod
    def _initialize_space() -> pymunk.Space:
        """
        Method to initialize Pymunk empty space for 2D physics.

        Returns:
            pymunk.Space: The initialized space.
        """
        space = pymunk.Space()
        space.gravity = pymunk.Vec2d(0.0, 0.0)
        space.damping = SPACE_DAMPING

        return space

    ###############
    # Entities
    ###############

    def _get_identifier(self, entity: Entity):
        """
        Generate a unique identifier and name for an entity.

        Args:
            entity (Entity): The entity to identify.

        Returns:
            tuple: (uid, name)
        """
        uid = None
        background_uid = (
                self._background[0]
                + self._background[1] * 256
                + self._background[2] * 256 * 256
        )

        while True:
            new_uid = self._rng.integers(0, 2 ** 24)

            if new_uid not in self._uids_to_entities and new_uid != background_uid:
                uid = new_uid
                break

        name = entity.name
        if not name:
            name = type(entity).__name__ + "_" + str(uid)

        if name in [ent.name for ent in self.elements]:
            raise ValueError("Entity with this name already in Playground")

        return uid, name

    def get_entity_from_uid(self, uid: int) -> Entity:
        """
        Retrieve an entity from its unique identifier.

        Args:
            uid (int): The unique identifier.

        Returns:
            Entity: The entity.
        """
        return self._uids_to_entities[uid]

    @property
    def agents(self) -> List[Agent]:
        """
        Returns the list of agents currently in the playground.

        Returns:
            List[Agent]: The agents.
        """
        # Cache the result to avoid recalculating every time
        if not hasattr(self, '_cached_agents') or self._agents_cache_needs_update:
            self._cached_agents = [agent for agent in self._agents if not agent.removed]
            self._agents_cache_needs_update = False
        return self._cached_agents

    @property
    def elements(self) -> List[SceneElement]:
        """
        Returns the list of scene elements currently in the playground.

        Returns:
            List[SceneElement]: The elements.
        """
        # Cache the result to avoid recalculating every time
        if not hasattr(self, '_cached_elements') or self._elements_cache_needs_update:
            self._cached_elements = [elem for elem in self._elements if not elem.removed]
            self._elements_cache_needs_update = False
        return self._cached_elements

    ###############
    # STEP
    ###############

    def step(
            self,
            all_commands: Optional[AllCommandsDict] = None,
            all_messages: Optional[AllSentMessagesDict] = None,
            pymunk_steps: int = PYMUNK_STEPS,
    ):
        """
        Update the Playground.

        Updates the Playground.
        Time moves by one unit of time.

        Args:
            all_commands (Optional[AllCommandsDict]): All commands for agents.
            all_messages (Optional[AllSentMessagesDict]): All messages for communicators.
            pymunk_steps (int): Number of steps for the pymunk physics engine to run.

        Returns:
            tuple: (messages, rewards)
        Notes:
            pymunk_steps only influences the micro-steps that
            the physical engine is taking to render
            the movement of objects and collisions.
            From an external point of view,
            one unit of time passes independent on the number
            of pymunk_steps.

        """
        mess, rew = None, None

        self._pre_step()

        self._apply_commands(all_commands)

        for _ in range(pymunk_steps):
            self.space.step(1.0 / pymunk_steps)

        self._compute_observations()

        self._post_step()

        rew = {agent: agent.reward for agent in self._agents}
        if all_messages:
            mess = self._transmit_messages(all_messages)

        self._timestep += 1

        return mess, rew

    def _pre_step(self) -> None:
        """
        Perform pre-step updates for all elements and agents.
        """
        for element in self.elements:
            element.pre_step()

        for agent in self.agents:
            agent.pre_step()

    def _post_step(self) -> None:
        """
        Perform post-step updates for all elements and agents.
        """
        for element in self.elements:
            element.post_step()

        for agent in self.agents:
            agent.post_step()

    def _apply_commands(self, all_commands: Optional[Dict[Agent, CommandsDict]] = None) -> None:
        """
        Apply commands to all agents.

        Args:
            all_commands (Optional[Dict[Agent, CommandsDict]]): Commands for agents.
        """
        if not all_commands:
            return

        for agent, commands_dict in all_commands.items():
            agent.receive_commands(commands_dict)

        for agent in self._agents:
            agent.apply_commands()

    def _transmit_messages(self, all_messages: Optional[AllSentMessagesDict] = None):
        """
        Transmit messages between communicators.

        Args:
            all_messages (Optional[AllSentMessagesDict]): Messages to transmit.

        Returns:
            dict: Received messages.
        """
        msgs = {agent: {} for agent in self.agents}

        all_sent_messages = [
            (agent, comm_source, target)
            for agent, comms_dict in all_messages.items()
            for comm_source, target in comms_dict.items()
        ]

        for agent, comm_source, target in all_sent_messages:

            assert comm_source.agent is agent

            comm_target, message = target
            msg = comm_source.send(message)

            if not msg:
                continue

            if isinstance(comm_target, list):
                for targ in comm_target:
                    assert isinstance(targ, Communicator)
                    received_msg = targ.receive(comm_source, msg)

                    if received_msg:
                        msgs[targ.agent][targ] = (comm_source, received_msg)

            elif isinstance(comm_target, Communicator):
                received_msg = comm_target.receive(comm_source, msg)

                if received_msg:
                    msgs[comm_target.agent][comm_target] = (comm_source, received_msg)

            elif comm_target is None:
                for agent2 in self.agents:
                    for comm in agent2.communicators:
                        received_msg = comm.receive(comm_source, msg)
                        if received_msg:
                            msgs[comm.agent][comm] = (comm_source, received_msg)

            else:
                raise ValueError

        return msgs

    def _compute_observations(self) -> None:
        """
        Compute observations for all agents.

        Returns:
            dict: Observations for each agent.
        """
        if self._ray_compute:
            self._ray_compute.update_sensors()

        for agent in self.agents:
            agent.compute_observations()

    def reset(self):
        """
        Reset the Playground to its initial state.
        """
        # reset elements that are still in playground
        for element in self._elements:

            if isinstance(element, Entity) and element.temporary:
                self.remove(element, definitive=True)
            elif isinstance(element, Entity) and element.removed:
                self.add(element, from_removed=True)
            elif isinstance(element, PhysicalElement) and element.movable:
                assert element.initial_coordinates
                element.move_to(
                    element.initial_coordinates,
                    element.allow_overlapping,
                )
            elif isinstance(element, EmbodiedEntity) and element.moved:
                assert element.initial_coordinates
                element.move_to(
                    element.initial_coordinates,
                    element.allow_overlapping,
                )

            element.reset()

        for agent in self._agents:
            agent.reset()
            if agent.removed:
                self.add(agent, from_removed=True)
            else:
                agent.base.move_to(
                    agent.initial_coordinates,
                    allow_overlapping=agent.allow_overlapping,
                    move_anchors=True,
                )

        for view in self._views:
            view.update_and_draw_in_framebuffer(force=True)

        self._timestep = 0

        self._compute_observations()


    def add(
            self,
            entity: Entity,
            initial_coordinates=None,
            allow_overlapping=True,
            from_removed=False,
    ):
        """
        Add an entity to the playground.

        Args:
            entity (Entity): The entity to add.
            initial_coordinates: Initial coordinates for the entity.
            allow_overlapping (bool): Whether to allow overlapping.
            from_removed (bool): Whether the entity is being re-added from removed.
        """

        entity.playground = self

        if from_removed:
            initial_coordinates = entity.initial_coordinates
            allow_overlapping = entity.allow_overlapping

        self._add_to_space(entity, initial_coordinates, allow_overlapping)

        if not from_removed:
            self._add_to_mappings(entity)

        self._add_to_views(entity)

        if isinstance(entity, Agent):
            self.add(
                entity.base,
                initial_coordinates=initial_coordinates,
                allow_overlapping=allow_overlapping,
                from_removed=from_removed,
            )

        if isinstance(entity, DronePart):
            for device in entity.devices:
                self.add(
                    device,
                    allow_overlapping=allow_overlapping,
                    from_removed=from_removed,
                )

                if isinstance(device, RaySensor):
                    self.ray_compute.add(device)

        elif isinstance(entity, PhysicalElement):
            for interactive in entity.interactives:
                self.add(
                    interactive,
                    allow_overlapping=allow_overlapping,
                    from_removed=from_removed,
                )

    def _add_to_space(self, entity, initial_coordinates, allow_overlapping):
        """
        Add the entity to the pymunk space.

        Args:
            entity: The entity to add.
            initial_coordinates: Initial coordinates.
            allow_overlapping: Whether to allow overlapping.
        """
        # Mark the entity as not removed
        entity.removed = False

        # Add shapes directly for InteractiveAnchored entities without moving them
        # because they are anchored to a fixed position
        if isinstance(entity, InteractiveAnchored):
            self._space.add(*entity.pm_elements)
            return

        # Check if the entity has initial coordinates, otherwise use the provided ones
        if entity.initial_coordinates:
            initial_coordinates = entity.initial_coordinates

        # Ensure initial coordinates are defined
        if not initial_coordinates:
            raise ValueError(
                "Either initial coordinate or size of the environment should be set"
            )

        # Assign the validated initial coordinates and overlapping allowance to the entity
        entity.initial_coordinates = initial_coordinates
        entity.allow_overlapping = allow_overlapping

        # Check if the entity is an Agent, in which case we skip adding it to the space
        # as his base will be added in the add() method.
        if isinstance(entity, Agent):
            return

        self._space.add(*entity.pm_elements)
        entity.move_to(
            coordinates=initial_coordinates,
            allow_overlapping=allow_overlapping,
        )

    def _add_to_mappings(self, entity):
        """
        Add the entity to internal mappings.

        Args:
            entity: The entity to map.
        """
        entity.uid, entity.name = self._get_identifier(entity)

        self._uids_to_entities[entity.uid] = entity

        if isinstance(entity, Agent):
            self._agents.append(entity)
            self._name_to_agents[entity.name] = entity
            self._agents_cache_needs_update = True

        elif isinstance(entity, SceneElement):
            self._elements.append(entity)
            self._elements_cache_needs_update = True

        if isinstance(entity, EmbodiedEntity):
            for pm_shape in entity.pm_shapes:
                self._shapes_to_entities[pm_shape] = entity

    def _add_to_views(self, entity):
        """
        Add the entity to all registered views.

        Args:
            entity: The entity to add.
        """
        if isinstance(entity, Agent):
            return

        for view in self._views:
            view.add_as_sprite(entity)

    def remove(self, entity, definitive=False):
        """
        Remove an entity from the playground.

        Args:
            entity: The entity to remove.
            definitive (bool): Whether to remove definitively.
        """
        if not entity.removed:
            self._remove_from_space(entity)
            self._remove_from_views(entity)

        if definitive:
            self._remove_from_mappings(entity)

        if isinstance(entity, Agent):
            self.remove(entity.base, definitive)

        if isinstance(entity, DronePart):
            for device in entity.devices:
                self.remove(device, definitive)

        elif isinstance(entity, PhysicalElement):

            for interactive in entity.interactives:
                self.remove(interactive, definitive)

            for grasper in entity.grasped_by:
                grasper.release(entity)

        entity.removed = True

    def _remove_from_space(self, entity):
        """
        Remove the entity from the pymunk space.

        Args:
            entity: The entity to remove.
        """
        if isinstance(entity, Agent):
            return

        self._space.remove(*entity.pm_elements)

    def _remove_from_mappings(self, entity):
        """
        Remove the entity from internal mappings.

        Args:
            entity: The entity to remove.
        """
        assert entity.uid

        # Protection: if already removed from mappings, skip
        if entity.uid not in self._uids_to_entities:
            return

        self._uids_to_entities.pop(entity.uid)

        if isinstance(entity, Agent):
            if entity in self._agents:
                self._agents.remove(entity)
                self._agents_cache_needs_update = True

            assert entity.name
            if entity.name in self._name_to_agents:
                self._name_to_agents.pop(entity.name)

        elif isinstance(entity, SceneElement):
            if entity in self._elements:
                self._elements.remove(entity)
                self._elements_cache_needs_update = True

        if not isinstance(entity, Agent):
            for pm_shape in entity.pm_shapes:
                if pm_shape in self._shapes_to_entities:
                    self._shapes_to_entities.pop(pm_shape)

        entity.playground = None

    def _remove_from_views(self, entity):
        """
        Remove the entity from all registered views.

        Args:
            entity: The entity to remove.
        """
        if isinstance(entity, Agent):
            return
        for view in self._views:
            view.remove_as_sprite(entity)

    def add_view(self, view):
        """
        Add a view to the playground and register all entities with it.

        Args:
            view: The view to add.
        """
        for entity in self.elements:
            view.add_as_sprite(entity)

            if isinstance(entity, PhysicalElement):
                for interactive in entity.interactives:
                    view.add_as_sprite(interactive)

        for agent in self.agents:
            view.add_as_sprite(agent.base)

            for device in agent.base.devices:
                view.add_as_sprite(device)

        self._views.append(view)

    def within_playground(
            self,
            entity: Optional[Union[Agent, EmbodiedEntity]] = None,
            coordinates: Optional[Coordinate] = None,
    ):
        """
        Check if an entity or coordinates are within the playground bounds.

        Args:
            entity (Optional[Union[Agent, EmbodiedEntity]]): The entity to check.
            coordinates (Optional[Coordinate]): The coordinates to check.

        Returns:
            bool: True if within bounds, False otherwise.
        """
        if not self._size:
            return True

        if isinstance(entity, Agent):
            for part in entity.parts:
                if not self.within_playground(part):
                    return False

        if entity:
            position = entity.position
        elif coordinates:
            position = coordinates[0]
        else:
            raise ValueError("entity or coordinates must be specified")

        if not -self._size[0] / 2 <= position[0] <= self._size[0] / 2:
            return False

        if not -self._size[1] / 2 <= position[1] <= self._size[1] / 2:
            return False

        return True

    def overlaps(self, entity: EmbodiedEntity, coordinates) -> bool:
        """
        Test whether a new coordinate would lead to a physical collision.

        Args:
            entity (EmbodiedEntity): The entity to test.
            coordinates: The coordinates to test.

        Returns:
            bool: True if overlaps, False otherwise.
        """
        dummy_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        dummy_shapes = []
        for pm_shape in entity.pm_shapes:
            dummy_shape = pm_shape.copy()
            dummy_shape.body = dummy_body
            dummy_shape.sensor = True
            dummy_shapes.append(dummy_shape)

        self.space.add(dummy_body, *dummy_shapes)

        dummy_body.position, dummy_body.angle = coordinates
        self.space.reindex_static()

        overlaps = []
        for dummy_shape in dummy_shapes:
            overlaps += self.space.shape_query(dummy_shape)
        self.space.remove(dummy_body, *dummy_shapes)

        # remove sensor shapes
        overlaps = [
            elem
            for elem in overlaps
            if elem.shape
               and not elem.shape.sensor
               and elem.shape not in entity.pm_shapes
        ]

        if isinstance(entity, DronePart):
            agent_shapes = []
            for part in entity.agent.parts:
                agent_shapes += part.pm_shapes

            overlaps = [elem for elem in overlaps if elem.shape not in agent_shapes]

        self.space.reindex_static()

        return bool(overlaps)

    def get_closest_agent(self, entity: EmbodiedEntity) -> Agent:
        """
        Get the closest agent to a given entity.

        Args:
            entity (EmbodiedEntity): The entity to compare.

        Returns:
            Agent: The closest agent.
        """
        return min(self.agents, key=lambda a: entity.position.get_dist_sqrd(a.position))

    def get_entity_from_shape(self, shape: pymunk.Shape) -> EmbodiedEntity:
        """
        Retrieve the entity associated with a pymunk shape.

        Args:
            shape (pymunk.Shape): The shape.

        Returns:
            EmbodiedEntity: The associated entity.
        """
        assert shape in self._shapes_to_entities

        entity = self._shapes_to_entities[shape]

        return entity

    def _handle_interactions(self) -> None:
        """
        Set up collision interactions for the playground.
        """
        ...

    def cleanup(self):
        """
        Clean up resources and prepare for garbage collection.
        Should be called when the playground is no longer needed.

        Note: This method cleans internal data structures and frees resources
        but does NOT close the GUI window. Close the window explicitly by
        calling `close_window()` when desired. This avoids closing a global
        window used by other tests or components.
        """
        # Clear all entities
        for agent in self._agents.copy():
            self.remove(agent, definitive=True)

        for element in self._elements.copy():
            self.remove(element, definitive=True)

        # Clear caches
        self._cached_agents.clear()
        self._cached_elements.clear()

        # Clear all mappings
        self._shapes_to_entities.clear()
        self._name_to_agents.clear()
        self._uids_to_entities.clear()

        # Clear views
        self._views.clear()

        # Note: Do NOT close the window here. Call close_window() explicitly when needed.

        # Clear ray compute
        if self._ray_compute:
            self._ray_compute = None

    def close_window(self) -> None:
        """
        Close the GUI window associated with this playground, if any.

        This is separated from `cleanup()` so tests and other callers can
        clean internal resources without closing a shared/global window.
        """
        if hasattr(self, '_window') and self._window:
            try:
                self._window.close()
            except Exception:
                # Ignore errors while closing window to avoid test flakes
                pass
            finally:
                # Ensure reference is removed
                self._window = None

    def add_interaction(
            self,
            collision_type_1: CollisionTypes,
            collision_type_2: CollisionTypes,
            interaction_function,
    ):
        """
        Add a collision interaction handler to the playground.

        Args:
            collision_type_1 (CollisionTypes): Collision type of the first entity.
            collision_type_2 (CollisionTypes): Collision type of the second entity.
            interaction_function: Function that handles the interaction.
        """
        handler: pymunk.CollisionHandler = self.space.add_collision_handler(collision_type_1, collision_type_2)
        handler.pre_solve = interaction_function
        handler.data["playground"] = self