from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Dict, Optional, Set, Tuple

import arcade
import numpy as np
from arcade.camera.default import ViewportProjector
from arcade.types import LBWH
from pyglet.gl import GL_SCISSOR_TEST, glDisable, glEnable, glIsEnabled
from pyglet.math import Mat4

from swarm_rescue.simulation.drone.interactive_anchored import InteractiveAnchored
from swarm_rescue.simulation.elements.interactive_zone import InteractiveZone
from swarm_rescue.simulation.elements.physical_entity import PhysicalEntity
from swarm_rescue.simulation.elements.wounded_person import WoundedPerson

if TYPE_CHECKING:
    from swarm_rescue.simulation.elements.embodied import EmbodiedEntity
    from swarm_rescue.simulation.gui_map.playground import Playground


class _WorldSpaceProjector(ViewportProjector):
    """Offscreen projector whose pixels are the world coordinates.

    Goal: a world point and its pixel in the uid image must be the *same*
    numbers, so the ray sensors need no frame conversion at all.

    `ViewportProjector` cannot do this. It builds

        ortho(0, viewport.width, 0, viewport.height)

    and ignores the viewport's `left`/`bottom`: moving them to `-w/2, -h/2`
    only shifts the OpenGL viewport, leaving the projection alone, so every
    drawn pixel lands outside the framebuffer (measured: an entirely empty
    image). An orthographic projection cannot be translated by moving the
    viewport, only by changing its bounds -- which is what this class does:

        ortho(-width / 2, width / 2, -height / 2, height / 2)

    The sprites are placed at their world position (`update_sprite` assigns
    `self._pm_body.position`), so world (0, 0) lands at pixel (w/2, h/2),
    the center of the image, and the map covers it entirely. This is also the
    projection the window camera uses (`GuiSR`), so the window and the uid
    image show the same map.
    """

    def __init__(self, width: int, height: int, *,
                 context: arcade.context.ArcadeContext) -> None:
        super().__init__(viewport=LBWH(0, 0, width, height), context=context)
        # The base class builds the corner-anchored projection and assigns
        # `self._viewport` directly, so the centered matrix is installed here.
        self._projection_matrix = Mat4.orthogonal_projection(
            -width / 2, width / 2, -height / 2, height / 2, -100, 100)

    @ViewportProjector.viewport.setter  # type: ignore[attr-defined]
    def viewport(self, viewport: arcade.types.Rect) -> None:
        """Keep the projection centered when the viewport changes."""
        self._viewport = viewport
        self._projection_matrix = Mat4.orthogonal_projection(
            -viewport.width / 2, viewport.width / 2,
            -viewport.height / 2, viewport.height / 2,
            -100, 100)


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
            only_static_geometry: bool = False,
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
            only_static_geometry (bool): Whether to draw only the static
                geometry, i.e. the walls and the boxes, leaving out the drones
                and the wounded persons. Used to render the map itself,
                independently of what currently stands on it.
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
        # Entities left out of a map-only render. Computed here, before
        # `playground.add_view(self)` below registers the existing entities,
        # so that `add_as_sprite` can consult it from the first call.
        self._excluded_entities = (
            self._static_geometry_only_exclusions(playground)
            if only_static_geometry else set()
        )
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
                    wrap_x=self._ctx.CLAMP_TO_EDGE,
                    wrap_y=self._ctx.CLAMP_TO_EDGE,
                    filter=(self._ctx.NEAREST, self._ctx.NEAREST),
                ),
            ]
        )

        self._offscreen_projector = _WorldSpaceProjector(
            width=self._width,
            height=self._height,
            context=self._ctx,
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

    def set_zoom(self, new_zoom: float) -> None:
        """
        Update the zoom factor and rescale all existing sprites accordingly.

        Args:
            new_zoom: The new zoom factor to apply
        """
        if new_zoom <= 0:
            return
        if new_zoom == self._zoom:
            return
        ratio = new_zoom / self._zoom
        # Rescale all sprites by the ratio. 'scale' is a (x, y) tuple, not a single float.
        for sprites_list in (
            self._transparent_sprites,
            self._interactive_sprites,
            self._zone_sprites,
            self._visible_sprites
        ):
            for sprite in sprites_list:
                sprite.scale = (sprite.scale[0] * ratio, sprite.scale[1] * ratio)
        self._zoom = new_zoom

    def set_center(self, center: Tuple[float, float]) -> None:
        """
        Update the view center used for converting world coordinates to screen positions.
        """
        self._center = center

    @property
    def width(self) -> int:
        """
        Returns the width of the view in pixels.
        """
        return self._width

    @property
    def height(self) -> int:
        """
        Returns the height of the view in pixels.
        """
        return self._height

    @property
    def center(self) -> Tuple[float, float]:
        """
        Returns the view's center coordinates in the pymunk world coordinate frame.
        So, it is not pixels but world units.
        """
        return self._center

    @property
    def sprites(self) -> Dict[EmbodiedEntity, arcade.Sprite]:
        """
        The dictionary of sprites in the view, with the entity as key and the
        sprite as value.
        """
        return self._sprites

    @staticmethod
    def _static_geometry_only_exclusions(playground: Playground) -> set:
        """
        The entities that must not appear on a map-only render.

        Everything that belongs to the simulation rather than to the map: the
        drones, the devices they carry (sensors, grasper, communicator, their
        controllers) and the wounded persons.

        The set is built from what the playground actually holds rather than
        from `isinstance` tests on the entity classes: a device is an
        `InteractiveAnchored`, not a `DronePart`, so a class test silently lets
        the whole sensor suite through and bakes it into the walls.

        Args:
            playground (Playground): The playground being rendered.

        Returns:
            set: The entities to leave out.
        """
        excluded: Set[object] = set()

        for agent in playground.agents:
            excluded.add(agent)
            excluded.add(agent.base)
            for device in agent.base.devices:
                excluded.add(device)

        for element in playground.elements:
            if isinstance(element, WoundedPerson):
                excluded.add(element)
                # A wounded person carries its own forward and lateral
                # controllers, registered in the playground like any other
                # interactive. Leaving them in bakes them into the walls too.
                excluded.update(element.interactives)

        return excluded

    def add_as_sprite(self, entity) -> None:
        """
        Add the entity to the view, create a sprite for it and add it to the
        appropriate sprite list.

        Args:
            entity: The entity to add.
        """
        if entity in self._excluded_entities:
            # The map is being rendered for its own sake, see
            # `ExploredMap.initialize_walls`: what stands on the map is not part
            # of it, and a drone drawn here would be baked into the walls.
            return

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
        if entity in self._excluded_entities:
            # Never added, see `add_as_sprite`.
            return

        if isinstance(entity, InteractiveAnchored) and not self._draw_interactive:
            return

        if isinstance(entity, InteractiveZone) and not self._draw_zone:
            return

        sprite = self._sprites.pop(entity, None)

        if sprite is None:
            # Already out. `hide_from_sensors` drops the sprite of the uid view
            # to make an entity invisible to the sensors, and `cleanup` walks
            # every view again afterward: removing twice has to be allowed.
            return

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
        for entity, sprite in self._sprites.items():
            if entity.needs_sprite_update or force:
                entity.update_sprite(self, sprite)

    @contextmanager
    def _scissor_disabled(self):
        """
        Turn the scissor test off for the duration of an offscreen render.

        Arcade enables the scissor test by default and keeps its box aligned
        with the *window* viewport -- `GuiSR` sets it explicitly to the
        letterboxed map area so the letterbox color survives outside it.

        The state is restored on exit: the window genuinely wants its scissor,
        and arcade re-applies it on the next `camera.use()` anyway.
        """
        was_enabled = bool(glIsEnabled(GL_SCISSOR_TEST))

        if was_enabled:
            glDisable(GL_SCISSOR_TEST)

        try:
            yield
        finally:
            if was_enabled:
                glEnable(GL_SCISSOR_TEST)

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
        with self._scissor_disabled(), self._fbo.activate() as fbo:
            # Clear the framebuffer
            if self._use_color_uid:
                fbo.clear()  # Clear without background if displaying UIDs
            else:
                fbo.clear(color=self._background)  # Clear with the background color

            # Set the 2D projection and the viewport to match the framebuffer
            # dimensions, and restore the previous state on exit.
            #
            # Both are needed: the viewport alone does not change the projection
            # matrix, and the projection alone does not change the viewport.
            # See the comment on `_offscreen_projector` for why this must not
            # depend on the window size.
            with self._offscreen_projector.activate():
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

    # --- UidProvider implementation ---------------------------------------
    # `TopDownView` is the only place where the uid image really exists. It is
    # the presentation side of the `UidProvider` contract that the ray sensors
    # depend on; see ray_sensors/uid_provider.py for why that contract exists.

    def render_uids(self) -> None:
        """
        Draw every entity into the uid image, with its uid as its color.

        Identical to `update_and_draw_in_framebuffer(force=True)`, which is
        the historical spelling used by the reporting code. Naming it here as
        well is what lets the sensors speak the provider interface instead of
        reaching for view internals.
        """
        self.update_and_draw_in_framebuffer(force=True)

    def read_uid_image(self) -> np.ndarray:
        """
        Return the uid image as an array of shape (height, width, 3).
        """
        return self.get_np_img()

    def bind_uid_texture(self) -> None:
        """
        Bind the uid image as the input texture of the compute shader.
        """
        self.texture.use()

    def draw_matplotlib(self) -> None:
        """
        Draw the image from the framebuffer using matplotlib.

        Imported lazily: `matplotlib` costs about half a second, and this
        method is a debugging aid called by hand.
        """
        import matplotlib.pyplot as plt

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
        self._sprites.clear()
