import math
from collections import deque
from typing import Tuple, List, Dict, Union, Deque

import arcade

from swarm_rescue.simulation.drone.drone_abstract import DroneAbstract


def _draw_pseudo_drone(position_screen: Tuple[int, int, float],
                       color: Union[Tuple[int, int, int], Tuple[int, int, int, int]],
                       radius: int = 15) -> None:
    """
    Drawing a pseudo drone on the screen.
    It takes the screen position of the drone, the color of the drone, and the
    radius as inputs, and uses the arcade library to draw the drone on the
    screen : a colored circle with a black outline and a line inside the circle
    that shows the orientation of the drone.
    This function is used to display the noisy position of the drone.

    Args:
        position_screen (Tuple[int, int, float]): (x, y, angle) screen position.
        color (Tuple[int, int, int] or Tuple[int, int, int, int]): RGB or RGBA color.
        radius (int): Radius of the drone.
    """

    if not isinstance(position_screen, tuple) or len(position_screen) != 3:
        raise ValueError("position_screen must be a tuple of length 3")
    if not isinstance(color, tuple) or len(color) not in (3, 4):
        raise ValueError("color must be a tuple of length 3 or 4 (RGB or RGBA)")
    if radius <= 0:
        raise ValueError("Radius must be a positive number.")

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
    """
    Visualization tool for displaying noisy and true positions of drones.

    Args:
        playground_size (Tuple[int, int]): Size of the playground.
        drones (List[DroneAbstract]): List of drones to visualize.
    """

    def __init__(self, playground_size: Tuple[int, int],
                 drones: List[DroneAbstract]):
        self._playground_size = playground_size
        self._drones = drones
        self._half_playground_size: Tuple[float, float] = (playground_size[0] / 2,
                                                           playground_size[1] / 2)

        self._scr_pos_gps: Dict[DroneAbstract, Tuple[int, int, float]] = {}
        self._gps_enabled: Dict[DroneAbstract, bool] = {}
        self._scr_pos_odom: Dict[DroneAbstract, Deque[Tuple[int, int, float]]] = {}
        self._last_world_pos_odom: Dict[DroneAbstract, Tuple[float, float, float]] = {}
        self._scr_pos_true: Dict[DroneAbstract, Deque[Tuple[float, float, float]]] = {}
        self._max_size_circular_buffer = 150

    def reset(self) -> None:
        """
        Reset the state of the VisuNoises object.
        By clearing all the dictionaries that store the
        screen positions and other data related to the drones.
        """
        self._scr_pos_gps.clear()
        self._gps_enabled.clear()
        self._scr_pos_odom.clear()
        self._last_world_pos_odom.clear()
        self._scr_pos_true.clear()

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
        if drone not in self._scr_pos_gps:
            return
        pos_screen = self._scr_pos_gps[drone]
        enabled = self._gps_enabled[drone]
        if enabled:
            _draw_pseudo_drone(position_screen=pos_screen,
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
        if not self._scr_pos_odom:
            return
        if drone not in self._scr_pos_odom:
            return

        last_pos_screen = self._scr_pos_odom[drone][-1]
        _draw_pseudo_drone(position_screen=last_pos_screen,
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
        if not self._scr_pos_odom:
            return
        if drone not in self._scr_pos_odom:
            return

        point_list = []
        for pos_screen in self._scr_pos_odom[drone]:
            point_list.append((pos_screen[0], pos_screen[1]))

        arcade.draw_line_strip(point_list=point_list, color=arcade.color.RED)

    def _draw_true_path(self, drone: DroneAbstract) -> None:
        """
        Draw the true path of a drone.
        """
        if not self._scr_pos_true:
            return
        if drone not in self._scr_pos_true:
            return

        point_list = []
        for pos_screen in self._scr_pos_true[drone]:
            point_list.append((pos_screen[0], pos_screen[1]))

        arcade.draw_line_strip(point_list=point_list, color=arcade.color.BLACK)

    def update(self, enable: bool = True) -> None:
        """
        Update the visualization state with current drone positions.

        Args:
            enable (bool): Whether to update.
        """
        if not enable:
            return

        if not self._scr_pos_true:
            self._scr_pos_true = \
                {None: deque(maxlen=self._max_size_circular_buffer)}

        for drone in self._drones:
            # GPS
            self._gps_enabled[drone] = False
            if (not drone.gps_is_disabled()
                    and not drone.compass_is_disabled()):
                pos = self.conv_world2screen(
                    pos_world=drone.measured_gps_position(),
                    angle=drone.measured_compass_angle())
                self._scr_pos_gps[drone] = pos
                self._gps_enabled[drone] = True

            # TRUE VALUES
            true_position = drone.true_position()
            true_angle = drone.true_angle()
            if true_position is not None:
                pos = self.conv_world2screen(
                    pos_world=true_position, angle=true_angle)
                if drone in self._scr_pos_true:
                    self._scr_pos_true[drone].append(pos)
                else:
                    self._scr_pos_true[drone] = (
                        deque([pos], maxlen=self._max_size_circular_buffer))

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
                new_pos_odom_screen = (
                    self.conv_world2screen(pos_world=(new_x, new_y),
                                           angle=new_orient))
                self._scr_pos_odom[drone].append(new_pos_odom_screen)
            else:
                x, y = tuple(drone.true_position())
                orient = drone.true_angle()
                self._last_world_pos_odom[drone] = (x, y, orient)
                new_pos_odom_screen = (
                    self.conv_world2screen(pos_world=(x, y), angle=orient))
                self._scr_pos_odom[drone] = (
                    deque([new_pos_odom_screen],
                          maxlen=self._max_size_circular_buffer))

    def conv_world2screen(self, pos_world: Tuple[float, float], angle: float) -> Tuple[int, int, float]:
        """
        Convert world coordinates to screen coordinates.

        Args:
            pos_world (Tuple[float, float]): World position.
            angle (float): Orientation angle.

        Returns:
            Tuple[int, int, float]: Screen position and angle.
        """
        if (math.isnan(pos_world[0])
                or math.isnan(pos_world[1])
                or math.isnan(angle)):
            return float('NaN'), float('NaN'), float('NaN')
        x = int(pos_world[0] + self._half_playground_size[0])
        y = int(pos_world[1] + self._half_playground_size[1])
        alpha = angle
        pos_screen: Tuple[int, int, float] = (x, y, alpha)
        return pos_screen

    def conv_screen2world(self, pos_screen: Tuple[int, int]) -> Tuple[Tuple[float, float], float]:
        """
        Convert screen coordinates to world coordinates.

        Args:
            pos_screen (Tuple[int, int]): Screen position.

        Returns:
            Tuple[Tuple[float, float], float]: World position and angle.
        """
        if math.isnan(pos_screen[0]) or math.isnan(pos_screen[1]):
            return float('NaN'), float('NaN'), float('NaN')
        x = float(pos_screen[0] - self._half_playground_size[0])
        y = float(pos_screen[1] - self._half_playground_size[1])
        angle = pos_screen[2]
        pos_world: Tuple[float, float] = (x, y)
        return pos_world, angle