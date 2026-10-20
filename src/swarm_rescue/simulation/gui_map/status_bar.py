"""The black band drawn across the top of the simulation window.

The bar shows the name of the map being played on the left and how far the
round has progressed on the right. It is window furniture, not map content, and
that distinction is the whole point of this module.

Why it cannot reach the sensors
-------------------------------
The lidars do not read the window. They read the *uid image*: an offscreen
framebuffer, sized to the map, in which every pixel carries an entity
identifier. That image is produced by `TopDownView.update_and_draw_in_framebuffer()`
-- a different render target, activated and deactivated around the sprite
drawing. The window is a third, separate surface.

So the bar is drawn from `GuiSR.on_draw()` and nowhere else. `on_draw()` is the
window frame callback: it is never called by the sensor path, by
`render_uids()`, or by the video recorder (which captures the offscreen
framebuffer through `update_and_draw_in_framebuffer()`). A label drawn there is
invisible to every ray sensor by construction, and it is absent from the
recorded video and from the reported screenshot as well.

Two window-space details the bar has to respect
-----------------------------------------------
- **Projection.** `GuiSR` draws the map through a centered `Camera2D`, so its
  coordinates are map pixels around the world origin. Drawing a rectangle with
  those numbers would put the bar in the middle of the playground. The bar
  therefore activates its own `ViewportProjector` over the whole window, which
  restores the corner-anchored projection where `(0, 0)` is the bottom-left
  pixel -- the coordinate system a status bar is written in.

- **Scissor.** The camera sets a scissor box equal to its viewport, which is
  what preserves the letterbox color around the map. That box is *smaller*
  than the window as soon as the window is not exactly the map aspect ratio, so
  a bar drawn without touching it would be clipped away -- on a letterboxed
  window it would lose its left and right ends, or vanish entirely. The scissor
  test is disabled for the duration of the bar and restored afterward.

Both the projector and the scissor are restored when the call returns, so the
next map drawing (and the next offscreen render) find the state they expect.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator, Optional, Tuple

import arcade
from arcade.camera.default import ViewportProjector
from arcade.types import LBWH
from pyglet.gl import GL_SCISSOR_TEST, glDisable, glEnable, glIsEnabled

from swarm_rescue.simulation.utils.constants import (
    WINDOW_STATUS_BAR_COLOR,
    WINDOW_STATUS_BAR_FONT_SIZE,
    WINDOW_STATUS_BAR_HEIGHT,
    WINDOW_STATUS_BAR_TEXT_COLOR,
    WINDOW_STATUS_BAR_TEXT_PADDING,
)


class StatusBar:
    """The map name and the round progress, painted across the top of the window.

    The two labels are created lazily and reused: an `arcade.Text` builds a
    pyglet label, and rebuilding both of them on every frame would re-do that
    work sixty times a second for a string that changes once in a while. The
    percentage is only pushed into the right label when it actually moves.

    Args:
        map_name (str): The text shown on the left of the bar.
        height (int): Bar thickness, in window pixels.
        background_color: Fill color of the band.
        text_color: Color of both labels.
        font_size (int): Label size, in window pixels.
        padding (int): Gap kept between a label and the window edge.
    """

    def __init__(
            self,
            map_name: str,
            height: int = WINDOW_STATUS_BAR_HEIGHT,
            background_color: Tuple[int, int, int] = WINDOW_STATUS_BAR_COLOR,
            text_color: Tuple[int, int, int] = WINDOW_STATUS_BAR_TEXT_COLOR,
            font_size: int = WINDOW_STATUS_BAR_FONT_SIZE,
            padding: int = WINDOW_STATUS_BAR_TEXT_PADDING,
    ) -> None:
        """
        Initialize the StatusBar.

        Args:
            map_name (str): The text shown on the left of the bar.
            height (int): Bar thickness, in window pixels.
            background_color: Fill color of the band.
            text_color: Color of both labels.
            font_size (int): Label size, in window pixels.
            padding (int): Gap kept between a label and the window edge.
        """
        self._map_name = map_name
        self._height = max(0, int(height))
        self._background_color = background_color
        self._text_color = text_color
        self._font_size = max(1, int(font_size))
        self._padding = max(0, int(padding))

        self._projector: Optional[ViewportProjector] = None
        self._left_text: Optional[arcade.Text] = None
        self._right_text: Optional[arcade.Text] = None
        self._last_right_label: Optional[str] = None
        # Window size the two labels were last laid out for, so a resize
        # rebuilds them at the new right-hand edge instead of leaving them
        # pinned to the old one.
        self._labels_window_size: Optional[Tuple[int, int]] = None

    @property
    def height(self) -> int:
        """
        Returns the bar thickness in window pixels.

        Returns:
            int: Bar thickness.
        """
        return self._height

    def effective_height(self, window_height: int) -> int:
        """
        The thickness actually painted in a window of this height.

        The single source of truth for "how much of the window does the band
        take". `GuiSR` reserves exactly this much room for the map, so the two
        can never disagree and leave the band covering map rows.

        It gives way in a window too short to hold both: the map keeps the last
        pixel and the band is clipped. The band is decoration and the map is
        the content, so when there is not enough room the content wins.

        Args:
            window_height (int): Height of the window, in pixels.

        Returns:
            int: Thickness in pixels, 0 when nothing can be painted.
        """
        # `height - 1` rather than `height`: an area of zero pixels would leave
        # the camera with a zero-sized viewport, and `Camera2D.unproject`
        # divides by the viewport width.
        return max(0, min(self._height, int(window_height) - 1))

    @staticmethod
    def progress_label(elapsed_timestep: int,
                       max_timestep_limit: Optional[int],
                       elapsed_walltime: float = 0.0,
                       max_walltime_limit: Optional[int] = None,
                       rescued_number: Optional[int] = None,
                       total_wounded_persons: Optional[int] = None) -> Optional[str]:
        """
        Build the right-hand label from the state of the round.

        The label carries the two limits as two separate readings, because a
        round ends on whichever is reached first and they say different things:
        the step count is the simulated progress, the wall time is the real
        time spent. The percentage is what the step count is measured against.
        The rescue count comes last: it is the point of the round.

        Each part is shown only when the map declares the matching information,
        and when none is available there is no label at all rather than a fake
        one: `None` is returned and the right-hand side of the bar stays empty.
        In particular the rescue count is left out when there is no rescue
        center or no wounded person: `3/0 wounded` says nothing.

        A non-positive limit yields a zeroed counter rather than a division by
        zero. This is only reachable for a map that declares an explicit limit
        of 0: no limit at all is `None`, handled above.

        Args:
            elapsed_timestep (int): Steps already simulated.
            max_timestep_limit (Optional[int]): Steps the round is allowed to
                run for, or None when the map declares no limit.
            elapsed_walltime (float): Real seconds elapsed since the start.
            max_walltime_limit (Optional[int]): Real seconds the round is
                allowed to run for, or None when the map declares no limit.
            rescued_number (Optional[int]): Wounded persons rescued so far, or
                None when the rescue count must not be shown.
            total_wounded_persons (Optional[int]): Wounded persons to rescue,
                or None when the rescue count must not be shown.

        Returns:
            Optional[str]: The formatted label, e.g.
            ``"12.5 % (50/400 timesteps) - 12s/600s - 3/7 wounded"``, or None
            when there is nothing to show.
        """
        parts = []

        if max_timestep_limit is not None:
            limit = int(max_timestep_limit)
            if limit <= 0:
                parts.append("0.0 % (0/0 timesteps)")
            else:
                elapsed = max(0, int(elapsed_timestep))
                # Clamped because the counter is incremented before the limit
                # is checked, so a round stopped by the limit can land one step
                # over it.
                percentage = min(100.0, 100.0 * elapsed / limit)
                parts.append("{:.1f} % ({}/{} timesteps)".format(
                    percentage, elapsed, limit))

        if max_walltime_limit is not None:
            walltime_limit = max(0, int(max_walltime_limit))
            walltime = max(0.0, float(elapsed_walltime))
            # Same reasoning as for the steps: the wall clock is read before
            # the limit is checked, so clamp to what the limit allows.
            walltime = min(walltime, float(walltime_limit))
            parts.append("{:.0f}s/{}s".format(walltime, walltime_limit))

        # No rescue center or nobody to rescue means the counter has no
        # meaning: both are needed for the `rescued/total` reading.
        if (total_wounded_persons is not None
                and total_wounded_persons > 0
                and rescued_number is not None):
            rescued = max(0, min(int(rescued_number),
                                 int(total_wounded_persons)))
            parts.append("{}/{} wounded".format(rescued,
                                                int(total_wounded_persons)))

        if not parts:
            return None

        return " - ".join(parts)

    def draw(self,
             window: arcade.Window,
             elapsed_timestep: int,
             max_timestep_limit: Optional[int],
             elapsed_walltime: float = 0.0,
             max_walltime_limit: Optional[int] = None,
             rescued_number: Optional[int] = None,
             total_wounded_persons: Optional[int] = None) -> None:
        """
        Draw the bar over the whole window.

        Args:
            window (arcade.Window): The window to paint on.
            elapsed_timestep (int): Steps already simulated.
            max_timestep_limit (Optional[int]): Steps the round is allowed to
                run for, or None when the map declares no limit. That part of
                the right-hand label is then omitted.
            elapsed_walltime (float): Real seconds elapsed since the start.
            max_walltime_limit (Optional[int]): Real seconds the round is
                allowed to run for, or None when the map declares no limit.
                That part of the right-hand label is then omitted.
            rescued_number (Optional[int]): Wounded persons rescued so far, or
                None when the rescue count must not be shown.
            total_wounded_persons (Optional[int]): Wounded persons to rescue,
                or None when the rescue count must not be shown.
        """
        # Nothing to paint into a degenerate window (width or height 0), and
        # nothing sensible to say about the round in a window that small: the
        # labels would not fit in the band anyway.
        if self._height <= 0:
            return

        width = int(window.width)
        height = int(window.height)
        if width <= 0 or height <= 0:
            return

        # Clamped by `effective_height`, so a window too short to hold both the band
        # and the map keeps the map. That is the same number `GuiSR` reserves,
        # which is what makes "the band hides nothing" true by construction.
        bar_height = self.effective_height(height)
        if bar_height <= 0:
            return

        projector = self._window_projector(window)
        # The band spans the full width, at the top of the window. In the
        # corner-anchored projection the top edge is y == height.
        with projector.activate(), _scissor_disabled():
            arcade.draw_lrbt_rectangle_filled(
                left=0.0,
                right=float(width),
                bottom=float(height - bar_height),
                top=float(height),
                color=self._background_color,
            )
            self._draw_labels(width, height, bar_height,
                              elapsed_timestep, max_timestep_limit,
                              elapsed_walltime, max_walltime_limit,
                              rescued_number, total_wounded_persons)

    def _window_projector(self, window: arcade.Window) -> ViewportProjector:
        """
        Return the projector mapping the bar to the window, creating it once.

        The viewport is refreshed on every call because the user can resize the
        window at any moment, and the projection matrix is derived from it.

        Args:
            window (arcade.Window): The window the bar is drawn into.

        Returns:
            ViewportProjector: A projector over the whole window.
        """
        if self._projector is None:
            projector = ViewportProjector(context=window.ctx)
            self._projector = projector
        else:
            projector = self._projector

        projector.viewport = LBWH(0, 0, int(window.width),
                                  int(window.height))
        return projector

    def _draw_labels(self,
                     width: int,
                     height: int,
                     bar_height: int,
                     elapsed_timestep: int,
                     max_timestep_limit: Optional[int],
                     elapsed_walltime: float,
                     max_walltime_limit: Optional[int],
                     rescued_number: Optional[int],
                     total_wounded_persons: Optional[int]) -> None:
        """
        Draw the map name on the left and the round progress on the right.

        Args:
            width (int): Window width in pixels.
            height (int): Window height in pixels.
            bar_height (int): Thickness actually used for the band.
            elapsed_timestep (int): Steps already simulated.
            max_timestep_limit (Optional[int]): Steps the round is allowed to
                run for, or None when the map declares no limit. That part of
                the right-hand label is then omitted.
            elapsed_walltime (float): Real seconds elapsed since the start.
            max_walltime_limit (Optional[int]): Real seconds the round is
                allowed to run for, or None when the map declares no limit.
                That part of the right-hand label is then omitted.
            rescued_number (Optional[int]): Wounded persons rescued so far, or
                None when the rescue count must not be shown.
            total_wounded_persons (Optional[int]): Wounded persons to rescue,
                or None when the rescue count must not be shown.
        """
        center_y = height - bar_height / 2.0

        if self._labels_window_size != (width, height):
            self._build_labels(width, center_y)
            self._labels_window_size = (width, height)

        if self._left_text is not None:
            self._left_text.draw()

        if self._right_text is None:
            return

        right_label = self.progress_label(elapsed_timestep, max_timestep_limit,
                                          elapsed_walltime, max_walltime_limit,
                                          rescued_number, total_wounded_persons)
        # Nothing to report: leave the right-hand side of the bar empty. The
        # text is cleared rather than merely skipped, so a label left over from
        # an earlier draw cannot linger.
        if right_label is None:
            if self._last_right_label is not None:
                self._right_text.text = ""
                self._last_right_label = None
            return

        # Only touch the label when the text changed: assigning it goes through
        # a pyglet label update, which re-lays out the glyphs.
        if right_label != self._last_right_label:
            self._right_text.text = right_label
            self._last_right_label = right_label

        self._right_text.draw()

    def _build_labels(self,
                      width: int,
                      center_y: float) -> None:
        """
        Create both labels for the current window width.

        The right label is anchored to the right edge rather than positioned at
        a fixed x, so widening the window moves the text with the edge instead
        of leaving it stranded mid-bar.

        Args:
            width (int): Window width in pixels.
            center_y (float): Vertical center of the band, in window pixels.
        """
        self._left_text = arcade.Text(
            text=self._map_name,
            x=float(self._padding),
            y=center_y,
            color=self._text_color,
            font_size=self._font_size,
            anchor_x="left",
            anchor_y="center",
        )

        self._right_text = arcade.Text(
            text="",
            x=float(width - self._padding),
            y=center_y,
            color=self._text_color,
            font_size=self._font_size,
            anchor_x="right",
            anchor_y="center",
        )
        # Force the progress label to be written on the next draw: the fresh
        # right label holds an empty string, whatever was shown before.
        self._last_right_label = None


@contextmanager
def _scissor_disabled() -> Generator[None, None, None]:
    """
    Turn the scissor test off for the duration of a window-space drawing.

    `GuiSR` keeps the scissor box aligned with the camera viewport, which is
    the letterboxed map area and generally smaller than the window. The bar
    spans the whole window, so without this it would be clipped to that area --
    losing its ends, or disappearing entirely on a letterboxed window.

    The state is restored on exit: the window wants its scissor, and arcade
    re-applies it on the next `camera.use()` anyway.
    """
    was_enabled = bool(glIsEnabled(GL_SCISSOR_TEST))

    if was_enabled:
        glDisable(GL_SCISSOR_TEST)

    try:
        yield
    finally:
        if was_enabled:
            glEnable(GL_SCISSOR_TEST)
