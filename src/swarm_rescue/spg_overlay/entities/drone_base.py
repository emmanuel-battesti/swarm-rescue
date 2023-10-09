import pymunk
from spg.agent.controller import CenteredContinuousController
from spg.agent.part import PhysicalPart
from spg.utils.definitions import LINEAR_FORCE, ANGULAR_VELOCITY

from resources import path_resources
from spg_overlay.utils.constants import LINEAR_SPEED_RATIO, ANGULAR_SPEED_RATIO


class DroneBase(PhysicalPart):
    """
    The DroneBase class represents a drone base in a simulation. It defines the behavior and properties of the drone,
    including its movement and control mechanisms.
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

        self.forward_controller = CenteredContinuousController(name="forward")
        self.add(self.forward_controller)

        self.lateral_controller = CenteredContinuousController(name="lateral")
        self.add(self.lateral_controller)

        self.angular_vel_controller = CenteredContinuousController(name="rotation")
        self.add(self.angular_vel_controller)

        self.linear_ratio = LINEAR_FORCE * linear_ratio
        self.angular_ratio = ANGULAR_VELOCITY * angular_ratio

    def _apply_commands(self, **kwargs):
        command_value = self.forward_controller.command_value
        self._pm_body.apply_force_at_local_point(
            pymunk.Vec2d(command_value, 0) * self.linear_ratio, (0, 0)
        )

        command_value = self.lateral_controller.command_value
        self._pm_body.apply_force_at_local_point(
            pymunk.Vec2d(0, command_value) * self.linear_ratio, (0, 0)
        )

        command_value = self.angular_vel_controller.command_value
        self._pm_body.angular_velocity = command_value * self.angular_ratio
