import math
import pathlib
import sys
import numpy as np

from typing import List, Type

# Insert the 'src' directory, located two levels up from the current script,
# into sys.path. This ensures Python can find project-specific modules
# (e.g., 'swarm_rescue') when the script is run from a subfolder like 'tests/'.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from swarm_rescue.simulation.drone.drone_abstract import DroneAbstract
from swarm_rescue.simulation.gui_map.closed_playground import ClosedPlayground
from swarm_rescue.simulation.gui_map.map_abstract import MapAbstract
from swarm_rescue.simulation.utils.misc_data import MiscData


class MyDrone(DroneAbstract):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def define_message_for_all(self):
        pass

    def control(self):
        command = {"forward": 1.0,
                   "lateral": 0.0,
                   "rotation": 0.0,
                   "grasper": 0}
        return command


class MyMap(MapAbstract):
    def __init__(self, drone_type: Type[DroneAbstract]):
        super().__init__(drone_type=drone_type)

        # PARAMETERS MAP
        self._size_area = (200, 200)

        # POSITIONS OF THE DRONES
        self._number_drones = 1
        self._drones_pos = [((0, 0), 0)]
        self._drones: List[DroneAbstract] = []

        self._playground = ClosedPlayground(size=self._size_area)

        # POSITIONS OF THE DRONES
        misc_data = MiscData(size_area=self._size_area,
                             number_drones=self._number_drones,
                             max_timestep_limit=self._max_timestep_limit,
                             max_walltime_limit=self._max_walltime_limit)
        for i in range(self._number_drones):
            drone = drone_type(identifier=i, misc_data=misc_data)
            self._drones.append(drone)
            self._playground.add(drone, self._drones_pos[i])


def test_move():
    the_map = MyMap(drone_type=MyDrone)

    drones_commands = {}
    for _ in range(100):
        command = the_map.drones[0].control()
        drones_commands[the_map.drones[0]] = command
        the_map.playground.step(all_commands=drones_commands)

    moved = not np.array_equal(the_map.playground.agents[0].true_position(), [0, 0])

    assert moved is True


def test_lidar():
    """
    Check values of the lidar
    """
    the_map = MyMap(drone_type=MyDrone)

    ok1 = True
    if the_map.drones[0].lidar().get_sensor_values() is None:
        ok1 = False
    assert ok1 is True

    for _ in range(1):
        the_map.playground.step()

    ok2 = True
    if the_map.drones[0].lidar().get_sensor_values() is None:
        ok2 = False
    assert ok2 is True

    w, h = the_map.size_area
    max_dist_theoretical = math.sqrt(w * w + h * h) / 2
    min_dist_theoretical = min(w, h) / 2

    max_dist = max(the_map.drones[0].lidar().get_sensor_values())
    min_dist = min(the_map.drones[0].lidar().get_sensor_values())
    # print("half_diag = ", half_diag)
    # print("max_dist = ", max_dist)

    assert max_dist < (max_dist_theoretical + 20)
    assert max_dist > (max_dist_theoretical - 20)
    assert min_dist > (min_dist_theoretical - 20)
    assert min_dist < (min_dist_theoretical + 20)


def test_lidar_nan():
    """
    Here, we don't use the step function of playground
    So, we don't have lidar value.
    """
    the_map = MyMap(drone_type=MyDrone)

    ok = True
    if the_map.drones[0].lidar().get_sensor_values() is None:
        ok = False

    val = max(the_map.drones[0].lidar().get_sensor_values())

    assert ok is True and np.isnan(val)


def test_positions():
    """
    Check values of the positions sensor
    """
    the_map = MyMap(drone_type=MyDrone)

    for _ in range(1):
        the_map.playground.step()

    # -- GPS -- #
    gps_pos = the_map.drones[0].measured_gps_position()
    # gps_pos = (12.3, 456.78)
    assert gps_pos is not None
    assert isinstance(gps_pos, np.ndarray)
    # -- TRUE POSITION -- #
    true_pos = the_map.drones[0].true_position()
    # true_pos = Vec2d(12.3, 456.78)
    assert true_pos is not None
    assert isinstance(true_pos, np.ndarray)

    # -- COMPASS -- #
    compass_angle = the_map.drones[0].measured_compass_angle()
    assert compass_angle is not None
    assert type(compass_angle) is float

    # -- TRUE ANGLE -- #
    true_angle = the_map.drones[0].true_angle()
    # true_angle = 1.2345
    assert true_angle is not None
    assert type(true_angle) is float


def test_positions_nan():
    """
    Check values of the positions sensor
    """
    the_map = MyMap(drone_type=MyDrone)

    # -- GPS -- #
    gps_pos = the_map.drones[0].measured_gps_position()
    # gps_pos = (nan, nan)
    assert gps_pos is not None
    assert isinstance(gps_pos, np.ndarray)
    assert np.isnan(gps_pos[0])
    assert np.isnan(gps_pos[1])

    # -- TRUE POSITION -- #
    true_pos = the_map.drones[0].true_position()
    # true_pos = Vec2d(12.3, 456.78)
    assert true_pos is not None
    assert isinstance(true_pos, np.ndarray)

    # -- COMPASS -- #
    # compass_angle_array = nan
    compass_angle_array = the_map.drones[0].measured_compass_angle()
    assert np.isnan(compass_angle_array)

    # -- TRUE ANGLE -- #
    true_angle = the_map.drones[0].true_angle()
    # true_angle = nan
    assert not np.isnan(true_angle)
    assert true_angle is not None
    assert type(true_angle) is float
