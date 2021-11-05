from abc import ABC, abstractmethod

from spg_overlay.explored_map import ExploredMap


class MapAbstract(ABC):
    """
    It is abstract class to construct every maps used in the directory maps
    """
    def __init__(self):
        self.explored_map = ExploredMap()

        # 'number_drones' is the number of drones that will be generated in the map
        self.number_drones = 1

        # 'time_step_limit' is the number of time steps after which the session will end.
        self.time_step_limit = 10000

        # 'real_time_limit' is the elapsed time (in seconds) after which the session will end.
        self.real_time_limit = 3600  # In seconds

        # 'number_wounded_persons' is the number of wounded persons that should be retrieved by the drones.
        self.number_wounded_persons = 0

    @abstractmethod
    def set_drones(self, drones):
        pass
