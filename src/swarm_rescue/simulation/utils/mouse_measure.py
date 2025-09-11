import math
from typing import Tuple

import arcade


class MouseMeasure:
    """
    The MouseMeasure class is a tool for measuring and visualizing mouse
    movements and clicks on a playground.
    By selecting a zone with the mouse, it draws the  zone rectangle, and the
    middle circle.
    It calculates the distance and delta values between mouse clicks.
    Used in GuiSR class.

    Attributes:
        x_mouse (int): Current x-coordinate of the mouse.
        y_mouse (int): Current y-coordinate of the mouse.
        x_mouse_prev (int): Previous x-coordinate of the mouse.
        y_mouse_prev (int): Previous y-coordinate of the mouse.
        draw_line (bool): Flag indicating whether to draw a line or not.
        _playground_size (Tuple[int, int]): Size of the playground.
    """

    def __init__(self, playground_size: Tuple[int, int]):
        """
        Initialize MouseMeasure.

        Args:
            playground_size (Tuple[int, int]): Size of the playground.
        """
        self.x_mouse = 0
        self.y_mouse = 0
        self.x_mouse_prev = 0
        self.y_mouse_prev = 0
        self.draw_line = False

        self._playground_size = playground_size

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
            arcade.draw_lrtb_rectangle_outline(left=left, right=right,
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
            x (int): X position.
            y (int): Y position.
            dx (int): Change in X.
            dy (int): Change in Y.
        """
        self.x_mouse = x
        self.y_mouse = y

    # Creating function to check the mouse clicks
    def on_mouse_press(self, x: int, y: int, button: int, enable: bool = True):
        """
        Called when the mouse button is pressed.

        Args:
            x (int): X position.
            y (int): Y position.
            button (int): Mouse button.
            enable (bool): Whether to enable measurement.
        """
        self.x_mouse = x
        self.y_mouse = y
        if enable and button == arcade.MOUSE_BUTTON_LEFT:
            if not self.draw_line:
                self.x_mouse_prev = self.x_mouse
                self.y_mouse_prev = self.y_mouse
                self.draw_line = True

            x_pix = round(self.x_mouse - self._playground_size[0] / 2)
            y_pix = round(self.y_mouse - self._playground_size[1] / 2)
            print("---------------------------------------------")
            print("Pixel position: ({}, {})".format(x_pix, y_pix))

    def on_mouse_release(self, x: int, y: int,
                         button: int, enable: bool = True):
        """
        Called when the mouse button is released.

        Args:
            x (int): X position.
            y (int): Y position.
            button (int): Mouse button.
            enable (bool): Whether to enable measurement.
        """
        if enable and button == arcade.MOUSE_BUTTON_LEFT:
            dx = self.x_mouse - self.x_mouse_prev
            dy = self.y_mouse - self.y_mouse_prev
            distance = round(math.sqrt(dx * dx + dy * dy), 1)
            if distance > 5:
                print("---------------------------------------------")
                print("distance = {} pixels".format(distance))
                print("delta_x = {}, delta_y = {}   OR   size=({}, {})"
                      .format(abs(dx), abs(dy), abs(dx), abs(dy)))
                c_x = 0.5 * (self.x_mouse + self.x_mouse_prev)
                c_y = 0.5 * (self.y_mouse + self.y_mouse_prev)
                center_x = round(c_x - self._playground_size[0] / 2)
                center_y = round(c_y - self._playground_size[1] / 2)
                tl_x = min(self.x_mouse, self.x_mouse_prev)
                tl_y = max(self.y_mouse, self.y_mouse_prev)
                top_left_x = round(tl_x - self._playground_size[0] / 2)
                top_left_y = round(tl_y - self._playground_size[1] / 2)
                br_x = max(self.x_mouse, self.x_mouse_prev)
                br_y = min(self.y_mouse, self.y_mouse_prev)
                bottom_right_x = round(br_x - self._playground_size[0] / 2)
                bottom_right_y = round(br_y - self._playground_size[1] / 2)
                print("center_x = {}, center_y = {}  OR   center=({}, {})"
                      .format(center_x, center_y, center_x, center_y))
                print("top_left_x = {}, top_left_y = {}  OR   top_left=({}, {})"
                      .format(top_left_x, top_left_y, top_left_x, top_left_y))
                print("bottom_right_x = {}, bottom_right_y = {}  OR   bottom_right=({}, {})"
                      .format(bottom_right_x, bottom_right_y, bottom_right_x, bottom_right_y))

            self.x_mouse_prev = self.x_mouse
            self.y_mouse_prev = self.y_mouse
            self.draw_line = False
