"""
The collision damage cooldown is counted in simulation steps, not in seconds.

It used to be a wall-clock `Timer`: a drone lost one health point per *real*
second spent in contact. Nothing crashed, the score still looked plausible, and
the run simply did not mean the same thing twice -- on a fast machine, or in
headless mode (about x7 more steps per second than with a window), the same
trajectory produced far fewer damage points. A measured pair, on the very same
400 steps of `examples/example_headless.py`: 96% health headless, 83.5% windowed.

These tests pin the property that fixes it: the damage is a function of the
number of steps alone. `test_the_wall_clock_cannot_change_the_damage` is the one
that matters -- it moves the clock and requires the damage not to move with it.
"""

import pathlib
import sys
import time

# Insert the 'src' directory into sys.path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from swarm_rescue.simulation.drone.drone_abstract import DroneAbstract
from swarm_rescue.simulation.gui_map.closed_playground import ClosedPlayground
from swarm_rescue.simulation.utils.constants import (
    COLLISION_DAMAGE_COOLDOWN_STEPS,
    DRONE_INITIAL_HEALTH,
)


class _ProbeDrone(DroneAbstract):
    """A drone that does nothing: only its collision handling is exercised."""

    def define_message_for_all(self):
        return None

    def control(self):
        return {"forward": 0.0, "lateral": 0.0, "rotation": 0.0, "grasper": 0}


def _make_drone():
    """
    Build a drone registered in a throwaway playground, and return both.

    The drone must be added to the playground: `pre_step()` walks down to the
    communicator, which asserts it has one. Only the cooldown counter is under
    test here, so the drone is never actually moved against a wall.
    """
    playground = ClosedPlayground(size=(400, 300))
    drone = _ProbeDrone()
    playground.add(drone, ((0, 0), 0))
    return playground, drone


def _damage_over(drone, nb_steps, collide_each_step=True):
    """
    Simulate `nb_steps` steps, hitting the drone on every one of them.

    `pre_step()` is what advances the cooldown in the real simulator, so it is
    called explicitly here rather than through a full `Playground.step()`: this
    keeps the test about the damage rule and nothing else.

    Returns the number of health points lost.
    """
    health_before = drone.drone_health
    for _ in range(nb_steps):
        drone.pre_step()
        if collide_each_step:
            drone.collide_wall()
    return health_before - drone.drone_health


def test_colliding_every_step_costs_one_damage_per_cooldown():
    """The point of the cooldown: staying in a wall is not one damage per step."""
    playground, drone = _make_drone()
    try:
        lost = _damage_over(drone, COLLISION_DAMAGE_COOLDOWN_STEPS * 3)
    finally:
        playground.close_window()

    assert lost == 3, (
        f"expected 3 damages over {COLLISION_DAMAGE_COOLDOWN_STEPS * 3} steps of "
        f"continuous contact, got {lost}"
    )


def test_collisions_inside_one_cooldown_cost_a_single_damage():
    """Several contacts during the same cooldown window cost one point."""
    playground, drone = _make_drone()
    try:
        # Every step collides, but fewer steps than the cooldown: no damage.
        lost = _damage_over(drone, COLLISION_DAMAGE_COOLDOWN_STEPS - 1)
    finally:
        playground.close_window()

    assert lost == 0, (
        f"a drone colliding during the first {COLLISION_DAMAGE_COOLDOWN_STEPS - 1} "
        f"steps must not lose any health, it lost {lost}"
    )


def test_a_damage_is_charged_on_the_cooldown_step():
    """The boundary itself: the cooldown-th step does cost one point."""
    playground, drone = _make_drone()
    try:
        lost = _damage_over(drone, COLLISION_DAMAGE_COOLDOWN_STEPS)
    finally:
        playground.close_window()

    assert lost == 1, (
        f"colliding during exactly {COLLISION_DAMAGE_COOLDOWN_STEPS} steps must "
        f"cost exactly one health point, it cost {lost}"
    )


def test_the_wall_clock_cannot_change_the_damage():
    """
    The regression itself.

    The same number of steps, on a machine whose clock races, must cost exactly
    the same number of health points. Before the fix, waiting (or pretending to
    wait) let a drone take damage again immediately.
    """
    nb_steps = COLLISION_DAMAGE_COOLDOWN_STEPS * 4

    playground, drone = _make_drone()
    try:
        reference = _damage_over(drone, nb_steps)
    finally:
        playground.close_window()

    # A clock that jumps by an hour between every single step: the old
    # `Timer.get_elapsed_time() > 1.0` test would return True every time.
    real_perf_counter = time.perf_counter

    def racing_clock():
        racing_clock.now += 3600.0
        return racing_clock.now

    racing_clock.now = real_perf_counter()

    playground, drone = _make_drone()
    time.perf_counter = racing_clock
    try:
        with_racing_clock = _damage_over(drone, nb_steps)
    finally:
        time.perf_counter = real_perf_counter
        playground.close_window()

    assert reference == with_racing_clock == 4, (
        "the collision damage must not depend on the wall clock: got "
        f"{reference} normally and {with_racing_clock} with a clock racing "
        f"1 hour per step, over {nb_steps} steps"
    )


def test_a_wall_and_a_drone_share_the_same_cooldown():
    """
    Bouncing between a wall and another drone costs one point, not two.

    The previous code shared a single timer between both handlers; the shared
    cooldown is kept on purpose.
    """
    playground, drone = _make_drone()
    try:
        health_before = drone.drone_health
        for _ in range(COLLISION_DAMAGE_COOLDOWN_STEPS):
            drone.pre_step()
            drone.collide_wall()
            drone.collide_drone()
        lost = health_before - drone.drone_health
    finally:
        playground.close_window()

    assert lost == 1, (
        f"a wall and a drone hit within one cooldown must cost a single health "
        f"point, it cost {lost}"
    )


def test_reset_clears_the_cooldown_and_restores_the_health():
    """A reset drone must be as healthy and as protected as a new one."""
    playground, drone = _make_drone()
    try:
        _damage_over(drone, COLLISION_DAMAGE_COOLDOWN_STEPS * 2)
        assert drone.drone_health < DRONE_INITIAL_HEALTH

        drone.reset()

        assert drone.drone_health == DRONE_INITIAL_HEALTH
        # The cooldown must be cleared too, otherwise a reset drone would be
        # immune to the first collisions.
        assert drone._steps_since_last_damage == 0
        assert _damage_over(drone, COLLISION_DAMAGE_COOLDOWN_STEPS) == 1
    finally:
        playground.close_window()


def test_the_cooldown_is_expressed_in_simulated_seconds():
    """
    30 steps is one simulated second at FRAME_RATE.

    This is the constant that keeps the scores of the windowed reference runs
    meaningful: the old rule charged one damage per real second, which at 30
    steps/s is one damage per 30 steps.
    """
    from swarm_rescue.simulation.utils.constants import FRAME_RATE

    assert COLLISION_DAMAGE_COOLDOWN_STEPS == round(1 / FRAME_RATE)
