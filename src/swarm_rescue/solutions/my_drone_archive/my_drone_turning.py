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

class MyDroneTurning(DroneAbstract):
    def __init__(self,
                 identifier: Optional[int] = None,
                 misc_data: Optional[MiscData] = None,
                 **kwargs):
        super().__init__(identifier=identifier,
                         misc_data=misc_data,
                         display_lidar_graph=False,
                         **kwargs)
        
        self.precision_rotation = 0.01
        self.angleStopTurning = 0
        self.isTurning = False
        self.max_step_turning = 100
        self.step_turning = 0
    
    def define_message_for_all(self):
        """
        Here, we don't need communication...
        """
        pass
    
    def control(self):
        #print(self.compass_is_disabled())
        command = {"forward": 0.0,"lateral": 0.0,"rotation": 0.0,"grasper": 0}
        
        
        if self.isTurning: # continuer la rotation
            command["rotation"] = self.rotate_to_angle(0)
        
        else : 
            if self.close_to_wall():
                command["rotation"] = self.rotate_to_angle(-math.pi/2) # initialisation de la rotation
            else : 
                command["forward"] = 0.5

        return command

    """
    SE BASE SUR LE CAPTEUR COMPASS. NE PAS UTILISER EN ZONE NON GPS.
    
    Fonction qui permet de tourner le drone vers un angle relatif donné. 
    Tant qu'il n'aura pas atteint cet angle, avec l'erreur tolérée, self.Turning=True .
    renvoie en float la commande de rotation à appliquer au drone.

    """
    
    def rotate_to_angle(self, angle) -> float:

        # COMPASS DESACTIVE
        if self.compass_is_disabled():
            return 0.0
        
        #  COMPAS ACTIF
        else :


            precision = self.precision_rotation
            compass_angle = normalize_angle(self.measured_compass_angle())
            
            # définit l'angle d'arrivé si le drone n'est pas en train de tourner.
            if not self.isTurning:
                self.angleStopTurning = normalize_angle(angle + compass_angle)
                self.isTurning = True

            # si le drone tourne 
            diff = normalize_angle(self.angleStopTurning - compass_angle)

            if abs(diff) < precision or self.step_turning > self.max_step_turning:
                self.isTurning = False
                self.step_turning = 0
                return 0.0

            else : 
                kp = 1/math.pi
                a = kp * diff
                a = min(a, 1.0)
                a = max(a, -1.0)
                return  a 
    
    def close_to_wall(self):
        
        lidar = self.lidar_values()
        min_distance = min(lidar)

        if min_distance < 40:
            return True
        
        return False
    