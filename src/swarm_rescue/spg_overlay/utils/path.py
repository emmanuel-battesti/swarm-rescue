from spg_overlay.utils.pose import Pose
import numpy as np


class Path:
    def __init__(self) -> None:
        self._poses = np.zeros((0, 3))

    def append(self, pose: Pose):
        my_array_pose = [[pose.position[0], pose.position[1], pose.orientation]]
        self._poses = np.append(self._poses, my_array_pose, axis=0)

    def length(self) -> int:
        return int(self._poses.shape[0])

    def get(self, index: int) -> Pose:
        v = self._poses[index]
        pose = Pose(v[0:2], v[2])
        return pose

    def reset(self):
        self._poses = np.zeros((0, 3))
