import math

import cv2
import numpy as np
from typing import List
# from spg.engine import Engine
from spg.playground import Playground
from spg.view import TopDownView

from spg_overlay.entities.drone_abstract import DroneAbstract
from spg_overlay.utils.utils import bresenham, circular_kernel


def _create_black_white_image(img_playground):
    map_color = cv2.normalize(src=img_playground, dst=None, alpha=0, beta=255,
                              norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8U)
    map_gray = cv2.cvtColor(map_color, cv2.COLOR_BGR2GRAY)
    # In map_playground, walls are black and free zone white
    ret, map_playground = cv2.threshold(map_gray, 127, 255,
                                        cv2.THRESH_BINARY)
    return map_playground


def fill_empty_blob_of_wall(map_img):
    # In map_img, wall should be black and free zone (and inside some walls)
    # should be white.
    # cv2.imshow("map_img", map_img)
    # cv2.waitKey(0)

    # Find connected components and count pixels
    analysis = cv2.connectedComponentsWithStats(map_img)
    (totalLabels, label_ids, stats, centroid) = analysis

    # Find the index of the biggest component. Label 0 is the wall
    # (background, here) so we start at 1
    biggest_area_index = np.argmax(stats[1:, cv2.CC_STAT_AREA]) + 1

    filled_wall_map = (label_ids == biggest_area_index).astype("uint8") * 255
    # cv2.imshow("filled_wall_map", filled_wall_map)
    # cv2.waitKey(0)
    # In filled_wall_map, walls are black and free zone white
    return filled_wall_map


