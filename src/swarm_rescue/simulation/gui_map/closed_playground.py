from typing import Tuple, Optional

from swarm_rescue.simulation.drone.drone_abstract import (drone_collision_wall,
                                                          drone_collision_drone)
from swarm_rescue.simulation.elements.normal_wall import NormalWall
from swarm_rescue.simulation.elements.rescue_center import wounded_rescue_center_collision
from swarm_rescue.simulation.elements.return_area import return_area_collision
from swarm_rescue.simulation.elements.sensor_disablers import disabler_zone_disables_device
from swarm_rescue.simulation.collision_handlers import grasper_grasps_wounded
from swarm_rescue.simulation.gui_map.playground import Playground
from swarm_rescue.simulation.utils.definitions import CollisionTypes


class ClosedPlayground(Playground):
    """
    The ClosedPlayground class is a subclass of the Playground class. It
    represents a closed playground with walls surrounding it. The class
    initializes the playground with a specified size and sets the background
    color. It also determines whether to use shaders based on the platform.
    The class defines the shape of the walls and adds them to the playground.

    Example Usage
        playground = ClosedPlayground((800, 600))

        In this example, a ClosedPlayground object is created with a size of
        800x600 pixels. The playground will have walls surrounding it and a
        default background color. The playground can then be used for various
        purposes, such as simulating physics or rendering graphics.

    Fields
        _width: The width of the playground.
        _height: The height of the playground.
    """

    def __init__(self,
                 size: Tuple[int, int],
                 border_thickness: int = 6,
                 use_shaders: Optional[bool] = None,
                 seed: Optional[int] = None,
                 window=None):
        """
        Initialize the ClosedPlayground.

        Args:
            size (Tuple[int, int]): Size of the playground (width, height).
            border_thickness (int): Thickness of the border walls.
            use_shaders (Optional[bool]): Whether to use shaders for rendering.
                If None, auto-detected by Playground (see ShaderConfig).
            seed (Optional[int]): Seed for the random number generator, used to
                assign entity UIDs. UIDs identify the entities hit by the
                sensors, so seeding them is what makes a round replayable.
            window: An existing window to draw in. None (the default) creates
                an invisible one that this playground closes itself; passing
                one in keeps it alive for the caller to close.
        """
        background = (220, 220, 220)


        super().__init__(size=size,
                         seed=seed,
                         background=background,
                         use_shaders=use_shaders,
                         window=window)

        self._walls_creation(border_thickness)

        # print(f"Version OpenGL: {self._window.ctx.gl_version}")

    def _walls_creation(self, border_thickness: int) -> None:
        """
        Create the border walls for the playground.

        Args:
            border_thickness (int): Thickness of the border walls.
        """
        size = self.size
        assert size is not None
        width, height = size
        h = height / 2
        w = width / 2
        o = border_thickness / 2
        pts = [
            [(-w + o, -h), (-w + o, h)],
            [(-w, h - o), (w, h - o)],
            [(w - o, h), (w - o, -h)],
            [(w, -h + o), (-w, -h + o)],
        ]
        for begin_pt, end_pt in pts:
            wall = NormalWall(pos_start=begin_pt, pos_end=end_pt,
                              wall_thickness=border_thickness)
            self.add(wall, wall.wall_coordinates)

    def _handle_interactions(self) -> None:
        """
        Set up collision interactions for the playground.
        """
        self.add_interaction(CollisionTypes.GRASPER,
                             CollisionTypes.WOUNDED,
                             grasper_grasps_wounded)

        self.add_interaction(CollisionTypes.DISABLER_ZONE,
                             CollisionTypes.DEVICE,
                             disabler_zone_disables_device)

        self.add_interaction(CollisionTypes.WOUNDED,
                             CollisionTypes.RESCUE_CENTER,
                             wounded_rescue_center_collision)

        self.add_interaction(CollisionTypes.DRONE,
                             CollisionTypes.WALL,
                             drone_collision_wall)

        self.add_interaction(CollisionTypes.DRONE,
                             CollisionTypes.DRONE,
                             drone_collision_drone)

        self.add_interaction(CollisionTypes.RETURN_AREA,
                             CollisionTypes.DRONE,
                             return_area_collision)

