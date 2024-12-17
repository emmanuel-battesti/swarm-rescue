"""
Le drone suit un path après avoir trouver le wounded person.
"""

from enum import Enum
import math
from typing import Optional
import cv2
import numpy as np
import arcade

from spg_overlay.utils.constants import MAX_RANGE_LIDAR_SENSOR
from spg_overlay.entities.drone_abstract import DroneAbstract
from spg_overlay.utils.misc_data import MiscData
from spg_overlay.entities.drone_distance_sensors import DroneSemanticSensor
from spg_overlay.entities.rescue_center import RescueCenter
from spg_overlay.entities.wounded_person import WoundedPerson
from spg_overlay.utils.utils import circular_mean, normalize_angle
from spg_overlay.utils.pose import Pose
from spg_overlay.utils.grid import Grid
from spg_overlay.utils.astar import *

class OccupancyGrid(Grid):
    """Simple occupancy grid"""

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
        1 = obstacle
        0 = free
        Cells with value >= 0 are considered obstacles.
        Cells with value < 0 are considered free.
        """
        print(np.count_nonzero(self.grid < 0))
        binary_map = np.zeros_like(self.grid, dtype=int)
        binary_map[self.grid >= 0] = 1
        return binary_map
    
    def update_grid(self, pose: Pose):
        """
        Bayesian map update with new observation
        lidar : lidar data
        pose : corrected pose in world coordinates
        """
        EVERY_N = 3
        LIDAR_DIST_CLIP = 40.0
        EMPTY_ZONE_VALUE = -0.602
        OBSTACLE_ZONE_VALUE = 2.0
        FREE_ZONE_VALUE = -4.0

        THRESHOLD_MIN = -40
        THRESHOLD_MAX = 40

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
            self.add_value_along_line(pose.position[0], pose.position[1],
                                      pt_x, pt_y,
                                      EMPTY_ZONE_VALUE)

        # For obstacle zones, all values of lidar_dist are < max_range
        select_collision = lidar_dist < max_range

        points_x = pose.position[0] + np.multiply(lidar_dist, cos_rays)
        points_y = pose.position[1] + np.multiply(lidar_dist, sin_rays)

        points_x = points_x[select_collision]
        points_y = points_y[select_collision]

        self.add_points(points_x, points_y, OBSTACLE_ZONE_VALUE)

        # the current position of the drone is free !
        self.add_points(pose.position[0], pose.position[1], FREE_ZONE_VALUE)

        # threshold values
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

class MyDroneFollowingPath(DroneAbstract):
    class State(Enum):
        """
        All the states of the drone as a state machine
        """
        WAITING = 1
        SEARCHING_WALL = 2
        FOLLOWING_WALL = 3
        GRASPING_WOUNDED = 4
        SEARCHING_RESCUE_CENTER = 5
        GOING_RESCUE_CENTER = 6
        SEARCHING_RETURN_AREA = 7
        GOING_RETURN_AREA = 8

    def __init__(self,
                 identifier: Optional[int] = None,
                 misc_data: Optional[MiscData] = None,
                 **kwargs):
        super().__init__(identifier=identifier,
                         misc_data=misc_data,
                         **kwargs)
        
        # MAPING
        self.estimated_pose = Pose() # Fonctionne que avec gps
        resolution = 8 # pourquoi ?  Ok bon compromis entre précision et temps de calcul
        self.grid = OccupancyGrid(size_area_world=self.size_area,
                                  resolution=resolution,
                                  lidar=self.lidar())
        self.default_initial_cell_value = -10.0
        self.display_map = True

        # Initialisation du state
        self.state  = self.State.SEARCHING_WALL
        self.previous_state = self.State.SEARCHING_WALL # Debugging purpose
        
        # WAITING STATE
        self.step_waiting = 50 # step waiting without mooving when loosing the sight of wounded
        self.step_waiting_count = 0

        # GRASPING 
        self.grasping_speed = 0.3

        # Paramètre following walls ---------------------
        self.dmax = 60 # distance max pour suivre un mur
        self.dist_to_stay = 40 # distance à laquelle on veut rester du mur
        self.speed_following_wall = 0.3
        self.speed_turning = 0.05

        self.Kp_angle = 4/math.pi # correction proportionnelle # theoriquement j'aurais du mettre 2
        self.Kp_angle_1 = 9/math.pi
        self.Kd_angle_1 = self.Kp_angle_1/10
        self.Kd_angle =self.Kp_angle/10 # correction dérivée
        self.Ki_angle = (1/10)*(1/20)*2/math.pi#4 # (1/10) * 1/20 # correction intégrale
        self.past_ten_errors_angle = [0]*10
        

        self.Kp_distance_1 = 2/(abs(10))
        self.Ki_distance_1 = 1/abs(10) *1/20 *1/10
        self.Kd_distance_1 = 2*self.Kp_distance_1


        self.Kp_distance = 2/(abs(self.dmax-self.dist_to_stay))
        self.Ki_distance = 1/abs(self.dist_to_stay-self.dmax) *1/20 *1/10
        self.Kd_distance = 2*self.Kp_distance
        self.past_ten_errors_distance = [0]*10
        # -----------------------------------------
        
        # following path
        self.indice_current_waypoint = 0
        self.inital_point_path = (0,0)
        self.finished_path = False
        self.path = []

        # paramètres logs
        self.record_log = True
        self.log_file = "logs/log.txt"
        self.log_initialized = False
        self.flush_interval = 50  # Number of timesteps before flushing buffer
        self.timestep_count = 0  # Counter to track timesteps        
      
    def define_message_for_all(self):
        """
        Here, we don't need communication...
        """
        pass

    def control(self):
        
        # increment the iteration counter
        self.timestep_count += 1
        
        # MAPPING
        self.mapping(display = self.display_map)
        
        # RECUPÈRATION INFORMATIONS SENSORS (LIDAR, SEMANTIC)
        found_wall,epsilon_wall_angle, min_dist = self.process_lidar_sensor(self.lidar())
        found_wounded, found_rescue_center,epsilon_wounded,epsilon_rescue_center,is_near_rescue_center = self.process_semantic_sensor()

        # paramètres responsables des transitions

        paramètres_transitions = { "found_wall": found_wall, "found_wounded": found_wounded, "found_rescue_center": found_rescue_center,"grasped_entities" : bool(self.base.grasper.grasped_entities), "\nstep_waiting_count": self.step_waiting_count} 
        #print(paramètres_transitions)
        # TRANSITIONS OF THE STATE 
        self.state_update(found_wall,found_wounded,found_rescue_center)

        ##########
        # COMMANDS FOR EACH STATE
        ##########
        command_nothing = {"forward": 0.0,"lateral": 0.0,"rotation": 0.0,"grasper": 0}
        command_following_walls = {"forward": self.speed_following_wall,"lateral": 0.0,"rotation": 0.0,"grasper": 0}
        command_grasping_wounded = {"forward": self.grasping_speed,"lateral": 0.0,"rotation": 0.0,"grasper": 1}
        command_tout_droit = {"forward": 0.5,"lateral": 0.0,"rotation": 0.0,"grasper": 0}
        command_searching_rescue_center = {"forward": self.speed_following_wall,"lateral": 0.0,"rotation": 0.0,"grasper": 1}
        command_going_rescue_center = {"forward": 3*self.grasping_speed,"lateral": 0.0,"rotation": 0.0,"grasper": 1}
        command_following_path_with_wounded = {"forward": 0.5,"lateral": 0.0,"rotation": 0.0,"grasper": 1}

        # WAITING STATE
        if self.state is self.State.WAITING:
            self.step_waiting_count += 1
            return command_nothing

        elif  self.state is self.State.SEARCHING_WALL:
            return command_tout_droit
         
        elif  self.state is self.State.FOLLOWING_WALL:

            epsilon_wall_angle = normalize_angle(epsilon_wall_angle) 
            epsilon_wall_distance =  min_dist - self.dist_to_stay 
            
            self.logging_variables({"epsilon_wall_angle": epsilon_wall_angle, "epsilon_wall_distance": epsilon_wall_distance})
            
            command_following_walls = self.pid_controller(command_following_walls,epsilon_wall_angle,self.Kp_angle,self.Kd_angle,self.Ki_angle,self.past_ten_errors_angle,"rotation")
            command_following_walls = self.pid_controller(command_following_walls,epsilon_wall_distance,self.Kp_distance,self.Kd_distance,self.Ki_distance,self.past_ten_errors_distance,"lateral")
        
            return command_following_walls

        elif self.state is self.State.GRASPING_WOUNDED:
            
            epsilon_wounded_angle = normalize_angle(epsilon_wounded) 
            command_grasping_wounded = self.pid_controller(command_grasping_wounded,epsilon_wounded_angle,self.Kp_angle,self.Kd_angle,self.Ki_angle,self.past_ten_errors_angle,"rotation")
            
            return command_grasping_wounded

        elif self.state is self.State.SEARCHING_RESCUE_CENTER:
            # Calculate path at the beginning of the state
            if self.previous_state is not self.State.SEARCHING_RESCUE_CENTER:
                #print(self.grid.grid)
                #print(np.count_nonzero(self.grid.grid < 0 ))
                self.inital_point_path = self.estimated_pose.position[0],self.estimated_pose.position[1]
                MAP = self.grid.to_binary_map()
                grid_current_pose = self.grid._conv_world_to_grid(self.estimated_pose.position[0],self.estimated_pose.position[1])

                Max_inflation = 4
                for x in range(Max_inflation+1):
                    print("iteration",x)
                    MAP_inflated = inflate_obstacles(MAP,Max_inflation-(x))
                    # redefinir le start comme le point libre le plus proche de la position actuelle.
                    start_point_x, start_point_y = next_point_free(MAP_inflated,grid_current_pose[0],grid_current_pose[1])
                    end_point_x, end_point_y = next_point_free(MAP_inflated,self.grid.initial_cell[0],self.grid.initial_cell[1])
                    print(f"Start point : {start_point_x},{start_point_y}")
                    print(f"verify : {MAP_inflated[start_point_x][start_point_y]}")
                    # nombres de 0 dans Map_inflated
                    #print(f"Nombre de 0 dans Map_inflated : {np.count_nonzero(MAP_inflated == 0)}")
                    path = a_star_search(MAP_inflated,(start_point_x,start_point_y),self.grid.initial_cell)
                    
                    if len(path) > 0:
                        print( f"inflation : {Max_inflation-(x)}")
                        break
                
                path_simplified = simplify_collinear_points(path)

                # 2.1. Simplification par ligne de vue
                path_line_of_sight = simplify_by_line_of_sight(path_simplified, MAP_inflated)
                print(path_simplified)
                # 2.2. Simplification par Ramer-Douglas-Peucker avec epsilon = 0.5 par exemple
                path_rdp = ramer_douglas_peucker(path_line_of_sight, 0.5)
                path_rdp_world = [self.grid._conv_grid_to_world(x,y) for x,y in path_rdp]
                self.indice_current_waypoint = 0
                print("Path calculated")
                self.path = path_rdp_world
                
                print(self.path)

            command = self.follow_path(self.path)
            
            return command
        
        elif self.state is self.State.GOING_RESCUE_CENTER:
            epsilon_rescue_center = normalize_angle(epsilon_rescue_center) 
            command_going_rescue_center = self.pid_controller(command_going_rescue_center,epsilon_rescue_center,self.Kp_angle,self.Kd_angle,self.Ki_angle,self.past_ten_errors_angle,"rotation")
            
            if is_near_rescue_center:
                command_going_rescue_center["forward"] = 0.0
                command_going_rescue_center["rotation"] = 1.0
            
            return command_going_rescue_center
        
        # STATE NOT FOUND raise error
        raise ValueError("State not found")
    
    def process_semantic_sensor(self):
        semantic_values = self.semantic_values()
        
        best_angle_wounded = 0
        best_angle_rescue_center = 0
        found_wounded = False
        found_rescue_center = False
        is_near_rescue_center = False
        angles_list = []

        scores = []
        for data in semantic_values:
            if (data.entity_type == DroneSemanticSensor.TypeEntity.RESCUE_CENTER):
                found_rescue_center = True
                angles_list.append(data.angle)
                is_near_rescue_center = (data.distance < 30)
                best_angle_rescue_center = circular_mean(np.array(angles_list))
            
            # If the wounded person detected is held by nobody
            elif (data.entity_type ==
                    DroneSemanticSensor.TypeEntity.WOUNDED_PERSON):
                found_wounded = True
                v = (data.angle * data.angle) + \
                    (data.distance * data.distance / 10 ** 5)
                scores.append((v, data.angle, data.distance))

        # Select the best one among wounded persons detected
        best_score = 10000
        for score in scores:
            if score[0] < best_score:
                best_score = score[0]
                best_angle_wounded = score[1]

        return found_wounded,found_rescue_center,best_angle_wounded,best_angle_rescue_center,is_near_rescue_center
    
    def process_lidar_sensor(self,self_lidar):
        """
        -> ( bool near_obstacle , float epsilon_wall_angle )
        where epsilon_wall_angle is the (counter-clockwise convention) angle made
        between the drone and the nearest wall - pi/2
        """
        lidar_values = self_lidar.get_sensor_values()

        if lidar_values is None:
            return (False,0)
        
        ray_angles = self_lidar.ray_angles
        size = self_lidar.resolution

        angle_nearest_obstacle = 0
        if size != 0:
            min_dist = min(lidar_values)
            angle_nearest_obstacle = ray_angles[np.argmin(lidar_values)]

        near_obstacle = False
        if min_dist < self.dmax: # pourcentage de la vitesse je pense
            near_obstacle = True

        epsilon_wall_angle = angle_nearest_obstacle - np.pi/2

        return (near_obstacle,epsilon_wall_angle,min_dist)

    # Takes the current relative error and with a PID controller, returns the command
    # mode : "rotation" or "lateral" for now could be speed or other if implemented
    def pid_controller(self,command,epsilon,Kp,Kd,Ki,past_ten_errors,mode,command_slow = 0.8):
        
        past_ten_errors.pop(0)
        past_ten_errors.append(epsilon)
        if mode == "rotation":
            epsilon = normalize_angle(epsilon)
            deriv_epsilon = normalize_angle(self.odometer_values()[2])
        elif mode == "lateral":
            deriv_epsilon = - np.sin(self.odometer_values()[1])*self.odometer_values()[0] # vitesse latérale
        else : 
            raise ValueError("Mode not found")
        
        correction_proportionnelle = Kp * epsilon
        correction_derivee = Kd * deriv_epsilon
        correction_integrale = 0
        #correction_integrale = Ki * sum(past_ten_errors)
        correction = correction_proportionnelle + correction_derivee + correction_integrale
        command[mode] = correction
        command[mode] = min( max(-1,correction) , 1 )


        if mode == "rotation" : 
            if correction > command_slow :
                command["forward"] = self.speed_turning

        return command
    
    def is_near_waypoint(self,waypoint):
        distance_to_waypoint = np.linalg.norm(waypoint - self.estimated_pose.position)
        print(f"Distance to waypoint : {distance_to_waypoint}")
        if distance_to_waypoint < 20:
            print("WAYPOINT REACH")
            return True
        return False

    def follow_path(self,path):
        if self.is_near_waypoint(path[self.indice_current_waypoint]):
            self.indice_current_waypoint += 1
            #print(f"Waypoint reached {self.indice_current_waypoint}")
            if self.indice_current_waypoint >= len(path):
                self.finished_path = True
                self.indice_current_waypoint = 0
                return
        return self.go_to_waypoint(path[self.indice_current_waypoint][0],path[self.indice_current_waypoint][1])

    def go_to_waypoint(self,x,y):
        # ASSERVISSEMENT EN ANGLE
        dx = x - self.estimated_pose.position[0]
        dy = y - self.estimated_pose.position[1]
        epsilon = math.atan2(dy,dx) - self.estimated_pose.orientation
        epsilon = normalize_angle(epsilon)
        print(f"Epsilon : {epsilon}")
        command_path = self.pid_controller({"forward": 1,"lateral": 0.0,"rotation": 0.0,"grasper": 1},epsilon,self.Kp_angle_1,self.Kd_angle_1,self.Ki_angle,self.past_ten_errors_angle,"rotation",0.5)

        # ASSERVISSEMENT LATERAL
        if self.indice_current_waypoint == 0:
            x_previous_waypoint,y_previous_waypoint = self.inital_point_path
        else : 
            x_previous_waypoint,y_previous_waypoint = self.path[self.indice_current_waypoint-1][0],self.path[self.indice_current_waypoint-1][1]

        epsilon_distance = compute_relative_distance_to_droite(x_previous_waypoint,y_previous_waypoint,x,y,self.estimated_pose.position[0],self.estimated_pose.position[1])
        # epsilon distance needs to be signed (positive if the drone is on the left of the path)

        print(f"Epsilon distance : {epsilon_distance}")
        command_path = self.pid_controller(command_path,epsilon_distance,self.Kp_distance_1,self.Kd_distance_1,self.Ki_distance_1,self.past_ten_errors_distance,"lateral",0.5)
        
        return command_path

    def state_update(self,found_wall,found_wounded,found_rescue_center):
        
        self.previous_state = self.state
        #print(f"Previous state : {self.previous_state}")
        if ((self.state in (self.State.SEARCHING_WALL,self.State.FOLLOWING_WALL)) and (found_wounded)):
            self.state = self.State.GRASPING_WOUNDED
        
        elif (self.state is self.State.SEARCHING_WALL and found_wall):
            self.state = self.State.FOLLOWING_WALL
        
        elif (self.state is self.State.FOLLOWING_WALL and not found_wall):
            self.state = self.State.SEARCHING_WALL
        
        elif (self.state is self.State.GRASPING_WOUNDED and not found_wounded and not self.base.grasper.grasped_entities):
            self.state = self.State.WAITING
        
        elif (self.state is self.State.WAITING and self.step_waiting_count >= self.step_waiting):
            self.state = self.State.SEARCHING_WALL
            self.step_waiting_count = 0
        
        elif (self.state is self.State.WAITING and found_wounded):
            self.state = self.State.GRASPING_WOUNDED
            self.step_waiting_count = 0
        
        elif (self.state is self.State.GRASPING_WOUNDED and bool(self.base.grasper.grasped_entities)):
            self.state = self.State.SEARCHING_RESCUE_CENTER
        
        elif ((self.state in (self.State.SEARCHING_RESCUE_CENTER, self.State.GOING_RESCUE_CENTER)) and (not self.base.grasper.grasped_entities)):
            self.state = self.State.WAITING
        
        elif (self.state is self.State.SEARCHING_RESCUE_CENTER and found_rescue_center):
            self.state = self.State.GOING_RESCUE_CENTER

        print(f"State : {self.state}")
    def mapping(self, display = False):
        
        if self.timestep_count == 1:
            print("Starting control")
            start_x, start_y = self.measured_gps_position()
            print(f"Initial position: {start_x}, {start_y}")
            self.grid.set_initial_cell(start_x, start_y)
        
        self.estimated_pose = Pose(np.asarray(self.measured_gps_position()),
                                   self.measured_compass_angle())
        
        self.grid.update_grid(pose=self.estimated_pose)
        
        if display and (self.timestep_count % 5 == 0):
             self.grid.display(self.grid.grid,
                               self.estimated_pose,
                               title="occupancy grid")
             self.grid.display(self.grid.zoomed_grid,
                               self.estimated_pose,
                               title="zoomed occupancy grid")

    # Use this function only at one place in the control method. Not handled othewise.
    # params : variables_to_log : dict of variables to log with keys as variable names and values as variable values.
    def logging_variables(self, variables_to_log):
        """
        Buffers and logs variables to the log file when the buffer reaches the flush interval.

        :param variables_to_log: dict of variables to log with keys as variable names 
                                and values as variable values.
        """
        if not self.record_log:
            return

        # Initialize the log buffer if not already done
        if not hasattr(self, "log_buffer"):
            self.log_buffer = []

        # Append the current variables to the buffer
        log_entry = {"Timestep": self.timestep_count, **variables_to_log}
        self.log_buffer.append(log_entry)

        # Write the buffer to file when it reaches the flush interval
        if len(self.log_buffer) >= self.flush_interval:
            mode = "w" if not self.log_initialized else "a"
            with open(self.log_file, mode) as log_file:
                # Write the header if not initialized
                if not self.log_initialized:
                    headers = ",".join(log_entry.keys())
                    log_file.write(headers + "\n")
                    self.log_initialized = True

                # Write buffered entries
                for entry in self.log_buffer:
                    line = ",".join(map(str, entry.values()))
                    log_file.write(line + "\n")

            # Clear the buffer
            self.log_buffer.clear()
        

    def draw_bottom_layer(self):
        #self.draw_setpoint()
        self.draw_path(self.path)

    def draw_setpoint(self):
        half_width = self._half_size_array[0]
        half_height = self._half_size_array[1]
        pt1 = np.array([half_width, 0])
        pt2 =  np.array([half_width, 2 * half_height])
        arcade.draw_line(float(pt2[0]),
                         float(pt2[1]),
                         float(pt1[0]),
                         float(pt1[1]),
                         color=arcade.color.GRAY)


    def draw_path(self, path):
        length = len(path)
        # print(length)
        pt2 = None
        for ind_pt in range(length):
            pose = path[ind_pt]
            pt1 = pose + self._half_size_array
            # print(ind_pt, pt1, pt2)
            if ind_pt > 0:
                arcade.draw_line(float(pt2[0]),
                                 float(pt2[1]),
                                 float(pt1[0]),
                                 float(pt1[1]), [125,125,125])
            pt2 = pt1