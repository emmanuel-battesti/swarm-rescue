from typing import Tuple


class MiscData:
    """
    This class should be used to contain miscellaneous data for the drone

    Attributes:
        size_area: A tuple representing the size of the area where the drone operates. It contains two float values:
        width and height.
        number_drones: An integer representing the number of drones.
    """

    def __init__(self,
                 size_area: Tuple[float, float] = None,
                 number_drones: int = None
                 ):
        self.size_area = size_area
        self.number_drones = number_drones
