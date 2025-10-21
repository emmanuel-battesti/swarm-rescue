import numpy as np

from swarm_rescue.simulation.utils.pose import Pose


class Path:
    """
    Represents a path as a sequence of poses.

    Attributes:
        _poses (np.ndarray): Array of poses (x, y, orientation).
    """

    def __init__(self) -> None:
        """
        Initialize an empty path.
        """
        self._poses = np.zeros((0, 3))

    def append(self, pose: Pose) -> None:
        """
        Append a pose to the path.

        Args:
            pose (Pose): The pose to append.
        """
        my_array_pose = [[pose.position[0], pose.position[1], pose.orientation]]
        self._poses = np.append(self._poses, my_array_pose, axis=0)

    def length(self) -> int:
        """
        Returns the number of poses in the path.

        Returns:
            int: Number of poses.
        """
        return int(self._poses.shape[0])

    def get(self, index: int) -> Pose:
        """
        Get the pose at the specified index.

        Args:
            index (int): Index of the pose.

        Returns:
            Pose: The pose at the index.
        """
        v = self._poses[index]
        pose = Pose(v[0:2], float(v[2]))
        return pose

    def reset(self) -> None:
        """
        Reset the path to be empty.
        """
        self._poses = np.zeros((0, 3))

