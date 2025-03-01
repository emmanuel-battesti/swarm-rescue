from dataclasses import dataclass, field
from collections import deque
from typing import List, Tuple, Optional
from enum import Enum, auto
import math

@dataclass
class MappingParams:
    resolution: int = 8     # 8 to 1 factor from simulation pixels to grid (efficiency)
    display_map: bool = True

@dataclass
class WaitingStateParams:
    step_waiting: int = 50

@dataclass
class GraspingParams:
    grasping_speed: float = 0.3

@dataclass
class WallFollowingParams:
    dmax: int = 60
    dist_to_stay: int = 40
    speed_following_wall: float = 0.3
    speed_turning: float = 0.05

@dataclass
class PIDParams:
    Kp_angle: float = 4 / math.pi
    Kp_angle_1: float = 9 / math.pi
    Kd_angle: float = Kp_angle / 10
    Kd_angle_1: float = Kp_angle / 10
    Ki_angle: float = (1 / 10) * (1 / 20) * 2 / math.pi
    
    Kp_distance: float = 2 / abs(WallFollowingParams.dmax - WallFollowingParams.dist_to_stay)
    Kp_distance_1 : float = 2 / abs(10)
    Ki_distance: float = 1 / abs(WallFollowingParams.dist_to_stay) * 1 / 200
    Ki_distance_1: float = 1 / abs(10) * 1 / 20 * 1 / 10
    Kd_distance: float = 2 * Kp_distance
    Kd_distance_1: float = 2 * Kp_distance_1

@dataclass
class PathParams:
    distance_close_waypoint: int = 20
    max_inflation_obstacle: int = 3

@dataclass
class LogParams:
    record_log: bool = False
    log_file: str = "logs/log.txt"
    log_initialized: bool = False
    flush_interval: int = 50

@dataclass
class VisualisationParams:
    draw_path: bool = True
    draw_frontier: bool = True