class ExploredMap:
    """
     The ExploredMap class is used to keep track of which parts of the map have
     been explored by drones. It provides methods to initialize the map, update
     it with the positions of the drones, and compute the score of exploration
     based on the percentage of explored area.

     Example Usage:
        # Create an instance of ExploredMap
        explored_map = ExploredMap()

        # Initialize the map with the playground
        explored_map.initialize_walls(playground)

        # Update the map with the positions of the drones
        explored_map.update_drones(drones)

        # Compute the score of exploration
        score = explored_map.score()

        # Display the map
        explored_map.display()

    Main functionalities
        Keep memory of which parts of the map have been explored by drones
        Compute the score of exploration based on the percentage of explored
        area
     """

    def __init__(self):
        """
        Initializes the ExploredMap object with empty maps and counters
        """
        # img_playground : colored image of the playground without wounded
        # persons and without drones
        self._img_playground = np.zeros((0, 0))
        # map_playground : black and white map of the playground without
        # wounded persons and drones
        self._map_playground = np.zeros((0, 0))
        self._map_shape = (0, 0)

        # _map_explo_lines : map of the point visited by drones (all positions
        # of the drones)
        # Initialize _map_explo_lines with 255 (white)
        self._map_explo_lines = np.ones((0, 0))
        # _map_explo_zones : map of the zone explored by drones
        # Initialize _map_explo_zones with zeros (black)
        self._map_explo_zones = np.zeros((0, 0))
        # Dictionary to store the positions of the drones
        self._explo_pts = dict()
        # Dictionary to store the last position of each drone
        self._last_position = dict()

        self._count_explored_pixels = 0
        self._count_pixel_total = 0

        # Flag to indicate if the map has been initialized or not
        self.initialized = False

    def reset(self):
        """
        Resets all the maps and counters to zero
        """
        # _map_explo_lines : map of the point visited by drones (all positions
        # of the drones)
        # Initialize _map_explo_lines with 255 (white)
        self._map_explo_lines = np.ones(self._map_shape, np.uint8) * 255
        # _map_explo_zones : map of the zone explored by drones
        # Initialize _map_explo_zones with zeros (black)
        self._map_explo_zones = np.zeros(self._map_shape, np.uint8)
        self._explo_pts = dict()
        self._last_position = dict()
        self._count_explored_pixels = 0
        self._count_pixel_total = 0

    def _create_image_walls(self, playground: Playground):
        """
        Fills _img_playground with a color image of the playground without
        drones and wounded persons
        """
        view = TopDownView(playground=playground, zoom=1)
        view.update()
        # self._img_playground have float values between 0 and 1
        # The image should be flip and the color channel permuted
        self._img_playground = cv2.flip(view.get_np_img(), 0)
        self._img_playground = cv2.cvtColor(self._img_playground, cv2.COLOR_BGR2RGB)
        return self._img_playground

    def initialize_walls(self, playground: Playground):
        """
        From _img_playground, it creates a black and white image of the walls
        saved in _map_playground.
        Creates an image of the playground without drones and wounded persons
        """
        self.initialized = True
        img_playground = self._create_image_walls(playground)

        # cv2.imshow("img_playground", img_playground)
        # cv2.waitKey(0)
        map_playground_tmp = _create_black_white_image(img_playground)
        self._map_playground = fill_empty_blob_of_wall(map_playground_tmp)
        self._map_shape = self._map_playground.shape

        # _map_explo_lines : map of the point visited by drones (all positions
        # of the drones)
        # Initialize _map_explo_lines with 255 (white)
        self._map_explo_lines = np.ones(self._map_shape, np.uint8) * 255
        # _map_explo_zones : map of the zone explored by drones
        # Initialize _map_explo_zones with zeros (black)
        self._map_explo_zones = np.zeros(self._map_shape, np.uint8)

    def update_drones(self, drones: [List[DroneAbstract]]):
        """
        Update the list of the positions of the drones
        """
        if not self.initialized:
            return

        # Fills explo_pts and self._map_explo_lines
        height, width = self._map_explo_lines.shape
        # print("width", width, "height", height)

        for drone in drones:
            position_ocv = (round(drone.true_position()[0] + width / 2),
                            round(-drone.true_position()[1] + height / 2))
            if 0 <= position_ocv[0] < width and 0 <= position_ocv[1] < height:
                if drone in self._last_position.keys():
                    cv2.line(img=self._map_explo_lines,
                             pt1=self._last_position[drone], pt2=position_ocv,
                             color=(0, 0, 0))
                if drone in self._explo_pts:
                    self._explo_pts[drone].append(position_ocv)
                else:
                    self._explo_pts[drone] = [position_ocv]
                self._last_position[drone] = position_ocv
            # else:
            #     print("Error")

    def get_pretty_map_explo_lines(self):
        """
        Returns a map with the explored lines highlighted
        """
        pretty_map = np.zeros(self._map_shape, np.uint8)
        pretty_map[self._map_playground == 0] = 255
        pretty_map[self._map_explo_lines == 0] = 128
        return pretty_map

    def get_pretty_map_explo_zones(self):
        """
        Return a nice map of the zones explored.
        Warning, the function score() should have been called before.
        """
        pretty_map = np.zeros(self._map_shape, np.uint8)
        pretty_map[self._map_playground == 0] = 255
        pretty_map[self._map_explo_zones == 255] = 128
        return pretty_map

    def display(self):
        """
        Display _map_explo_lines and _map_explo_zones
        """
        if not self.initialized:
            print("warning : explored_map was not initialized, "
                  "cannot display map !")
            return

        cv2.imshow("explored lines", self._map_explo_lines)
        cv2.imshow("exploration zones", self._map_explo_zones)
        cv2.waitKey(1)

    def _process_positions(self):
        """
        Process the list of the positions of the drones to draw the map of the explored zones
        """
        radius_explo = 200

        # we will erode several time the self._map_explo_lines and correct each
        # times the wall
        # In eroded_image, the explored zone is black
        eroded_image = self._map_explo_lines.copy()
        remain_radius = radius_explo
        # one_time_radius_kernel should be equal to the width(+1 because of bug
        # in SPG)
        one_time_radius_kernel = 5

        kernel = circular_kernel(one_time_radius_kernel)

        while remain_radius != 0:
            # Creating kernel
            if remain_radius < one_time_radius_kernel:
                one_time_radius_kernel = remain_radius
                remain_radius = 0
            else:
                remain_radius -= one_time_radius_kernel

            # Using cv2.erode() method
            eroded_image = cv2.erode(eroded_image, kernel, cv2.BORDER_REFLECT)

            # The pixels of the eroded_image where there are walls
            # (map_playground == 0) should stay white (255)
            eroded_image[self._map_playground == 0] = 255

            # cv2.imshow("eroded_image", eroded_image)
            # cv2.imshow("_map_explo_lines", self._map_explo_lines)
            # cv2.waitKey(0)

        self._map_explo_zones = cv2.bitwise_not(eroded_image)

    def _process_positions_bresenham(self):
        """
        Processes the positions of the drones using Bresenham ray casting
        algorithm to draw the map of explored zones
        Not used...
        """
        width = self._map_shape[1]
        height = self._map_shape[0]

        radius_explo = 200
        nb_rays = 32
        ray_angles = [n * 2 * math.pi / nb_rays for n in range(nb_rays)]
        cos_ray_angles = np.cos(ray_angles)
        sin_ray_angles = np.sin(ray_angles)
        ox = cos_ray_angles * radius_explo
        oy = sin_ray_angles * radius_explo

        laser_beams = []
        for (x, y) in zip(ox, oy):
            laser_beam = bresenham((0, 0),
                                   (int(x + 0.5), int(y + 0.5)))
            laser_beams.append(laser_beam)

        # 'ray_angles' is an array which contains the angles of the laser rays
        # of the lidar
        # ray_angles = np.array(ray_angles)

        explo_pts = sum(self._explo_pts.values(), [])

        prev_pt = [0, 0]
        for pt in explo_pts:
            # Compute only if the point pt is far enough from the previous one
            if abs(prev_pt[0] - pt[0]) < 10 or abs(prev_pt[1] - pt[1]) < 10:
                continue
            for laser_beam in laser_beams:
                laser_beam_around_pt = laser_beam + pt
                for idx, pix in enumerate(laser_beam_around_pt):

                    if (pix[0] < 0
                            or pix[0] >= width
                            or pix[1] < 0
                            or pix[1] >= height):
                        # print("Index outside, pix:{}, size({},{})", pix, width, height)
                        break

                    # Compute only one point on 4
                    if idx % 4 != 0:
                        continue

                    if self._map_playground[pix[1]][pix[0]] == 255:
                        self._map_explo_zones[pix[1]][pix[0]] = 0
                    else:
                        break

                # print(pt)
                # cv2.imshow("_map_explo_zones", self._map_explo_zones)
                # cv2.imshow("_map_explo_lines", self._map_explo_lines)
                # cv2.waitKey(1)

            prev_pt = pt

        cv2.imshow("_map_explo_zones", self._map_explo_zones)
        cv2.imshow("_map_explo_lines", self._map_explo_lines)

        # Remove noise and connect point of exploration into a zone
        kernel = circular_kernel(4)
        self._map_explo_zones = cv2.morphologyEx(self._map_explo_zones,
                                                 cv2.MORPH_CLOSE, kernel)
        self._map_explo_zones[self._map_playground == 0] = 0
        cv2.imshow("_map_explo_zones 2 ", self._map_explo_zones)
        cv2.waitKey(0)
        # Remove the last points of exploration not connected with a zone.
        # kernel = circular_kernel(1)
        # self._map_explo_zones = cv2.morphologyEx(self._map_explo_zones,
        #                                          cv2.MORPH_OPEN, kernel)
        # Remove exploration points inside walls
        self._map_explo_zones[self._map_playground == 0] = 0

    def _compute_reachable_pixels(self):
        # In self._map_playground, wall are black and free zone are white.

        # Find connected components and count pixels
        _, labels, stats, _ = (
            cv2.connectedComponentsWithStats(self._map_playground))
        # Find the index of the biggest component. Label 0 is the wall so we
        # start at 1
        biggest_area_index = np.argmax(stats[1:, cv2.CC_STAT_AREA]) + 1
        # Extract area of the biggest component
        biggest_area = stats[biggest_area_index, cv2.CC_STAT_AREA]
        count_reachable = biggest_area
        print("count_reachable v3 =", count_reachable)
        # for i, area in enumerate(stats[0:, cv2.CC_STAT_AREA]):
        #     print(f"Component {i} = {area} pixels")
        return count_reachable

    def score(self):
        """
        Computes a score of the exploration of all the drones based on the
        percentage of explored area
        """
        if not self.initialized:
            return 0

        # Computing map
        self._process_positions()

        # Compute _count_explored_pixels
        self._count_explored_pixels = cv2.countNonZero(self._map_explo_zones)
        # print("self._count_pixel_explored=", self._count_pixel_explored)

        # Compute percentage of explored pixels
        count_reachable_pixels = self._compute_reachable_pixels()
        score = self._count_explored_pixels / count_reachable_pixels
        if score > 1.0:
            score = 1.0
        # print("score exploration as % =", score * 100)

        return score
