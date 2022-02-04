import cv2
import numpy as np
from simple_playgrounds.engine import Engine


class ExploredMap:
    """
     Keep memory of which parts of the map was explored by drones.
     It is used to compute the score of exploration of your swarm of drones.
     """

    def __init__(self, **kwargs):
        # img_playground : colored image of the playground without wounded persons and without drones
        self._img_playground = np.zeros((0, 0))
        # map_playground : black and white map of the playground without wounded persons and without drones
        self._map_playground = np.zeros((0, 0))

        # map_exploration : map of the point visited by drones (all positions of the drones) in black
        self._map_explo_lines = np.ones((0, 0))
        self._map_explo_zones = np.zeros((0, 0))
        self._explo_pts = []
        self._last_position = dict()

        self._count_pixel_walls = 0
        self._count_pixel_explored = 0
        self._count_pixel_total = 0

        self.initialized = False

    def reset(self):
        """
        Reset everything to zero
        """
        # Initialize map_exploration with zeros
        self._map_explo_lines = np.ones(self._map_playground.shape, np.uint8) * 255
        self._map_explo_zones = np.zeros(self._map_playground.shape, np.uint8)
        self._explo_pts = []
        self._last_position = dict()
        self._count_pixel_walls = 0
        self._count_pixel_explored = 0
        self._count_pixel_total = 0

    def _create_image_walls(self, playground):
        """
        Fills _img_playground with an color image of the playground without drones and wounded persons
        """
        engine = Engine(time_limit=10, playground=playground, screen=False)
        # self._img_playground have float values between 0 and 1
        self._img_playground = engine.generate_playground_image(max_size=None)
        engine.terminate()
        return self._img_playground

    def initialize_walls(self, playground):
        """
        From _img_playground, it creates a black and white image of the walls saved in _map_playground
        """
        self.initialized = True
        img_playground = self._create_image_walls(playground)

        map_color = cv2.normalize(src=img_playground, dst=None, alpha=0, beta=255,
                                  norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8U)

        map_gray = cv2.cvtColor(map_color, cv2.COLOR_BGR2GRAY)

        ret, self._map_playground = cv2.threshold(map_gray, 10, 255, cv2.THRESH_BINARY)

        # Initialize map_exploration with zeros
        self._map_explo_lines = np.ones(self._map_playground.shape, np.uint8) * 255
        self._map_explo_zones = np.zeros(self._map_playground.shape, np.uint8)

    def update(self, drones):
        """
        Update the list of the positions of the drones
        """
        if not self.initialized:
            return

        # Fills explo_pts and self._map_explo_lines
        dim = self._map_explo_lines.shape

        for drone in drones:
            position = (round(drone.position[0]), round(drone.position[1]))
            if 0 <= position[0] < dim[1] and 0 <= position[1] < dim[0]:
                if drone in self._last_position.keys():
                    cv2.line(img=self._map_explo_lines, pt1=self._last_position[drone], pt2=position,
                             color=(0, 0, 0))
                self._explo_pts.append(position)
                self._last_position[drone] = position
            # else:
            #     print("Error")

    def get_pretty_map_explo_lines(self):
        pretty_map = np.zeros(self._map_playground.shape, np.uint8)
        pretty_map[self._map_playground == 255] = 255
        pretty_map[self._map_explo_lines == 0] = 128
        return pretty_map

    def get_pretty_map_explo_zones(self):
        """
        Return a nice map of the zones explorated.
        Warning, the function score() should have been called before.
        """
        pretty_map = np.zeros(self._map_playground.shape, np.uint8)
        pretty_map[self._map_playground == 255] = 255
        pretty_map[self._map_explo_zones == 255] = 128
        return pretty_map

    def display(self):
        """
        Display _map_explo_lines and _map_explo_zones
        """
        if not self.initialized:
            print("warning : explored_map was not initialized, cannot display map !")
            return

        cv2.imshow("explored lines", self._map_explo_lines)
        cv2.imshow("exploration zones", self._map_explo_zones)
        cv2.waitKey(1)

    def _process_positions(self):
        """
        Process the list of the positions of the drones to draw the map of the explored zones
        """
        radius_explo = 100

        # we will erode several time the self._map_explo_lines and correct each times the wall
        # In eroded_image, the explored zone is black
        eroded_image = self._map_explo_lines.copy()
        remain_radius = radius_explo
        one_time_size_kernel = 10
        while remain_radius != 0:
            # Creating kernel
            if remain_radius < one_time_size_kernel:
                one_time_size_kernel = remain_radius
                remain_radius = 0
            else:
                remain_radius -= one_time_size_kernel
            # kernel = np.ones((one_time_size_kernel, one_time_size_kernel), np.uint8)
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (one_time_size_kernel, one_time_size_kernel))

            # Using cv2.erode() method
            eroded_image = cv2.erode(eroded_image, kernel, cv2.BORDER_REFLECT)
            # The pixels of the eroded_image where there are walls (map_playground == 255) should stay white (255)
            eroded_image[self._map_playground == 255] = 255

        self._map_explo_zones = cv2.bitwise_not(eroded_image)

    def score(self):
        """
        Give a score of the exploration of all the drones by computing of the percentage of exploration
        """
        if not self.initialized:
            return 0

        # Computing map
        self._process_positions()

        # Computation of the score by counting pixels in the resulting map
        d = self._map_playground.shape
        self._count_pixel_total = d[0] * d[1]

        # Compute count_pixel_walls
        self._count_pixel_walls = cv2.countNonZero(self._map_playground)
        # print("self._count_pixel_walls=", self._count_pixel_walls)

        # Compute count_pixel_explored
        self._count_pixel_explored = cv2.countNonZero(self._map_explo_zones)
        # print("self._count_pixel_explored=", self._count_pixel_explored)

        # Compute percentage_walls
        # percentage_walls = self._count_pixel_walls / self._count_pixel_total * 100.0
        # print("total pix=", self._count_pixel_total, " percentage walls=", percentage_walls)

        # Compute percentage_explored
        count_explorable = self._count_pixel_total - self._count_pixel_walls
        score = self._count_pixel_explored / count_explorable
        # print("score exploration as % =", score * 100)

        return score
