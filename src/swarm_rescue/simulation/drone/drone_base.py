import math

import arcade
import pymunk

from swarm_rescue.resources import path_resources
from swarm_rescue.simulation.drone.controller import CenteredContinuousController
from swarm_rescue.simulation.drone.drone_part import DronePart
from swarm_rescue.simulation.utils.constants import LINEAR_SPEED_RATIO, ANGULAR_SPEED_RATIO
from swarm_rescue.simulation.utils.definitions import CollisionTypes
from swarm_rescue.simulation.utils.definitions import LINEAR_FORCE, ANGULAR_VELOCITY


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

        # Load the dead drone texture
        self._dead_texture = arcade.load_texture(
            path_resources + "/drone_v2_dead.png",
            hit_box_algorithm="Simple",
            hit_box_detail=1,
            flipped_diagonally=True,
            flipped_horizontally=True,
        )

        # Store the alive texture for later use
        self._alive_texture = self._base_sprite.texture

        # Track if the drone is currently in a kill zone (visual state)
        self._is_in_kill_zone = False
        # Flag to track if a kill zone collision occurred during the current frame
        self._kill_zone_collision_this_frame = False

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

        Args:
            in_kill_zone (bool): True if the drone is in a kill zone, False otherwise.
        """
        # Only update sprites if the state actually changed
        if self._is_in_kill_zone == in_kill_zone:
            return  # State already correct, nothing to do

        self._is_in_kill_zone = in_kill_zone

        # Update the base sprite texture
        self._base_sprite.texture = self._dead_texture if in_kill_zone else self._alive_texture

        #print(f"DroneBase UID {self.uid} texture changed to {'dead' if in_kill_zone else 'alive'}.")

        # Update the sprites in all views
        self._update_sprites_in_views()

    def _update_sprites_in_views(self) -> None:
        """
        Update the drone sprite in all views after texture change.
        This updates the texture directly.
        """
        if not self._playground or not self._playground._views:
            return

        for view in self._playground._views:
            if self not in view.sprites:
                continue

            # Update the texture of the existing sprite directly
            current_sprite = view.sprites[self]
            current_sprite.texture = self._base_sprite.texture

            # Force a redraw of the sprite to reflect the texture change
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

    def post_step(self) -> None:
        """
        Finalize the drone base after a simulation step.
        If no collision with kill zone occurred this frame, reset to alive state.
        """
        super().post_step()
        # If no kill zone collision occurred during this step, ensure we're in alive state
        # This is checked at the END of the step, after all collisions have been processed
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
