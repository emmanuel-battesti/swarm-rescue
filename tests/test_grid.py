"""
Tests for `Grid`, the spatial accumulation helper.

`Grid` had no test at all, which is why two things went unnoticed:

- the array is allocated as `np.zeros((x_max_grid, y_max_grid))`, i.e. the
  *X* axis comes first. That looks like a transposition bug, but it is the
  intended convention: callers index `grid[x_px, y_px]`, and `display()`
  transposes with `.T` before handing the array to OpenCV, which needs
  (rows=y, cols=x). These tests pin that convention so a future "fix" that
  silently swaps the axes is caught.

- `_conv_world_to_grid()` returns negative or out-of-range indices for
  positions outside the map (negative indices wrap around in numpy). The
  *writing* methods are the ones that must not trust them, and they already
  filter. These tests pin that filter: an out-of-map point or segment must be
  dropped, not silently wrapped onto the opposite side of the map.
"""

import pathlib
import sys

import numpy as np

# Insert the 'src' directory into sys.path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from swarm_rescue.simulation.utils.grid import Grid
from swarm_rescue.simulation.utils.pose import Pose


class TestAxisConvention:
    """`grid` is indexed [x, y], not [row, column]."""

    def test_shape_puts_x_first(self):
        g = Grid(size_area_world=(800, 400), resolution=1.0)
        assert g.x_max_grid == 800
        assert g.y_max_grid == 400
        # X first, so shape == (x_max, y_max).
        assert g.grid.shape == (g.x_max_grid, g.y_max_grid)

    def test_world_x_maps_to_first_axis(self):
        """Moving along world X must move along axis 0."""
        g = Grid(size_area_world=(800, 400), resolution=1.0)
        x_grid, y_grid = g._conv_world_to_grid(100.0, 0.0)
        assert x_grid == 500
        assert y_grid == 200

        x_grid2, _ = g._conv_world_to_grid(-100.0, 0.0)
        assert x_grid2 == 300  # first axis, and smaller: X decreased

    def test_world_y_maps_to_second_axis(self):
        """Moving along world Y must move along axis 1, and be inverted."""
        g = Grid(size_area_world=(800, 400), resolution=1.0)
        _, y_grid = g._conv_world_to_grid(0.0, 100.0)
        assert y_grid == 100  # world +Y is up, so a smaller row index
        _, y_grid2 = g._conv_world_to_grid(0.0, -100.0)
        assert y_grid2 == 300

    def test_write_lands_on_x_axis(self):
        """An asymmetric position must not be mirrored across the diagonal."""
        g = Grid(size_area_world=(800, 400), resolution=1.0)
        g.add_points(399, 199, 1)

        assert g.grid[799, 1] == 1.0
        assert g.grid.sum() == 1.0

    def test_write_is_not_mirrored_across_the_diagonal(self):
        """Both index orders are in bounds here, so only one may be written.

        A world point of (-200, 100) maps to grid (200, 100). In an 800x400
        grid the transposed cell (100, 200) is also a valid index, so this
        pins that the value went to the X-axis cell and not the mirrored one.
        """
        g = Grid(size_area_world=(800, 400), resolution=1.0)
        g.add_points(-200.0, 100.0, 7)

        assert g.grid[200, 100] == 7.0
        assert g.grid[100, 200] == 0.0
        assert g.grid.sum() == 7.0

    def test_display_transposes_for_opencv(self):
        """`display` hands cv2 a (rows=y, cols=x) array via `.T`."""
        g = Grid(size_area_world=(800, 400), resolution=1.0)
        assert g.grid.T.shape == (g.y_max_grid, g.x_max_grid)


