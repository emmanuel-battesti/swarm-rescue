"""
Constants used throughout the drone simulation.
"""

from typing import Tuple

FRAME_RATE: float = 1 / 30

# 'COLLISION_DAMAGE_COOLDOWN_STEPS' is the number of simulation steps between
# two collision damages: a drone bouncing on a wall loses one health point every
# COLLISION_DAMAGE_COOLDOWN_STEPS steps.
#
# 30 steps is one simulated second at FRAME_RATE. Counting steps rather than
# real seconds is what makes the damage reproducible: a headless run simulates
# about x7 more steps per second than a windowed one, and the same trajectory
# must cost the same health in both modes.
COLLISION_DAMAGE_COOLDOWN_STEPS: int = 30

# How a drone can be destroyed. The cause is not cosmetic: it decides whether
# the wreck still blocks the others and whether the sensors keep seeing it.
# 'DEATH_BY_DAMAGE' leaves a wreck that is passable and invisible to the sensors,
# 'DEATH_BY_KILL_ZONE' leaves a disabled drone that keeps both.
DEATH_BY_DAMAGE: str = "damage"
DEATH_BY_KILL_ZONE: str = "kill_zone"

# How opaque a wreck is drawn once its turn is over, on a 0-255 scale.
#
# This is not decoration: it is how the cause of death is read on the map at a
# glance, and it follows exactly what the sensors do. A wreck the sensors cannot
# see is drawn see-through, a wreck they still see is drawn solid. So a drone
# destroyed by damage -- taken out of the uid image -- fades to
# 'DEATH_WRECK_ALPHA_HIDDEN', while a drone destroyed by a kill zone -- still in
# the image, still solid to the others -- keeps the full
# 'DEATH_WRECK_ALPHA_SOLID'.
DEATH_WRECK_ALPHA_HIDDEN: int = 110
DEATH_WRECK_ALPHA_SOLID: int = 255

# 'DEATH_ANIMATION_STEPS' is how many simulated steps the turn lasts before the
# wreck comes to rest on the dead-drone sprite. Forty steps is a second and a
# third at 30 FPS: slow enough for the spin-down to read as a spin-down rather
# than as a cut, short enough not to hold up a round.
DEATH_ANIMATION_STEPS: int = 40

# The wreck spins on itself, quickly at first and more and more slowly until it
# stops, and is back to its normal size when the turn ends. No fade: the wreck
# has to stay readable as a destroyed drone once the animation is over.
#
# 'DEATH_ANIMATION_TURN_DEGREES' is the total angle of the turn, and
# 'DEATH_ANIMATION_EASE_POWER' the shape of the slowdown: the angle covered at
# step `n` of `N` is `TOTAL * (1 - (1 - n/N) ** POWER)`, whose per-step increment
# shrinks all along and reaches exactly `TOTAL` on the last step. A higher power
# starts faster and stays fast longer, so 2 is a soft start and 5 a sharp one
# that drops off late.
#
# A longer turn for the same total angle slows the wreck down: the peak speed is
# the angle covered by the very first step, which shrinks as the turn is spread
# over more steps.
#
# Keep the total a whole number of turns. The wreck comes to rest at whatever
# angle the turn ends on, and only a multiple of 360 degrees lands it back on the
# orientation of the dead sprite.
DEATH_ANIMATION_TURN_DEGREES: float = 720.0
DEATH_ANIMATION_EASE_POWER: float = 3.0

# 'DEATH_ANIMATION_PEAK_ZOOM' is how much bigger the wreck looks on the first step
# of the animation, as a ratio over its normal size. It shrinks quadratically to
# nothing, so the sprite is back to its normal scale when the rotation ends.
DEATH_ANIMATION_PEAK_ZOOM: float = 0.25

LINEAR_SPEED_RATIO: float = 3.0
ANGULAR_SPEED_RATIO: float = 0.6

LINEAR_SPEED_RATIO_WOUNDED: float = 1.0

DRONE_INITIAL_HEALTH: int = 40

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

# 'WINDOW_LETTERBOX_COLOR' is the color filling the window outside of the map
# area, when the window aspect ratio differs from the map one.
WINDOW_LETTERBOX_COLOR: Tuple[int, int, int] = (64, 64, 64)

# 'MAX_WINDOW_WIDTH' and 'MAX_WINDOW_HEIGHT' cap the size of the window at
# startup: whatever the map resolution and 'window_scale', the window never
# opens larger than this. The aspect ratio is preserved, so the map stays
# entirely visible. Sized for a 1366x768 screen.
MAX_WINDOW_WIDTH: int = 1366
MAX_WINDOW_HEIGHT: int = 768

# 'ENABLE_WINDOW_RESIZING' controls whether the user (OS) can manually resize
# the created Arcade window. Set to False to make the window non-resizable.
# Default True preserves existing behavior.
ENABLE_WINDOW_RESIZING: bool = True

# --- Window status bar ------------------------------------------------------
# The status bar is the black band `GuiSR` paints across the top of the window,
# with the map name on the left and the progress of the round on the right.
#
# Its height is expressed in window pixels, not in map pixels: the bar belongs
# to the window, not to the playground, so it keeps its thickness whatever the
# zoom, the window size, or the map resolution. See `gui_map/status_bar.py`.
WINDOW_STATUS_BAR_HEIGHT: int = 28

# 'WINDOW_STATUS_BAR_COLOR' is the near-black filling the bar. It is darker
# than 'WINDOW_LETTERBOX_COLOR' (64, 64, 64) on purpose: the bar has to read as
# a distinct band and not as more letterbox.
WINDOW_STATUS_BAR_COLOR: Tuple[int, int, int] = (16, 16, 16)

# 'WINDOW_STATUS_BAR_TEXT_COLOR' is the light gray of both labels. Light enough
# to stay readable on the near-black band, muted enough not to compete with the
# map underneath.
WINDOW_STATUS_BAR_TEXT_COLOR: Tuple[int, int, int] = (200, 200, 200)

# 'WINDOW_STATUS_BAR_FONT_SIZE' and 'WINDOW_STATUS_BAR_TEXT_PADDING' are the
# label size and the gap kept between a label and the edge of the window. The
# font is small because the right-hand label now carries both limits -- the
# timestep count and the wall time -- side by side.
WINDOW_STATUS_BAR_FONT_SIZE: int = 11
WINDOW_STATUS_BAR_TEXT_PADDING: int = 10

