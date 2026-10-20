"""The simulation must shut down silently, whatever ended the run.

Ending a run (the timer, or Q/E) closes the window from inside `on_update`,
and pyglet still schedules `on_update`/`on_draw` for a frame or two afterward.
At that point the GL context is gone, so every GL call raises:

    GLException: No GL context; create a Window first

and, before the fix, the run ended with two GLException tracebacks on the
console -- one for the extra `on_update`, one for the `on_draw` that the
exception handler triggered. The user's report was that closing the map, either
by itself at the timer limit or with the Q key, printed a wall of tracebacks.

These tests pin the two halves of the contract:
  - the shutdown sequence runs exactly once (the last framebuffer image is read
    before the window is closed, not skipped),
  - nothing touches the GPU after the window is closed.
"""

import pytest

from swarm_rescue.simulation.gui_map.gui_sr import GuiSR


@pytest.fixture
def gui():
    """A headless GuiSR on a tiny map, closed at the end of the test."""
    from swarm_rescue.simulation.drone.drone_motionless import DroneMotionless
    from swarm_rescue.maps.map_intermediate_01 import MapIntermediate01

    view = GuiSR(
        the_map=MapIntermediate01(drone_type=DroneMotionless),
        size=(400, 300),
        headless=True,
    )
    try:
        yield view
    finally:
        view.close()


def _run_to_termination(gui, limit=1):
    """Drive updates until the run terminates, and return how it terminated."""
    gui._max_timestep_limit = limit
    for _ in range(limit + 5):
        gui.on_update(1 / 60)
        if gui._window_closed:
            return "timer"
    return "never"


class TestShutdown:
    def test_the_shutdown_sequence_runs_once(self, gui):
        """The last image is read, then the window is closed, exactly once.

        The image has to be read *before* closing: it comes from the offscreen
        framebuffer, which needs the GL context. So a single run must both set
        `_last_image` and close the window, and a second `on_update` must not
        try to do it again (that second call is the crash the user saw).
        """
        assert _run_to_termination(gui) == "timer"

        assert gui._window_closed is True
        assert gui._last_image is not None, (
            "the last image must still be read, before the window is closed"
        )
        assert gui._last_image.shape[0] > 0 and gui._last_image.shape[1] > 0

    def test_no_gl_call_after_the_window_is_closed(self, gui):
        """Updates and draws after the close are no-ops, not exceptions.

        This is the actual regression: with the window closed, `clear()` raises
        `GLException: No GL context; create a Window first`.
        """
        assert _run_to_termination(gui) == "timer"

        # pyglet keeps calling both for a few frames after `close()`.
        for _ in range(5):
            gui.on_update(1 / 60)
            gui.on_draw()

    def test_q_terminates_and_shuts_down_silently(self, gui):
        """The Q key goes through the same shutdown path as the timer."""
        import arcade

        gui.on_key_press(arcade.key.Q, 0)
        assert gui._terminate is True
        assert gui._window_closed is False

        gui.on_update(1 / 60)

        assert gui._window_closed is True
        assert gui._last_image is not None

        # And the frames that follow stay silent.
        for _ in range(5):
            gui.on_update(1 / 60)
            gui.on_draw()

    def test_reset_is_refused_after_the_window_is_closed(self, gui):
        """R re-registers entities on the GPU, so it is refused once closed."""
        import arcade

        assert _run_to_termination(gui) == "timer"

        # Must not raise: the playground was released along with the context.
        gui.on_key_press(arcade.key.R, 0)
