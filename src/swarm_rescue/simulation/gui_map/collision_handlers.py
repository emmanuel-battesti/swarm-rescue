from __future__ import annotations

from typing import TYPE_CHECKING

import pymunk

from swarm_rescue.simulation.drone.grasper import Grasper

if TYPE_CHECKING:
    from swarm_rescue.simulation.gui_map.playground import Playground


def get_colliding_entities(playground: "Playground", arbiter: pymunk.Arbiter):
    """
    Retrieve the two entities involved in a collision from the arbiter.

    Args:
        playground (Playground): The playground instance.
        arbiter (pymunk.Arbiter): The collision arbiter.

    Returns:
        tuple: The two colliding entities.
    """
    shape_1, shape_2 = arbiter.shapes
    entity_1 = playground.get_entity_from_shape(shape_1)
    entity_2 = playground.get_entity_from_shape(shape_2)

    return entity_1, entity_2


def grasper_grasps_wounded(arbiter: pymunk.Arbiter, _, data):
    """
    Handle the event where a grasper attempts to grasp a wounded entity.

    Args:
        arbiter (pymunk.Arbiter): The collision arbiter.
        _ : Unused.
        data: Dictionary containing the playground.

    Returns:
        bool: True to continue processing the collision.
    """
    playground: Playground = data["playground"]
    grasper, wounded = get_colliding_entities(playground, arbiter)

    assert isinstance(grasper, Grasper)

    if grasper.can_grasp:
        grasper.grasps(wounded)

    return True
