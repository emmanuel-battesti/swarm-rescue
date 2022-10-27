import platform
from typing import Tuple

from spg.playground import Playground

from spg_overlay.entities.normal_wall import NormalWall


class ClosedPlayground(Playground):
    def __init__(self, size: Tuple[int, int]):
        background = (220, 220, 220)
        use_shaders = True
        if platform.system() == "Darwin":
            use_shaders = False

        super().__init__(size=size,
                         seed=None,
                         background=background,
                         use_shaders=use_shaders)

        assert isinstance(self._width, int)
        assert isinstance(self._height, int)

        h = self._height / 2
        w = self._width / 2
        o = 2

        pts = [
            [(-w + o, -h), (-w + o, h), ],
            [(-w, h - o), (w, h - o)],
            [(w - o, h), (w - o, -h)],
            [(w, -h + o), (-w, -h + o), ],
        ]

        for begin_pt, end_pt in pts:
            wall = NormalWall(begin_pt, end_pt)
            self.add(wall, wall.wall_coordinates)
