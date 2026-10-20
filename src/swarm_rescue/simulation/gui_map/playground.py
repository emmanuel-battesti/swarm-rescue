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
import numpy as np
import pymunk

from swarm_rescue.simulation.drone.agent import Agent
from swarm_rescue.simulation.drone.communicator import Communicator, Message
from swarm_rescue.simulation.drone.controller import CommandsDict
from swarm_rescue.simulation.drone.drone_part import DronePart
from swarm_rescue.simulation.drone.grasper import Grasper
from swarm_rescue.simulation.drone.interactive_anchored import InteractiveAnchored
from swarm_rescue.simulation.ray_sensors.ray_compute import RayCompute
from swarm_rescue.simulation.ray_sensors.ray_sensor import RaySensor
from swarm_rescue.simulation.drone.sensor import Sensor, SensorValue
from swarm_rescue.simulation.elements.embodied import EmbodiedEntity
from swarm_rescue.simulation.elements.entity import Entity
from swarm_rescue.simulation.elements.physical_element import PhysicalElement
from swarm_rescue.simulation.gui_map.top_down_view import TopDownView
from swarm_rescue.simulation.simulation_stepper import SimulationStepper
from swarm_rescue.simulation.entity_registry import EntityRegistry
from swarm_rescue.simulation.utils.definitions import (
    PYMUNK_STEPS,
    SPACE_DAMPING,
    CollisionTypes,
)
from swarm_rescue.simulation.utils.position import Coordinate
from swarm_rescue.simulation.utils.constants import ENABLE_WINDOW_RESIZING
from swarm_rescue.simulation.utils.shader_config import ShaderConfig

# pylint: disable=unused-argument
# pylint: disable=line-too-long

AllCommandsDict = Dict[Agent, CommandsDict]
TargetCommunicator = Optional[Union[Communicator, List[Communicator]]]
AllSentMessagesDict = Dict[Agent, Dict[Communicator, Tuple[TargetCommunicator, Message]]]

ObservationsDict = Dict[Agent, Dict[Sensor, SensorValue]]
ReceivedMessagesDict = Dict[Agent, Dict[Communicator, Tuple[Communicator, Message]]]
RewardsDict = Dict[Agent, float]