class TestBoundsFiltering:
    """Writers must drop out-of-map geometry instead of wrapping it."""

    def test_out_of_map_point_is_ignored(self):
        g = Grid(size_area_world=(800, 400), resolution=1.0)
        g.add_points(500, 0, 1)   # x beyond +400
        g.add_points(-500, 0, 1)  # x beyond -400
        g.add_points(0, 300, 1)   # y beyond +200
        assert g.grid.sum() == 0.0

    def test_in_map_point_is_kept(self):
        g = Grid(size_area_world=(800, 400), resolution=1.0)
        g.add_points(0, 0, 3)
        assert g.grid.sum() == 3.0
        assert g.grid[400, 200] == 3.0

    def test_out_of_map_line_is_ignored(self):
        g = Grid(size_area_world=(800, 400), resolution=1.0)
        g.add_value_along_line(500, 0, 600, 100, 1)
        assert g.grid.sum() == 0.0

    def test_in_map_line_is_drawn(self):
        g = Grid(size_area_world=(800, 400), resolution=1.0)
        g.add_value_along_line(0, 0, 100, 100, 2)
        assert g.grid.sum() > 0.0

    def test_nan_line_is_ignored(self):
        """NaN coordinates come from an invalid pose; they must not raise."""
        g = Grid(size_area_world=(800, 400), resolution=1.0)
        g.add_value_along_line(float("nan"), 0, 100, 100, 1)
        assert g.grid.sum() == 0.0


class TestRoundTrip:
    """world -> grid -> world must be the identity for in-range indices."""

    def test_round_trip(self):
        g = Grid(size_area_world=(800, 400), resolution=1.0)
        for x_grid, y_grid in [(0, 0), (400, 200), (799, 399), (100, 350)]:
            x_world, y_world = g._conv_grid_to_world(x_grid, y_grid)
            back = g._conv_world_to_grid(x_world, y_world)
            assert back == (x_grid, y_grid)

    def test_grid_to_world_center(self):
        g = Grid(size_area_world=(800, 400), resolution=1.0)
        x_world, y_world = g._conv_grid_to_world(400, 200)
        assert (x_world, y_world) == (0.0, 0.0)


class TestScalarFloatPoints:
    """A scalar float must be written; this used to be silently dropped."""

    def test_python_float_is_written(self):
        g = Grid(size_area_world=(800, 400), resolution=1.0)
        g.add_points(100.0, -100.0, 4)
        assert g.grid[500, 300] == 4.0

    def test_numpy_float64_is_written(self):
        """`pose.position[0]` is a np.float64, which is neither int nor array.

        `examples/example_mapping.py` uses exactly this call to mark the
        drone's own cell as free, so the mapping example never marked it.
        """
        g = Grid(size_area_world=(800, 400), resolution=1.0)
        g.add_points(np.float64(100.0), np.float64(-100.0), 4)
        assert g.grid[500, 300] == 4.0

    def test_pose_position_is_written(self):
        """The exact call the mapping example makes."""
        g = Grid(size_area_world=(800, 400), resolution=1.0)
        pose = Pose(np.array([10.0, -20.0]))
        g.add_points(pose.position[0], pose.position[1], 1)
        assert g.grid.sum() == 1.0

    def test_out_of_map_float_is_still_filtered(self):
        """The bounds check must survive the scalar handling."""
        g = Grid(size_area_world=(800, 400), resolution=1.0)
        g.add_points(5000.0, 0.0, 1)
        g.add_points(0.0, 5000.0, 1)
        assert g.grid.sum() == 0.0

    def test_integer_still_written(self):
        g = Grid(size_area_world=(800, 400), resolution=1.0)
        g.add_points(100, -100, 4)
        assert g.grid[500, 300] == 4.0


class TestArrayInput:
    """Vectorised writes, as used by the mapping example."""

    def test_array_points_are_filtered_per_element(self):
        g = Grid(size_area_world=(800, 400), resolution=1.0)
        xs = np.array([0.0, 0.0, 5000.0])
        ys = np.array([0.0, -100.0, 0.0])
        g.add_points(xs, ys, 1)
        # Only the two in-range points survive.
        assert g.grid.sum() == 2.0
