from abc import ABC, abstractmethod
from typing import List, Type

from spg.playground import Playground

from spg_overlay.entities.drone_abstract import DroneAbstract
from spg_overlay.reporting.evaluation import ZonesConfig
from spg_overlay.reporting.explored_map import ExploredMap


class MapAbstract(ABC):
    """
    The MapAbstract class is an abstract class that serves as a blueprint for constructing different types of maps
    used in the directory "maps".
    """

    def __init__(self, zones_config: ZonesConfig = ()):
        self._explored_map = ExploredMap()
        self._size_area = None
        self._zones_config = zones_config
        self._drones: List[DroneAbstract] = []
        # '_number_drones' is the number of drones that will be generated in the map
        self._number_drones = None
        # '_time_step_limit' is the number of time steps after which the session will end.
        self._time_step_limit = None
        # 'real_time_limit' is the elapsed time (in seconds) after which the session will end.
        self._real_time_limit = None  # In seconds
        # 'number_wounded_persons' is the number of wounded persons that should be retrieved by the drones.
        self._number_wounded_persons = None

    @abstractmethod
    def construct_playground(self, drone_type: Type[DroneAbstract]) -> Playground:
        pass

    @property
    def drones(self):
        return self._drones

    @property
    def number_drones(self):
        return self._number_drones

    @property
    def time_step_limit(self):
        return self._time_step_limit

    @property
    def real_time_limit(self):
        return self._real_time_limit

    @property
    def number_wounded_persons(self):
        return self._number_wounded_persons

    @property
    def size_area(self):
        return self._size_area

    @property
    def zones_config(self):
        return self._zones_config

    @property
    def explored_map(self):
        return self._explored_map
