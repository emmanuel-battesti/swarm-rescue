from typing import Tuple, Union

import pymunk

from simple_playgrounds.elements.collection.basic import Wall


class NormalWall(Wall):
    def __init__(self, start_point: Union[Tuple[float, float], pymunk.Vec2d],
                 end_point: Union[Tuple[float, float], pymunk.Vec2d],
                 **kwargs):
        self.wall_depth = 4
        self.texture = [140, 140, 100]
        super().__init__(start_point=start_point,
                         end_point=end_point,
                         wall_depth=self.wall_depth,
                         texture=self.texture,
                         **kwargs)