def _needs_repositioning(element) -> bool:
    """
    Whether `Playground.reset()` must put an element back in its initial place.

    Two independent reasons, kept as separate tests because they do not cover
    the same entities:

    - the entity actually moved. `moved` is defined on `EmbodiedEntity`, and
      is True as soon as it has been displaced (or is a moving dynamic body).
    - the entity is a `PhysicalEntity` with a mass, so something could have
      pushed it around. `movable` only exists on `PhysicalEntity`, which is why
      the isinstance test guards it.

    Args:
        entity: The element to check.

    Returns:
        bool: True if the element must be moved back.
    """
    if not isinstance(element, EmbodiedEntity):
        return False

    if element.moved:
        return True

    if isinstance(element, PhysicalElement) and element.movable:
        return True

    return False


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
            use_shaders: Optional[bool] = None,
            window: Optional[arcade.Window] = None,
    ):
        """
        Initialize the Playground.

        Args:
            size (Optional[Tuple[int, int]]): Size of the playground (width, height).
            seed (Optional[int]): Seed for the random number generator.
            background (Optional[Tuple[int, int, int] or List[int] or Tuple[int, int, int, int]]): Background color.
            use_shaders (Optional[bool]): Whether to use shaders for rendering.
                If None, uses ShaderConfig.get_use_shaders() for auto-detection.
            window (Optional[arcade.Window]): An existing window to draw in.
                Defaults to a new invisible 1x1 window owned by the playground.
                Passing one in is what lets a caller own the window's lifetime
                -- see `close_window`.
        """

        # Random number generator for replication, rewind, etc.
        self._rng = np.random.default_rng(seed)
        self._seed = seed

        # We need an independent generator for the sensor noise. It is derived from the
        # same seed, so that a seeded run will replay its noisy readings, too. However, it
        # is kept apart from the other generator `_rng`: the generated UIDs must not shift
        # when a sensor consumes a different amount of generated noise.
        # The value "None" leaves the noise on the global RNG.
        self._noise_rng = np.random.default_rng(seed)

        # By default, size is infinite and center is at (0,0)
        self._center = (0, 0)
        self._size = size

        # Background color
        if not background:
            background = (0, 0, 0, 0)

        self._background = background

        # Initialization of the pymunk space, modeling all the physics
        self._space = self._initialize_space()

        # Who exists, and how to find them again by uid or by shape.
        #
        # The lists, the caches and the lookup tables live in the registry, not
        # here: answering "who is in the world" has nothing to do with the
        # window this class also owns. See simulation/entity_registry.py.
        self._registry = EntityRegistry()

        # Private attributes for managing interactions in playground
        self._timestep: int = 0

        # The step loop lives in its own object; this attribute is the handle.
        self._stepper = SimulationStepper(self)

        self._handle_interactions()
        self._views = []

        # Arcade window necessary to create contexts, views, sensors and gui.
        #
        # The playground accepts one instead of always creating it, so that the
        # caller can decide the lifetime: a caller that passes a window keeps
        # it, and `close_window()` leaves it alone. When no window is passed,
        # the playground creates a throwaway invisible one and closes it itself.
        self._owns_window = window is None

        if window is None:
            self._window = arcade.Window(
                width=1, height=1, visible=False, antialiasing=True,
                resizable=ENABLE_WINDOW_RESIZING
            )
            # Prevent the window from being resized too small
            self._window.set_minimum_size(320, 240)
        else:
            self._window = window


        self._ray_compute = None
        # Use ShaderConfig for smart shader detection
        self._use_shaders = ShaderConfig.get_use_shaders(override=use_shaders)

    def debug_draw(
        self,
        plt_width: int = 10,
        center: Optional[Tuple[float, float]] = None,
        size: Optional[Tuple[int, int]] = None,
    ) -> None:
        """
        Draw the playground using matplotlib for debugging.

        `matplotlib` is imported here rather than at module level: it costs
        about half a second to import, `debug_draw()` is called by hand from a
        debugger, and every other module that needs the playground should not
        pay for it.

        Args:
            plt_width (int): Width of the plot.
            center (Optional[Tuple[float, float]]): Center of the plot.
            size (Optional[Tuple[int, int]]): Size of the plot.
        """
        import matplotlib.pyplot as plt
        import pymunk.matplotlib_util

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
        if self._ray_compute is None:
            assert self._size
            self._ray_compute = RayCompute(
                self.ctx,
                self._create_uid_view(),
                use_shader=self._use_shaders,
            )

        assert self._ray_compute is not None
        return self._ray_compute

    def _create_uid_view(self) -> TopDownView:
        """
        Build the offscreen view the ray sensors read the entity uids from.

        This is the seam between the two layers. `Playground` is part of the
        presentation, so it is allowed to know about `TopDownView`; `RayCompute`
        is part of the model and only receives the `UidProvider` contract. The
        alternative -- having `RayCompute` build its own view -- is what let a
        window resize corrupt the physics.
        """
        assert self._size
        return TopDownView(
            self,
            self._size,
            self._center,
            zoom=1,
            use_color_uid=True,
            draw_interactive=False,
            draw_transparent=False,
            draw_zone=False,
        )

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
    def noise_rng(self) -> np.random.Generator:
        """
        Returns the generator the sensor noise comes from.

        Seeded from the playground seed (offset, so it does not overlap the
        UID stream); unseeded when the playground is. Sensors that want their
        noise to replay with the run should use this generator instead of the
        global numpy RNG.

        Returns:
            np.random.Generator: The noise generator.
        """
        return self._noise_rng

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

    def get_entity_from_uid(self, uid: int) -> Entity:
        """
        Retrieve an entity from its unique identifier.

        Args:
            uid (int): The unique identifier.

        Returns:
            Entity: The entity.
        """
        entity = self._registry.get_entity_from_uid(uid)
        assert entity is not None, f"No entity for uid {uid}"
        return entity

    @property
    def agents(self) -> List[Agent]:
        """
        Returns the list of agents currently in the playground.

        Returns:
            List[Agent]: The agents.
        """
        return self._registry.agents

    @property
    def elements(self) -> List[Entity]:
        """
        Returns the list of scene elements currently in the playground.

        Returns:
            List[Entity]: The elements.
        """
        return self._registry.elements

    @property
    def _elements(self) -> List[Entity]:
        """
        Every element ever added, including the ones flagged as removed.

        This is the *raw* list, not `elements`. The difference matters: a
        non-definitive `remove()` leaves the entity in here so that a sensor
        reading taken during the step can still be resolved, while `elements`
        already hides it. Both views are needed.

        Returns:
            List[Entity]: The registered elements, removed ones included.
        """
        return self._registry._elements

    @property
    def _uids_to_entities(self) -> Dict[int, Entity]:
        """
        The uid lookup table, kept as a property for the existing callers.

        A non-definitive removal keeps its uid here on purpose, for the same
        reason it keeps the element.

        Returns:
            Dict[int, Entity]: uid -> entity.
        """
        return self._registry.uids_to_entities

    def _agents_with_removals(self) -> List[Agent]:
        """
        The agents, *including* the ones flagged as removed.

        `step()` needs this: an agent removed mid-step still has to be told the
        step ended, or its last action is never applied.

        Returns:
            List[Agent]: Every agent ever added and not definitively removed.
        """
        return self._registry._agents

    @property
    def _background_uid(self) -> int:
        """
        The uid the background color encodes to.

        An entity must never receive it: the uid image is cleared with the
        background color, so such an entity would be invisible to every
        sensor while still having a valid uid.

        Returns:
            int: The background uid.
        """
        return (
            self._background[0]
            + self._background[1] * 256
            + self._background[2] * 256 * 256
        )

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
        Updates the Playground.
        Time moves by one unit of time.

        Args:
            all_commands (Optional[AllCommandsDict]): All commands for agents.
            all_messages (Optional[AllSentMessagesDict]): All messages for communicators.
            pymunk_steps (int): Number of steps for the pymunk physics engine to run.

        Returns:
            tuple: (messages, rewards)

        Notes:
            The loop itself lives in `SimulationStepper`, which also documents
            the order of the phases. This method stays as the entry point every
            caller already uses.

            pymunk_steps only influences the micro-steps that
            the physical engine is taking to render
            the movement of objects and collisions.
            From an external point of view,
            one unit of time passes independent on the number
            of pymunk_steps.
        """
        return self._stepper.step(
            all_commands=all_commands,
            all_messages=all_messages,
            pymunk_steps=pymunk_steps,
        )

    def reset(self):
        """
        Reset the Playground to its initial state.
        """
        # Reset elements that are still in the playground.
        #
        # The raw list, not `elements`: an element flagged as removed but not
        # definitively removed is exactly the case below that has to be put
        # back, and `elements` hides those.
        for element in list(self._elements):

            if isinstance(element, Entity) and element.temporary:
                self.remove(element, definitive=True)
            elif isinstance(element, Entity) and element.removed:
                self.add(element, from_removed=True)
            elif _needs_repositioning(element):
                assert isinstance(element, EmbodiedEntity)
                assert element.initial_coordinates
                element.move_to(
                    element.initial_coordinates,
                    element.allow_overlapping,
                )

            element.reset()

        for agent in self._agents_with_removals():
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

        # Sensors must report the restored world, not the pre-reset one.
        self._stepper._compute_observations()


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
            assert isinstance(entity, EmbodiedEntity)
            initial_coordinates = entity.initial_coordinates
            allow_overlapping = entity.allow_overlapping

        self._add_to_space(entity, initial_coordinates, allow_overlapping)

        if not from_removed:
            self._add_to_mappings(entity)

        self._add_to_views(entity)

        if isinstance(entity, Agent):
            if self._seed is not None:
                self._wire_sensor_noise(entity)
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

    def _wire_sensor_noise(self, agent: Agent) -> None:
        """
        Hand the playground's noise generator to every sensor of the agent.

        The sensors are built in the drone's constructor, before the drone
        knows which playground it lands in, so the generator cannot be passed
        there; wiring them here, when the playground claims the agent, is the
        first moment both sides exist. A seeded playground gives a generator
        derived from its seed (offset from the UID stream), so the noisy
        readings replay with the run; an unseeded one leaves each sensor on
        the global numpy RNG, the historical behavior.

        Args:
            agent (Agent): The agent whose sensors are to be wired.
        """
        for sensor in agent.sensors:
            sensor.set_noise_rng(self._noise_rng)

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

        self._registry.mark_changed(entity)

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
        Record the entity in the registry, and give it a uid and a name.

        Args:
            entity: The entity to map.
        """
        self._registry.register(entity, self._rng, self._background_uid)

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
        if isinstance(entity, Grasper) and not entity.removed:
            entity.release_all_persons()

        if isinstance(entity, RaySensor) and self._ray_compute:
            self._ray_compute.remove(entity)

        if isinstance(entity, Agent):
            self.remove(entity.base, definitive)

        if isinstance(entity, DronePart):
            for device in entity.devices:
                self.remove(device, definitive)

        elif isinstance(entity, PhysicalElement):

            for interactive in entity.interactives:
                self.remove(interactive, definitive)

            for grasper in list(entity.grasped_by):
                grasper.release_one_person(entity)

        if not entity.removed:
            self._remove_from_space(entity)
            self._remove_from_views(entity)

        if definitive:
            self._remove_from_mappings(entity)

        entity.removed = True

        self._registry.mark_changed(entity)

    def _remove_from_space(self, entity):
        """
        Remove the entity from the pymunk space.

        Shapes that the space does not hold are skipped: pymunk asserts on them,
        and an entity can legitimately be out of the space already --
        `make_passable` takes a wreck out without removing it, and `cleanup`
        walks it again afterward.

        Args:
            entity: The entity to remove.
        """
        if isinstance(entity, Agent):
            return

        # pymunk keeps a shape and its body in two separate sets, so each kind
        # has to be looked up in its own set: a shape left in `space.shapes` is
        # asserted on, and so is a body. An entity can legitimately be half out
        # already -- `make_passable` takes a wreck out of the space without
        # removing it, and `cleanup` walks it again afterward.
        present = []
        for element in entity.pm_elements:
            known = (self._space.shapes if isinstance(element, pymunk.Shape)
                     else self._space.bodies)
            if element in known:
                present.append(element)

        if present:
            self._space.remove(*present)

    def make_passable(self, entity) -> None:
        """
        Take an entity out of the physical space without removing it.

        The entity keeps its sprites, so it is still drawn, and it keeps its uid,
        so `hide_from_sensors` decides separately whether the sensors still see
        it. This is what a drone out of health becomes: a wreck on the map that
        nobody collides with any more.

        Args:
            entity (Entity): The entity to take out of the space.
        """
        if isinstance(entity, Agent):
            entity = entity.base

        if isinstance(entity, DronePart):
            for device in entity.devices:
                self._remove_from_space(device)
            self._remove_from_space(entity)
            return

        self._remove_from_space(entity)

    def hide_from_sensors(self, entity) -> None:
        """
        Take an entity out of the uid image, and nothing else.

        The ray sensors read the uid image and nothing else, so dropping the
        sprite from that one view is exactly what makes an entity invisible to
        them, while it stays drawn on the map.

        Args:
            entity (Entity): The entity to hide from the sensors.
        """
        uid_view = self.uid_view
        if uid_view is None:
            return

        if isinstance(entity, Agent):
            entity = entity.base

        if entity in uid_view.sprites:
            uid_view.remove_as_sprite(entity)

    def restore_collision_and_sensors(self, entity) -> None:
        """
        Undo `make_passable` and `hide_from_sensors`, as `reset` does.

        Args:
            entity (Entity): The entity to put back in the world.
        """
        if isinstance(entity, Agent):
            entity = entity.base

        if not entity.removed:
            # pymunk tracks shapes and bodies in two separate sets and asserts on
            # anything it already holds, so an entity that is only half out of the
            # space -- which is what `make_passable` leaves behind -- is put back
            # one element at a time. Adding only what is missing also leaves a
            # drone that never died untouched.
            missing = []
            for element in entity.pm_elements:
                known = (self._space.shapes if isinstance(element, pymunk.Shape)
                         else self._space.bodies)
                if element not in known:
                    missing.append(element)

            if missing:
                self._space.add(*missing)

        uid_view = self.uid_view
        if uid_view is not None and entity not in uid_view.sprites:
            uid_view.add_as_sprite(entity)

    @property
    def uid_view(self):
        """
        The view the ray sensors read, or None when there is no ray sensor.

        A dedicated accessor because the uid view must never be confused with a
        display one: its colors *are* the entity identifiers, so a sprite
        swapped there invents a uid that belongs to nothing.
        """
        if self._ray_compute is None:
            return None
        return self._ray_compute.uid_provider

    def _remove_from_mappings(self, entity):
        """
        Forget the entity for good.

        Args:
            entity: The entity to forget.
        """
        self._registry.unregister(entity)

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
        self._views.append(view)

        for entity in self.elements:
            view.add_as_sprite(entity)

            if isinstance(entity, PhysicalElement):
                for interactive in entity.interactives:
                    view.add_as_sprite(interactive)

        for agent in self.agents:
            view.add_as_sprite(agent.base)

            for device in agent.base.devices:
                view.add_as_sprite(device)

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
            # An agent is a single physical part (its base) since the drone
            # model was simplified: see `Agent.base`.
            if not self.within_playground(entity.base):
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

        if isinstance(entity, DronePart) and entity.agent is not None:
            # Ignore the shapes of the agent the part belongs to: an agent is a
            # single physical part (its base) since the drone model was
            # simplified, so its shapes are the base's.
            agent_shapes = list(entity.agent.base.pm_shapes)

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
        entity = self._registry.get_entity_from_shape(shape)
        assert entity is not None, (
            "This pymunk shape belongs to no entity the playground knows. "
            "That happens when the entity was removed while the collision was "
            "still queued."
        )
        assert isinstance(entity, EmbodiedEntity), (
            f"Shape of {entity!r} has no physical body."
        )

        return entity

    def _handle_interactions(self) -> None:
        """
        Set up collision interactions for the playground.

        Subclasses must implement this. It is called from __init__, and an
        empty implementation is silent: the playground then has no collision
        handler at all, so the drones pass through the walls, nothing can be
        grasped and nobody can be rescued, with no error to point at the
        cause. Failing loudly here turns that into an obvious mistake.

        Raises:
            NotImplementedError: Always, unless overridden.
        """
        raise NotImplementedError(
            f"{type(self).__name__} must implement _handle_interactions() "
            f"to register its collision handlers. See ClosedPlayground for "
            f"an example."
        )

    def cleanup(self):
        """
        Clean up resources and prepare for garbage collection.
        Should be called when the playground is no longer needed.

        Note: This method cleans internal data structures and frees resources
        but does NOT close the GUI window. Close the window explicitly by
        calling `close_window()` when desired. This avoids closing a global
        window used by other tests or components.
        """
        # Drop the RayCompute object (and its sensor list) before removing
        # entities, so that Playground.remove() does not attempt to touch
        # GPU buffers via ray_compute.remove() during cleanup. This matters
        # in particular when cleanup() is called after the GUI window (and
        # its GL context) has already been closed.
        self._ray_compute = None

        # Clear all entities
        for agent in self._agents_with_removals().copy():
            self.remove(agent, definitive=True)

        for element in self._registry._elements.copy():
            self.remove(element, definitive=True)

        # The lists, the caches and the lookup tables all at once.
        self._registry.clear()

        # Clear views
        self._views.clear()

        # Note: Do NOT close the window here. Call close_window() explicitly when needed.

    def close_window(self) -> None:
        """
        Close the GUI window associated with this playground, if any.

        This is separated from `cleanup()` so tests and other callers can
        clean internal resources without closing a shared/global window.

        A window that was *passed in* at construction is not closed here: the
        playground never created it, so it is not the playground's to close. The
        caller that supplied it stays responsible for it.
        """
        if hasattr(self, '_window') and self._window:
            if not self._owns_window:
                return

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
