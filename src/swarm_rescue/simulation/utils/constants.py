"""
Constants used throughout the drone simulation.
"""

FRAME_RATE: float = 1 / 30
LINEAR_SPEED_RATIO: float = 3.0
ANGULAR_SPEED_RATIO: float = 0.6

LINEAR_SPEED_RATIO_WOUNDED: float = 1.0

DRONE_INITIAL_HEALTH: int = 50

RESOLUTION_SEMANTIC_SENSOR: int = 35
MAX_RANGE_SEMANTIC_SENSOR: int = 200
FOV_SEMANTIC_SENSOR: int = 360

RESOLUTION_LIDAR_SENSOR: int = 181
MAX_RANGE_LIDAR_SENSOR: int = 300
FOV_LIDAR_SENSOR: int = 360

# 'RANGE_COMMUNICATION' is the radius, in pixels, of the area around the drone
# in which we will have the other drones with which we can communicate (receive
# and send messages)
RANGE_COMMUNICATION: int = 250

# 'WINDOW_AUTO_RESIZE_RATIO' is the percentage of screen size used as maximum
# for automatic window resizing (0.85 = 85% of screen size)
WINDOW_AUTO_RESIZE_RATIO: float = 0.85

# 'ENABLE_WINDOW_AUTO_RESIZE' allows to completely disable automatic window resizing
# Set to False to disable auto-resize for all windows
ENABLE_WINDOW_AUTO_RESIZE: bool = True

