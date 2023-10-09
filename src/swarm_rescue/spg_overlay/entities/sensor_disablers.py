from enum import IntEnum, auto

from typing import List, Optional, Type, Union, Tuple

from arcade.texture import Texture
from PIL import Image
from PIL import ImageDraw

from spg.agent.communicator import Communicator
from spg.agent.device import Device
from spg.element import ZoneElement
from spg.playground import Playground, get_colliding_entities
from spg.utils.definitions import CollisionTypes

from spg_overlay.entities.drone_sensors import DroneGPS, DroneCompass


class ZoneType(IntEnum):
    NO_COM_ZONE = auto()
    NO_GPS_ZONE = auto()
    KILL_ZONE = auto()


def srdisabler_disables_device(arbiter, _, data):
    playground: Playground = data["playground"]
    (disabler, _), (device, _) = get_colliding_entities(playground, arbiter)

    assert isinstance(device, Device)
    assert isinstance(disabler, SRDisabler)

    disabler.disable(device)

    return True


class SRDisabler(ZoneElement):
    """
    The SRDisabler class is a subclass of ZoneElement and represents a zone in a playground that disables certain
    devices when they collide with it. It is used to create different types of disabling zones, such as zones that
    disable GPS, communication, or all devices.
    """
    def __init__(self,
                 disable_cls: [List[Type[Device]]],
                 size: Optional[Tuple[int, int]] = None,
                 color: Union[str, int, Tuple[int, int, int], Tuple[int, int, int, int]] = (0, 0, 0),
                 text_to_draw: str = None):
        if size is None:
            size = (0, 0)

        width, height = size

        img = Image.new("RGBA", (int(width), int(height)), color)

        if text_to_draw is not None:
            # Call Draw method to add 2D graphics in an image
            img_draw = ImageDraw.Draw(img)
            # font = ImageFont.truetype('font.ttf', 25)
            # Add text to an image
            img_draw.text((5, 5), text_to_draw, fill=(0, 0, 0))

        texture = Texture(
            name=f"Disabler_{width}_{height}_{color}",
            image=img,
            hit_box_algorithm="Detailed",
            hit_box_detail=1,
        )
        super().__init__(texture=texture)

        self._disable_cls = disable_cls

    @property
    def _collision_type(self):
        return CollisionTypes.DISABLER

    def disable(self, device: Device):
        for disabled_device in self._disable_cls:
            if isinstance(device, disabled_device):
                device.disable()


class NoGpsZone(SRDisabler):
    """
    The NoGpsZone class is a subclass of SRDisabler that represents a zone in a playground where the GPS and compass
    sensors of a drone are disabled when they collide with it.
    """
    def __init__(self, size: Optional[Tuple[int, int]]):
        super().__init__(disable_cls=[DroneGPS, DroneCompass],
                         size=size,
                         color="grey",
                         text_to_draw="No GPS Zone")


class NoComZone(SRDisabler):
    """
    The NoComZone class is a subclass of the SRDisabler class. It represents a zone in a playground that disables the
    Communicator device when it collides with it. This class is used to create a zone that disables communication.
    """
    def __init__(self, size: Optional[Tuple[int, int]]):
        super().__init__(disable_cls=[Communicator],
                         size=size,
                         color="yellow",
                         text_to_draw="No Com Zone")


class KillZone(SRDisabler):
    """
    The KillZone class is a subclass of the SRDisabler class, which represents a zone in a playground that disables
    devices when they collide with it. It is specifically used to create a "kill zone" that disables all devices when
    they collide with it.
    """
    def __init__(self, size: Optional[Tuple[int, int]]):
        super().__init__(disable_cls=[Device],
                         size=size,
                         color="HotPink",
                         text_to_draw="Kill Zone")
