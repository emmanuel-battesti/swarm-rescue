"""
Le drone suit un path après avoir trouvé le wounded person.

Chaque drone communique aux autres les nouvelles informations de mapping qu'il
a récoltés à chaque timestep. Tous les drones mettent à jour leur
occupancy grid en conséquence.
"""

from enum import Enum, auto
from collections import deque
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
from solutions.utils.pose import Pose
from spg_overlay.utils.grid import Grid
from solutions.utils.astar import *
from solutions.utils.messages import DroneMessage
from solutions.utils.grids import OccupancyGrid
from solutions.utils.dataclasses_config import *

class MyDroneFrontex(DroneAbstract):
    class State(Enum):
        """
        All the states of the drone as a state machine
        """
        WAITING = auto()    # Assigns 1

        SEARCHING_WALL = auto()     # Assigns 2 etc ... This allows to easily add new states
        FOLLOWING_WALL = auto()

        EXPLORING_FRONTIERS = auto()

        GRASPING_WOUNDED = auto()
        SEARCHING_RESCUE_CENTER = auto()
        GOING_RESCUE_CENTER = auto()

        SEARCHING_RETURN_AREA = auto()
        GOING_RETURN_AREA = auto()

    def __init__(self,
                 identifier: Optional[int] = None,
                 misc_data: Optional[MiscData] = None,
                 **kwargs):
        super().__init__(identifier=identifier,
                         misc_data=misc_data,
                         **kwargs)
        
        # MAPPING
        self.mapping_params = MappingParams()
        self.estimated_pose = Pose() # Fonctionne commant sans le GPS ?  erreur ou qu'est ce que cela retourne ? 
        self.grid = OccupancyGrid(size_area_world=self.size_area,
                                  resolution=self.mapping_params.resolution,
                                  lidar=self.lidar())

        # POSITION
        self.previous_position = deque(maxlen=1) 
        self.previous_position.append((0,0))  
        self.previous_orientation = deque(maxlen=1) 
        self.previous_orientation.append(0) 

        # STATE INITIALISATION
        self.state  = self.State.WAITING
        self.previous_state = self.State.WAITING # Utile pour vérfier que c'est la première fois que l'on rentre dans un état
        
        # WAITING STATE
        self.waiting_params = WaitingStateParams()

        # GRASPING 
        self.grasping_params = GraspingParams()

        # WALL FOLLOWING
        self.wall_following_params = WallFollowingParams()

        # FRONTIER EXPLORATION
        self.reached_frontier = True

        # PID PARAMS
        self.pid_params = PIDParams()
        self.past_ten_errors_angle = [0] * 10
        self.past_ten_errors_distance = [0] * 10
        
        # PATH FOLLOWING
        self.path_params = PathParams()
        self.indice_current_waypoint = 0
        self.inital_point_path = (0,0)
        self.finished_path = False
        self.path = []
        self.path_grid = []

        # LOG PARAMS
        self.log_params = LogParams()     
      
    def define_message_for_all(self):
        message = self.grid.to_update(pose=self.estimated_pose)
        return message

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
                
                # CREATION DU PATH : 
                
                # enregistre la position lorsque l'on rentre dans LE STATE. -> use to make l'asservissement lateral
                self.inital_point_path = self.estimated_pose.position[0],self.estimated_pose.position[1]
                MAP = self.grid.to_binary_map() # Convertit la MAP de proba en MAP binaire
                grid_initial_point_path = self.grid._conv_world_to_grid(self.inital_point_path[0],self.inital_point_path[1]) # initial point in grid coordinates

                # On élargie les mur au plus large possible pour trouver un chemin qui passe le plus loin des murs/obstacles possibles.
                Max_inflation =  7
                for x in range(Max_inflation+1):
                    #print("inflation : ",Max_inflation - x)
                    MAP_inflated = inflate_obstacles(MAP,Max_inflation-x)
                    # redefinir le start comme le point libre le plus proche de la position actuelle à distance max d'inflation pour pas que le point soit inacessible.
                    # SUREMENT UNE MEILLEUR MANIERE DE FAIRE.
                    start_point_x, start_point_y = next_point_free(MAP_inflated,grid_initial_point_path[0],grid_initial_point_path[1],Max_inflation-x + 3)
                    end_point_x, end_point_y = next_point_free(MAP_inflated,self.grid.initial_cell[0],self.grid.initial_cell[1],Max_inflation-x+ 3) # initial cell already in grid coordinates.
                    path = a_star_search(MAP_inflated,(start_point_x,start_point_y),(end_point_x,end_point_y))
                    
                    if len(path) > 0:
                        #print( f"inflation : {Max_inflation-(x)}")
                        break
                
                # Remove colinear points
                path_simplified = simplify_collinear_points(path)

                # Simplification par ligne de vue
                path_line_of_sight = simplify_by_line_of_sight(path_simplified, MAP_inflated)
               
                # Simplification par Ramer-Douglas-Peucker avec epsilon = 0.5 par exemple
                path_rdp = ramer_douglas_peucker(path_line_of_sight, 0.5)
                self.path_grid = path_rdp
                self.path = [self.grid._conv_grid_to_world(x,y) for x,y in self.path_grid]
                self.indice_current_waypoint = 0
                #print("Path calculated")
                
            command = self.follow_path(self.path)
            return command
        
        elif self.state is self.State.GOING_RESCUE_CENTER:
            epsilon_rescue_center = normalize_angle(epsilon_rescue_center) 
            command_going_rescue_center = self.pid_controller(command_going_rescue_center,epsilon_rescue_center,self.Kp_angle,self.Kd_angle,self.Ki_angle,self.past_ten_errors_angle,"rotation")
            
            if is_near_rescue_center:
                command_going_rescue_center["forward"] = 0.0
                command_going_rescue_center["rotation"] = 1.0
            
            return command_going_rescue_center
        
        elif self.state is self.State.EXPLORING_FRONTIERS:
            # Calculate path at the beginning of the state
            self.grid.frontiers_update()
            if self.reached_frontier:
                # CREATION DU PATH : 
                
                # enregistre la position lorsque l'on rentre dans LE STATE. -> use to make l'asservissement lateral
                self.inital_point_path = self.estimated_pose.position[0],self.estimated_pose.position[1]
                MAP = self.grid.to_binary_map() # Convertit la MAP de proba en MAP binaire
                grid_initial_point_path = self.grid._conv_world_to_grid(self.inital_point_path[0],self.inital_point_path[1]) # initial point in grid coordinates

                # On élargie les mur au plus large possible pour trouver un chemin qui passe le plus loin des murs/obstacles possibles.
                Max_inflation =  7
                for x in range(Max_inflation+1):
                    #print("inflation : ",Max_inflation - x)
                    MAP_inflated = inflate_obstacles(MAP,Max_inflation-x)
                    # redefinir le start comme le point libre le plus proche de la position actuelle à distance max d'inflation pour pas que le point soit inacessible.
                    # SUREMENT UNE MEILLEUR MANIERE DE FAIRE.
                    start_point_x, start_point_y = next_point_free(MAP_inflated,grid_initial_point_path[0],grid_initial_point_path[1],Max_inflation-x + 3)
                    closest_centroid_frontier = self.grid.closest_centroid_frontier(self.estimated_pose)
                    print()
                    print(closest_centroid_frontier)
                    print()
                    end_point_x, end_point_y = next_point_free(MAP_inflated,closest_centroid_frontier[0],closest_centroid_frontier[1],Max_inflation-x+ 3) # initial cell already in grid coordinates.
                    world_end_pose = self.grid._conv_grid_to_world(end_point_x,end_point_y)
                    path = a_star_search(MAP_inflated,(start_point_x,start_point_y),(end_point_x,end_point_y))
                    self.finished_path = False
                    
                    if len(path) > 0:
                        #print( f"inflation : {Max_inflation-(x)}")
                        break
                
                # Remove colinear points
                path_simplified = simplify_collinear_points(path)

                # Simplification par ligne de vue
                path_line_of_sight = simplify_by_line_of_sight(path_simplified, MAP_inflated)
               
                # Simplification par Ramer-Douglas-Peucker avec epsilon = 0.5 par exemple
                path_rdp = ramer_douglas_peucker(path_line_of_sight, 0.5)
                self.path_grid = path_rdp
                self.path = [self.grid._conv_grid_to_world(x,y) for x,y in self.path_grid]
                self.indice_current_waypoint = 0
                #print("Path calculated")
                self.reached_frontier = False
            command = self.follow_path(self.path)
            if self.finished_path:
                self.reached_frontier = True
            return command

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
                    DroneSemanticSensor.TypeEntity.WOUNDED_PERSON and not data.grasped):
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
            deriv_epsilon = -np.sin(self.odometer_values()[1])*self.odometer_values()[0] # vitesse latérale
        elif mode == "forward" : 
            deriv_epsilon = self.odometer_values()[0]*np.cos(self.odometer_values()[1]) # vitesse longitudinale
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
        if distance_to_waypoint < self.distance_close_waypoint:
            #print(f"WAYPOINT {self.indice_current_waypoint} REACH")
            return True
        return False

    def follow_path(self,path):
        if self.is_near_waypoint(path[self.indice_current_waypoint]):
            self.indice_current_waypoint += 1 # next point in path
            #print(f"Waypoint reached {self.indice_current_waypoint}")
            if self.indice_current_waypoint >= len(path):
                self.finished_path = True # NOT USE YET
                self.indice_current_waypoint = 0
                self.path = []
                self.path_grid = []
                return
        
        return self.go_to_waypoint(path[self.indice_current_waypoint][0],path[self.indice_current_waypoint][1])

    def go_to_waypoint(self,x,y):
        
        # ASSERVISSEMENT EN ANGLE
        dx = x - self.estimated_pose.position[0]
        dy = y - self.estimated_pose.position[1]
        epsilon = math.atan2(dy,dx) - self.estimated_pose.orientation
        epsilon = normalize_angle(epsilon)
        command_path = self.pid_controller({"forward": 1,"lateral": 0.0,"rotation": 0.0,"grasper": 1},epsilon,self.Kp_angle_1,self.Kd_angle_1,self.Ki_angle,self.past_ten_errors_angle,"rotation",0.5)

        # ASSERVISSEMENT LATERAL
        if self.indice_current_waypoint == 0:
            x_previous_waypoint,y_previous_waypoint = self.inital_point_path
        else : 
            x_previous_waypoint,y_previous_waypoint = self.path[self.indice_current_waypoint-1][0],self.path[self.indice_current_waypoint-1][1]

        epsilon_distance = compute_relative_distance_to_droite(x_previous_waypoint,y_previous_waypoint,x,y,self.estimated_pose.position[0],self.estimated_pose.position[1])
        # epsilon distance needs to be signed (positive if the angle relative to the theoritical path is positive)
        command_path = self.pid_controller(command_path,epsilon_distance,self.Kp_distance_1,self.Kd_distance_1,self.Ki_distance_1,self.past_ten_errors_distance,"lateral",0.5)
        
        # ASSERVISSENT EN DISTANCE 
        epsilon_distance_to_waypoint = np.linalg.norm(np.array([x,y]) - self.estimated_pose.position)
        #command_path = self.pid_controller(command_path,epsilon_distance_to_waypoint,self.Kp_distance,self.Kd_distance,self.Ki_distance,self.past_ten_errors_distance,"forward",1)

        return command_path

    def state_update(self,found_wall,found_wounded,found_rescue_center):
        
        self.previous_state = self.state
        #print(f"Previous state : {self.previous_state}")
        
        # Exploring the map by following walls

        if ((self.state in (self.State.SEARCHING_WALL,self.State.FOLLOWING_WALL)) and (found_wounded)):
            self.state = self.State.GRASPING_WOUNDED
        
        elif (self.state is self.State.SEARCHING_WALL and found_wall):
            self.state = self.State.FOLLOWING_WALL
        
        elif (self.state is self.State.FOLLOWING_WALL and not found_wall):
            self.state = self.State.SEARCHING_WALL

        # Exploring the map by exploring frontiers

        if (self.state is self.State.EXPLORING_FRONTIERS and len(self.grid.frontiers)==0):
            print("frontiers",self.grid.frontiers)
            self.grid.frontiers_update()
            print("frontiers",self.grid.frontiers)
            self.grid.frontiers_update()
            print("frontiers",self.grid.frontiers)
            self.state = self.State.FOLLOWING_WALL
        
        # Getting back to rescue center with a wounded person

        elif (self.state is self.State.GRASPING_WOUNDED and not found_wounded and not self.base.grasper.grasped_entities):
            self.state = self.State.WAITING
        
        elif (self.state is self.State.WAITING and self.step_waiting_count >= self.step_waiting):
            self.state = self.State.EXPLORING_FRONTIERS
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
        #print(f"State : {self.state}")
    
    def mapping(self, display = False):
        
        if self.timestep_count == 1: # first iteration
            print("Starting control")
            start_x, start_y = self.measured_gps_position() # never none ? 
            print(f"Initial position: {start_x}, {start_y}")
            self.grid.set_initial_cell(start_x, start_y)
        

        self.estimated_pose = Pose(np.asarray(self.measured_gps_position()),
                                   self.measured_compass_angle(),self.odometer_values(),self.previous_position[-1],self.previous_orientation[-1],self.size_area)
        
        self.previous_position.append(self.estimated_pose.position)
        self.previous_orientation.append(self.estimated_pose.orientation)
        
        grid_update_informations = self.grid.to_update(pose=self.estimated_pose)
        if self.communicator:
            received_messages = self.communicator.received_messages
            for msg in received_messages:
                message = msg[1]
                grid_update_informations += message
        self.grid.update(grid_update_informations)
        
        if display and (self.timestep_count % 5 == 0):
             self.grid.display(self.grid.zoomed_grid,
                               self.estimated_pose,
                               title=f"Drone {self.identifier} zoomed occupancy grid")

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
        
    def draw_top_layer(self):
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