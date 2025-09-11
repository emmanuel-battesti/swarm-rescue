import arcade
import numpy as np
import pymunk
from PIL import Image
from skimage.draw import disk, polygon


def get_texture_from_shape(pm_shape, color, name_texture) -> arcade.Texture:
    """
    Generate an arcade.Texture from a pymunk shape and color.

    Args:
        pm_shape: The pymunk shape (Segment, Circle, or Poly).
        color: The RGB color tuple.
        name_texture: Name for the texture.

    Returns:
        arcade.Texture: The generated texture.
    """
    color_rgba = list(color) + [255]

    if isinstance(pm_shape, pymunk.Segment):
        radius = int(pm_shape.radius)
        length = int((pm_shape.a - pm_shape.b).length)
        img = np.zeros((radius, length, 4))
        img[:, :] = color_rgba

    elif isinstance(pm_shape, pymunk.Circle):
        radius = int(pm_shape.radius)

        img = np.zeros((2 * radius + 1, 2 * radius + 1, 4))
        rr, cc = disk((radius, radius), radius)
        img[rr, cc] = color_rgba

    elif isinstance(pm_shape, pymunk.Poly):
        vertices = pm_shape.get_vertices()

        top = max(vert[0] for vert in vertices)
        bottom = min(vert[0] for vert in vertices)
        left = min(vert[1] for vert in vertices)
        right = max(vert[1] for vert in vertices)

        w = int(right - left)
        h = int(top - bottom)

        center = int(h / 2), int(w / 2)

        img = np.zeros((h, w, 4))
        r = [y + center[0] for x, y in vertices]
        c = [x + center[1] for x, y in vertices]

        rr, cc = polygon(r, c, (h, w))

        img[rr, cc] = color_rgba

    else:
        raise ValueError

    PIL_image = Image.fromarray(np.uint8(img)).convert("RGBA")

    texture = arcade.Texture(
        name=name_texture,
        image=PIL_image,
        hit_box_algorithm="Detailed",
        hit_box_detail=1,
    )

    return texture