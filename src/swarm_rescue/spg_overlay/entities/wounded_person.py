from spg.utils.definitions import CollisionTypes
from spg.entity import Graspable
from spg.element import PhysicalElement, RewardElement

from resources import path_resources


class WoundedPerson(PhysicalElement, RewardElement):
    """
    The WoundedPerson class represents a wounded person in a simulation. It inherits from the PhysicalElement and
    RewardElement classes. This class is used in conjunction with a RescueCenter to receive rewards. When a
    WoundedPerson comes into contact with its associated RescueCenter, it disappears.

    Example Usage
        rescue_center = RescueCenter()
        wounded_person = WoundedPerson(rescue_center)
        In this example, a RescueCenter object is created and then a WoundedPerson object is instantiated, passing the
        rescue_center object as an argument. This creates a connection between the WoundedPerson and the RescueCenter.
        The WoundedPerson can now receive rewards when it comes into contact with the RescueCenter.
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
