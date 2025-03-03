"""
At instant t, we give the drone a relative rotation command, and he takes the time he need (steps) to reach 
the desired angle.

"""
from enum import Enum
import math
import random
from typing import List, Optional, Tuple

import numpy as np
from spg_overlay.entities.drone_abstract import DroneAbstract
from spg_overlay.utils.misc_data import MiscData
from spg_overlay.utils.utils import normalize_angle,circular_mean
from spg_overlay.entities.drone_distance_sensors import DroneSemanticSensor
from spg_overlay.entities.rescue_center import RescueCenter
from spg_overlay.entities.wounded_person import WoundedPerson

class MyDroneTurningV2(DroneAbstract):

    class Activity(Enum):
        """
        All the states of the drone as a state machine
        """
        SEARCHING_WOUNDED = 1
        GRASPING_WOUNDED = 2
        SEARCHING_RESCUE_CENTER = 3
        DROPPING_AT_RESCUE_CENTER = 4
    
    
    def __init__(self,
                 identifier: Optional[int] = None,
                 misc_data: Optional[MiscData] = None,
                 **kwargs):
        super().__init__(identifier=identifier,
                         misc_data=misc_data,
                         display_lidar_graph=False,
                         **kwargs)
        

        self.state = self.Activity.SEARCHING_WOUNDED

        ############ PARAMETRES DE ROTATION ############
        
        # GENERAL :
        self.isTurning = False
        self.max_step_turning = 100
        self.step_turning = 0
        self.precision_rotation = 0.01

        # compass : 
        self.angleStopTurning = 0

        # no compass : 
        self.angle_left_to_turn = 0
        self.turn_with_odometer = False # si True, la rotation se fait avec l'odomètre
        self.initiated_with_odometer = False

        ################################################

    def define_message_for_all(self):
        """
        Here, we don't need communication...
        """
        pass
    
    def control(self):
        command = {"forward": 0.0,"lateral": 0.0,"rotation": 0,"grasper": 0}
        
        found_wounded, found_rescue_center, command_semantic = (
            self.process_semantic_sensor())
        

        if self.state is self.Activity.SEARCHING_WOUNDED and found_wounded:
            self.state = self.Activity.GRASPING_WOUNDED

        elif (self.state is self.Activity.GRASPING_WOUNDED and
              self.base.grasper.grasped_entities):
            self.state = self.Activity.SEARCHING_RESCUE_CENTER

        elif (self.state is self.Activity.GRASPING_WOUNDED and
              not found_wounded):
            self.state = self.Activity.SEARCHING_WOUNDED

        elif (self.state is self.Activity.SEARCHING_RESCUE_CENTER and
              found_rescue_center):
            self.state = self.Activity.DROPPING_AT_RESCUE_CENTER

        elif (self.state is self.Activity.DROPPING_AT_RESCUE_CENTER and
              not self.base.grasper.grasped_entities):
            self.state = self.Activity.SEARCHING_WOUNDED

        elif (self.state is self.Activity.DROPPING_AT_RESCUE_CENTER and
              not found_rescue_center):
            self.state = self.Activity.SEARCHING_RESCUE_CENTER

        print("state: {}, can_grasp: {}, grasped entities: {}"
              .format(self.state.name,
                      self.base.grasper.can_grasp,
                      self.base.grasper.grasped_entities))
        
          ##########
        # COMMANDS FOR EACH STATE
        # Searching randomly, but when a rescue center or wounded person is
        # detected, we use a special command
        ##########
        
        if self.state is self.Activity.SEARCHING_WOUNDED:
            command = self.explore()
            command["grasper"] = 0

        elif self.state is self.Activity.GRASPING_WOUNDED:
            command = command_semantic
            command["grasper"] = 1

        elif self.state is self.Activity.SEARCHING_RESCUE_CENTER:
            command = self.explore()
            command["grasper"] = 1

        elif self.state is self.Activity.DROPPING_AT_RESCUE_CENTER:
            command = command_semantic
            command["grasper"] = 1


        command["rotation"] = self.continue_turning()
        return command
        
    def process_semantic_sensor(self): # initie/force les rotations mais ne les continues jamais
        
        detection_semantic = self.semantic_values()
        found_wounded = False
        if (self.state is self.Activity.SEARCHING_WOUNDED
            or self.state is self.Activity.GRASPING_WOUNDED) \
                and detection_semantic is not None:
                scores = []
                for data in detection_semantic:
                    # If the wounded person detected is held by nobody
                    if (data.entity_type ==
                            DroneSemanticSensor.TypeEntity.WOUNDED_PERSON and
                            not data.grasped):
                        found_wounded = True
                        v = (data.angle * data.angle) + \
                            (data.distance * data.distance / 10 ** 5)
                        scores.append((v, data.angle, data.distance))

                # Select the best one among wounded persons detected
                best_score = 10000
                for score in scores:
                    if score[0] < best_score:
                        best_score = score[0]
                        best_angle = score[1]

        
        found_rescue_center = False
        is_near = False
        angles_list = []
        if (self.state is self.Activity.SEARCHING_RESCUE_CENTER
            or self.state is self.Activity.DROPPING_AT_RESCUE_CENTER) \
                and detection_semantic:
            for data in detection_semantic:
                if (data.entity_type ==
                        DroneSemanticSensor.TypeEntity.RESCUE_CENTER):
                    found_rescue_center = True
                    angles_list.append(data.angle)
                    is_near = (data.distance < 30)

            if found_rescue_center:
                best_angle = circular_mean(np.array(angles_list))
        
        if found_rescue_center or found_wounded:
            self.initiate_turning(best_angle)
        
        return found_wounded, found_rescue_center, {"forward": 0.5,"lateral": 0.0,"rotation": 0.0}


    # explore la carte avec le lidar en allant vers la plus grande ouverture et ne revenant pas sur ses pas
    def explore(self):

        start_index, end_index, direction = self.find_largest_opening_direction(self.lidar_values()[45:135])# devant lui

        # convertir la direction en angle en radians : direction = 0 -> angle = math.pi/2 direction = 90 -> angle = -math.pi/2
        angle = (direction - 90) * math.pi / 180
        self.initiate_turning(angle)
        command = {"forward": 0.5,"lateral": 0.0,"rotation": 0.0}
        return command


    def find_largest_opening_direction(self, data: List[float], threshold: float = 0.9) -> Tuple[int, int, int]:
        """
        Trouve la direction avec la plus grande ouverture basée sur les valeurs élevées.
        
        Args:
            data (List[float]): Liste des distances mesurées par le LIDAR.
            threshold (float): Pourcentage du maximum considéré comme haute valeur.
            
        Returns:
            Tuple[int, int, float]: Indice de début, indice de fin, et direction moyenne (milieu de la plage).
        """
        # if len(data) != 181:
        #     raise ValueError("La liste n'est pas au format LIDAR.")
        
        # Définir la limite inférieure pour les valeurs "élevées"
        max_value = max(data)
        min_high_value = threshold * max_value
        
        # Trouver les indices des valeurs élevées
        high_value_indices = [i for i, value in enumerate(data) if value >= min_high_value]
        
        if not high_value_indices:
            return self.find_largest_opening_direction(data, threshold=threshold - 0.1)
        
        # Identifier les plages consécutives
        ranges = []
        current_range = [high_value_indices[0]]

        for i in range(1, len(high_value_indices)):
            if high_value_indices[i] == high_value_indices[i - 1] + 1:
                current_range.append(high_value_indices[i])
            else:
                ranges.append(current_range)
                current_range = [high_value_indices[i]]

        # Ajouter la dernière plage
        ranges.append(current_range)
        
        # Trouver la plage la plus longue
        largest_range = max(ranges, key=len)
        
        # Calculer les indices et la direction moyenne
        start_index = largest_range[0]
        end_index = largest_range[-1]
        direction = (start_index + end_index) // 2
        
        return start_index, end_index, direction


    """
    Si drone a un ordre de rotation, renvoie commande pour continuer cet ordre (float).
    Si pas d'ordre de rotation, renvoie 0.0  (pas de rotation)
    """


    def continue_turning(self) -> float: 
        
        if not self.isTurning: 
                return 0.0
        
        precision = self.precision_rotation
        self.step_turning += 1
        
        # COMPASS DESACTIVE 
        if (self.compass_is_disabled() or self.initiated_with_odometer) or self.turn_with_odometer:
            print("TURNING WITH ODOMETER")
            step_angle_variation = self.odometer_values()[2]
            self.angle_left_to_turn = normalize_angle(self.angle_left_to_turn- step_angle_variation)
            
            if abs(self.angle_left_to_turn) < precision or self.step_turning > self.max_step_turning:
                self.isTurning = False
                self.step_turning = 0
                self.initiated_with_odometer = False
                self.angle_left_to_turn = 0
                return 0.0
            
            else : 
                kp = 1/math.pi
                a = kp * self.angle_left_to_turn
                a = min(a, 1.0)
                a = max(a, -1.0)
                return  a
        
        #  COMPAS ACTIF
        else :
            print("TURNING WITH COMPASS")
            compass_angle = normalize_angle(self.measured_compass_angle())
            self.angle_left_to_turn = normalize_angle(self.angleStopTurning - compass_angle)

            if abs(self.angle_left_to_turn) < precision or self.step_turning > self.max_step_turning:
                self.isTurning = False
                self.step_turning = 0
                self.angle_left_to_turn = 0
                self.angleStopTurning = 0
                return 0.0

            else : 
                kp = 1/math.pi
                a = kp * self.angle_left_to_turn
                a = min(a, 1.0)
                a = max(a, -1.0)
                return  a 
    
    """
    Initie une rotation du drone vers un angle donné en radian.
    
    Relancer une initiation de rotation alors que la précédente et entrain de s'éxécuter ne fait rien. (ancienne rotation continue)
    -> Pour forcer une nouvelle rotation, utiliser force_new_turning()

    Pour juste arrêter la rotation, utiliser stop_turning()

    Lorsque une rotation est initialisé dans une zone sans compas (ou avec odomètre), toute la rotation se fera avec l'odomètre.
    Par contre si on initie une rotation avec le compas, 
    et que le compas est désactivé pendant la rotation, la rotation continue avec l'odomètre. (pas besoin de relancer la rotation)
    """
    def initiate_turning(self, angle) -> None : # angle en radian
        if not self.isTurning: 
            
            # Compas desactivé
            if self.compass_is_disabled() or self.turn_with_odometer:
                self.initiated_with_odometer = True
                self.angle_left_to_turn = normalize_angle(angle)
                self.isTurning = True
            
            # Compas activé
            else :   
                compass_angle = normalize_angle(self.measured_compass_angle())
                self.angleStopTurning = normalize_angle(angle + compass_angle)
                self.isTurning = True

                # au cas ou il y ait un changement de zone : 
                self.angle_left_to_turn = normalize_angle(angle)
        return None

    def force_new_turning(self, angle) -> None:
        self.stop_turning_compass()
        self.initiate_turning_compass(angle) 
        return None
    
    def stop_turning(self) -> None:
        self.isTurning = False
        self.angle_left_to_turn = 0
        self.step_turning = 0
        self.initiated_with_odometer = False
        self.angleStopTurning = 0
        return None
    
    def close_to_wall(self):
        
        lidar = self.lidar_values()
        min_distance = min(lidar)

        if min_distance < 40:
            return True
        
        return False
    