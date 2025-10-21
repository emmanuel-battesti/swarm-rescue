""" This module lists all the definitions.
"""

# pylint: disable=missing-class-docstring
from collections import namedtuple
from enum import IntEnum, auto
from typing import Type

SIMULATION_STEPS: int = 10
SPACE_DAMPING: float = 0.95  # https://www.pymunk.org/en/latest/pymunk.html#pymunk.Space.damping
# SPACE_DAMPING: a value of 0.9 means that each body will lose 10% of its velocity per second. Defaults to 1.
LINEAR_FORCE: int = 100
ANGULAR_VELOCITY: float = 0.3
ARM_MAX_FORCE: int = 500
MAX_GRASP_FORCE: int = 600

WALL_DEPTH: int = 10

PYMUNK_STEPS: int = 10

VISIBLE_ALPHA: int = 255
INVISIBLE_ALPHA: int = 75
SPECIAL_ZONE_ALPHA: int = 75
DEFAULT_INTERACTION_RANGE: int = 5

FRICTION_ENTITY: float = 0.8
ELASTICITY_ENTITY: float = 0.5


class CollisionTypes(IntEnum):
    """
    Enum for collision types in the simulation.
    """
    ELEMENT = auto()
    PART = auto()

    WALL = auto()
    DRONE = auto()
    WOUNDED = auto()
    RESCUE_CENTER = auto()

    DEVICE = auto()
    DISABLER_ZONE = auto()

    GRASPER = auto()
    RETURN_AREA = auto()


def add_custom_collision(collision_types: Type[IntEnum], name: str) -> type:
    """
    Function that allows to add new collisions to CollisionTypes.
    This is used when a user wants to create a new type of Entity,
    that requires particular collision handler and behavior.

    Examples:
        CustomCollisionTypes = add_custom_collision(CollisionTypes, JELLY)

    Args:
        collision_types: CollisionTypes enum.
            Either the default one or a custom one.
        name: name of the new collision type (UPPERCASE)

    Returns:
        New CollisionTypes Enum.

    """
    names = [m.name for m in collision_types] + [name]
    extended_enum = IntEnum("CollisionTypes", names)
    return extended_enum


Detection = namedtuple("Detection", "entity, distance, angle")

