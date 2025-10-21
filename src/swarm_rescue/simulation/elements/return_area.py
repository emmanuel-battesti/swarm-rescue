from typing import Optional, Tuple, Set

import arcade
import pymunk
from PIL import Image
from PIL import ImageDraw

from swarm_rescue.simulation.drone.drone_abstract import DroneAbstract
from swarm_rescue.simulation.drone.drone_base import DroneBase
from swarm_rescue.simulation.elements.interactive_zone import InteractiveZone
from swarm_rescue.simulation.elements.scene_element import SceneElement
from swarm_rescue.simulation.gui_map.collision_handlers import get_colliding_entities
from swarm_rescue.simulation.gui_map.playground import Playground
from swarm_rescue.simulation.utils.definitions import CollisionTypes


def return_area_collision(arbiter: pymunk.Arbiter, _, data):
    """
    Handles the collision between a drone and the return area.

    Args:
        arbiter (pymunk.Arbiter): The collision arbiter.
        _ : Unused.
        data: Dictionary containing the playground.

    Returns:
        bool: True to continue processing the collision.
    """
    playground: Playground = data["playground"]
    return_area, drone_base = get_colliding_entities(playground, arbiter)

    assert isinstance(drone_base, DroneBase)
    assert isinstance(return_area, ReturnArea)

    if isinstance(drone_base, DroneBase):
        return_area.detect_one_drone(drone_base.agent)

    return True


class ReturnArea(InteractiveZone, SceneElement):
    """
    The ReturnArea class is a subclass of InteractiveZone and represents a zone in a playground where drones start and
    end their exploration.
    """

    def __init__(
        self,
        size: Optional[Tuple[int, int]] = None,
        text_to_draw: Optional[str] = None
    ):
        """
        Initialize the ReturnArea.

        Args:
            size (Optional[Tuple[int, int]]): Size of the return area (width, height).
            text_to_draw (Optional[str]): Text to display on the area.
        """
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

        texture = arcade.Texture(
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

        self.drone_inside_set: Set[DroneAbstract] = set()

    @property
    def _collision_type(self):
        """
        Returns the collision type for the return area.
        """
        return CollisionTypes.RETURN_AREA

    def clear(self) -> None:
        """
        Clear the set of drones currently inside the return area.
        """
        self.drone_inside_set = set()

    def detect_one_drone(self, drone: DroneAbstract) -> None:
        """
        Mark a drone as being inside the return area.

        Args:
            drone (DroneAbstract): The drone to mark as inside.
        """
        self.drone_inside_set.add(drone)
        drone.is_inside_return_area = True

    def get_nb_drones_inside(self) -> int:
        """
        Get the number of drones currently inside the return area.

        Returns:
            int: Number of drones inside.
        """
        return len(self.drone_inside_set)

    def pre_step(self) -> None:
        """
        Prepare the return area for a new simulation step.
        """
        # print(f"nb_drones_inside = {self.get_nb_drones_inside()}")
        self.clear()
        super().pre_step()

    def compute_total_health_returned(self) -> int:
        """
        Compute the total health of all drones inside the return area.

        Returns:
            int: Total health returned.
        """
        total_health_returned = 0
        for drone in self.drone_inside_set:
            total_health_returned += drone.drone_health

        return total_health_returned
