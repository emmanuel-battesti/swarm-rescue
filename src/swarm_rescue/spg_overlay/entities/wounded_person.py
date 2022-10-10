from spg.utils.definitions import CollisionTypes
from spg.entity import Graspable
from spg.element import PhysicalElement, RewardElement

from resources import path_resources


class WoundedPerson(PhysicalElement, RewardElement):
    """
    WoundedPerson are used with a RescueCenter to get rewards.
    A WoundedPerson disappears when in contact with its RescueCenter.
    """

    def __init__(self, rescue_center):
        super().__init__(
            mass=5,
            filename=path_resources + "/character_v2.png",
            shape_approximation="circle",
            radius=12,
        )

        grasp_halo = Graspable(anchor=self)
        self.add(grasp_halo)

        self.rescue_center = rescue_center
        self.graspable = True

    def _set_pm_collision_type(self):
        for pm_shape in self._pm_shapes:
            pm_shape.collision_type = CollisionTypes.GEM

    @property
    def _base_reward(self) -> float:
        return 1
