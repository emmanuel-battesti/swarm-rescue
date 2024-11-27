"""
At instant t, we give the drone a relative rotation command, and he takes the time he need (steps) to reach 
the desired angle.

"""
import math
import random
from typing import Optional

from spg_overlay.entities.drone_abstract import DroneAbstract
from spg_overlay.utils.misc_data import MiscData
from spg_overlay.utils.utils import normalize_angle

class MyDroneTurningV2(DroneAbstract):
    def __init__(self,
                 identifier: Optional[int] = None,
                 misc_data: Optional[MiscData] = None,
                 **kwargs):
        super().__init__(identifier=identifier,
                         misc_data=misc_data,
                         display_lidar_graph=False,
                         **kwargs)
        
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
        command = {"forward": 0.0,"lateral": 0.0,"rotation": self.continue_turning(),"grasper": 0}
        
        if self.close_to_wall():
            self.initiate_turning(-math.pi/2) # initialisation de la rotation
        else : 
            command["forward"] = 0.5

        return command

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
                return 0.0

            else : 
                kp = 1/math.pi
                a = kp * self.angle_left_to_turn
                a = min(a, 1.0)
                a = max(a, -1.0)
                return  a 
    
    """"
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
    