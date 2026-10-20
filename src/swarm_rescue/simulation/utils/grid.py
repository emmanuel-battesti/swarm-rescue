import math
from typing import Tuple

import cv2
import numpy as np

from swarm_rescue.simulation.utils.pose import Pose


class Grid:
    """Simple grid for spatial representation and value accumulation."""

    def __init__(self,
                 size_area_world: tuple,
                 resolution: float):
        """
        Initialize the grid.

        Args:
            size_area_world (tuple): Size of the area in world units.
            resolution (float): Resolution of the grid.
        """
        self.size_area_world = size_area_world
        self.resolution = resolution

        self.x_max_grid: int = (
            int(self.size_area_world[0] / self.resolution + 0.5))
        self.y_max_grid: int = (
            int(self.size_area_world[1] / self.resolution + 0.5))

        self.grid = np.zeros((self.x_max_grid, self.y_max_grid))

    def _conv_world_to_grid(self, x_world, y_world):
        """
        Convert from world coordinates to map coordinates (i.e. cell index in
        the grid map).

        Args:
            x_world: X coordinate(s) in world units.
            y_world: Y coordinate(s) in world units.

        Returns:
            Tuple of grid indices.
        """

        x_grid = (x_world + self.size_area_world[0] / 2) / self.resolution
        y_grid = (-y_world + self.size_area_world[1] / 2) / self.resolution

        if isinstance(x_grid, float):
            x_grid = int(x_grid)
            y_grid = int(y_grid)
        elif isinstance(x_grid, np.ndarray):
            x_grid = x_grid.astype(int)
            y_grid = y_grid.astype(int)

        return x_grid, y_grid

    def _conv_grid_to_world(self, x_grid, y_grid):
        """
        Convert from map coordinates to world coordinates.

        Args:
            x_grid: X grid index or array.
            y_grid: Y grid index or array.

        Returns:
            Tuple of world coordinates.
        """
        if isinstance(x_grid, int):
            x_grid = float(x_grid)
            y_grid = float(y_grid)
        elif isinstance(x_grid, np.ndarray):
            x_grid = x_grid.astype(float)
            y_grid = y_grid.astype(float)

        x_world = -self.size_area_world[0] / 2 + x_grid * self.resolution
        y_world = self.size_area_world[1] / 2 - y_grid * self.resolution

        if isinstance(x_world, np.ndarray):
            x_world = x_world.astype(float)
            y_world = y_world.astype(float)

        return x_world, y_world

    def add_value_along_line(self, x_0: float, y_0: float, x_1: float,
                             y_1: float, val):
        """
        Add a value to a line of points using Bresenham algorithm, input in
        world coordinates.

        Args:
            x_0 (float): X of the starting point, in m.
            y_0 (float): Y of the starting point, in m.
            x_1 (float): X of the end point, in m.
            y_1 (float): Y of the end point, in m.
            val: Value to add to each cell of the line.
        """

        if (math.isnan(x_0) or
                math.isnan(y_0) or
                math.isnan(x_1) or
                math.isnan(y_1)):
            return

        # convert to pixels
        x_start, y_start = self._conv_world_to_grid(x_0, y_0)
        x_end, y_end = self._conv_world_to_grid(x_1, y_1)

        if (x_start < 0
                or x_start >= self.x_max_grid
                or y_start < 0
                or y_start >= self.y_max_grid):
            # print("add_value_along_line: warning ray exits 1")
            return

        if (x_end < 0
                or x_end >= self.x_max_grid
                or y_end < 0
                or y_end >= self.y_max_grid):
            # print("add_value_along_line: warning ray exits 2")
            return

        # Bresenham line drawing
        dx = x_end - x_start
        dy = y_end - y_start
        is_steep = abs(dy) > abs(dx)  # determine how steep the line is
        if is_steep: # rotate line
            x_start, y_start = y_start, x_start
            x_end, y_end = y_end, x_end
        # swap start and end points if necessary and store swap state
        if x_start > x_end:
            x_start, x_end = x_end, x_start
            y_start, y_end = y_end, y_start
        dx = x_end - x_start  # recalculate differentials
        dy = y_end - y_start  # recalculate differentials
        error = int(dx / 2.0)  # calculate error
        y_step = 1 if y_start < y_end else -1
        # iterate over bounding box generating points between start and end
        y = y_start
        points = []
        for x in range(x_start, x_end + 1):
            coord = [y, x] if is_steep else [x, y]
            points.append(coord)
            error -= abs(dy)
            if error < 0:
                y += y_step
                error += dx
        points = np.array(points).T

        # add value to the points
        self.grid[points[0], points[1]] += val

    def add_points(self, points_x, points_y, val):
        """
        Add a value to an array of points, input coordinates in meters.

        Args:
            points_x: X coordinates in m. A scalar, or an array of them.
            points_y: Y coordinates in m, matching `points_x`.
            val: Value to add to the cells of the points.
        """

        x_px, y_px = self._conv_world_to_grid(points_x, points_y)

        # Scalars must be handled before the array branch: `np.float64` (what
        # indexing a numpy array yields, e.g. `pose.position[0]`) is not an
        # `int` and not an `ndarray`, so an `isinstance(points_x, int)` test
        # silently dropped every scalar float. `examples/example_mapping.py`
        # relies on it to mark the drone's own cell as free.
        if np.isscalar(points_x):
            if 0 <= x_px < self.x_max_grid and 0 <= y_px < self.y_max_grid:
                self.grid[x_px, y_px] += val
        elif isinstance(points_x, np.ndarray):
            select = np.logical_and(np.logical_and(x_px >= 0,
                                                   x_px < self.x_max_grid),
                                    np.logical_and(y_px >= 0,
                                                   y_px < self.y_max_grid))
            x_px = x_px[select]
            y_px = y_px[select]
            self.grid[x_px, y_px] += val

    def display(self, grid_to_display: np.ndarray,
                robot_pose: Pose,
                title: str = "grid",
                scale: float = 1.0,
                origin: Tuple[int, int] = (0, 0),
                arrow_length_px: float = 25.0):
        """
        Screen display of grid and robot pose,
        using opencv (faster than the matplotlib version).

        Args:
            grid_to_display (np.ndarray): Grid to display, indexed [x, y].
            robot_pose (Pose): Robot pose.
            title (str): Window title.
            scale (float): Number of pixels per grid cell. `display()` resizes
                the grid accordingly, and uses the same factor to place the
                robot marker. Pass it whenever the map is too small to read
                (a coarse grid is typically 1 px/cell, which is unreadable), or
                when displaying a cropped window.
            origin (Tuple[int, int]): Grid coordinates of the top-left cell of
                `grid_to_display`, so a cropped window can be displayed.
            arrow_length_px (float): Length of the heading arrow, in pixels.
                Drawn along the robot orientation, so it stays readable at any
                zoom level.
        """
        img = grid_to_display.T
        img = img - img.min()
        img_max = img.max()
        if img_max > 0:
            # A uniform grid (e.g. a brand new one) would divide by zero here.
            img = img / img_max * 255
        img = np.uint8(img)

        if scale != 1.0:
            # `img` is (rows=y, cols=x) and cv2 wants (width, height), so the
            # width is the x extent. Nearest neighbor keeps cell borders crisp,
            # which matters when zooming in on a coarse occupancy grid.
            new_size = (int(round(img.shape[1] * scale)),
                        int(round(img.shape[0] * scale)))
            img = cv2.resize(img, new_size, interpolation=cv2.INTER_NEAREST)

        img_color = cv2.applyColorMap(src=img, colormap=cv2.COLORMAP_JET)

        def _to_pixel(x_world, y_world):
            """World coordinates -> (col, row) in the displayed image."""
            x_cell, y_cell = self._conv_world_to_grid(x_world, y_world)
            return (int(round((x_cell - origin[0]) * scale)),
                    int(round((y_cell - origin[1]) * scale)))

        pt1 = _to_pixel(robot_pose.position[0], robot_pose.position[1])

        # Heading in pixel space. World +Y is up, rows grow downwards, hence
        # the minus sign on the sine.
        pt2 = (int(round(pt1[0] + np.cos(robot_pose.orientation)
                         * arrow_length_px)),
               int(round(pt1[1] - np.sin(robot_pose.orientation)
                         * arrow_length_px)))

        # Marker radius and line thickness follow the zoom so the drone stays
        # visible on a 1 px/cell overview as well as on a zoomed-in window.
        thickness = max(1, int(round(arrow_length_px / 10.0)))
        radius = max(2, int(round(arrow_length_px / 4.0)))

        cv2.circle(img=img_color, center=pt1, radius=radius,
                   color=(0, 255, 255), thickness=-1)
        cv2.arrowedLine(img=img_color, pt1=pt1, pt2=pt2,
                        color=(0, 0, 255), thickness=thickness)

        cv2.imshow(title, img_color)
        cv2.waitKey(1)
