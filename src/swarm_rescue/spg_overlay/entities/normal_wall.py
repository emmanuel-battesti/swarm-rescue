import random
from typing import Tuple, Union

import math
import numpy as np
import pymunk
from arcade.texture import Texture, load_texture
from PIL import Image

from spg.element import PhysicalElement

from resources import path_resources


class SrColorWall(PhysicalElement):
    """
    The SrColorWall class is a subclass of the PhysicalElement class. It represents a colored wall or a wall with a
    texture. The class is used to create walls with different colors or textures in the simulation environment.

    Example Usage
        # Creating a colored wall
        wall = SrColorWall(pos_start=(0, 0), pos_end=(10, 0), width=2, color=(255, 0, 0))

        # Creating a textured wall
        wall = SrColorWall(pos_start=(0, 0), pos_end=(10, 0), width=2, file_name="wall_texture.png")
    """
    def __init__(self,
                 pos_start: Union[Tuple[float, float], pymunk.Vec2d],
                 pos_end: Union[Tuple[float, float], pymunk.Vec2d],
                 width: float,
                 color: Tuple[int, int, int] = None,
                 file_name: str = None,
                 **kwargs):
        height = (pymunk.Vec2d(*pos_start) - pos_end).length + width

        position = (pymunk.Vec2d(*pos_start) + pos_end) / 2
        angle = (pymunk.Vec2d(*pos_end) - pos_start).angle + math.pi / 2

        self.wall_coordinates = position, angle

        if color is not None:
            img = Image.new("RGBA", (int(width), int(height)), color)
            texture = Texture(
                name=f"Barrier_{width}_{height}_{color}",
                image=img,
                hit_box_algorithm="Detailed",
                hit_box_detail=1,
            )
        elif file_name is not None:
            w_img = 2000
            h_img = 2000
            x = random.randint(0, int(w_img - width - 1))
            y = random.randint(0, int(h_img - height - 1))
            texture = load_texture(file_name=file_name,
                                   x=x,
                                   y=y,
                                   width=width,
                                   height=height)
        else:
            raise ValueError('Either color or file_name must be provided')

        super().__init__(texture=texture, **kwargs)


class NormalWall(SrColorWall):
    """
    The NormalWall class is a subclass of the SrColorWall class. It is used by the tool 'image_to_map.py' in the directory tools. This class represents a normal wall with a specific color and texture.

    Example Usage
        # Creating a normal wall
        wall = NormalWall(pos_start=(0, 0), pos_end=(10, 0))
    """

    def __init__(self, pos_start: Union[Tuple[float, float], pymunk.Vec2d],
                 pos_end: Union[Tuple[float, float], pymunk.Vec2d],
                 **kwargs):
        width_wall = 4

        self.color = (200, 240, 230)

        p_start = np.asarray(pos_start)
        p_end = np.asarray(pos_end)

        v = p_end - p_start
        magnitude_v = math.sqrt(v[0] ** 2 + v[1] ** 2)
        uv = v / magnitude_v

        new_pos_start = tuple(p_start + width_wall / 2 * uv)
        new_pos_end = tuple(p_end - width_wall / 2 * uv)

        filename = path_resources + "/stone_texture_g_04.png"

        super().__init__(pos_start=new_pos_start,
                         pos_end=new_pos_end,
                         width=width_wall,
                         file_name=filename,
                         **kwargs)


class NormalBox(SrColorWall):
    """
    The NormalBox class is a subclass of the SrColorWall class. It represents a custom wall in the shape of a box.
    This class is used by the tool 'image_to_map.py' in the directory tools.

    Example Usage
        # Creating a NormalBox object
        box = NormalBox(up_left_point=(0, 0), width=5, height=3)
    """

    def __init__(self, up_left_point: Union[Tuple[float, float], pymunk.Vec2d], width: float, height: float,
                 **kwargs):
        # self.color = (200, 240, 230)

        if width > height:  # horizontal box
            correction = 0.5 * height
            pos_start = (up_left_point[0] + correction, up_left_point[1] - 0.5 * height)
            pos_end = (up_left_point[0] + width - correction, up_left_point[1] - 0.5 * height)
            width_wall = height
        else:  # vertical box
            correction = 0.5 * width
            pos_start = (up_left_point[0] + 0.5 * width, up_left_point[1] - correction)
            pos_end = (up_left_point[0] + 0.5 * width, up_left_point[1] - height + correction)
            width_wall = width

        filename = path_resources + "/stone_texture_g_04.png"

        super().__init__(pos_start=pos_start,
                         pos_end=pos_end,
                         width=width_wall,
                         file_name=filename,
                         **kwargs)
