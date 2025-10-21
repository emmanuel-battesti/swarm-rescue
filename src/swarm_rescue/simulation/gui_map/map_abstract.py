from abc import ABC
from typing import List, Type, Union, Optional

from swarm_rescue.simulation.drone.drone_abstract import DroneAbstract
from swarm_rescue.simulation.gui_map.playground import Playground
from swarm_rescue.simulation.reporting.evaluation import ZonesConfig
from swarm_rescue.simulation.reporting.explored_map import ExploredMap
from swarm_rescue.simulation.utils.constants import DRONE_INITIAL_HEALTH


class MapAbstract(ABC):
    """
    The MapAbstract class is an abstract class that serves as a blueprint for
    constructing different types of maps used in the directory "maps".
    """

    def __init__(self, drone_type: Type[DroneAbstract], zones_config: ZonesConfig = ()):
        """
        Initialize the MapAbstract.

        Args:
            drone_type (Type[DroneAbstract]): The type of drone to use.
            zones_config (ZonesConfig): Configuration for special zones.
        """
        self._playground: Optional[Playground] = None
        self._drone_type = drone_type
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

    @property
    def playground(self) -> Union[Playground, Type[None]]:
        """
        Returns the playground instance.

        Returns:
            Playground or None: The playground.
        """
        return self._playground

    @property
    def drones(self) -> List[DroneAbstract]:
        """
        Returns the list of drones in the map.

        Returns:
            List[DroneAbstract]: The drones.
        """
        return self._drones

    @property
    def number_drones(self) -> int:
        """
        Returns the number of drones in the map.

        Returns:
            int: Number of drones.
        """
        return self._number_drones

    @property
    def max_timestep_limit(self) -> int:
        """
        Returns the maximum timestep limit.

        Returns:
            int: Maximum timestep limit.
        """
        return self._max_timestep_limit

    @property
    def max_walltime_limit(self) -> int:
        """
        Returns the maximum walltime limit in seconds.

        Returns:
            int: Maximum walltime limit.
        """
        return self._max_walltime_limit

    @property
    def number_wounded_persons(self) -> int:
        """
        Returns the number of wounded persons to be rescued.

        Returns:
            int: Number of wounded persons.
        """
        return self._number_wounded_persons

    @property
    def size_area(self):
        """
        Returns the size of the area.

        Returns:
            Any: The size of the area.
        """
        return self._size_area

    @property
    def zones_config(self) -> ZonesConfig:
        """
        Returns the configuration for special zones.

        Returns:
            ZonesConfig: The zones configuration.
        """
        return self._zones_config

    @property
    def explored_map(self) -> ExploredMap:
        """
        Returns the explored map object.

        Returns:
            ExploredMap: The explored map.
        """
        return self._explored_map

    def compute_score_health_returned(self) -> float:
        """
        The method calculates a health score for returned UAVs, usually at the
        end of a run. This score is calculated only on a zone called the
        ‘return area’ if it exists. If it does not exist, the score is
        calculated over the entire map.  The score is a number between 0 and 1.
        A value of 1 means that all the drones have been returned and are in
        perfect health.

        Returns:
            float: The health score (0 to 1).
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
