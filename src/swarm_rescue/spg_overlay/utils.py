import math

import numpy as np


def normalize_angle(angle):
    """
    :param angle: (float)
    :return: (float) Angle in radian in [-pi, pi]
    """

    angle = angle % (2 * math.pi)
    if angle > math.pi:
        angle -= 2 * math.pi

    return angle


def sign(x):
    return math.copysign(1, x)


def rad2deg(x):
    """
    Convert radians to degrees
    """
    return x / math.pi * 180.0


def deg2rad(x):
    """
    Convert degrees to radians
    """
    return x * math.pi / 180.0


def bresenham(start, end):
    """
    Implementation of Bresenham's line drawing algorithm
    See en.wikipedia.org/wiki/Bresenham's_line_algorithm
    Bresenham's Line Algorithm
    Produces a np.array from start and end (original from roguebasin.com)
    points1 = bresenham((4, 4), (6, 10))
    print(points1)
    np.array([[4,4], [4,5], [5,6], [5,7], [5,8], [6,9], [6,10]])
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


def circular_kernel(radius):
    """
    The function cv2.getStructuringElement(cv2.MORPH_ELLIPSE, ...) of OpenCV is not satisfying because
    the result is not symmetrical...
    So here we use this code to do it. This was find here :
    https://stackoverflow.com/questions/8647024/how-to-apply-a-disc-shaped-mask-to-a-numpy-array
    :param radius:
    :return: circle structuring element, that is, a filled circle inscribed into the
    rectangle Rect(0, 0, 2*radius + 1, 2*radius + 1)
    """
    kernel = np.zeros((2 * radius + 1, 2 * radius + 1), np.uint8)
    y, x = np.ogrid[-radius:radius + 1, -radius:radius + 1]
    mask = x ** 2 + y ** 2 <= radius ** 2
    kernel[mask] = 1
    return kernel
