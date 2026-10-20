import math
from typing import Optional

import arcade
import arcade.hitbox
import pymunk

from swarm_rescue.resources import path_resources
from swarm_rescue.simulation.drone.controller import CenteredContinuousController
from swarm_rescue.simulation.drone.drone_part import DronePart
from swarm_rescue.simulation.utils.constants import (
    ANGULAR_SPEED_RATIO,
    DEATH_ANIMATION_EASE_POWER,
    DEATH_ANIMATION_PEAK_ZOOM,
    DEATH_ANIMATION_STEPS,
    DEATH_ANIMATION_TURN_DEGREES,
    LINEAR_SPEED_RATIO,
)
from swarm_rescue.simulation.utils.definitions import CollisionTypes
from swarm_rescue.simulation.utils.definitions import LINEAR_FORCE, ANGULAR_VELOCITY
from swarm_rescue.simulation.utils.texture_cache import load_texture_cached


class DroneBase(DronePart):
    """
    The DroneBase class represents a drone base in a simulation. It defines the
    behavior and properties of the drone, including its movement and control
     mechanisms.
    """

    def __init__(
            self,
            linear_ratio: float = LINEAR_SPEED_RATIO,
            angular_ratio: float = ANGULAR_SPEED_RATIO,
            **kwargs,
    ):
        """
        Initialize the DroneBase.

        Args:
            linear_ratio (float): Ratio for linear speed.
            angular_ratio (float): Ratio for angular speed.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(
            mass=50,
            filename=path_resources + "/drone_v2.png",
            sprite_front_is_up=True,
            shape_approximation="hull",
            # radius=15,
            **kwargs,
        )

        # Load the dead-drone texture, then apply the flip transformations.
        dead_tex = load_texture_cached(
            path_resources + "/drone_v2_dead.png",
            hit_box_algorithm=arcade.hitbox.algo_simple,
        )
        self._dead_texture = dead_tex.flip_diagonally().flip_horizontally()

        # Store the alive texture for later use
        self._alive_texture = self._base_sprite.texture

        # Track if the drone is currently in a kill zone (visual state)
        self._is_in_kill_zone = False
        # Flag to track if a kill zone collision occurred during the current frame
        self._kill_zone_collision_this_frame = False

        # Step of the death animation in progress, or None while the drone is
        # alive. Compared against DEATH_ANIMATION_STEPS, where the wreck settles.
        self._death_animation_step: Optional[int] = None
        # Opacity the wreck settles on, which is how the cause of death is read
        # on the map: see DEATH_WRECK_ALPHA_HIDDEN and DEATH_WRECK_ALPHA_SOLID.
        self._death_target_alpha = 255
        # The scale to go back to once the explosion is over.
        self._alive_scale = (1.0, 1.0)

        # Friction normally goes between 0 (no friction) and 1.0 (high friction)
        # Friction is between two objects in contact. It is important to remember
        # in top-down games that friction moving along the 'floor' is controlled
        # by damping.
        # See: https://api.arcade.academy/en/latest/examples/pymunk_demo_top_down.html
        for pm_shape in self._pm_shapes:
            pm_shape.elasticity = 0.5
            pm_shape.friction = 0.9  # default value in arcade is 0.2

        self.forward_controller = CenteredContinuousController(name="forward")
        self.add_device(self.forward_controller)

        self.lateral_controller = CenteredContinuousController(name="lateral")
        self.add_device(self.lateral_controller)

        self.angular_vel_controller = (
            CenteredContinuousController(name="rotation"))
        self.add_device(self.angular_vel_controller)

        self.linear_ratio = LINEAR_FORCE * linear_ratio
        self.angular_ratio = ANGULAR_VELOCITY * angular_ratio

        self.inside_return_area = False



    def set_in_kill_zone(self, in_kill_zone: bool) -> None:
        """
        Set whether the drone is in a kill zone and update the sprite accordingly.

        Leaving a kill zone does not bring a destroyed drone back to life. The
        flag follows the zone -- it is cleared, so it stops claiming the drone is
        inside one -- while the picture follows the drone, which stays destroyed.
        """
        # Only update sprites if the state actually changed
        if self._is_in_kill_zone == in_kill_zone:
            return  # State already correct, nothing to do

        self._is_in_kill_zone = in_kill_zone

        agent = self.agent
        if not in_kill_zone and agent is not None and agent.is_dead:
            return

        # Update the base sprite texture
        self._base_sprite.texture = self._dead_texture if in_kill_zone else self._alive_texture

        # print(f"DroneBase UID {self.uid} texture changed to "
        #       f"{'dead' if in_kill_zone else 'alive'}.")

        # Update the sprites in all views
        self._update_sprites_in_views()

    def _update_sprites_in_views(self) -> None:
        """
        Update the drone sprite in all views after texture change.
        This updates the texture directly for visual display.
        """
        if not self._playground or not self._playground._views:
            return

        # Get the uid view if it exists. It must never have its sprite
        # textures swapped: the colors of that view *are* the entity uids.
        uid_view = None
        if self._playground._ray_compute is not None:
            uid_view = self._playground._ray_compute.uid_provider

        for view in self._playground._views:
            if self not in view.sprites:
                continue

            # Skip the uid view entirely - we don't want to change its texture
            # because that would create invalid UIDs when rendering
            if view is uid_view:
                continue

            # Update the texture of the existing sprite directly (only in display views)
            current_sprite = view.sprites[self]
            current_sprite.texture = self._base_sprite.texture

            # Redraw the view to show the new texture
            view.update_and_draw_in_framebuffer(force=True)


    @property
    def in_kill_zone(self) -> bool:
        """
        Returns whether the drone is currently in a kill zone.

        Returns:
            bool: True if in kill zone, False otherwise.
        """
        return self._is_in_kill_zone

    def pre_step(self) -> None:
        """
        Prepare the drone base for a new simulation step.
        """
        super().pre_step()

    def start_death_animation(self, target_alpha: int) -> None:
        """
        Begin the turn that plays when the drone is destroyed.

        The animation is procedural -- the drone spins on itself, slowing down to
        a stop, while fading to `target_alpha` over `DEATH_ANIMATION_STEPS` steps,
        then stays as the dead sprite. No frame assets are involved, which is why
        the wreck is the only picture there was to work from.

        The fade is not decoration: `target_alpha` is what says whether the
        sensors can still see this wreck, and the sprite is faded to it over the
        turn so that the wreck does not change opacity in one jump once it stops.

        Args:
            target_alpha (int): Opacity the wreck settles on, 0 to 255.
        """
        if self._death_animation_step is not None:
            return

        self._death_animation_step = 0
        self._death_target_alpha = target_alpha
        self._alive_scale = self._base_sprite.scale
        self._base_sprite.texture = self._dead_texture
        self._update_sprites_in_views()

    def update_sprite(self, view, sprite) -> None:
        """
        Place the sprite, then run the death animation on it if there is one.

        Args:
            view: The view being updated.
            sprite: This drone's sprite in that view.
        """
        super().update_sprite(view, sprite)

        if self._playground is not None and view is self._playground.uid_view:
            # Scaling or fading a sprite of the uid view would change what the
            # sensors read out of it.
            return

        step = self._death_animation_step
        if step is None:
            # No animation: make sure nothing of a previous one is left on the
            # sprite. A wreck faded to `DEATH_WRECK_ALPHA_HIDDEN` keeps that
            # opacity on the sprite of every view it was drawn in -- those are
            # separate objects from `_base_sprite` -- and only this method ever
            # writes to them, so this is where a restored drone gets its look
            # back. Harmless on a drone that never died: it is already there.
            sprite.scale = self._alive_scale
            sprite.alpha = 255
            return

        if step >= DEATH_ANIMATION_STEPS:
            # The wreck has come to rest: back to the plain dead sprite, at the
            # opacity that says whether the sensors can see it.
            sprite.scale = self._alive_scale
            sprite.alpha = self._death_target_alpha
            return

        progress = step / DEATH_ANIMATION_STEPS

        # Rotation, eased out: the turn is at full speed on the first step and
        # slows down until it stops, instead of running at a constant rate and
        # freezing. `1 - (1 - progress) ** 3` reaches 1.0 exactly at the end, so
        # the wreck comes to rest on the dead sprite rather than next to it.
        sprite.angle += DEATH_ANIMATION_TURN_DEGREES * \
            (1.0 - (1.0 - progress) ** DEATH_ANIMATION_EASE_POWER)

        # A slight swell that is already gone when the rotation ends: the zoom
        # returns to normal by the last step.
        swell = 1.0 + DEATH_ANIMATION_PEAK_ZOOM * (1.0 - progress) ** 2
        sprite.scale = (swell, swell)

        # Fade to the opacity the wreck keeps for the rest of the run, reaching it
        # exactly on the last step. A drone destroyed by damage fades away to show
        # that the sensors no longer see it; one destroyed by a kill zone can still be
        # seen by sensors, so it stays fully opaque.
        sprite.alpha = round(255.0
                             + (self._death_target_alpha - 255.0) * progress)

    @property
    def needs_sprite_update(self) -> bool:
        """
        Whether the sprite has to be refreshed this step.

        While the turn plays it has to be refreshed even though the wreck
        does not move: the animation is the only thing that changes.
        """
        step = self._death_animation_step
        if step is not None and step < DEATH_ANIMATION_STEPS:
            return True
        return super().needs_sprite_update

    def reset_death_animation(self) -> None:
        """
        Cancel the turn and put the alive sprite back on.

        The counterpart of `start_death_animation`, called by the drone's own
        `reset()`: a drone brought back to life must not be drawn as a wreck any
        more, so the opacity it had faded to is undone too.

        That opacity is not on `_base_sprite`, it is on the sprite of each view,
        and only `update_sprite()` writes to those. Which is enough: a drone is
        `movable`, so `PhysicalEntity.needs_sprite_update` is true on every step
        and the next view repaints it. Nothing has to be requested here.
        """
        self._death_animation_step = None
        self._death_target_alpha = 255
        self._alive_scale = (1.0, 1.0)
        self._base_sprite.scale = self._alive_scale
        self._base_sprite.alpha = 255
        self._base_sprite.texture = self._alive_texture
        self._update_sprites_in_views()

    def post_step(self) -> None:
        """
        Finalize the drone base after a simulation step.
        If no collision with kill zone occurred this frame, reset to alive state.
        """
        super().post_step()

        if (self._death_animation_step is not None
                and self._death_animation_step < DEATH_ANIMATION_STEPS):
            self._death_animation_step += 1

        # If no kill zone collision occurred during this step, the drone has left
        # the zone and the flag is cleared. Whether that puts the alive sprite
        # back is `set_in_kill_zone`'s business: a destroyed drone stays drawn
        # destroyed.
        if not self._kill_zone_collision_this_frame:
            self.set_in_kill_zone(False)
        # Reset the collision flag for next frame
        self._kill_zone_collision_this_frame = False

    def _apply_commands(self, **kwargs) -> None:
        """
        Apply the control commands to the drone's physical body.

        Args:
            **kwargs: Additional keyword arguments.
        """
        cmd_forward = self.forward_controller.command_value
        cmd_lateral = self.lateral_controller.command_value

        cmd_forward = max(min(cmd_forward, 1.0), -1.0)
        cmd_lateral = max(min(cmd_lateral, 1.0), -1.0)

        sqr_norm = cmd_forward ** 2 + cmd_lateral ** 2
        if sqr_norm > 1.0:
            norm = math.sqrt(sqr_norm)
            cmd_forward = cmd_forward / norm
            cmd_lateral = cmd_lateral / norm

        self._pm_body.apply_force_at_local_point(
            force=pymunk.Vec2d(cmd_forward, 0) * self.linear_ratio, point=(0, 0)
        )

        self._pm_body.apply_force_at_local_point(
            force=pymunk.Vec2d(0, cmd_lateral) * self.linear_ratio, point=(0, 0)
        )

        cmd_angular = self.angular_vel_controller.command_value
        self._pm_body.angular_velocity = cmd_angular * self.angular_ratio

    @property
    def _collision_type(self):
        """
        Returns the collision type for the drone base.
        """
        return CollisionTypes.DRONE
