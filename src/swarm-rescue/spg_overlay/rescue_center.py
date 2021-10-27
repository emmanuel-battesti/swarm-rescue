from typing import Optional

from simple_playgrounds.common.definitions import ElementTypes
from simple_playgrounds.elements.collection.activable import ActivableByGem
from simple_playgrounds.elements.collection.gem import GemElement


class RescueCenter(ActivableByGem):
    """
    When in contact with a wounded_person, provide a reward to the drone closest to the wounded_person.
    """
    def __init__(
        self,
        reward: float,
        quantity_rewards: Optional[int] = None,
        **kwargs,
    ):
        """ rescue center Entity.
        Default: Orange square of size 20, provides a reward of 10.
        """

        super().__init__(ElementTypes.VENDING_MACHINE, reward=reward, **kwargs)
        self._quantity_rewards = quantity_rewards
        self._count_rewards = 0

    def activate(
        self,
        activating: GemElement,
    ):
        list_remove = None

        if activating.elem_activated:
            list_remove = [activating]

        return list_remove, None

    @property
    def reward(self):
        rew = super().reward

        if self._quantity_rewards and self._count_rewards >= self._quantity_rewards:
            return 0

        self._count_rewards += 1
        return rew

    @reward.setter
    def reward(self, rew: float):
        self._reward = rew

    def reset(self):
        super().reset()
        self._count_rewards = 0
