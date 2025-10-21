#import pathlib
#import sys

# Insert the 'src' directory, located two levels up from the current script,
# into sys.path. This ensures Python can find project-specific modules
# (e.g., 'swarm_rescue') when the script is run from a subfolder like 'tests/'.
#sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

# from swarm_rescue.solutions.utils.pose import Pose
# from swarm_rescue.solutions.utils.trajectory import Trajectory
#

#
# def test_append():
#     my_traj = Trajectory()
#     my_pose = Pose()
#     my_traj.append(my_pose)
#     assert my_traj.traj.shape[0] == 1 and my_traj.traj[0].shape[0] == 3
#
#
# def test_length():
#     assert False
#
#
# def test_get():
#     assert False
