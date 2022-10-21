import math
import arcade
from typing import Tuple


class MouseMeasure:
    def __init__(self, playground_size: Tuple[int, int]):
        self.x_mouse = 0
        self.y_mouse = 0
        self.x_mouse_prev = 0
        self.y_mouse_prev = 0
        self.draw_line = False

        self._playground_size = playground_size

    def draw(self, enable: bool = True):
        if enable and self.draw_line:
            arcade.draw_line(self.x_mouse, self.y_mouse,
                             self.x_mouse_prev, self.y_mouse_prev,
                             arcade.color.GREEN, 3)

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        """
        Called whenever the mouse moves.
        """
        self.x_mouse = x
        self.y_mouse = y

    # Creating function to check the mouse clicks
    def on_mouse_press(self, x: int, y: int, button: int, enable: bool = True):
        self.x_mouse = x
        self.y_mouse = y
        if enable and button == arcade.MOUSE_BUTTON_LEFT:
            if not self.draw_line:
                self.x_mouse_prev = self.x_mouse
                self.y_mouse_prev = self.y_mouse
                self.draw_line = True

            x_pix = int(self.x_mouse - self._playground_size[0] / 2)
            y_pix = int(self.y_mouse - self._playground_size[1] / 2)
            print("Pixel position: ({}, {})".format(x_pix, y_pix))

    def on_mouse_release(self, x: int, y: int, button: int, enable: bool = True):
        if enable and button == arcade.MOUSE_BUTTON_LEFT:
            dx = self.x_mouse - self.x_mouse_prev
            dy = self.y_mouse - self.y_mouse_prev
            distance = round(math.sqrt(dx * dx + dy * dy), 1)
            if distance > 5:
                print("Distance: {:.1f} pixels".format(distance))

            self.x_mouse_prev = self.x_mouse
            self.y_mouse_prev = self.y_mouse
            self.draw_line = False
