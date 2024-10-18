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
    The SrColorWall class is a subclass of the PhysicalElement class. It
    represents a colored wall or a wall with a texture. The class is used to
    create walls with different colors or textures in the simulation
    environment.

    Example Usage
        # Creating a colored wall
        wall = SrColorWall(pos_start=(0, 0), pos_end=(10, 0), width=2, color=(255, 0, 0))

        # Creating a textured wall
        wall = SrColorWall(pos_start=(0, 0), pos_end=(10, 0), width=2, file_name="wall_texture.png")
    """

    def __init__(self,
                 pos_start: Union[Tuple[float, float], pymunk.Vec2d],
                 pos_end: Union[Tuple[float, float], pymunk.Vec2d],
                 wall_thickness: float,
                 color: Tuple[int, int, int] = None,
                 file_name: str = None,
                 **kwargs):
        length = (pymunk.Vec2d(*pos_start) - pos_end).length + wall_thickness

        position = (pymunk.Vec2d(*pos_start) + pos_end) / 2
        angle = (pymunk.Vec2d(*pos_end) - pos_start).angle + math.pi / 2

        self.wall_coordinates = position, angle

        if color is not None:
            img = Image.new("RGBA",
                            (int(wall_thickness), int(length)), color)
            texture = Texture(
                name=f"Barrier_{wall_thickness}_{length}_{color}",
                image=img,
                hit_box_algorithm="Detailed",
                hit_box_detail=1,
            )
        elif file_name is not None:
            w_img = 2000
            h_img = 2000
            x = random.randint(0, int(w_img - wall_thickness - 1))
            y = random.randint(0, int(h_img - length - 1))
            texture = load_texture(file_name=file_name,
                                   x=x,
                                   y=y,
                                   width=wall_thickness,
                                   height=length)
        else:
            raise ValueError('Either color or file_name must be provided')

        super().__init__(texture=texture, **kwargs)

        # Friction normally goes between 0 (no friction) and 1.0 (high friction)
        # Friction is between two objects in contact. It is important to remember
        # in top-down games that friction moving along the 'floor' is controlled
        # by damping.
        # See: https://api.arcade.academy/en/latest/examples/pymunk_demo_top_down.html
        for pm_shape in self._pm_shapes:
            pm_shape.elasticity = 0.5
            pm_shape.friction = 0.9 # default value in arcade is 0.2


class NormalWall(SrColorWall):
    """
    The NormalWall class is a subclass of the SrColorWall class. It is used by
    the tool 'image_to_map.py' in the directory tools. This class represents
    a normal wall with a specific color and texture.

    Example Usage
        # Creating a normal wall
        wall = NormalWall(pos_start=(0, 0), pos_end=(10, 0))
    """

    def __init__(self, pos_start: Union[Tuple[float, float], pymunk.Vec2d],
                 pos_end: Union[Tuple[float, float], pymunk.Vec2d],
                 wall_thickness: int = 6,
                 **kwargs):
        self.color = (200, 240, 230)

        p_start = np.asarray(pos_start)
        p_end = np.asarray(pos_end)

        v = p_end - p_start
        magnitude_v = math.sqrt(v[0] ** 2 + v[1] ** 2)
        uv = v / magnitude_v

        new_pos_start = tuple(p_start + wall_thickness / 2 * uv)
        new_pos_end = tuple(p_end - wall_thickness / 2 * uv)

        filename = path_resources + "/stone_texture_g_04.png"

        super().__init__(pos_start=new_pos_start,
                         pos_end=new_pos_end,
                         wall_thickness=wall_thickness,
                         file_name=filename,
                         **kwargs)


class NormalBox(SrColorWall):
    """
    The NormalBox class is a subclass of the SrColorWall class. It represents a
     custom wall in the shape of a box.
    This class is used by the tool 'image_to_map.py' in the directory tools.

    Example Usage
        # Creating a NormalBox object
        box = NormalBox(up_left_point=(0, 0), width=5, height=3)
    """

    def __init__(self, up_left_point: Union[Tuple[float, float], pymunk.Vec2d],
                 width: float, height: float,
                 **kwargs):
        # self.color = (200, 240, 230)

        if width > height:  # horizontal box
            correction = 0.5 * height
            pos_start = (up_left_point[0] +
                         correction, up_left_point[1] - 0.5 * height)
            pos_end = (up_left_point[0] +
                       width - correction, up_left_point[1] - 0.5 * height)
            wall_thickness = height
        else:  # vertical box
            correction = 0.5 * width
            pos_start = (up_left_point[0] +
                         0.5 * width, up_left_point[1] - correction)
            pos_end = (up_left_point[0] +
                       0.5 * width, up_left_point[1] - height + correction)
            wall_thickness = width

        filename = path_resources + "/stone_texture_g_04.png"

        super().__init__(pos_start=pos_start,
                         pos_end=pos_end,
                         wall_thickness=wall_thickness,
                         file_name=filename,
                         **kwargs)
