import numpy as np

class Pose:
    """
    Represents a 2D pose with position and orientation.

    Attributes:
        position (np.ndarray): The (x, y) position.
        orientation (float): The orientation angle in radians.
    """

    def __init__(self, position: np.ndarray = np.zeros(2,), orientation: float = 0.0):
        """
        Initialize a Pose.

        Args:
            position (np.ndarray): The (x, y) position.
            orientation (float): The orientation angle in radians.
        """
        if not isinstance(position, np.ndarray):
            print("type position=", type(position))
            raise TypeError("position must be an instance of np.ndarray")
        self.position: np.ndarray = position
        self.orientation: float = orientation

