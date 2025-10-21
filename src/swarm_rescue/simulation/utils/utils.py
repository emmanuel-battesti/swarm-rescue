import math
from typing import Union

import numpy as np


def normalize_angle(angle: Union[float, np.ndarray], zero_2_2pi: bool = False) -> Union[float, np.ndarray]:
    """
    Normalize an angle or array of angles to a specified range.

    Args:
        angle (float or np.ndarray): Angle or array of angles to normalize.
        zero_2_2pi (bool): If True, normalize to [0, 2pi). Otherwise, [-pi, pi).

    Returns:
        float or np.ndarray: Normalized angle(s).
    """
    if isinstance(angle, float) or isinstance(angle, int):
        is_float = True
        angle = float(angle)
    else:
        is_float = False

    if not isinstance(angle, (float, np.ndarray)):
        raise TypeError("Input angle must be a float or a numpy.ndarray.")

    angle = np.asarray(angle).flatten()

    if zero_2_2pi:
        mod_angle = angle % (2 * np.pi)
    else:
        mod_angle = (angle + np.pi) % (2 * np.pi) - np.pi

    if is_float:
        return mod_angle.item()
    else:
        return mod_angle


def sign(x: float) -> float:
    """
    Return the sign of a number as +1.0 or -1.0.

    Args:
        x (float): Input value.

    Returns:
        float: 1.0 if x >= 0, -1.0 if x < 0.
    """
    return math.copysign(1, x)


def rad2deg(angle: Union[int, float]) -> Union[int, float]:
    """
    Convert radians to degrees.

    The rad2deg function takes a value in radians and converts it to degrees
    using the math.degrees function from the math module. If the input value is
    None, the function returns None.

    Example Usage
        # Convert 1.5708 radians to degrees
        result = rad2deg(1.5708)
        print(result)
        # Output: around 90.0

        # Convert -3.1416 radians to degrees
        result = rad2deg(-3.1416)
        print(result)
        # Output: around -180.0

        # Convert None to degrees
        result = rad2deg(None)
        print(result)
        # Output: None

    Args:
        angle (int or float): Angle in radians.

    Returns:
        int or float: Angle in degrees.
    """
    if not isinstance(angle, (int, float)):
        raise TypeError("Input angle must be an integer or a float.")

    return math.degrees(angle)


def deg2rad(angle: Union[int, float]) -> Union[int, float]:
    """
    Convert degrees to radians.

    The deg2rad function is used to convert an angle from degrees to radians.
    It takes an angle as input and returns the corresponding angle in radians.
    If the input angle is None, the function returns None.

    Example Usage
        angle_in_degrees = 45
        angle_in_radians = deg2rad(angle_in_degrees)
        print(angle_in_radians)

    Args:
        angle (int or float): Angle in degrees.

    Returns:
        int or float: Angle in radians.
    """
    if not isinstance(angle, (int, float)):
        raise TypeError("Input angle must be an integer or a float.")

    return math.radians(angle)


def circular_mean(angles: np.ndarray) -> float:
    """
    Compute the circular mean of an array of angles. cf: https://en.wikipedia.org/wiki/Circular_mean

    Args:
        angles (np.ndarray): Array of angles in radians.

    Returns:
        float: Circular mean angle in radians.
    """
    if len(angles) == 0:
        raise ValueError("Input angles cannot be empty.")

    if not np.issubdtype(angles.dtype, np.number):
        raise ValueError("Input angles must contain numeric values.")

    sum_sin = np.sum(np.sin(angles))
    sum_cos = np.sum(np.cos(angles))
    mean_angle = math.atan2(sum_sin, sum_cos)
    return mean_angle


def bresenham(start: tuple, end: tuple) -> np.ndarray:
    """
    Implementation of Bresenham's line drawing algorithm.
    It takes two points, start and end, as inputs and returns an array of
    points that form a line between the two points.
    See en.wikipedia.org/wiki/Bresenham's_line_algorithm

    Produces a np.array from start and end (original from roguebasin.com)
    points1 = bresenham((4, 4), (6, 10))
    print(points1)
    np.array([[4,4], [4,5], [5,6], [5,7], [5,8], [6,9], [6,10]])

    Args:
        start (tuple): The starting point of the line.
        end (tuple): The ending point of the line.

    Returns:
        np.ndarray: Array of points forming the line.
    """
    # setup initial conditions
    x1, y1 = start
    x2, y2 = end
    dx = x2 - x1
    dy = y2 - y1
    is_steep = abs(dy) > abs(dx)  # determine how steep the line is
    if is_steep:  # rotate line
        x1, y1 = y1, x1
        x2, y2 = y2, x2
    # swap start and end points if necessary and store swap state
    swapped = False
    if x1 > x2:
        x1, x2 = x2, x1
        y1, y2 = y2, y1
        swapped = True
    dx = x2 - x1  # recalculate differentials
    dy = y2 - y1  # recalculate differentials
    error = int(dx / 2.0)  # calculate error
    y_step = 1 if y1 < y2 else -1
    # iterate over bounding box generating points between start and end
    y = y1
    points = []
    for x in range(x1, x2 + 1):
        coord = [y, x] if is_steep else (x, y)
        points.append(coord)
        error -= abs(dy)
        if error < 0:
            y += y_step
            error += dx
    if swapped:  # reverse the list if the coordinates were swapped
        points.reverse()
    points = np.array(points)
    return points


def circular_kernel(radius: int) -> np.ndarray:
    """
    Create a circular structuring element (filled disk) for image processing.

    The function cv2.getStructuringElement(cv2.MORPH_ELLIPSE, ...) of OpenCV is
    not satisfying because the result is not symmetrical...
    So here we use this code to do it. This was find here :
    https://stackoverflow.com/questions/8647024/how-to-apply-a-disc-shaped-mask-to-a-numpy-array
    :param radius:
    :return: circle structuring elements, that is, a filled circle inscribed
    into the rectangle Rect(0, 0, 2*radius + 1, 2*radius + 1)

    Args:
        radius (int): Radius of the disk.

    Returns:
        np.ndarray: Binary mask of the disk.
    """
    if not isinstance(radius, int) or radius <= 0:
        raise ValueError("Radius must be a positive integer.")

    kernel = np.zeros((2 * radius + 1, 2 * radius + 1), np.uint8)
    y, x = np.ogrid[-radius:radius + 1, -radius:radius + 1]
    mask = x ** 2 + y ** 2 <= radius ** 2
    kernel[mask] = 1
    return kernel


def clamp(val: Union[float, int], min_val: Union[float, int],
          max_val: Union[float, int]) -> Union[float, int]:
    """
    Clamp a value between a minimum and maximum.

    Args:
        val (float or int): Value to clamp.
        min_val (float or int): Minimum allowed value.
        max_val (float or int): Maximum allowed value.

    Returns:
        float or int: Clamped value.
    """
    if val < min_val:
        return min_val
    elif val > max_val:
        return max_val
    else:
        return val