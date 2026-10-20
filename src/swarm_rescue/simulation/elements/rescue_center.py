from typing import TYPE_CHECKING, Tuple

import arcade
import arcade.hitbox
import pymunk

from swarm_rescue.resources import path_resources
from swarm_rescue.simulation.elements.physical_element import PhysicalElement
from swarm_rescue.simulation.elements.wounded_person import WoundedPerson
from swarm_rescue.simulation.collision_handlers import get_colliding_entities
from swarm_rescue.simulation.utils.definitions import CollisionTypes
from swarm_rescue.simulation.utils.texture_cache import load_texture_cached

if TYPE_CHECKING:
    # `Playground` is only used as an annotation on a *local* variable, and
    # those are never evaluated at runtime (PEP 526). Importing the
    # presentation package here would make the model depend on it for nothing.
    from swarm_rescue.simulation.gui_map.playground import Playground


def wounded_rescue_center_collision(arbiter: pymunk.Arbiter, _, data):
    """
    Handles the collision between a wounded person and a rescue center.

    Args:
        arbiter (pymunk.Arbiter): The collision arbiter.
        _: Unused.
        data: Dictionary containing the playground.

    Returns:
        bool: True to continue processing the collision.
    """
    playground: Playground = data["playground"]
    wounded_person, rescue_center = get_colliding_entities(playground, arbiter)

    assert isinstance(wounded_person, WoundedPerson)
    assert isinstance(rescue_center, RescueCenter)

    if wounded_person.rescue_center == rescue_center:
        rescue_center.activate(wounded_person)

    return True


class RescueCenter(PhysicalElement):
    """
    The RescueCenter class represents a rescue center in the simulation. When a
    WoundedPerson comes into contact with the rescue center, it provides a
    reward of 1 to the drone bringing the wounded person. Then the wounded
    person disappears.
    """

    def __init__(self, size: Tuple[int, int], **kwargs):
        """
        Initialize the RescueCenter.

        Args:
            size (Tuple[int, int]): Size of the rescue center (width, height).
            **kwargs: Additional keyword arguments.
        """
        filename = path_resources + "/rescue_center.png"
        width = size[0]
        height = size[1]
        orig_x = int((800 - width) / 2)
        orig_y = int((800 - height) / 2)

        # The full texture is loaded, then cropped to the sub-region.
        hit_box_algo = arcade.hitbox.PymunkHitBoxAlgorithm(detail=1.0)
        full_texture: arcade.Texture = load_texture_cached(
            file_path=filename,
            hit_box_algorithm=hit_box_algo,
        )
        texture: arcade.Texture = full_texture.crop(
            x=orig_x,
            y=orig_y,
            width=width,
            height=height,
        )
        super().__init__(texture=texture, **kwargs)

        # Friction normally goes between 0 (no friction) and 1.0 (high friction)
        # Friction is between two objects in contact. It is important to remember
        # in top-down games that friction moving along the 'floor' is controlled
        # by damping.
        # elasticity: How bouncy this object is. 0 is no bounce.
        # Values of 1.0 and higher may behave badly.
        # See: https://api.arcade.academy/en/latest/examples/pymunk_demo_top_down.html
        for pm_shape in self._pm_shapes:
            pm_shape.elasticity = 0.1
            pm_shape.friction = 0.0  # default value in arcade is 0.2

        self._quantity_rewards = None
        self._count_rewards = 0

    @property
    def _collision_type(self):
        """
        Returns the collision type for the rescue center.
        """
        return CollisionTypes.RESCUE_CENTER

    def activate(self, entity: WoundedPerson) -> None:
        """
        Activate the rescue center for a wounded person, reward the drone, and
        remove the wounded person.

        Args:
            entity (WoundedPerson): The wounded person to rescue.
        """
        if self._playground is None:
            raise ValueError("RescueCenter is not "
                             "associated with a playground.")

        grasped_by_list = entity.grasped_by.copy()
        grasped_by_size = len(entity.grasped_by)

        if grasped_by_list:
            for part in grasped_by_list:
                agent = part.agent
                agent.reward += entity.reward / grasped_by_size
                agent.grasper.reset()
        else:
            # Get the closest drone agent to the rescue center.
            agent = min(self._playground.agents, key=lambda a: self.position.get_dist_sqrd(a.true_position()))
            agent.reward += entity.reward

        self._playground.remove(entity)
