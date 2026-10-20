import pathlib
import sys
import time

# Insert the 'src' directory, located two levels up from the current script,
# into sys.path. This ensures Python can find project-specific modules
# (e.g., 'swarm_rescue') when the script is run from a subfolder like 'tests/'.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from swarm_rescue.simulation.utils.timer import Timer

# `time.sleep()` is not precise: on a loaded CI runner (macOS arm64 in
# particular) a requested 0.1 s can take 0.25 s. Asserting against the
# *requested* duration is therefore flaky, and a fixed slack is not a fix
# either: a test running N sleeps accumulates N times the jitter.
#
# So the tests below measure how long the sleep really took (same
# `time.perf_counter()` clock the Timer uses) and compare the Timer against
# that measurement. Only Python's own overhead separates the two, hence a
# small tolerance.
#
# That tolerance stays far below the "distractor" sleeps (0.2 s after a stop,
# 0.2/0.3/0.4 s while paused), so a Timer wrongly accounting for one of them
# is still caught.
TIMER_TOLERANCE = 0.02


def _sleep(seconds):
    """Sleep, and return the wall-clock duration actually spent (>= seconds)."""
    before = time.perf_counter()
    time.sleep(seconds)
    return time.perf_counter() - before


def _assert_timer_matches(elapsed_time, active_time, context):
    """Assert the Timer measured `active_time` and nothing more."""
    assert abs(elapsed_time - active_time) < TIMER_TOLERANCE, (
        f"{context}: Timer reports {elapsed_time:.4f} s but {active_time:.4f} s "
        f"of active time elapsed (tolerance {TIMER_TOLERANCE} s)"
    )


def test_start_timer():
    """Tests that the timer starts and measures the elapsed time"""
    timer = Timer()
    timer.start()
    active_time = _sleep(0.2)  # Simulate some processing time
    elapsed_time = timer.get_elapsed_time()
    _assert_timer_matches(elapsed_time, active_time, "running")


def test_pause_and_resume_timer():
    """Tests that the timer can be paused and resumed and the elapsed time
    is correct"""
    timer = Timer()
    timer.start()
    active_time = _sleep(0.1)  # Simulate some processing time
    timer.pause_on()
    paused_time = _sleep(0.3)  # Simulate more processing time during pause
    timer.pause_off()
    active_time += _sleep(0.1)  # Simulate more processing time after pause
    elapsed_time = timer.get_elapsed_time()
    # Only the two 0.1 s windows count; the pause must not.
    _assert_timer_matches(elapsed_time, active_time, "pause excluded")
    assert paused_time > 0.2, "the pause must have actually lasted some time"


def test_stop_timer():
    """Tests that the timer can be stopped and the elapsed time is
     correct"""
    timer = Timer()
    timer.start()
    active_time = _sleep(0.1)  # Simulate some processing time
    timer.stop()
    after_stop_time = _sleep(0.2)  # Simulate some processing time
    elapsed_time = timer.get_elapsed_time()
    # The time spent after stop() must not be counted.
    _assert_timer_matches(elapsed_time, active_time, "stopped")
    assert after_stop_time > 0.15, "the post-stop sleep must have actually happened"


def test_restart_timer():
    """Tests that the timer can be restarted and the elapsed time is
     reset"""
    timer = Timer()
    timer.start()
    _sleep(0.1)  # Simulate some processing time
    timer.restart()
    elapsed_time = timer.get_elapsed_time()
    # The counter restarts from zero: the 0.1 s slept before restart() must be
    # forgotten. `restart()` returning a large value would mean it did not reset.
    assert elapsed_time < 0.05


def test_get_elapsed_time_in_milliseconds():
    """Tests that the elapsed time can be obtained in milliseconds"""
    timer = Timer()
    timer.start()
    active_time = _sleep(0.1)  # Simulate some processing time
    elapsed_time_ms = timer.get_elapsed_time_in_milliseconds()
    assert abs(elapsed_time_ms - active_time * 1000.0) < TIMER_TOLERANCE * 1000


def test_get_timer_state_as_string():
    """Tests that the timer state can be obtained as a string"""
    timer = Timer()
    assert timer.get_state_str() == "stopped"
    timer.start()
    assert timer.get_state_str() == "running"
    timer.pause_on()
    assert timer.get_state_str() == "pause"
    timer.pause_off()
    assert timer.get_state_str() == "running"
    timer.stop()
    assert timer.get_state_str() == "stopped"


def test_start_timer_multiple_times():
    """Tests that the timer can be started multiple times and the
    elapsed time is correct"""
    timer = Timer()
    for requested in (0.1, 0.2, 0.3):
        timer.start()
        active_time = _sleep(requested)  # Simulate some processing time
        elapsed_time = timer.get_elapsed_time()
        _assert_timer_matches(elapsed_time, active_time, f"after sleep({requested})")
        timer.stop()


def test_start_after_pause_forgets_paused_time():
    """A fresh start() must not inherit the pauses of the previous run.

    The accumulated pause duration lives on the Timer; if `start()` did not
    reset it, the next run would subtract the previous pauses again and report
    a negative elapsed time.
    """
    timer = Timer()
    timer.start()
    _sleep(0.1)
    timer.pause_on()
    _sleep(0.3)
    timer.pause_off()
    timer.stop()

    timer.start()
    active_time = _sleep(0.1)
    elapsed_time = timer.get_elapsed_time()
    assert elapsed_time > 0, "a new run must not report a negative duration"
    _assert_timer_matches(elapsed_time, active_time, "restart after a pause")


def test_pause_timer_multiple_times():
    """Tests that the timer can be paused multiple times and the
    elapsed time is correct"""
    timer = Timer()
    timer.start()
    active_time = _sleep(0.1)  # Simulate some processing time

    # Each round pauses for a while; none of it may be counted.
    for paused in (0.2, 0.3, 0.4):
        timer.pause_on()
        _sleep(paused)  # Simulate some processing time
        timer.pause_off()
        _assert_timer_matches(timer.get_elapsed_time(), active_time, f"paused {paused}s")
