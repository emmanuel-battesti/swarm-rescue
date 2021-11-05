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
        self._map_exploration = np.ones((0, 0))
        self._exploration_zone = np.zeros((0, 0))
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
        self._map_exploration = np.ones(self._map_playground.shape, np.uint8) * 255
        self._exploration_zone = np.zeros(self._map_playground.shape, np.uint8)
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
        self._map_exploration = np.ones(self._map_playground.shape, np.uint8) * 255
        self._exploration_zone = np.zeros(self._map_playground.shape, np.uint8)

    def update(self, drones):
        """
        Update the list of the positions of the drones
        """
        if not self.initialized:
            return

        # Fills explo_pts and self._map_exploration
        dim = self._map_exploration.shape

        for drone in drones:
            position = (round(drone.position[0]), round(drone.position[1]))
            if 0 <= position[0] < dim[1] and 0 <= position[1] < dim[0]:
                if drone in self._last_position.keys():
                    cv2.line(img=self._map_exploration, pt1=self._last_position[drone], pt2=position,
                             color=(0, 0, 0))
                self._explo_pts.append(position)
                self._last_position[drone] = position
            # else:
            #     print("Error")

    def display(self):
        """
        Display _map_exploration and _exploration_zone
        """
        if not self.initialized:
            return

        cv2.imshow("explored map", self._map_exploration)
        cv2.imshow("exploration_zone", self._exploration_zone)
        cv2.waitKey(1)

    def _process_positions(self):
        """
        Process the list of the positions of the drones to draw the map of the explored zones
        """
        # compute distance from zeros pixels
        dist_img = cv2.distanceTransform(self._map_exploration, distanceType=cv2.DIST_L2, maskSize=5)
        max_dist = dist_img.max()
        # The pixel of the dist_img where there are walls take the maximum value
        dist_img[self._map_playground == 255] = max_dist
        dist_img_float = dist_img / max_dist

        radius_explo = 50
        up_diff = radius_explo / max_dist
        explo_zone = -1
        for pt in self._explo_pts:
            pt2 = (pt[1], pt[0])
            if dist_img_float[pt2] == 0:
                mask = np.zeros((dist_img_float.shape[0] + 2, dist_img_float.shape[1] + 2), np.uint8)
                cv2.floodFill(image=dist_img_float, mask=mask, seedPoint=pt, loDiff=0, upDiff=up_diff,
                              newVal=explo_zone, flags=cv2.FLOODFILL_FIXED_RANGE)

        self._exploration_zone = np.zeros(dist_img_float.shape, np.uint8)
        self._exploration_zone[dist_img_float == explo_zone] = 255

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
        self._count_pixel_explored = cv2.countNonZero(self._exploration_zone)
        # print("self._count_pixel_explored=", self._count_pixel_explored)

        # Compute percentage_walls
        # percentage_walls = self._count_pixel_walls / self._count_pixel_total * 100.0
        # print("total pix=", self._count_pixel_total, " percentage walls=", percentage_walls)

        # Compute percentage_explored
        count_explorable = self._count_pixel_total - self._count_pixel_walls
        score = self._count_pixel_explored / count_explorable
        # print("score exploration as % =", score * 100)

        return score
