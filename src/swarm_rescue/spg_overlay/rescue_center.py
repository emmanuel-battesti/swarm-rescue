from simple_playgrounds.common.definitions import ElementTypes
from simple_playgrounds.element.elements.activable import ActivableByGem
from simple_playgrounds.element.elements.gem import GemElement


class RescueCenter(ActivableByGem):
    """
    When in contact with a wounded_person, provide a reward of 1 to the drone closest to the wounded_person.
    """

    def __init__(self, **kwargs):

        texture = {'texture_type': 'random_tiles',
                   'color_min': [226, 10, 10],
                   'color_max': [255, 32, 41],
                   'size_tiles': 6}

        super().__init__(config_key=ElementTypes.VENDING_MACHINE,
                         reward=1,
                         texture=texture,
                         **kwargs)

        self._quantity_rewards = None
        self._count_rewards = 0

    def activate(self, activating: GemElement, ):
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
