from typing import Tuple


class MiscData:
    """
    This class should be used to contains miscellaneous data for the drone
    """

    def __init__(self,
                 size_area: Tuple[float, float] = None,
                 ):
        self.size_area = size_area
