import pathlib
import sys
import numpy as np
import pytest

# Insert the 'src' directory, located two levels up from the current script,
# into sys.path. This ensures Python can find project-specific modules
# (e.g., 'swarm_rescue') when the script is run from a subfolder like 'tests/'.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from swarm_rescue.simulation.utils.utils import (normalize_angle, sign,
                                                 circular_mean, bresenham)


def test_normalize_angle():
    assert normalize_angle(0) == 0
    assert normalize_angle(3) == 3
    assert normalize_angle(-3) == -3
    assert normalize_angle(-4) > 0
    assert normalize_angle(4) < 0
    assert normalize_angle(-400) > -3.1416
    assert normalize_angle(-400) < 3.1416
    assert normalize_angle(400) > -3.1416
    assert normalize_angle(400) < 3.1416

    angles = np.array([0.1, 0.5, -0.3, 2.7])
    assert np.allclose(normalize_angle(angles), np.array([0.1, 0.5, -0.3, 2.7]))

    assert np.isnan(normalize_angle(np.nan))
    assert np.isnan(normalize_angle(np.inf))

    # Test multiples of pi
    assert normalize_angle(np.pi) == pytest.approx(-np.pi)
    assert normalize_angle(-np.pi) == pytest.approx(-np.pi)
    assert normalize_angle(2 * np.pi) == 0
    assert normalize_angle(-2 * np.pi) == 0
    assert normalize_angle(3 * np.pi) == pytest.approx(-np.pi)
    assert normalize_angle(-3 * np.pi) == pytest.approx(-np.pi)
    # Test array with multiples of pi
    angles = np.array([np.pi, -np.pi, 2 * np.pi, -2 * np.pi, 3 * np.pi, -3 * np.pi])
    expected = np.array([-np.pi, -np.pi, 0, 0, -np.pi, -np.pi])
    assert np.allclose(normalize_angle(angles), expected)
    # Test very large values
    assert -np.pi < normalize_angle(1e10) < np.pi
    assert -np.pi < normalize_angle(-1e10) < np.pi


def test_sign():
    assert sign(0) == 1
    assert sign(1) == 1
    assert sign(-1) == -1
    assert sign(10000) == 1
    assert sign(-10000) == -1

    assert sign(np.nan) == 1
    assert sign(np.inf) == 1


def test_single_angle():
    angles = np.array([0])
    result = circular_mean(angles)
    assert result == 0


def test_multiple_angles():
    angles = np.array([0, np.pi / 2, np.pi])
    result = circular_mean(angles)
    assert result == pytest.approx(np.pi / 2)
    angles = np.array([0, -np.pi / 2, np.pi])
    result = circular_mean(angles)
    assert result == pytest.approx(-np.pi / 2)
    angles = np.array([0, -np.pi / 2])
    result = circular_mean(angles)
    assert result == pytest.approx(-np.pi / 4)


def test_angles_0_to_pi():
    angles = np.linspace(0, np.pi, 100)
    result = circular_mean(angles)
    assert result == pytest.approx(np.pi / 2)
    angles = np.linspace(0, -np.pi, 100)
    result = circular_mean(angles)
    assert result == pytest.approx(-np.pi / 2)
    angles = np.linspace(-np.pi * 0.9, np.pi * 0.9, 100)
    result = circular_mean(angles)
    assert result == pytest.approx(0)


def test_empty_input_array():
    angles = np.array([])
    with pytest.raises(ValueError):
        circular_mean(angles)


def test_non_numeric_values():
    angles = np.array(['a', 'b', 'c'])
    with pytest.raises(ValueError):
        circular_mean(angles)


class TestBresenham:

    #  Tests that the function correctly generates points for
    #  a horizontal line between two points
    def test_horizontal_line(self):
        start = (4, 4)
        end = (10, 4)
        expected = np.array([[4, 4], [5, 4], [6, 4],
                             [7, 4], [8, 4], [9, 4], [10, 4]])
        assert np.array_equal(bresenham(start, end), expected)

    #  Tests that the function correctly generates points for
    #  a vertical line between two points
    def test_vertical_line(self):
        start = (4, 4)
        end = (4, 10)
        expected = np.array([[4, 4], [4, 5], [4, 6],
                             [4, 7], [4, 8], [4, 9], [4, 10]])
        assert np.array_equal(bresenham(start, end), expected)

    #  Tests that the function correctly generates points for a
    #  diagonal line with positive slope between two points
    def test_positive_slope(self):
        start = (4, 4)
        end = (6, 10)
        expected = np.array([[4, 4], [4, 5], [5, 6],
                             [5, 7], [5, 8], [6, 9], [6, 10]])
        assert np.array_equal(bresenham(start, end), expected)

    #  Tests that the function correctly generates points for a
    #  diagonal line with negative slope between two points
    def test_negative_slope(self):
        start = (6, 10)
        end = (4, 4)
        expected = np.array([[6, 10], [6, 9], [5, 8],
                             [5, 7], [5, 6], [4, 5], [4, 4]])
        assert np.array_equal(bresenham(start, end), expected)

    #  Tests that the function correctly generates points for a
    #  diagonal line with slope 1 between two points
    def test_slope_1(self):
        start = (4, 4)
        end = (10, 10)
        expected = np.array([[4, 4], [5, 5], [6, 6],
                             [7, 7], [8, 8], [9, 9], [10, 10]])
        assert np.array_equal(bresenham(start, end), expected)

    #  Tests that the function correctly generates points for a
    #  diagonal line with slope -1 between two points
    def test_slope_minus_1(self):
        start = (10, 4)
        end = (4, 10)
        expected = np.array([[10, 4], [9, 5], [8, 6],
                             [7, 7], [6, 8], [5, 9], [4, 10]])
        assert np.array_equal(bresenham(start, end), expected)
