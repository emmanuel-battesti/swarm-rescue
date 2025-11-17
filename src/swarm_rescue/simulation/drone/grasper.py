from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Optional

import pymunk

from swarm_rescue.simulation.drone.controller import GrasperController
from swarm_rescue.simulation.drone.device import Device
from swarm_rescue.simulation.elements.wounded_person import WoundedPerson
from swarm_rescue.simulation.utils.definitions import CollisionTypes

if TYPE_CHECKING:
    from swarm_rescue.simulation.drone.drone_part import DronePart


class Grasper(Device):
    """
    Device for grasping wounded persons in the simulation.
    """

    def __init__(
            self, anchor: DronePart, max_grasped: Optional[int] = None, **kwargs
    ):
        """
        Initialize the Grasper.

        Args:
            anchor (DronePart): The drone part to attach the grasper to.
            max_grasped (Optional[int]): Maximum number of wounded persons that can be grasped.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(anchor=anchor, **kwargs)

        self.grasp_controller = GrasperController("grasper")
        self._grasped_wounded_persons: List[WoundedPerson] = []
        self._grasp_joints: Dict[WoundedPerson, List[pymunk.Constraint]] = {}
        self._can_grasp = False
        self._max_grasped = max_grasped

    @property
    def can_grasp(self) -> bool:
        """
        Returns whether the grasper can currently grasp.
        """
        return self._can_grasp

    @property
    def grasped_wounded_persons(self) -> List[WoundedPerson]:
        """
        Returns the list of wounded persons currently grasped.
        """
        return self._grasped_wounded_persons

    def grasps(self, wounded: WoundedPerson) -> None:
        """
        Grasp a wounded person if possible.

        Args:
            wounded (WoundedPerson): The wounded person to grasp.
        """
        assert self._can_grasp

        if wounded not in self._grasped_wounded_persons:

            if self._max_grasped and self._max_grasped <= len(self._grasped_wounded_persons):
                return

            self._grasped_wounded_persons.append(wounded)
            self._add_joints(wounded)
            wounded.grasped_by.append(self)

            for sensor in self._anchor.agent.external_sensors:
                if sensor.invisible_grasped:
                    sensor.add_to_temporary_invisible(wounded)

    @property
    def _collision_type(self):
        """
        Returns the collision type for the grasper.
        """
        return CollisionTypes.GRASPER

    def _add_joints(self, wounded: WoundedPerson) -> None:
        """
        Add physical joints between the grasper and the wounded person.

        Args:
            wounded (WoundedPerson): The wounded person to attach.
        """
        assert self._anchor

        # j_1 = pymunk.PinJoint(self._anchor.pm_body, entity.pm_body, (0, 0), (0, 20))
        # j_2 = pymunk.PinJoint(self._anchor.pm_body, entity.pm_body, (0, 0), (0, -20))
        #
        # j_3 = pymunk.PinJoint(self._anchor.pm_body, entity.pm_body, (0, 20), (0, 0))
        # j_4 = pymunk.PinJoint(self._anchor.pm_body, entity.pm_body, (0, -20), (0, 0))

        # joint_position = (self._anchor.pm_body.position + entity.pm_body.position) * 0.5
        joint_position = 0.3 * self._anchor.pm_body.position + 0.7 * wounded.pm_body.position

        joint = pymunk.PivotJoint(self._anchor.pm_body, wounded.pm_body, tuple(joint_position)) # type: ignore[arg-type]
        joint.collide_bodies = False

        # grasp_joints = [j_1, j_2, j_3, j_4]
        grasp_joints = [joint]
        self._grasp_joints[wounded] = grasp_joints
        self._anchor.playground.space.add(*grasp_joints)

        # draw_options = pymunk.pygame_util.DrawOptions(screen)
        # space.debug_draw(draw_options)

    def _release_grasping(self) -> None:
        """
        Release all currently grasped wounded persons.
        """
        for wounded in list(self._grasped_wounded_persons):
            self.release(wounded)

        self._can_grasp = False

        assert not self._grasped_wounded_persons
        assert not self._grasp_joints

    def release(self, wounded: WoundedPerson) -> None:
        """
        Release a specific wounded person.

        Args:
            wounded (WoundedPerson): The wounded person to release.
        """
        wounded.grasped_by.remove(self)

        # Handle sensors if anchor still exists
        if self._anchor and hasattr(self._anchor, 'agent'):
            for sensor in self._anchor.agent.external_sensors:
                if sensor.invisible_grasped:
                    sensor.remove_from_temporary_invisible(wounded)

        # Remove joints from physics space if anchor and playground still exist
        joints = self._grasp_joints.pop(wounded)
        if self._anchor and hasattr(self._anchor, 'playground') and self._anchor.playground:
            self._anchor.playground.space.remove(*joints)

        self._grasped_wounded_persons.remove(wounded)

    def reset(self) -> None:
        """
        Reset the grasper and release all grasped persons.
        """
        self._release_grasping()
        super().reset()

    def apply_commands(self) -> None:
        """
        Apply the current grasp command.
        """
        command_value = self.grasp_controller.command_value

        if not command_value:
            self._release_grasping()
        else:
            self._can_grasp = True
