from simple_playgrounds.common.definitions import ElementTypes
from simple_playgrounds.element.elements.gem import GemElement


class WoundedPerson(GemElement):
    """
    WoundedPerson are used with a RescueCenter to get rewards.
    A WoundedPerson disappears when in contact with its RescueCenter.
    """

    def __init__(self, rescue_center, **kwargs):
        super().__init__(
            config_key=ElementTypes.COIN,
            elem_activated=rescue_center,
            physical_shape='pentagon',
            texture={'texture_type': 'color', 'color': (250, 130, 30)},
            **kwargs,
        )
