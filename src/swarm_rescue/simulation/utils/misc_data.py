from typing import Tuple, Optional

class MiscData:
    """
    This class should be used to contain miscellaneous data for the drone.

    Attributes:
        size_area (Optional[Tuple[float, float]]): Size of the area (width, height).
        number_drones (Optional[int]): Number of drones.
        max_timestep_limit (Optional[int]): Maximum timestep limit.
        max_walltime_limit (Optional[float]): Maximum walltime limit.
    """

    def __init__(
        self,
        size_area: Optional[Tuple[float, float]] = None,
        number_drones: Optional[int] = None,
        max_timestep_limit: Optional[int] = None,
        max_walltime_limit: Optional[float] = None
    ):
        """
        Initialize MiscData.

        Args:
            size_area (Optional[Tuple[float, float]]): Size of the area.
            number_drones (Optional[int]): Number of drones.
            max_timestep_limit (Optional[int]): Maximum timestep limit.
            max_walltime_limit (Optional[float]): Maximum walltime limit.
        """
        self.size_area = size_area
        self.number_drones = number_drones
        self.max_timestep_limit = max_timestep_limit
        self.max_walltime_limit = max_walltime_limit

