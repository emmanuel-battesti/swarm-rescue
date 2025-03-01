import numpy as np
from scipy.ndimage import label
import cv2
from spg_overlay.utils.constants import MAX_RANGE_LIDAR_SENSOR
from solutions.utils.pose import Pose
from spg_overlay.utils.grid import Grid
from solutions.utils.messages import DroneMessage
from solutions.utils.astar import *

class OccupancyGrid(Grid):
    """Self updating occupancy grid"""

    OBSTACLE = 1
    FREE = 0
    UNDISCOVERED = -2

    class Frontier:

        MIN_FRONTIER_SIZE = 6

        def __init__(self, cells):
            """
            Initialize a frontier with a list of grid cells.
            :param cells: List of tuples [(x1, y1), (x2, y2), ...]
            """
            self.cells = cells

        def compute_centroid(self):
            """
            Compute the centroid of the frontier.
            """
            if self.cells.size == 0:
                return None
            x_coords, y_coords = zip(*self.cells)
            return np.array([sum(x_coords) / len(x_coords), sum(y_coords) / len(y_coords)], dtype=int)

        def size(self):
            """
            Return the number of cells in the frontier.
            """
            return len(self.cells)

    def __init__(self,
                 size_area_world,
                 resolution: float,
                 lidar):
        super().__init__(size_area_world=size_area_world,
                         resolution=resolution)

        self.size_area_world = size_area_world
        self.resolution = resolution

        self.lidar = lidar

        self.x_max_grid: int = int(self.size_area_world[0] / self.resolution
                                   + 0.5)
        self.y_max_grid: int = int(self.size_area_world[1] / self.resolution
                                   + 0.5)

        self.initial_cell = None
        self.initial_cell_value = None

        self.grid = np.zeros((self.x_max_grid, self.y_max_grid))
        self.zoomed_grid = np.empty((self.x_max_grid, self.y_max_grid))

        self.frontier_connectivity_structure = np.ones((3, 3), dtype=int)  # Connects points that are adjacent (even diagonally)
        self.frontiers = []

    def set_initial_cell(self, world_x, world_y):
        """
        Store the cell that corresponds to the initial drone position 
        This should be called once the drone initial position is known.
        """
        cell_x, cell_y = self._conv_world_to_grid(world_x, world_y)
        
        if 0 <= cell_x < self.x_max_grid and 0 <= cell_y < self.y_max_grid:
            self.initial_cell = (cell_x, cell_y)
    
    def to_binary_map(self):
        """
        Convert the probabilistic occupancy grid into a binary grid.
        OBSTACLE = 1
        FREE = 0
        UNDISCOVERED = -2
        Cells with value > 0 are considered obstacles.
        Cells with value < 0 are considered free.
        Cells with value = 0 are considered undiscovered
        """
        #print(np.count_nonzero(self.grid < 0))
        binary_map = np.zeros_like(self.grid, dtype=int)
        binary_map[self.grid > 0] = self.OBSTACLE
        binary_map[self.grid == 0] = self.UNDISCOVERED
        return binary_map
    
    def to_update(self, pose: Pose):
        """
        Returns the list of things to update on the grid
        """
        to_update = []

        EVERY_N = 3
        LIDAR_DIST_CLIP = 40.0
        EMPTY_ZONE_VALUE = -0.602
        OBSTACLE_ZONE_VALUE = 2.0
        FREE_ZONE_VALUE = -4.0

        lidar_dist = self.lidar.get_sensor_values()[::EVERY_N].copy()
        lidar_angles = self.lidar.ray_angles[::EVERY_N].copy()

        # Compute cos and sin of the absolute angle of the lidar
        cos_rays = np.cos(lidar_angles + pose.orientation)
        sin_rays = np.sin(lidar_angles + pose.orientation)

        max_range = MAX_RANGE_LIDAR_SENSOR * 0.9 # pk ? 

        # For empty zones
        # points_x and point_y contains the border of detected empty zone
        # We use a value a little bit less than LIDAR_DIST_CLIP because of the
        # noise in lidar
        lidar_dist_empty = np.maximum(lidar_dist - LIDAR_DIST_CLIP, 0.0)
        # All values of lidar_dist_empty_clip are now <= max_range
        lidar_dist_empty_clip = np.minimum(lidar_dist_empty, max_range)
        points_x = pose.position[0] + np.multiply(lidar_dist_empty_clip,
                                                  cos_rays)
        points_y = pose.position[1] + np.multiply(lidar_dist_empty_clip,
                                                  sin_rays)

        for pt_x, pt_y in zip(points_x, points_y):
            to_update.append(DroneMessage(
                            subject=DroneMessage.Subject.MAPPING,
                            code=DroneMessage.Code.LINE,
                            arg=(pose.position[0], pose.position[1], pt_x, pt_y, EMPTY_ZONE_VALUE))
                            )

        # For obstacle zones, all values of lidar_dist are < max_range
        select_collision = lidar_dist < max_range

        points_x = pose.position[0] + np.multiply(lidar_dist, cos_rays)
        points_y = pose.position[1] + np.multiply(lidar_dist, sin_rays)

        points_x = points_x[select_collision]
        points_y = points_y[select_collision]

        
        to_update.append(DroneMessage(
                        subject=DroneMessage.Subject.MAPPING,
                        code=DroneMessage.Code.POINTS,
                        arg=(points_x, points_y, OBSTACLE_ZONE_VALUE))
                        )

        # the current position of the drone is free !
        to_update.append(DroneMessage(
                        subject=DroneMessage.Subject.MAPPING,
                        code=DroneMessage.Code.POINTS,
                        arg=(pose.position[0], pose.position[1], FREE_ZONE_VALUE))
                        )

        return to_update

    def update(self, to_update):
        """
        Bayesian map update with new observation
        lidar : lidar data
        pose : corrected pose in world coordinates
        """
        THRESHOLD_MIN = -40
        THRESHOLD_MAX = 40

        for message in to_update:
            # Ensure the message is a valid DroneMessage instance
            if not isinstance(message, DroneMessage):
                raise ValueError("Invalid message type. Expected a DroneMessage instance.")

            code = message.code
            arg = message.arg

            if code == DroneMessage.Code.LINE:
                self.add_value_along_line(*arg)
            elif code == DroneMessage.Code.POINTS:
                self.add_points(*arg)
            else:
                raise ValueError(f"Unknown code in DroneMessage: {code}")

        # Threshold values in the grid
        self.grid = np.clip(self.grid, THRESHOLD_MIN, THRESHOLD_MAX)


        # # Restore the initial cell value # That could have been set to free or empty
        # if self.initial_cell and self.initial_cell_value is not None:
        #     cell_x, cell_y = self.initial_cell
        #     if 0 <= cell_x < self.x_max_grid and 0 <= cell_y < self.y_max_grid:
        #         self.grid[cell_x, cell_y] = self.initial_cell_value

        # compute zoomed grid for displaying
        self.zoomed_grid = self.grid.copy()
        
        new_zoomed_size = (int(self.size_area_world[1] * 0.5),
                           int(self.size_area_world[0] * 0.5))
        self.zoomed_grid = cv2.resize(self.zoomed_grid, new_zoomed_size,
                                      interpolation=cv2.INTER_NEAREST)
    
    def frontiers_update(self):
        binary_map = self.to_binary_map()

        # Différences sur les axes X et Y
        diff_x = np.diff(binary_map, axis=1)
        diff_y = np.diff(binary_map, axis=0)

        # Détection des frontières entre FREE et UNDISCOVERED
        boundaries_x = np.abs(diff_x) == 2
        boundaries_y = np.abs(diff_y) == 2

        # Combinaison des résultats
        boundaries_map = np.pad(boundaries_x, ((0, 0), (0, 1))) | np.pad(boundaries_y, ((0, 1), (0, 0)))
        boundaries_map = boundaries_map

        labeled_array, num_features = label(boundaries_map, self.frontier_connectivity_structure)

        # Extraction des points de chaque frontière
        frontiers = [np.argwhere(labeled_array == i) for i in range(1, num_features + 1)]
        self.frontiers = [self.Frontier(cells) for cells in frontiers if len(cells) >= self.Frontier.MIN_FRONTIER_SIZE]
    
    def closest_largest_centroid_frontier(self, pose: Pose):
        """
        Returns the centroid of the frontier with best interest considering both distance to pose and size.
        IN GRID COORDINATES.
        """
        self.frontiers_update()
        if not self.frontiers:
            return None

        pos_drone_grid = np.array(self._conv_world_to_grid(*pose.position))
        centroids_with_size = [
            (frontier.compute_centroid(), frontier.size()) for frontier in self.frontiers
        ]
        
        def interest_measure(frontier_data):
            centroid, size = frontier_data
            distance = np.linalg.norm(centroid - pos_drone_grid)
            return distance / (size + 1)**2
        
        closest_centroid, _ = min(centroids_with_size, key=interest_measure, default=(None, None))
        return closest_centroid

    def compute_safest_path(self, start_cell, target_cell, max_inflation):
        """
        Returns the path, if it exists, that joins drone's position to target_cell
        while approaching the least possible any wall
        start_cell, target_cell : GRID COORDINATES
        """
        MAP = self.to_binary_map()

        for inflation in range(max_inflation, 0, -1):   # Decreasing inflation to find the safest path
            MAP_inflated = inflate_obstacles(MAP, inflation)
            start_x, start_y = next_point_free(MAP_inflated, *start_cell, max_inflation - inflation + 3)
            end_x, end_y = next_point_free(MAP_inflated, *target_cell, max_inflation - inflation + 3)

            path = a_star_search(MAP_inflated, (start_x, start_y), (end_x, end_y))

            if path:
                path_simplified = self.simplify_path(path, MAP_inflated) or [start_cell]
                return [self._conv_grid_to_world(x, y) for x, y in path_simplified]
        
        return [self._conv_grid_to_world(*start_cell)]*2

    def simplify_path(self, path, MAP):
        path_simplified = simplify_collinear_points(path)
        path_line_of_sight = simplify_by_line_of_sight(path_simplified, MAP)
        return ramer_douglas_peucker(path_line_of_sight, 0.5)