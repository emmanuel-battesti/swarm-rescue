"""
imports
"""

class MyDroneEval(DroneAbstract):
    class Activity(Enum):
        """
        All the states of the drone as a state machine
        """

    def __init__(self,
                 identifier: Optional[int] = None, **kwargs):
        super().__init__(identifier=identifier,
                         display_lidar_graph=False,
                         **kwargs)
        # Initialisation de l'activité


        # Initialisation des paramètres cinétiques
        

    def define_message_for_all(self):
        pass

    def control(self):
        #############
        # TRANSITIONS DE L'ACTIVITE
        #############


        ##########
        # COMMANDE EN FONCTION DE L'ACTIVITE ET DES PARAMETRES CINETIQUES
        ##########

        pass