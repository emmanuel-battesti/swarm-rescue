# pylint: disable=too-many-public-methods

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Union

import arcade
import pymunk
import pymunk.autogeometry
from PIL import Image

from swarm_rescue.simulation.elements.entity import Entity
from swarm_rescue.simulation.utils.definitions import ELASTICITY_ENTITY, FRICTION_ENTITY
from swarm_rescue.simulation.utils.position import Coordinate, CoordinateSampler, InitCoord


class EmbodiedEntity(Entity, ABC):
    """
    Represents entities physically present in the playground, capable of interacting
    with others through pymunk collisions. These entities have physical properties
    such as position, velocity, and dimensions, and can be rendered as sprites.
    """

    def __init__(
            self,
            name: Optional[str] = None,
            filename: Optional[str] = None,
            texture: Optional[arcade.Texture] = None,
            radius: Optional[float] = None,
            width: Optional[float] = None,
            height: Optional[float] = None,
            temporary: bool = False,
            shape_approximation: Optional[str] = None,
            sprite_front_is_up: bool = False,
            color: Optional[Tuple[int, int, int]] = None,
    ):
        """
        Initializes an EmbodiedEntity with the given parameters.

        Args:
            name (Optional[str]): Name of the entity.
            filename (Optional[str]): Path to the texture file.
            texture (Optional[arcade.Texture]): Arcade texture for the entity.
            radius (Optional[float]): Radius of the entity.
            width (Optional[float]): Width of the entity.
            height (Optional[float]): Height of the entity.
            temporary (bool): Whether the entity is temporary.
            shape_approximation (Optional[str]): Shape approximation method.
            sprite_front_is_up (bool): Whether the sprite's front is up.
            color (Optional[Tuple[int, int, int]]): Color of the entity.
        """
        super().__init__(name, temporary)

        # Initialize the base sprite with the given texture or filename
        self._sprite_front_is_up = sprite_front_is_up
        self._base_sprite = arcade.Sprite(
            texture=texture,
            filename=filename,
            hit_box_algorithm="Detailed",
            hit_box_detail=1,
            flipped_diagonally=sprite_front_is_up,
            flipped_horizontally=sprite_front_is_up,
        )  # type: ignore

        self._color = color

        # Calculate scale and dimensions
        self._scale, self._radius, self._width, self._height = self._get_dimensions(
            radius, width, height
        )

        # Initialize pymunk body and shapes
        self._pm_body = self._get_pm_body()
        self._pm_shapes = self._get_pm_shapes_from_sprite(shape_approximation)

        # Set collision type for pymunk shapes
        self._set_pm_collision_type()

        # Flags for movement and overlapping
        self._moved = False
        self._allow_overlapping = False
        self._initial_coordinates: Optional[InitCoord] = None

    #############
    # Properties
    #############
    @property
    def pm_elements(self) -> List[Union[pymunk.Shape, pymunk.Body]]:
        """
        Returns the list of pymunk shapes and the pymunk body for this entity.

        Returns:
            List[Union[pymunk.Shape, pymunk.Body]]: List of shapes and body.
        """
        return self._pm_shapes + [self._pm_body]

    @property
    def pm_shapes(self) -> List[pymunk.Shape]:
        """
        Returns the list of pymunk shapes for this entity.

        Returns:
            List[pymunk.Shape]: List of shapes.
        """
        return self._pm_shapes

    @property
    def pm_body(self) -> pymunk.Body:
        """
        Returns the pymunk body for this entity.

        Returns:
            pymunk.Body: The pymunk body.
        """
        return self._pm_body

    @property
    def texture(self) -> Optional[arcade.Texture]:
        """
        Returns the texture of the entity.

        Returns:
            Optional[arcade.Texture]: The texture.
        """
        return self._base_sprite.texture

    @property
    def radius(self) -> float:
        """
        Returns the radius of the entity.

        Returns:
            float: The radius.
        """
        return self._radius

    @property
    def scale(self) -> float:
        """
        Returns the scale of the entity.

        Returns:
            float: The scale.
        """
        return self._scale

    @property
    def width(self) -> float:
        """
        Returns the width of the entity.

        Returns:
            float: The width.
        """
        return self._width

    @property
    def height(self) -> float:
        """
        Returns the height of the entity.

        Returns:
            float: The height.
        """
        return self._height

    @property
    def coordinates(self) -> Tuple[pymunk.Vec2d, float]:
        """
        Returns the position and angle of the entity.

        Returns:
            Tuple[pymunk.Vec2d, float]: Position and angle.
        """
        return self.position, self.angle

    @property
    def position(self) -> pymunk.Vec2d:
        """
        Returns the current position of the entity.

        Returns:
            pymunk.Vec2d: Position as a 2D vector.
        """
        return self._pm_body.position

    @property
    def angle(self) -> float:
        """
        Returns the absolute orientation of the entity.

        Returns:
            float: Angle in radians.
        """
        return self._pm_body.angle % (2 * math.pi)

    @property
    def velocity(self) -> pymunk.Vec2d:
        """
        Returns the velocity of the entity.

        Returns:
            pymunk.Vec2d: Velocity vector.
        """
        return self._pm_body.velocity

    @property
    def angular_velocity(self) -> float:
        """
        Returns the angular velocity of the entity.

        Returns:
            float: Angular velocity.
        """
        return self._pm_body.angular_velocity

    @property
    def color_uid(self) -> Tuple[int, int, int, int]:
        """
        Returns the color UID (unique identifier as color).

        Returns:
            Tuple[int, int, int, int]: RGBA color tuple.
        """
        return self._uid & 255, (self._uid >> 8) & 255, (self._uid >> 16) & 255, 255

    @property
    def moved(self) -> bool:
        """
        Returns whether the entity has moved.

        Returns:
            bool: True if moved, False otherwise.
        """
        if self._moved:
            return True

        if self._pm_body.body_type == pymunk.Body.DYNAMIC:
            vel = self._pm_body.velocity.length
            if vel > 0.001:
                return True

            ang_vel = self._pm_body.angular_velocity
            if abs(ang_vel) > 0.001:
                return True

        return False

    @property
    def allow_overlapping(self) -> bool:
        """
        Returns whether overlapping is allowed for this entity.

        Returns:
            bool: True if allowed, False otherwise.
        """
        return self._allow_overlapping

    @allow_overlapping.setter
    def allow_overlapping(self, allow: bool) -> None:
        """
        Set whether overlapping is allowed for this entity.

        Args:
            allow (bool): Allow overlapping.
        """
        self._allow_overlapping = allow

    @property
    def initial_coordinates(self) -> Optional[InitCoord]:
        """
        Returns the initial coordinates of the entity.

        Returns:
            Optional[InitCoord]: Initial coordinates.
        """
        return self._initial_coordinates

    @initial_coordinates.setter
    def initial_coordinates(self, init_coord: InitCoord) -> None:
        """
        Set the initial coordinates of the entity.

        Args:
            init_coord (InitCoord): Initial coordinates.
        """
        self._initial_coordinates = init_coord

    ##############
    # Init pm Elements
    ###############
    def _get_dimensions(
            self,
            radius: Optional[float],
            width: Optional[float],
            height: Optional[float],
    ) -> Tuple[float, float, float, float]:
        """
        Calculates the scale and dimensions of the entity based on the given parameters.

        Args:
            radius (Optional[float]): Desired radius of the entity.
            width (Optional[float]): Desired width of the entity.
            height (Optional[float]): Desired height of the entity.

        Returns:
            Tuple[float, float, float, float]: Scale, radius, width, and height.
        """
        orig_radius = max(
            pymunk.Vec2d(*vert).length for vert in self._base_sprite.get_hit_box()
        )

        horiz = [pymunk.Vec2d(*vert).x for vert in self._base_sprite.get_hit_box()]
        vert = [pymunk.Vec2d(*vert).y for vert in self._base_sprite.get_hit_box()]

        orig_width = max(horiz) - min(horiz)
        orig_height = max(vert) - min(vert)

        if radius:
            scale = radius / orig_radius
        elif height:
            scale = height / orig_height
        elif width:
            scale = width / orig_width
        else:
            scale = 1

        width = scale * orig_width
        height = scale * orig_height
        radius = scale * orig_radius

        return scale, radius, width, height

    def _get_pm_shapes_from_sprite(self, shape_approximation: Optional[str]):
        """
        Creates pymunk shapes for the entity based on its sprite and shape approximation.

        Args:
            shape_approximation (Optional[str]): Shape approximation method.

        Returns:
            List[pymunk.Shape]: List of pymunk shapes.

        TODO:
            EB: why not use the arcade function to do that ??
            shape = self.physics_engine.get_physics_object(sprite)

        """
        vertices = self._base_sprite.get_hit_box()
        vertices = [(x * self._scale, y * self._scale) for x, y in vertices]

        if shape_approximation == "circle":
            pm_shapes = [pymunk.Circle(self._pm_body, self._radius)]

        elif shape_approximation == "box":
            top = max(vert[0] for vert in vertices)
            bottom = min(vert[0] for vert in vertices)
            left = min(vert[1] for vert in vertices)
            right = max(vert[1] for vert in vertices)

            box_vertices = ((top, left), (top, right), (bottom, right), (bottom, left))
            pm_shapes = [pymunk.Poly(self._pm_body, box_vertices)]

        elif shape_approximation == "hull":
            pm_shapes = [pymunk.Poly(self._pm_body, vertices)]

        elif shape_approximation == "decomposition":
            if not pymunk.autogeometry.is_closed(vertices):
                vertices += [vertices[0]]

            if pymunk.area_for_poly(vertices) < 0:
                vertices = list(reversed(vertices))

            list_vertices = pymunk.autogeometry.convex_decomposition(
                vertices, tolerance=0.5
            )

            pm_shapes = []
            for vertices in list_vertices:
                pm_shape = pymunk.Poly(body=self._pm_body, vertices=vertices)
                pm_shapes.append(pm_shape)

        else:
            pm_shapes = [pymunk.Poly(body=self._pm_body, vertices=vertices)]

        for pm_shape in pm_shapes:
            pm_shape.friction = FRICTION_ENTITY
            pm_shape.elasticity = ELASTICITY_ENTITY

        return pm_shapes

    ##############
    # Sprites
    ##############

    def get_sprite(self, zoom: float = 1, use_color_uid: bool = False) -> arcade.Sprite:
        """
        Returns the arcade.Sprite for this entity, optionally using a color UID.

        Args:
            zoom (float): Zoom factor.
            use_color_uid (bool): Whether to use color UID.

        Returns:
            arcade.Sprite: The sprite.
        """
        texture = self._base_sprite.texture
        if use_color_uid:
            texture = self.generate_texture_with_id_color(texture)

        assert isinstance(texture, arcade.Texture)

        sprite = arcade.Sprite(
            texture=texture,
            scale=zoom * self._scale,
            hit_box_algorithm="Detailed",
            hit_box_detail=1,
        )

        if self._color and not use_color_uid:
            sprite.color = self._color

        return sprite

    def generate_texture_with_id_color(self, texture: arcade.Texture) -> arcade.Texture:
        """
        Generates a new texture where the entity's unique identifier (UID) is encoded
        as a color. This is useful for rendering objects with unique colors for debugging
        or identification purposes.

        Args:
            texture (arcade.Texture): The original texture of the entity.

        Returns:
            arcade.Texture: A new texture with the UID encoded as a color.
        """
        # Create a new blank RGBA image with the same size as the input texture
        img_uid = Image.new("RGBA", texture.size)
        pixels = img_uid.load()  # Access the pixel data of the new image
        pixels_texture = texture.image.load()  # Access the pixel data of the original texture

        # Iterate over each pixel in the new image img_uid
        for i in range(img_uid.size[0]):
            for j in range(img_uid.size[1]):

                # If the pixel is fully transparent in the original texture,
                # set the pixel to fully transparent and black in the new image
                if pixels_texture[i, j][3] == 0:
                    pixels[i, j] = (0, 0, 0, 0)

                # Else if the pixel is not black in the original texture
                else:
                    pixels[i, j] = self.color_uid  # type: ignore

        texture = arcade.Texture(
            name=str(self._uid),
            image=img_uid,
            hit_box_algorithm="Detailed",
            hit_box_detail=1,
        )

        return texture

    @property
    def needs_sprite_update(self) -> bool:
        """
        Returns whether the sprite needs to be updated.

        Returns:
            bool: True if update needed, False otherwise.
        """
        return self._moved

    def update_sprite(self, view, sprite) -> None:
        """
        Updates the position and angle of the sprite based on the entity's current position
        and orientation in the playground (and in pymunk).

        Args:
            view: The current view of the playground, containing information about
                  the center, zoom level, width, and height of the visible area.
            sprite: The sprite object to be updated, representing the visual appearance
                    of the entity.

        The method calculates the sprite's position in the view by adjusting the entity's
        physical position (`_pm_body.position`) relative to the view's center and applying
        the zoom level. It also updates the sprite's angle to match the entity's orientation.
        """
        pos_x = (
                        self._pm_body.position.x - view.center[0]
                ) * view.zoom + view.width // 2
        pos_y = (
                        self._pm_body.position.y - view.center[1]
                ) * view.zoom + view.height // 2

        # Set the sprite's position in the view
        sprite.set_position(pos_x, pos_y)

        # Update the sprite's angle to match the entity's orientation in degrees
        sprite.angle = int(math.degrees(self._pm_body.angle))

    ###################
    # Pymunk objects
    ###################

    @abstractmethod
    def _get_pm_body(self) -> pymunk.Body:
        """
        Set pymunk body. Shapes are attached to a body.

        Returns:
            pymunk.Body: The pymunk body.
        """

    def _set_pm_collision_type(self) -> None:
        """
        Set the collision type for the pm shapes.
        """
        for pm_shape in self._pm_shapes:
            pm_shape.collision_type = self._collision_type

    @property
    @abstractmethod
    def _collision_type(self):
        """
        Returns the collision type for the pm shapes.
        """

    ###################
    # Position and Move
    ###################
    def move_to(
            self,
            coordinates: Union[Coordinate, CoordinateSampler],
            allow_overlapping: bool = True,
            check_within: bool = False,
    ) -> None:
        """
        Moves the entity to the specified coordinates.

        Args:
            coordinates (Union[Coordinate, CoordinateSampler]): Target coordinates.
            allow_overlapping (bool): Whether overlapping is allowed.
            check_within (bool): Whether to check if the entity is within bounds.

        Raises:
            ValueError: If overlapping is not allowed and the entity overlaps.
            ValueError: If the entity is not within bounds.
        """
        assert self._playground

        if isinstance(coordinates, CoordinateSampler):
            coordinates = self._sample_valid_coordinate()

        if (not allow_overlapping) and self._playground.overlaps(self, coordinates):
            raise ValueError("Entity overlaps but overlap is not allowed")

        if check_within and not self._playground.within_playground(
                coordinates=coordinates
        ):
            raise ValueError("Entity is not placed within Playground boundaries")

        position, angle = coordinates

        # Calculate Velocities
        absolute_velocity, angular_velocity = (0, 0), 0

        # Apply new position and velocities
        self._pm_body.position, self._pm_body.angle = position, angle
        self._pm_body.velocity = absolute_velocity
        self._pm_body.angular_velocity = angular_velocity

        if self._pm_body.space:
            self._pm_body.space.reindex_shapes_for_body(self._pm_body)

        self._moved = True

    def _sample_valid_coordinate(self) -> Coordinate:
        """
        Samples a valid coordinate for the entity that does not overlap with others.

        Returns:
            Coordinate: Valid coordinate.

        Raises:
            ValueError: If no valid coordinate is found.
        """
        assert self._playground
        sampler = self._initial_coordinates
        assert isinstance(sampler, CoordinateSampler)

        for coordinate in sampler.sample():
            if not self._playground.overlaps(self, coordinate):
                return coordinate

        raise ValueError("Entity could not be placed without overlapping")

    ##############
    # Playground Interactions
    ################

    def pre_step(self) -> None:
        """
        Reset the moved flag before each simulation step.
        """
        self._moved = False
