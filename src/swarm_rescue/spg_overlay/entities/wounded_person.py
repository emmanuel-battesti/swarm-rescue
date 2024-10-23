import math
import numpy as np
import pymunk

from spg.agent.controller import CenteredContinuousController
from spg.utils.definitions import CollisionTypes
from spg.entity import Graspable
from spg.element import PhysicalElement, RewardElement
from spg.utils.definitions import LINEAR_FORCE

from resources import path_resources
from spg_overlay.utils.constants import LINEAR_SPEED_RATIO_WOUNDED

from spg_overlay.utils.pose import Pose
from spg_overlay.utils.path import Path
from spg_overlay.utils.utils import clamp
from spg_overlay.utils.utils import normalize_angle


class WoundedPerson(PhysicalElement, RewardElement):
    """
    The WoundedPerson class represents a wounded person in a simulation. It
     inherits from the PhysicalElement and RewardElement classes. This class is
     used in conjunction with a RescueCenter to receive rewards. When a
     WoundedPerson comes into contact with its associated RescueCenter, it
     disappears.

    Example Usage
        rescue_center = RescueCenter()
        wounded_person = WoundedPerson(rescue_center)
        In this example, a RescueCenter object is created and then a
        WoundedPerson object is instantiated, passing the rescue_center object
        as an argument. This creates a connection between the WoundedPerson and
        the RescueCenter.
        The WoundedPerson can now receive rewards when it comes into contact
        with the RescueCenter.
    """

    def __init__(self,
                 rescue_center,
                 linear_ratio: float = LINEAR_SPEED_RATIO_WOUNDED,
                 **kwargs,
                 ):
        super().__init__(
            mass=100,
            filename=path_resources + "/character_v2.png",
            shape_approximation="circle",
            radius=12,
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

        grasp_halo = Graspable(anchor=self)
        self.add(grasp_halo)

        self.rescue_center = rescue_center
        self.graspable = True

        self.forward_controller = CenteredContinuousController(name="forward")
        self.add(self.forward_controller)

        self.lateral_controller = CenteredContinuousController(name="lateral")
        self.add(self.lateral_controller)

        self.linear_ratio = LINEAR_FORCE * linear_ratio

        self.path = Path()
        self.reverse = False
        self.goal_index = 0

        self.pose = Pose(np.asarray(self.true_position()), self.true_angle())

    def _set_pm_collision_type(self):
        for pm_shape in self._pm_shapes:
            pm_shape.collision_type = CollisionTypes.GEM

    @property
    def _base_reward(self) -> float:
        return 1

    def set_path(self, path: Path):
        self.path = path

    def clear_path(self):
        self.path = Path()

    def add_pose_to_path(self, pose: Pose):
        self.path.append(pose)

    def pre_step(self):
        super().pre_step()
        self.pose = Pose(np.asarray(self.true_position()), self.true_angle())
        self.compute_movement()

    def compute_movement(self):
        cmd_forward, cmd_lateral = self.follow_path()

        cmd_forward = max(min(cmd_forward, 1.0), -1.0)
        cmd_lateral = max(min(cmd_lateral, 1.0), -1.0)

        sqr_norm = cmd_forward ** 2 + cmd_lateral ** 2
        if sqr_norm > 1.0:
            norm = math.sqrt(sqr_norm)
            cmd_forward = cmd_forward / norm
            cmd_lateral = cmd_lateral / norm

        self._pm_body.apply_force_at_world_point(
            force=pymunk.Vec2d(cmd_forward, cmd_lateral) * self.linear_ratio,
            point=tuple(self.true_position())
        )

        self._pm_body.angular_velocity = -0.02*(self.true_angle())


    def follow_path(self):
        """
        The WoundedPerson goes from his position to the end of the path (reverse= False) or to the beginning of
        the path (reverse = True).
        The next point to be reached is found by traversing the path from the end to the beginning.
        """
        if self.path.length() == 0:
            return 0, 0

        RADIUS_ARRIVED = 10.0

        goal_pose = self.path.get(index=self.goal_index)
        vector_to_goal = goal_pose.position - self.pose.position
        dist_to_goal = math.sqrt(vector_to_goal[0] ** 2 + vector_to_goal[1] ** 2)

        if dist_to_goal < RADIUS_ARRIVED:
            # if we arrived at the goal, we need a new goal. The new goal is the next one (in reverse or not) and only
            # if it is stay inside.
            if self.path.length() == 1:
                return 0, 0
            elif (not self.reverse) and self.goal_index < (self.path.length() - 1):
                self.goal_index += 1
            elif (not self.reverse) and self.goal_index == (self.path.length() - 1):
                self.goal_index -= 1
                self.reverse = True
            elif self.reverse and self.goal_index > 0:
                self.goal_index -= 1
            elif self.reverse and self.goal_index == 0:
                self.goal_index += 1
                self.reverse = False

        abs_goal_direction = np.arctan2(vector_to_goal[1], vector_to_goal[0])

        intensity = 0.5
        long_force = np.cos(abs_goal_direction)
        lat_force = np.sin(abs_goal_direction)
        if dist_to_goal < 10:
            force_intensity = intensity * math.atan(dist_to_goal / 10) * 2 / np.pi
        else:
            force_intensity = intensity / max(abs(long_force), abs(lat_force))
        long_force *= force_intensity
        lat_force *= force_intensity

        long_force = clamp(long_force, -1.0, 1.0)
        lat_force = clamp(lat_force, -1.0, 1.0)

        return long_force, lat_force

    def true_position(self) -> np.ndarray:
        """
        Give the true position of the woundedPerson, in pixels
        You must NOT use this value for your calculation in the control() function. But you can use it for
        debugging or logging.
        """
        return np.array(self._pm_body.position)

    def true_angle(self) -> float:
        """
        Give the true orientation of the woundedPerson, in radians between -Pi and Pi.
        You must NOT use this value for your calculation in the control() function. But you can use it for
        debugging or logging.
        """
        return normalize_angle(self._pm_body.angle)
