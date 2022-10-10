from typing import Tuple


class MiscData:
    """
    This class should be used to contain miscellaneous data for the drone
    """

    def __init__(self,
                 size_area: Tuple[float, float] = None,
                 number_drones: int = None
                 ):
        self.size_area = size_area
        self.number_drones = number_drones
