from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Optional, Tuple

import arcade
import matplotlib.pyplot as plt
import numpy as np

from swarm_rescue.simulation.drone.interactive_anchored import InteractiveAnchored
from swarm_rescue.simulation.elements.interactive_zone import InteractiveZone
from swarm_rescue.simulation.elements.physical_entity import PhysicalEntity

if TYPE_CHECKING:
    from swarm_rescue.simulation.elements.embodied import EmbodiedEntity
    from swarm_rescue.simulation.gui_map.playground import Playground


class TopDownView:
    """
    TopDownView provides a 2D top-down rendering of the playground and its entities.
    """

    def __init__(
            self,
            playground: Playground,
            size: Optional[Tuple[int, int]] = None,
            center: Tuple[float, float] = (0, 0),
            zoom: float = 1,
            use_color_uid: bool = False,
            draw_transparent: bool = True,
            draw_interactive: bool = True,
            draw_zone: bool = True,
    ) -> None:
        """
        Initialize the TopDownView.

        Args:
            playground (Playground): The playground to render.
            size (Optional[Tuple[int, int]]): Size of the view (width, height).
            center (Tuple[float, float]): Center of the view.
            zoom (float): Zoom factor.
            use_color_uid (bool): Whether to use color UID for sprites.
            draw_transparent (bool): Whether to draw transparent sprites.
            draw_interactive (bool): Whether to draw interactive sprites.
            draw_zone (bool): Whether to draw zone sprites.
        """
        self._center = center

        if not size:
            size = playground.size

        if not size:
            raise ValueError("Size should be set")

        self._width, self._height = self._size = size

        self._zoom = zoom
        self._draw_transparent = draw_transparent
        self._draw_interactive = draw_interactive
        self._draw_zone = draw_zone
        self._use_color_uid = use_color_uid

        self._transparent_sprites = arcade.SpriteList()
        self._visible_sprites = arcade.SpriteList()
        self._interactive_sprites = arcade.SpriteList()
        self._zone_sprites = arcade.SpriteList()

        self._sprites: Dict[EmbodiedEntity, arcade.Sprite] = {}

        self._background = playground.background

        self._playground = playground
        self._ctx = playground.ctx
        # Create the framebuffer object which will be used to draw the map
        self._fbo = self._ctx.framebuffer(
            color_attachments=[
                self._ctx.texture(
                    size,
                    components=4,
                    wrap_x=self._ctx.CLAMP_TO_BORDER,  # type: ignore
                    wrap_y=self._ctx.CLAMP_TO_BORDER,  # type: ignore
                    # type: ignore
                    filter=(self._ctx.NEAREST, self._ctx.NEAREST),
                ),
            ]
        )

        playground.add_view(self)

    @property
    def texture(self):
        """
        The OpenGL texture containing the map pixel data.
        """
        return self._fbo.color_attachments[0]

    @property
    def zoom(self) -> float:
        """
        Returns the zoom factor.
        """
        return self._zoom

    @property
    def width(self) -> int:
        """
        Returns the width of the view.
        """
        return self._width

    @property
    def height(self) -> int:
        """
        Returns the height of the view.
        """
        return self._height

    @property
    def center(self) -> Tuple[float, float]:
        """
        Returns the center of the view.
        """
        return self._center

    def update_size(self, new_size: Tuple[int, int]) -> None:
        """
        Update the view dimensions after window resize.

        Args:
            new_size: New (width, height) dimensions
        """
        self._width, self._height = self._size = new_size


    @property
    def sprites(self) -> Dict[EmbodiedEntity, arcade.Sprite]:
        """
        The dictionary of sprites in the view, with the entity as key and the
        sprite as value.
        """
        return self._sprites

    def add_as_sprite(self, entity) -> None:
        """
        Add the entity to the view, create a sprite for it and add it to the
        appropriate sprite list.

        Args:
            entity: The entity to add.
        """
        if isinstance(entity, InteractiveAnchored):
            if not self._draw_interactive:
                return

            if self._use_color_uid:
                raise ValueError(
                    "Cannot display uid of interactive, set draw_interactive to False"
                )

            sprite = entity.get_sprite(self._zoom)
            self._interactive_sprites.append(sprite)

        elif isinstance(entity, InteractiveZone):
            if not self._draw_zone:
                return

            if self._use_color_uid:
                raise ValueError("Cannot display uid of zones, set draw_zones to False")

            sprite = entity.get_sprite(self._zoom)
            self._zone_sprites.append(sprite)

        elif isinstance(entity, PhysicalEntity):
            sprite = entity.get_sprite(self._zoom, use_color_uid=self._use_color_uid)

            if entity.transparent:
                if self._draw_transparent:
                    self._transparent_sprites.append(sprite)

            else:
                self._visible_sprites.append(sprite)

        else:
            raise ValueError("Not implemented")

        entity.update_sprite(self, sprite)
        self._sprites[entity] = sprite

    def remove_as_sprite(self, entity) -> None:
        """
        Remove the entity from the view and remove the sprite from the sprite lists.

        Args:
            entity: The entity to remove.
        """
        if isinstance(entity, InteractiveAnchored) and not self._draw_interactive:
            return

        if isinstance(entity, InteractiveZone) and not self._draw_zone:
            return

        sprite = self._sprites.pop(entity)

        if isinstance(entity, InteractiveAnchored):
            self._interactive_sprites.remove(sprite)

        elif isinstance(entity, InteractiveZone):
            self._zone_sprites.remove(sprite)

        elif isinstance(entity, PhysicalEntity):
            if entity.transparent:
                self._transparent_sprites.remove(sprite)

            else:
                self._visible_sprites.remove(sprite)

    def update_sprites_position(self, force: bool = False) -> None:
        """
        Update the sprites position and angle of the entities in the view from
        the pymunk position and angle.

        Args:
            force (bool): If True, force update all sprites.
        """
        # check that
        for entity, sprite in self._sprites.items():
            if entity.needs_sprite_update or force:
                entity.update_sprite(self, sprite)

    def update_and_draw_in_framebuffer(self, force: bool = False) -> None:
        """
        Update and draw all sprites in the framebuffer.

        This method updates the positions and angles of all sprites in the view
        and then draws them into the framebuffer attached to the view. The framebuffer
        is used to render the map or scene.

        Args:
            force (bool): If True, forces the update of all sprite positions and angles,
                          even if they do not require an update.
        """
        # Update the sprites' positions and angles
        self.update_sprites_position(force)

        # Activate the framebuffer for drawing
        with self._fbo.activate() as fbo:
            # Clear the framebuffer
            if self._use_color_uid:
                fbo.clear()  # Clear without background if displaying UIDs
            else:
                fbo.clear(self._background)  # Clear with the background color

            # Set the 2D projection to match the framebuffer dimensions
            self._ctx.projection_2d = 0, self._width, 0, self._height

            # Draw the transparent sprites if enabled
            if self._draw_transparent:
                self._transparent_sprites.draw(pixelated=True)

            # Draw the interactive sprites if enabled
            if self._draw_interactive:
                self._interactive_sprites.draw(pixelated=True)

            # Draw the special zone sprites if enabled
            if self._draw_zone:
                self._zone_sprites.draw(pixelated=True)

            # Draw the visible sprites
            self._visible_sprites.draw(pixelated=True)

    def get_np_img(self) -> np.ndarray:
        """
        Get the image from the framebuffer as a numpy array.

        Returns:
            np.ndarray: The image array.
        """
        img = np.frombuffer(self._fbo.read(), dtype=np.dtype("B")).reshape(
            self._height, self._width, 3
        )
        return img

    def draw_matplotlib(self) -> None:
        """
        Draw the image from the framebuffer using matplotlib.
        """
        img = self.get_np_img()
        plt.imshow(img)
        plt.axis("off")
        plt.show()

    def reset(self) -> None:
        """
        Reset the view by clearing all the sprites.
        """
        self._transparent_sprites.clear()
        self._interactive_sprites.clear()
        self._zone_sprites.clear()
        self._visible_sprites.clear()
