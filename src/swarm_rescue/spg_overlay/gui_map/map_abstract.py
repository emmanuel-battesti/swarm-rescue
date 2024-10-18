from abc import ABC, abstractmethod
from typing import List, Type

from spg.playground import Playground

from spg_overlay.entities.drone_abstract import DroneAbstract
from spg_overlay.reporting.evaluation import ZonesConfig
from spg_overlay.reporting.explored_map import ExploredMap
from spg_overlay.utils.constants import DRONE_INITIAL_HEALTH


class MapAbstract(ABC):
    """
    The MapAbstract class is an abstract class that serves as a blueprint for
    constructing different types of maps used in the directory "maps".
    """

    def __init__(self, zones_config: ZonesConfig = ()):
        self._explored_map = ExploredMap()
        self._size_area = None
        self._zones_config = zones_config
        self._drones: List[DroneAbstract] = []
        # '_number_drones' is the number of drones that will be generated in
        # the map
        self._number_drones = None
        # '_max_timestep_limit' is the number of timesteps after which the
        # session will end.
        self._max_timestep_limit = None
        # 'max_walltime_limit' is the elapsed time (in seconds) after which the
        # session will end.
        self._max_walltime_limit = None  # In seconds
        # 'number_wounded_persons' is the number of wounded persons that should
        # be retrieved by the drones.
        self._number_wounded_persons = None

        self._return_area = None

    @abstractmethod
    def construct_playground(self, drone_type: Type[DroneAbstract]) \
            -> Playground:
        pass

    @property
    def drones(self):
        return self._drones

    @property
    def number_drones(self):
        return self._number_drones

    @property
    def max_timestep_limit(self):
        return self._max_timestep_limit

    @property
    def max_walltime_limit(self):
        return self._max_walltime_limit

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

    def compute_score_health_returned(self):
        """
        The method calculates a health score for returned UAVs, usually at the
        end of a run. This score is calculated only on a zone called the
        ‘return area’ if it exists. If it does not exist, the score is
        calculated over the entire map.  The score is a number between 0 and 1.
        A value of 1 means that all the drones have been returned and are in
        perfect health.
        """
        total_health = 0
        if self._return_area:
            total_health = self._return_area.compute_total_health_returned()
        else:
            for drone in self.drones:
                total_health += drone.drone_health

        mean_total_health = total_health / self.number_drones
        score_total_health = mean_total_health / DRONE_INITIAL_HEALTH
        return score_total_health