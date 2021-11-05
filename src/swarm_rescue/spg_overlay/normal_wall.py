from typing import Tuple, Union

import pymunk

from simple_playgrounds.element.elements.basic import Wall


class NormalWall(Wall):
    """
    Custom Walls used by the the tool 'image_to_map.py' in the directory tools
    """
    def __init__(self, start_point: Union[Tuple[float, float], pymunk.Vec2d],
                 end_point: Union[Tuple[float, float], pymunk.Vec2d],
                 **kwargs):
        self.wall_depth = 4

        self.texture = {'texture_type': 'random_tiles',
                        'color_min': [200, 240, 230],
                        'color_max': [220, 255, 250],
                        'size_tiles': 4}

        super().__init__(start_point=start_point,
                         end_point=end_point,
                         wall_depth=self.wall_depth,
                         texture=self.texture,
                         **kwargs)


class NormalBox(Wall):
    """
    A kind of custom wall but in the shape of box.
    Used by the the tool 'image_to_map.py' in the directory tools
    """
    def __init__(self, up_left_point: Union[Tuple[float, float], pymunk.Vec2d],
                 width: float, height: float,
                 **kwargs):
        self.wall_depth = 4

        self.texture = {'texture_type': 'random_tiles',
                        'color_min': [200, 240, 230],
                        'color_max': [220, 255, 250],
                        'size_tiles': 4}

        self.wall_depth = width
        start_point = (up_left_point[0] + 0.5 * width, up_left_point[1])
        end_point = (up_left_point[0] + 0.5 * width, up_left_point[1] + height)

        super().__init__(start_point=start_point,
                         end_point=end_point,
                         wall_depth=self.wall_depth,
                         texture=self.texture,
                         **kwargs)
