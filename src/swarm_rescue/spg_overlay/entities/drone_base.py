import math

import pymunk
from spg.agent.controller import CenteredContinuousController
from spg.agent.part import PhysicalPart
from spg.utils.definitions import LINEAR_FORCE, ANGULAR_VELOCITY

from resources import path_resources
from spg_overlay.utils.constants import LINEAR_SPEED_RATIO, ANGULAR_SPEED_RATIO


class DroneBase(PhysicalPart):
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
        super().__init__(
            mass=50,
            filename=path_resources + "/drone_v2.png",
            sprite_front_is_up=True,
            shape_approximation="circle",
            # radius=15,
            **kwargs,
        )

        # Friction normally goes between 0 (no friction) and 1.0 (high friction)
        # Friction is between two objects in contact. It is important to remember
        # in top-down games that friction moving along the 'floor' is controlled
        # by damping.
        # See: https://api.arcade.academy/en/latest/examples/pymunk_demo_top_down.html
        for pm_shape in self._pm_shapes:
            pm_shape.elasticity = 0.5
            pm_shape.friction = 0.9 # default value in arcade is 0.2

        self.forward_controller = CenteredContinuousController(name="forward")
        self.add(self.forward_controller)

        self.lateral_controller = CenteredContinuousController(name="lateral")
        self.add(self.lateral_controller)

        self.angular_vel_controller = (
            CenteredContinuousController(name="rotation"))
        self.add(self.angular_vel_controller)

        self.linear_ratio = LINEAR_FORCE * linear_ratio
        self.angular_ratio = ANGULAR_VELOCITY * angular_ratio

        self.inside_return_area = False

    def _apply_commands(self, **kwargs):
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
