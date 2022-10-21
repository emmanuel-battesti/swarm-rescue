from enum import IntEnum

from typing import List, Optional, Type, Union, Tuple

from arcade.texture import Texture
from PIL import Image

from spg.agent.communicator import Communicator
from spg.agent.device import Device
from spg.element import ZoneElement
from spg.playground import Playground, get_colliding_entities
from spg.utils.definitions import CollisionTypes

from spg_overlay.entities.drone_sensors import DroneGPS, DroneCompass


class EnvironmentType(IntEnum):
    EASY = 0
    NO_COM_ZONE = 1
    NO_GPS_ZONE = 2
    KILL_ZONE = 3


def srdisabler_disables_device(arbiter, _, data):
    playground: Playground = data["playground"]
    (disabler, _), (device, _) = get_colliding_entities(playground, arbiter)

    assert isinstance(device, Device)
    assert isinstance(disabler, SRDisabler)

    disabler.disable(device)

    return True


class SRDisabler(ZoneElement):
    def __init__(self,
                 disable_cls: [List[Type[Device]]],
                 size: Optional[Tuple[int, int]] = None,
                 color: Union[str, int, Tuple[int, int, int], Tuple[int, int, int, int]] = 0):
        if size is None:
            size = (0, 0)

        if color == 0:
            color = (0, 0, 0)

        width, height = size

        img = Image.new("RGBA", (int(width), int(height)), color)

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
    def __init__(self, size: Optional[Tuple[int, int]] = None):
        if size is None:
            size = (0, 0)

        super().__init__(disable_cls=[DroneGPS, DroneCompass],
                         size=size,
                         color="grey")


class NoComZone(SRDisabler):
    def __init__(self, size: Optional[Tuple[int, int]] = None):
        if size is None:
            size = (0, 0)

        super().__init__(disable_cls=[Communicator],
                         size=size,
                         color="yellow")


class KillZone(SRDisabler):
    def __init__(self, size: Optional[Tuple[int, int]] = None):
        if size is None:
            size = (0, 0)

        super().__init__(disable_cls=[Device],
                         size=size,
                         color="HotPink")
