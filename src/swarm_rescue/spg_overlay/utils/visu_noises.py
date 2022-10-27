import math
import arcade
from typing import Tuple, List, Dict
from collections import deque
from spg_overlay.entities.drone_abstract import DroneAbstract


def _draw_pseudo_drone(position_screen: Tuple[int, int, float],
                       color: Tuple[int, int, int],
                       radius=15):
    length_line = 2 * radius
    arcade.draw_circle_filled(position_screen[0],
                              position_screen[1],
                              radius=radius,
                              color=color)
    arcade.draw_circle_outline(position_screen[0],
                               position_screen[1],
                               radius=radius,
                               color=arcade.color.BLACK)
    angle = position_screen[2]
    end_x = position_screen[0] + length_line * math.cos(angle)
    end_y = position_screen[1] + length_line * math.sin(angle)
    arcade.draw_line(position_screen[0],
                     position_screen[1],
                     end_x,
                     end_y,
                     color=arcade.color.BLACK)


class VisuNoises:
    def __init__(self, playground_size: Tuple[int, int], drones: [List[DroneAbstract]]):
        self._playground_size = playground_size
        self._drones = drones
        self._half_playground_size: Tuple[float, float] = (playground_size[0] / 2,
                                                           playground_size[1] / 2)

        self._scr_pos_gps: Dict[DroneAbstract, Tuple[int, int, float]] = {}
        self._scr_pos_odom: Dict[DroneAbstract, deque[Tuple[int, int, float]]] = {}
        self._last_world_pos_odom: Dict[DroneAbstract, Tuple[float, float, float]] = {}
        self._scr_pos_true: Dict[DroneAbstract, deque[Tuple[float, float, float]]] = {}
        self._max_size_circular_buffer = 150

    def reset(self):
        self._scr_pos_gps.clear()
        self._scr_pos_odom.clear()
        self._last_world_pos_odom.clear()
        self._scr_pos_true.clear()

    def draw(self, enable: bool = True):
        if not enable:
            return

        self._draw_gps_compass()

        for drone in self._drones:
            self._draw_odom(drone)

        for drone in self._drones:
            self._draw_true(drone)

    def _draw_gps_compass(self):
        for pos_screen in self._scr_pos_gps.values():
            _draw_pseudo_drone(position_screen=pos_screen, color=arcade.color.GREEN)

    def _draw_odom(self, drone: DroneAbstract, enable: bool = True):
        if not enable:
            return
        if not self._scr_pos_odom:
            return
        if drone not in self._scr_pos_odom:
            return

        prev_pos_screen = None
        for pos_screen in self._scr_pos_odom[drone]:
            if prev_pos_screen is not None:
                arcade.draw_line(pos_screen[0],
                                 pos_screen[1],
                                 prev_pos_screen[0],
                                 prev_pos_screen[1],
                                 color=arcade.color.RED)
            prev_pos_screen = pos_screen

        last_pos_screen = self._scr_pos_odom[drone][-1]
        _draw_pseudo_drone(position_screen=last_pos_screen, color=arcade.color.RED)

    def _draw_true(self, drone: DroneAbstract):
        if not self._scr_pos_true:
            return
        if drone not in self._scr_pos_true:
            return

        prev_pos_screen = None
        for pos_screen in self._scr_pos_true[drone]:
            if prev_pos_screen is not None:
                arcade.draw_line(pos_screen[0],
                                 pos_screen[1],
                                 prev_pos_screen[0],
                                 prev_pos_screen[1],
                                 color=arcade.color.BLACK)
            prev_pos_screen = pos_screen

    def update(self, enable: bool = True):
        if not enable:
            return

        if not self._scr_pos_true:
            self._scr_pos_true = {None: deque(maxlen=self._max_size_circular_buffer)}

        for drone in self._drones:
            # GPS
            if not drone.gps_is_disabled() and not drone.compass_is_disabled():
                pos = self.conv_world2screen(pos_world=drone.measured_gps_position(),
                                             angle=drone.measured_compass_angle())
                self._scr_pos_gps[drone] = pos

            # TRUE VALUES
            true_position = drone.true_position()
            true_angle = drone.true_angle()
            if true_position and true_angle:
                pos = self.conv_world2screen(pos_world=true_position, angle=true_angle)
                if drone in self._scr_pos_true:
                    self._scr_pos_true[drone].append(pos)
                else:
                    self._scr_pos_true[drone] = deque([pos], maxlen=self._max_size_circular_buffer)

            # ODOMETER
            dist, alpha, theta = (0.0, 0.0, 0.0)
            if not drone.odometer_is_disabled():
                dist, alpha, theta = tuple(drone.odometer_values())
            if drone in self._last_world_pos_odom:
                x, y, orient = self._last_world_pos_odom[drone]
                new_x = x + dist * math.cos(alpha + orient)
                new_y = y + dist * math.sin(alpha + orient)
                new_orient = orient + theta

                self._last_world_pos_odom[drone] = (new_x, new_y, new_orient)
                new_pos_odom_screen = self.conv_world2screen(pos_world=(new_x, new_y),
                                                             angle=new_orient)
                self._scr_pos_odom[drone].append(new_pos_odom_screen)
            else:
                x, y = tuple(drone.true_position())
                orient = drone.true_angle()
                self._last_world_pos_odom[drone] = (x, y, orient)
                new_pos_odom_screen = self.conv_world2screen(pos_world=(x, y), angle=orient)
                self._scr_pos_odom[drone] = deque([new_pos_odom_screen],
                                                  maxlen=self._max_size_circular_buffer)

    def conv_world2screen(self, pos_world: Tuple[float, float], angle: float):
        if math.isnan(pos_world[0]) or math.isnan(pos_world[1]) or math.isnan(angle):
            return float('NaN'), float('NaN'), float('NaN')
        x = int(pos_world[0] + self._half_playground_size[0])
        y = int(pos_world[1] + self._half_playground_size[1])
        alpha = angle
        pos_screen: Tuple[int, int, float] = (x, y, alpha)
        return pos_screen

    def conv_screen2world(self, pos_screen: Tuple[int, int]):
        if math.isnan(pos_screen[0]) or math.isnan(pos_screen[1]):
            return float('NaN'), float('NaN'), float('NaN')
        x = float(pos_screen[0] - self._half_playground_size[0])
        y = float(pos_screen[1] - self._half_playground_size[1])
        angle = pos_screen[2]
        pos_world: Tuple[float, float] = (x, y)
        return pos_world, angle
