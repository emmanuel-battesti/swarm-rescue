import math
import random
from typing import Tuple

import arcade
import numpy as np
import pymunk
from PIL import Image

from swarm_rescue.resources import path_resources
from swarm_rescue.simulation.elements.physical_element import PhysicalElement
from swarm_rescue.simulation.utils.definitions import CollisionTypes


class ColorWall(PhysicalElement):
    """
    The ColorWall class is a subclass of the PhysicalElement class. It
    represents a colored wall or a wall with a texture. The class is used to
    create walls with different colors or textures in the simulation
    environment.

    Example Usage
        # Creating a colored wall
        wall = ColorWall(pos_start=(0, 0), pos_end=(10, 0), width=2, color=(255, 0, 0))

        # Creating a textured wall
        wall = ColorWall(pos_start=(0, 0), pos_end=(10, 0), width=2, file_name="wall_texture.png")
    """

    def __init__(
        self,
        pos_start: Tuple[float, float],
        pos_end: Tuple[float, float],
        wall_thickness: int = 6,
        color: Tuple[int, int, int] = None,
        file_name: str = None,
        **kwargs
    ):
        """
        Initialize a ColorWall.

        Args:
            pos_start (Tuple[float, float]): Start position of the wall.
            pos_end (Tuple[float, float]): End position of the wall.
            wall_thickness (int): Thickness of the wall.
            color (Tuple[int, int, int], optional): Color of the wall.
            file_name (str, optional): Texture file for the wall.
            **kwargs: Additional keyword arguments.
        """
        length = (pymunk.Vec2d(*pos_start) - pos_end).length + wall_thickness

        position = (pymunk.Vec2d(*pos_start) + pos_end) / 2
        angle = (pymunk.Vec2d(*pos_end) - pos_start).angle

        self.wall_coordinates = (position.x, position.y), angle

        if color is not None:
            img = Image.new("RGBA",
                            (int(wall_thickness), int(length)), color)
            texture = arcade.Texture(
                name=f"Wall_{int(position.x)}_{int(position.y)}_{int(math.degrees(angle))}_{length}",
                image=img,
                hit_box_algorithm="Detailed",
                hit_box_detail=1,
            )
        elif file_name is not None:
            w_img = 2000
            h_img = 2000
            x = random.randint(0, int(w_img - length - 1))
            y = random.randint(0, int(h_img - wall_thickness - 1))
            texture = arcade.load_texture(file_name=file_name,
                                          x=x,
                                          y=y,
                                          width=length,
                                          height=wall_thickness)
        else:
            raise ValueError('Either color or file_name must be provided')

        super().__init__(texture=texture, **kwargs)

        # Friction normally goes between 0 (no friction) and 1.0 (high friction)
        # Friction is between two objects in contact. It is important to remember
        # in top-down games that friction moving along the 'floor' is controlled
        # by damping.
        # elasticity: How bouncy this object is. 0 is no bounce.
        # Values of 1.0 and higher may behave badly.
        # See: https://api.arcade.academy/en/2.6.7/examples/pymunk_demo_top_down.html
        for pm_shape in self._pm_shapes:
            pm_shape.elasticity = 0.5  # default value in pymunk is 0
            pm_shape.friction = 0.9  # default value in arcade is 0.2

    @property
    def _collision_type(self):
        """
        Returns the collision type for the wall.
        """
        return CollisionTypes.WALL


class NormalWall(ColorWall):
    """
    The NormalWall class is a subclass of the ColorWall class. It is used by
    the tool 'image_to_map.py' in the directory tools. This class represents
    a normal wall with a specific color and texture.

    Example Usage
        # Creating a normal wall
        wall = NormalWall(pos_start=(0, 0), pos_end=(10, 0))
    """

    def __init__(
        self,
        pos_start: Tuple[float, float],
        pos_end: Tuple[float, float],
        wall_thickness: int = 6,
        **kwargs
    ):
        """
        Initialize a NormalWall.

        Args:
            pos_start (Tuple[float, float]): Start position of the wall.
            pos_end (Tuple[float, float]): End position of the wall.
            wall_thickness (int): Thickness of the wall.
            **kwargs: Additional keyword arguments.
        """
        self.color = (128, 128, 128)

        p_start = np.asarray(pos_start)
        p_end = np.asarray(pos_end)

        v = p_end - p_start
        magnitude_v = math.sqrt(v[0] ** 2 + v[1] ** 2)
        uv = v / magnitude_v

        new_p_start = p_start + wall_thickness / 2 * uv
        new_p_end = p_end - wall_thickness / 2 * uv

        new_pos_start = (float(new_p_start[0]), float(new_p_start[1]))
        new_pos_end = (float(new_p_end[0]), float(new_p_end[1]))

        filename = path_resources + "/stone_texture_g_04.png"

        super().__init__(pos_start=new_pos_start,
                         pos_end=new_pos_end,
                         wall_thickness=wall_thickness,
                         file_name=filename,
                         **kwargs)


class NormalBox(ColorWall):
    """
    The NormalBox class is a subclass of the ColorWall class. It represents a
     custom wall in the shape of a box.
    This class is used by the tool 'image_to_map.py' in the directory tools.

    Example Usage
        # Creating a NormalBox object
        box = NormalBox(up_left_point=(0, 0), width=5, height=3)
    """

    def __init__(
        self,
        up_left_point: Tuple[float, float],
        width: float,
        height: float,
        **kwargs
    ):
        """
        Initialize a NormalBox.

        Args:
            up_left_point (Tuple[float, float]): Upper left point of the box.
            width (float): Width of the box.
            height (float): Height of the box.
            **kwargs: Additional keyword arguments.
        """
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
                         wall_thickness=int(wall_thickness),
                         file_name=filename,
                         **kwargs)
