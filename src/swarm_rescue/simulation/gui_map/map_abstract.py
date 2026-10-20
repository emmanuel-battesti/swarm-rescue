from abc import ABC
from typing import List, Tuple, Type, Optional

import numpy as np

from swarm_rescue.simulation.drone.drone_abstract import DroneAbstract
from swarm_rescue.simulation.elements.return_area import ReturnArea
from swarm_rescue.simulation.gui_map.playground import Playground
from swarm_rescue.simulation.reporting.evaluation import ZonesConfig
from swarm_rescue.simulation.reporting.explored_map import ExploredMap
from swarm_rescue.simulation.utils.constants import DRONE_INITIAL_HEALTH


class MapAbstract(ABC):
    """
    The MapAbstract class is an abstract class that serves as a blueprint for
    constructing different types of maps used in the directory "maps".
    """

    def __init__(self,
                 drone_type: Type[DroneAbstract],
                 zones_config: ZonesConfig = (),
                 seed: Optional[int] = None):
        """
        Initialize the MapAbstract.

        Args:
            drone_type (Type[DroneAbstract]): The type of drone to use.
            zones_config (ZonesConfig): Configuration for special zones.
            seed (Optional[int]): Seed for this map's random number generator.
                Maps must draw their random placements from ``self.rng``
                instead of the global ``random`` module for a run to be
                reproducible. The same seed is forwarded to the playground so
                that entity UIDs (used by the lidar) are reproducible too.
                ``None`` (the default) leaves the run non-reproducible.
        """
        self._playground: Optional[Playground] = None
        self._drone_type = drone_type
        self._explored_map = ExploredMap()
        self._zones_config = zones_config
        self._drones: List[DroneAbstract] = []
        self._seed = seed
        # Dedicated generator. It cannot be `playground.rng` because most
        # maps draw their drone positions *before* the playground is built.
        self._rng = np.random.default_rng(seed)
        # Every concrete map assigns these in its own `__init__`, before it
        # uses them. They are declared here, per instance, so that the map
        # itself can rely on them existing: a subclass that forgets one fails
        # on the `None` default instead of raising `AttributeError`.
        self._size_area: Optional[Tuple[int, int]] = None
        self._number_drones: Optional[int] = None
        self._max_timestep_limit: Optional[int] = None
        self._max_walltime_limit: Optional[int] = None
        self._number_wounded_persons: Optional[int] = None

        self._return_area: Optional[ReturnArea] = None

    @property
    def seed(self) -> Optional[int]:
        """
        Returns the seed used to build this map.

        Returns:
            Optional[int]: The seed, or None when the map is not reproducible.
        """
        return self._seed

    @property
    def rng(self) -> np.random.Generator:
        """
        Returns the random number generator for this map.

        Map implementations must draw their random placements from this
        generator rather than from the global ``random`` module, otherwise the
        seed only controls part of the randomness.

        Returns:
            np.random.Generator: The generator seeded with ``seed``.
        """
        return self._rng

    @property
    def playground(self) -> Optional[Playground]:
        """
        Returns the playground instance.

        Returns:
            Playground or None: The playground, None while the map has not
            been built yet.
        """
        return self._playground

    @property
    def _playground(self) -> Optional[Playground]:
        """
        Returns the playground, and hands it to the explored map when set.

        The explored map measures the map, so it has to know which playground
        it is measuring. The map is what holds the playground, so the link is
        made here, once, as the playground is assigned.
        """
        return self.__playground

    @_playground.setter
    def _playground(self, playground: Optional[Playground]) -> None:
        self.__playground = playground

        # `__init__` assigns None before `_explored_map` exists, hence the
        # getattr: this setter runs for that assignment too.
        explored_map = getattr(self, "_explored_map", None)
        if explored_map is not None and playground is not None:
            # Only remembered, never rendered here: the walls are not in the
            # playground yet, they are added by the subclass right after.
            explored_map.attach_playground(playground)

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

        Every concrete map sets it in its `__init__`, before anything reads it.

        Returns:
            int: Number of drones.
        """
        assert self._number_drones is not None, "The map does not declare its drone count."
        return self._number_drones

    @property
    def max_timestep_limit(self) -> Optional[int]:
        """
        Returns the maximum timestep limit, if the map sets one.

        Returns:
            Optional[int]: Maximum timestep limit, None meaning "no limit".
        """
        return self._max_timestep_limit

    @property
    def max_walltime_limit(self) -> Optional[int]:
        """
        Returns the maximum walltime limit in seconds, if the map sets one.

        Returns:
            Optional[int]: Maximum walltime limit, None meaning "no limit".
        """
        return self._max_walltime_limit

    @property
    def number_wounded_persons(self) -> Optional[int]:
        """
        Returns the number of wounded persons to be rescued.

        Returns:
            Optional[int]: Number of wounded persons, or None when the map does
            not declare it (nothing to rescue and no counter to display).
        """
        return self._number_wounded_persons

    @property
    def size_area(self) -> Tuple[int, int]:
        """
        Returns the size of the area.

        Every concrete map sets it in its `__init__`, before building the
        playground.

        Returns:
            Tuple[int, int]: The size of the area.
        """
        assert self._size_area is not None, "The map does not declare its size."
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
        total_health = 0.0
        number_drones = self.number_drones
        assert number_drones is not None, "The map does not declare its drone count."

        if number_drones == 0:
            return 1.0

        if self._return_area:
            total_health = self._return_area.compute_total_health_returned()
        else:
            for drone in self.drones:
                total_health += drone.drone_health

        mean_total_health = total_health / number_drones
        score_total_health = mean_total_health / DRONE_INITIAL_HEALTH
        return score_total_health
