import math
from typing import Callable, Tuple

import arcade

# A function taking window pixel coordinates and returning world coordinates.
# Supplied by the view, which owns the camera: this module has no way to know
# the zoom, the viewport or where the camera is centered.
ScreenToWorld = Callable[[Tuple[float, float]], Tuple[float, float]]


class MouseMeasure:
    """
    The MouseMeasure class is a tool for measuring and visualizing mouse
    movements and clicks on a playground.
    By selecting a zone with the mouse, it draws the  zone rectangle, and the
    middle circle.
    It calculates the distance and delta values between mouse clicks.
    Used in GuiSR class.

    The mouse callbacks give window pixels, not world coordinates. Converting
    them is the camera's job (`Camera2D.unproject` in arcade 3.x)

    Attributes:
        x_mouse_pix (float): Current x-coordinate of the mouse, in pixel units.
        y_mouse_pix (float): Current y-coordinate of the mouse, in pixel units.
        x_mouse (float): Current x-coordinate of the mouse, in world units.
        y_mouse (float): Current y-coordinate of the mouse, in world units.
        x_mouse_prev (float): Previous x-coordinate of the mouse, in world units.
        y_mouse_prev (float): Previous y-coordinate of the mouse, in world units.
        draw_line (bool): Flag indicating whether to draw a line or not.
        _screen_to_world (ScreenToWorld): Converts window pixels to world units.
    """

    def __init__(self, screen_to_world: ScreenToWorld):
        """
        Initialize MouseMeasure.

        Args:
            screen_to_world (ScreenToWorld): Converts a window pixel position
                into world coordinates, normally `camera.unproject`.

        Raises:
            ValueError: If `screen_to_world` is not callable.
        """
        if not callable(screen_to_world):
            raise ValueError(
                "MouseMeasure needs a screen_to_world function -- normally "
                "the view's camera.unproject. Without it, the measured "
                "positions would be wrong by an amount that changes with the "
                "window size."
            )
        self.x_mouse_pix = 0
        self.y_mouse_pix = 0
        self.x_mouse = 0.0
        self.y_mouse = 0.0
        self.x_mouse_prev = 0.0
        self.y_mouse_prev = 0.0
        self.draw_line = False

        self._screen_to_world = screen_to_world

    def _to_world(self, x: int, y: int) -> Tuple[float, float]:
        """
        Convert a window pixel position into world coordinates.

        Args:
            x (int): X position, in window pixels.
            y (int): Y position, in window pixels.

        Returns:
            Tuple of world coordinates.
        """
        return self._screen_to_world((float(x), float(y)))

    def draw(self, enable: bool = True):
        """
        Draw the measurement graphics if enabled.

        Args:
            enable (bool): Whether to draw.
        """
        if enable and self.draw_line:
            arcade.draw_line(self.x_mouse, self.y_mouse,
                             self.x_mouse_prev, self.y_mouse_prev,
                             arcade.color.BITTER_LEMON, 3)
            left = min(self.x_mouse, self.x_mouse_prev)
            right = max(self.x_mouse, self.x_mouse_prev)
            top = max(self.y_mouse, self.y_mouse_prev)
            bottom = min(self.y_mouse, self.y_mouse_prev)
            arcade.draw_lrbt_rectangle_outline(left=left, right=right,
                                               top=top, bottom=bottom,
                                               color=arcade.color.BITTER_LIME,
                                               border_width=3)
            center_x = 0.5 * (left + right)
            center_y = 0.5 * (top + bottom)
            arcade.draw_circle_filled(center_x=center_x,
                                      center_y=center_y,
                                      radius=5,
                                      color=arcade.color.BITTER_LIME)

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        """
        Called whenever the mouse moves.

        Args:
            x (int): X position, in window pixels.
            y (int): Y position, in window pixels.
            dx (int): Change in X.
            dy (int): Change in Y.
        """
        self.x_mouse, self.y_mouse = self._to_world(x, y)

    # Creating function to check the mouse clicks
    def on_mouse_press(self, x: int, y: int, button: int, enable: bool = True):
        """
        Called when the mouse button is pressed.

        Args:
            x (int): X position, in window pixels.
            y (int): Y position, in window pixels.
            button (int): Mouse button.
            enable (bool): Whether to enable measurement.
        """
        self.x_mouse_pix = x
        self.y_mouse_pix = y
        self.x_mouse, self.y_mouse = self._to_world(x, y)

        if enable and button == arcade.MOUSE_BUTTON_LEFT:
            if not self.draw_line:
                self.x_mouse_prev = self.x_mouse
                self.y_mouse_prev = self.y_mouse
                self.draw_line = True

            print("---------------------------------------------")
            print("World position: ({}, {})".format(round(self.x_mouse),
                                                   round(self.y_mouse)))
            print("Screen position: ({}, {})".format(self.x_mouse_pix, self.y_mouse_pix))

    def on_mouse_release(self, x: int, y: int,
                         button: int, enable: bool = True):
        """
        Called when the mouse button is released.

        Args:
            x (int): X position, in window pixels.
            y (int): Y position, in window pixels.
            button (int): Mouse button.
            enable (bool): Whether to enable measurement.
        """
        if enable and button == arcade.MOUSE_BUTTON_LEFT:
            dx = self.x_mouse - self.x_mouse_prev
            dy = self.y_mouse - self.y_mouse_prev
            distance = round(math.sqrt(dx * dx + dy * dy), 1)
            if distance > 5:
                delta_x = round(abs(dx))
                delta_y = round(abs(dy))
                print("---------------------------------------------")
                print("distance = {} pixels".format(distance))
                print("delta_x = {}, delta_y = {}   OR   size=({}, {})"
                      .format(delta_x, delta_y, delta_x, delta_y))

                c_x = 0.5 * (self.x_mouse + self.x_mouse_prev)
                c_y = 0.5 * (self.y_mouse + self.y_mouse_prev)
                center_x = round(c_x)
                center_y = round(c_y)

                tl_x = min(self.x_mouse, self.x_mouse_prev)
                tl_y = max(self.y_mouse, self.y_mouse_prev)
                top_left_x = round(tl_x)
                top_left_y = round(tl_y)

                br_x = max(self.x_mouse, self.x_mouse_prev)
                br_y = min(self.y_mouse, self.y_mouse_prev)
                bottom_right_x = round(br_x)
                bottom_right_y = round(br_y)

                print("center_x = {}, center_y = {}  OR   center=({}, {})"
                      .format(center_x, center_y, center_x, center_y))
                print("top_left_x = {}, top_left_y = {}  OR   top_left=({}, {})"
                      .format(top_left_x, top_left_y, top_left_x, top_left_y))
                print("bottom_right_x = {}, bottom_right_y = {}  OR   bottom_right=({}, {})"
                      .format(bottom_right_x, bottom_right_y, bottom_right_x, bottom_right_y))

            self.x_mouse_prev = self.x_mouse
            self.y_mouse_prev = self.y_mouse
            self.draw_line = False
