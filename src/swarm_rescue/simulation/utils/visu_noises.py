import math
from collections import deque
from typing import Tuple, List, Dict, Union, Deque

import arcade

from swarm_rescue.simulation.drone.drone_abstract import DroneAbstract


def _draw_pseudo_drone(position: Tuple[float, float, float],
                       color: Union[Tuple[int, int, int], Tuple[int, int, int, int]],
                       radius: int = 15) -> None:
    """
    Drawing a pseudo drone on the screen.
    It takes the position of the drone, the color of the drone, and the
    radius as inputs, and uses the arcade library to draw the drone on the
    screen: a colored circle with a black outline and a line inside the circle
    that shows the orientation of the drone.
    This function is used to display the noisy position of the drone.

    Args:
        position (Tuple[int, int, float]): (x, y, angle) position.
        color (Tuple[int, int, int] or Tuple[int, int, int, int]): RGB or RGBA color.
        radius (int): Radius of the drone.
    """

    if not isinstance(position, tuple) or len(position) != 3:
        raise ValueError("position must be a tuple of length 3")
    if not isinstance(color, tuple) or len(color) not in (3, 4):
        raise ValueError("color must be a tuple of length 3 or 4 (RGB or RGBA)")
    if radius <= 0:
        raise ValueError("Radius must be a positive number.")

    length_line = 2 * radius
    arcade.draw_circle_filled(position[0],
                              position[1],
                              radius=radius,
                              color=color)
    arcade.draw_circle_outline(position[0],
                               position[1],
                               radius=radius,
                               color=arcade.color.BLACK)
    angle = position[2]
    end_x = position[0] + length_line * math.cos(angle)
    end_y = position[1] + length_line * math.sin(angle)
    arcade.draw_line(position[0],
                     position[1],
                     end_x,
                     end_y,
                     color=arcade.color.BLACK)


class VisuNoises:
    """
    Visualization tool for displaying noisy and true positions of drones.

    Args:
        playground_size (Tuple[int, int]): Retained for compatibility; positions
            are already in the coordinate system used for drawing.
        drones (List[DroneAbstract]): List of drones to visualize.
    """

    def __init__(self, playground_size: Tuple[int, int],
                 drones: List[DroneAbstract]):
        self._drones = drones

        self._pos_gps: Dict[DroneAbstract, Tuple[float, float, float]] = {}
        self._pos_odom: Dict[DroneAbstract, Deque[Tuple[float, float, float]]] = {}
        self._last_pos_odom: Dict[DroneAbstract, Tuple[float, float, float]] = {}
        self._pos_true: Dict[DroneAbstract, Deque[Tuple[float, float, float]]] = {}
        self._max_size_circular_buffer = 150

    def reset(self) -> None:
        """
        Reset the state of the VisuNoises object.
        By clearing all the dictionaries that store the
        positions and other data related to the drones.
        """
        self._pos_gps.clear()
        self._pos_odom.clear()
        self._last_pos_odom.clear()
        self._pos_true.clear()

    def draw(self, enable: bool = True) -> None:
        """
        Draw all noisy and true drone positions and paths.

        Args:
            enable (bool): Whether to draw.
        """
        if not enable:
            return

        for drone in self._drones:
            self._draw_gps_compass_position(drone)

        for drone in self._drones:
            self._draw_odom_path(drone, enable=True)
            self._draw_odom_position(drone, enable=True)

        for drone in self._drones:
            self._draw_true_path(drone)

    def _draw_gps_compass_position(self, drone: DroneAbstract) -> None:
        """
        Draw the GPS/compass position of a drone.
        """
        if drone not in self._pos_gps:
            return
        _draw_pseudo_drone(position=self._pos_gps[drone],
                           color=arcade.color.GREEN)

    def _draw_odom_position(self, drone: DroneAbstract, enable: bool = True) -> None:
        """
        Draw the odometry position of a drone.

        Args:
            drone (DroneAbstract): The drone.
            enable (bool): Whether to draw.
        """
        if not enable:
            return
        if drone not in self._pos_odom:
            return

        _draw_pseudo_drone(position=self._pos_odom[drone][-1],
                           color=arcade.color.RED)

    def _draw_odom_path(self, drone: DroneAbstract, enable: bool = True):
        """
        Draw the odometry path of a drone.
        This trajectory may drift and not correspond at all to reality.

        Args:
            drone (DroneAbstract): The drone.
            enable (bool): Whether to draw.
        """
        if not enable:
            return
        if drone not in self._pos_odom:
            return

        points = [(x, y) for x, y, _ in self._pos_odom[drone]]
        arcade.draw_line_strip(point_list=points, color=arcade.color.RED)

    def _draw_true_path(self, drone: DroneAbstract) -> None:
        """
        Draw the true path of a drone.
        """
        if drone not in self._pos_true:
            return

        points = [(x, y) for x, y, _ in self._pos_true[drone]]
        arcade.draw_line_strip(point_list=points, color=arcade.color.BLACK)

    def update(self, enable: bool = True) -> None:
        """
        Update the visualization state with current drone positions.

        Args:
            enable (bool): Whether to update.
        """
        if not enable:
            return

        for drone in self._drones:
            # GPS
            if (not drone.gps_is_disabled()
                    and not drone.compass_is_disabled()):
                gps_position = drone.measured_gps_position()
                if gps_position is None:
                    self._pos_gps.pop(drone, None)
                    continue
                x, y = gps_position
                angle = drone.measured_compass_angle()
                self._pos_gps[drone] = (x, y, angle)
            else:
                self._pos_gps.pop(drone, None)

            # TRUE VALUES
            true_position = drone.true_position()
            true_angle = drone.true_angle()
            if true_position is not None:
                true_point = (true_position[0], true_position[1], true_angle)
                if drone in self._pos_true:
                    self._pos_true[drone].append(true_point)
                else:
                    self._pos_true[drone] = deque(
                        [true_point], maxlen=self._max_size_circular_buffer)

            # ODOMETER
            dist, alpha, theta = (0.0, 0.0, 0.0)
            if not drone.odometer_is_disabled():
                dist, alpha, theta = tuple(drone.odometer_values())
            if drone in self._last_pos_odom:
                x, y, orient = self._last_pos_odom[drone]
                new_x = x + dist * math.cos(alpha + orient)
                new_y = y + dist * math.sin(alpha + orient)
                new_orient = orient + theta

                self._last_pos_odom[drone] = (new_x, new_y, new_orient)
                self._pos_odom[drone].append((new_x, new_y, new_orient))
            else:
                x, y = tuple(drone.true_position())
                orient = drone.true_angle()
                self._last_pos_odom[drone] = (x, y, orient)
                self._pos_odom[drone] = deque(
                    [(x, y, orient)], maxlen=self._max_size_circular_buffer)
