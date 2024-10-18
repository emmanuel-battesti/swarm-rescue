from enum import IntEnum, auto

from typing import List, Optional, Type, Union, Tuple

from arcade.texture import Texture
from PIL import Image
from PIL import ImageDraw
from spg.agent import Agent

from spg.element import ZoneElement
from spg.playground import Playground, get_colliding_entities
from spg.utils.definitions import CollisionTypes

from spg_overlay.entities.drone_abstract import DroneAbstract
from spg_overlay.entities.drone_base import DroneBase


def return_area_collision(arbiter, _, data):
    playground: Playground = data["playground"]
    (return_area, _), (drone_base, _) = get_colliding_entities(playground, arbiter)

    # print("type part= ", type(part_drone))
    assert isinstance(drone_base, DroneBase)
    assert isinstance(return_area, ReturnArea)

    if isinstance(drone_base, DroneBase):
        return_area.detect_one_drone(drone_base.agent)

    return True


class ReturnArea(ZoneElement):
    """
    The ReturnArea class is a subclass of ZoneElement and represents a zone in a playground where drones starts and
    ends their exploration.
    """

    def __init__(self,
                 size: Optional[Tuple[int, int]] = None,
                 text_to_draw: str = None):

        color = "DeepSkyBlue"
        if text_to_draw is None:
            text_to_draw = "Return Area"
        if size is None:
            size = (0, 0)

        width, height = size

        img = Image.new("RGBA", (int(width), int(height)), color)

        if text_to_draw is not None:
            # Call Draw method to add 2D graphics in an image
            img_draw = ImageDraw.Draw(img)
            # font = ImageFont.truetype('font.ttf', 25)
            # Add text to an image
            img_draw.text((5, 5), text_to_draw, fill="black")

        texture = Texture(
            name=f"Return_area_{width}_{height}_{color}",
            image=img,
            hit_box_algorithm="Simple",
            hit_box_detail=1,
        )

        # On change un peu la hitbox pour que le drone soit complètement dans la zone
        # on fait donc en sorte que la hitbox soit un peu plus petite que le sprite.
        offset = 25
        p1 = (-texture.image.width / 2 + offset, -texture.image.height / 2 + offset)
        p2 = (texture.image.width / 2 - offset, -texture.image.height / 2 + offset)
        p3 = (texture.image.width / 2 - offset, texture.image.height / 2 - offset)
        p4 = (-texture.image.width / 2 + offset, texture.image.height / 2 - offset)

        texture._hit_box_points = p1, p2, p3, p4

        super().__init__(texture=texture)

        self.drone_inside_set = set()

    @property
    def _collision_type(self):
        return CollisionTypes.ACTIVATOR

    def clear(self):
        self.drone_inside_set = set()

    def detect_one_drone(self, drone: DroneAbstract):
        self.drone_inside_set.add(drone)
        drone.is_inside_return_area = True

    def get_nb_drones_inside(self):
        return len(self.drone_inside_set)

    def pre_step(self):
        # print(f"nb_drones_inside = {self.get_nb_drones_inside()}")
        self.clear()
        super().pre_step()

    def compute_total_health_returned(self):
        total_health_returned = 0
        for drone in self.drone_inside_set:
            total_health_returned += drone.drone_health

        return total_health_returned

