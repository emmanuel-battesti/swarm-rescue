from enum import IntEnum, auto
from typing import List, Optional, Type, Union, Tuple

import arcade
import pymunk
from PIL import Image
from PIL import ImageDraw

from swarm_rescue.simulation.drone.communicator import Communicator
from swarm_rescue.simulation.drone.device import Device
from swarm_rescue.simulation.drone.drone_sensors import DroneGPS, DroneCompass
from swarm_rescue.simulation.elements.interactive_zone import InteractiveZone
from swarm_rescue.simulation.elements.scene_element import SceneElement
from swarm_rescue.simulation.gui_map.collision_handlers import get_colliding_entities
from swarm_rescue.simulation.gui_map.playground import Playground
from swarm_rescue.simulation.utils.definitions import CollisionTypes


class ZoneType(IntEnum):
    """
    Enumeration of disabling zone types.
    """
    NO_COM_ZONE = auto()
    NO_GPS_ZONE = auto()
    KILL_ZONE = auto()


def disabler_zone_disables_device(arbiter: pymunk.Arbiter, _, data) -> bool:
    """
    Handles the collision between a device and a disabler zone.

    Args:
        arbiter (pymunk.Arbiter): The collision arbiter.
        _ : Unused.
        data: Dictionary containing the playground.

    Returns:
        bool: True to continue processing the collision.
    """
    playground: Playground = data["playground"]
    disabler_zone, device = get_colliding_entities(playground, arbiter)

    assert isinstance(device, Device)
    assert isinstance(disabler_zone, DisablerZone)

    disabler_zone.disable(device)

    # If this is a KillZone, update the drone's visual appearance
    # Check that the device's anchor has an 'agent' attribute (to avoid WoundedPerson)
    if isinstance(disabler_zone, KillZone) and hasattr(device._anchor, 'agent'):
        agent = device._anchor.agent
        if agent is not None:
            from swarm_rescue.simulation.drone.drone_base import DroneBase
            if isinstance(agent.base, DroneBase):
                # Mark that the drone collided with a kill zone this frame
                agent.base._kill_zone_collision_this_frame = True
                # Update the visual state if needed
                agent.base.set_in_kill_zone(True)

    return True


class DisablerZone(InteractiveZone, SceneElement):
    """
    Zone that disables certain devices when they collide with it.
    Used to create disabling zones for GPS, communication, or all devices.
    """

    def __init__(
        self,
        disable_cls: List[Type[Device]],
        size: Optional[Tuple[int, int]] = None,
        color: Union[str, int, Tuple[int, int, int], Tuple[int, int, int, int]] = (0, 0, 0),
        text_to_draw: Optional[str] = None
    ):
        """
        Initialize the DisablerZone.

        Args:
            disable_cls (List[Type[Device]]): List of device classes to disable.
            size (Optional[Tuple[int, int]]): Size of the zone.
            color: Color of the zone.
            text_to_draw (Optional[str]): Text to display on the zone.
        """
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

        texture = arcade.Texture(
            name=f"Disabler_{width}_{height}_{color}",
            image=img,
            hit_box_algorithm="Simple",
            hit_box_detail=1,
        )
        super().__init__(texture=texture)

        self._disable_cls = disable_cls

    @property
    def _collision_type(self) -> int:
        """
        Returns the collision type for the disabler zone.
        """
        return CollisionTypes.DISABLER_ZONE

    def disable(self, device: Device) -> None:
        """
        Disable the device if it matches any of the specified classes.

        Args:
            device (Device): The device to disable.
        """
        for disabled_device in self._disable_cls:
            if isinstance(device, disabled_device):
                device.disable()


class NoGpsZone(DisablerZone):
    """
    Zone that disables GPS and compass sensors of a drone.
    """

    def __init__(self, size: Optional[Tuple[int, int]]):
        """
        Initialize the NoGpsZone.

        Args:
            size (Optional[Tuple[int, int]]): Size of the zone.
        """
        super().__init__(
            disable_cls=[DroneGPS, DroneCompass],
            size=size,
            color="grey",
            text_to_draw="No GPS Zone"
        )


class NoComZone(DisablerZone):
    """
    Zone that disables the Communicator device.
    """

    def __init__(self, size: Optional[Tuple[int, int]]):
        """
        Initialize the NoComZone.

        Args:
            size (Optional[Tuple[int, int]]): Size of the zone.
        """
        super().__init__(
            disable_cls=[Communicator],
            size=size,
            color="yellow",
            text_to_draw="No Com Zone"
        )


class KillZone(DisablerZone):
    """
    Zone that disables all devices when they collide with it ("kill zone").
    """

    def __init__(self, size: Optional[Tuple[int, int]]):
        """
        Initialize the KillZone.

        Args:
            size (Optional[Tuple[int, int]]): Size of the zone.
        """
        super().__init__(
            disable_cls=[Device],
            size=size,
            color="HotPink",
            text_to_draw="Kill Zone"
        )
