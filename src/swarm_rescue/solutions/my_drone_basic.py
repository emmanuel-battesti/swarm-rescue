"""
Le drone suit les murs
"""

from enum import Enum
import math
from typing import Optional
import cv2
import numpy as np

from spg_overlay.entities.drone_abstract import DroneAbstract
from spg_overlay.utils.misc_data import MiscData
from spg_overlay.entities.drone_distance_sensors import DroneSemanticSensor
from spg_overlay.entities.rescue_center import RescueCenter
from spg_overlay.entities.wounded_person import WoundedPerson
from spg_overlay.utils.utils import circular_mean, normalize_angle


class MyDroneBasic(DroneAbstract):
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
        self.Kd_angle = 2*self.Kp_angle # correction dérivée
        self.Ki_angle = (1/10)*(1/20)*2/math.pi#4 # (1/10) * 1/20 # correction intégrale
        self.past_ten_errors_angle = [0]*10
        
        self.Kp_distance = 2/(abs(self.dmax-self.dist_to_stay))
        self.Ki_distance = 1/abs(self.dist_to_stay-self.dmax) *1/20 *1/10
        self.Kd_distance = 2*self.Kp_distance
        self.past_ten_errors_distance = [0]*10
        # -----------------------------------------
        
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
        
        # RECUPÈRATION INFORMATIONS SENSORS (LIDAR, SEMANTIC)
        found_wall,epsilon_wall_angle, min_dist = self.process_lidar_sensor(self.lidar())
        found_wounded, found_rescue_center,epsilon_wounded,epsilon_rescue_center,is_near_rescue_center = self.process_semantic_sensor()

        # paramètres responsables des transitions
        paramètres_transitions = { "found_wall": found_wall, "found_wounded": found_wounded, "found_rescue_center": found_rescue_center,"grasped_entities" : bool(self.base.grasper.grasped_entities), "\nstep_waiting_count": self.step_waiting_count} 
        
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

        # WAITING STATE
        if self.state is self.State.WAITING:
            self.step_waiting_count += 1
            return command_nothing

        elif  self.state is self.State.SEARCHING_WALL:
            return command_tout_droit
         
        elif  self.state is self.State.FOLLOWING_WALL:

            epsilon_wall_angle = normalize_angle(epsilon_wall_angle) 
            # self.log["epsilon_wall_angle"].append(epsilon_wall_angle)
            epsilon_wall_distance =  min_dist - self.dist_to_stay 
            # self.log["epsilon_wall_distance"].append(epsilon_wall_distance)
            
            self.logging_variables({"epsilon_wall_angle": epsilon_wall_angle, "epsilon_wall_distance": epsilon_wall_distance})
            ## LOGGING
            # self.timestep_count += 1
            # # Periodically flush the buffer to the log file
            # if self.timestep_count % self.flush_interval == 0 and self.record_log:
            #     mode = "w" if not self.log_initialized else "a"  # Open file in write mode only once pour écraser la data
            #     with open(self.log_file, mode) as log_file:
                    
            #         # Write the header if the log file is empty
            #         if not self.log_initialized:
            #             log_file.write("Timestep,Epsilon_Wall_Angle,Epsilon_Wall_Distance\n")
            #             self.log_initialized = True
                    
            #         for i in range(self.flush_interval):
            #             log_file.write(f"{self.timestep_count - self.flush_interval + i},"
            #                            f"{self.log['epsilon_wall_angle'][i]},"
            #                            f"{self.log['epsilon_wall_distance'][i]}\n")
                 
            #     self.log["epsilon_wall_distance"].clear()  # Clear the buffer
            #     self.log["epsilon_wall_angle"].clear()  # Clear the buffer

            
            command_following_walls = self.pid_controller(command_following_walls,epsilon_wall_angle,self.Kp_angle,self.Kd_angle,self.Ki_angle,self.past_ten_errors_angle,"rotation")
            command_following_walls = self.pid_controller(command_following_walls,epsilon_wall_distance,self.Kp_distance,self.Kd_distance,self.Ki_distance,self.past_ten_errors_distance,"lateral")
            #print(command_following_walls)
        
            return command_following_walls

        elif self.state is self.State.GRASPING_WOUNDED:
            
            epsilon_wounded_angle = normalize_angle(epsilon_wounded) 
            command_grasping_wounded = self.pid_controller(command_grasping_wounded,epsilon_wounded_angle,self.Kp_angle,self.Kd_angle,self.Ki_angle,self.past_ten_errors_angle,"rotation")
            
            return command_grasping_wounded

        elif self.state is self.State.SEARCHING_RESCUE_CENTER:
            epsilon_wall_angle = normalize_angle(epsilon_wall_angle) 
            epsilon_wall_distance =  min_dist - self.dist_to_stay 
            command_searching_rescue_center = self.pid_controller(command_searching_rescue_center,epsilon_wall_angle,self.Kp_angle,self.Kd_angle,self.Ki_angle,self.past_ten_errors_angle,"rotation")
            command_searching_rescue_center = self.pid_controller(command_searching_rescue_center,epsilon_wall_distance,self.Kp_distance,self.Kd_distance,self.Ki_distance,self.past_ten_errors_distance,"lateral")
            return command_searching_rescue_center
        
        elif self.state is self.State.GOING_RESCUE_CENTER:
            epsilon_rescue_center = normalize_angle(epsilon_rescue_center) 
            command_going_rescue_center = self.pid_controller(command_going_rescue_center,epsilon_rescue_center,self.Kp_angle,self.Kd_angle,self.Ki_angle,self.past_ten_errors_angle,"rotation")
            
            if is_near_rescue_center:
                command_going_rescue_center["forward"] = 0.0
                command_going_rescue_center["rotation"] = 1.0
            
            return command_going_rescue_center
        
        # STATE NOT FOUND raise error
        raise ValueError("State not found")
        return command_nothing
    
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
    def pid_controller(self,command,epsilon,Kp,Kd,Ki,past_ten_errors,mode):
        
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
        correction_integrale = Ki * sum(past_ten_errors)
        correction = correction_proportionnelle + correction_derivee + correction_integrale
        command[mode] = correction
        command[mode] = min( max(-1,correction) , 1 )


        if mode == "rotation" : 
            if correction > 0.8 :
                command["forward"] = self.speed_turning

        return command
    
    def state_update(self,found_wall,found_wounded,found_rescue_center):
        
        self.previous_state = self.state
        
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
        
        self.timestep_count += 1