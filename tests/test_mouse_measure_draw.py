"""
Regression tests for `MouseMeasure.draw()`.

The `draw()` path is only reached after a left mouse press sets
`draw_line = True`, so it was never exercised by the test suite. It
therefore hid a stale Arcade 2.x call (`arcade.draw_lrtb_rectangle_outline`,
renamed to `draw_lrbt_rectangle_outline` in Arcade 3.x) which raised
`AttributeError` at runtime in the interactive GUI.

`draw()` issues real GL commands, so these tests need a genuine
`arcade.Window` with an OpenGL context: the headless stub installed by
`conftest` (which sets `ctx = None`) is not enough.

What these tests do *not* check is whether the measured numbers are right --
they assert that nothing raises. That gap let a constant offset survive here
untested; it is covered by `test_mouse_measure_coordinates.py`, which is why
the fixture below passes an explicit stand-in conversion.
"""

import pathlib
import sys

import pytest
import arcade
import arcade.window_commands as window_commands

# Insert the 'src' directory into sys.path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from swarm_rescue.simulation.utils.mouse_measure import MouseMeasure


@pytest.fixture
def gl_window():
    """A real (invisible) window, so `ctx` and its GL programs exist."""
    try:
        window_commands.get_window()
    except RuntimeError:
        pass
    if getattr(window_commands.get_window(), "ctx", None) is None:
        arcade.Window(width=64, height=64, visible=False)
    yield window_commands.get_window()


def _identity(point):
    """A stand-in camera: pixels are world units.

    `draw()` does not care about the conversion -- it only needs the world
    positions it was given. The conversion itself is covered by
    `test_mouse_measure_coordinates.py`, which aims at points whose world
    position is known and checks what comes back.
    """
    return (point[0], point[1])


@pytest.fixture
def measure() -> MouseMeasure:
    """A measure with a non-zero drag, so `draw_line` is True."""
    mm = MouseMeasure(screen_to_world=_identity)
    mm.on_mouse_motion(100, 200, 0, 0)
    mm.on_mouse_press(100, 200, arcade.MOUSE_BUTTON_LEFT)
    mm.on_mouse_motion(160, 260, 60, 60)
    assert mm.draw_line is True
    return mm


def test_draw_line_flag_set_after_left_click(measure: MouseMeasure) -> None:
    """Sanity check: the guarded path is actually reachable."""
    assert measure.draw_line is True


def test_draw_does_not_raise(gl_window, measure: MouseMeasure) -> None:
    """`draw()` must not raise once a drag is in progress.

    This is the assertion that catches the removed Arcade 2.x symbol.
    """
    measure.draw()


def test_draw_is_noop_without_drag(gl_window) -> None:
    """`draw()` before any click must stay a no-op."""
    MouseMeasure(screen_to_world=_identity).draw()


def test_draw_accepts_disable_flag(gl_window, measure: MouseMeasure) -> None:
    """`draw(enable=False)` must not draw the measurement."""
    measure.draw(enable=False)


def test_draw_after_release(gl_window, measure: MouseMeasure) -> None:
    """Drawing after releasing the button must still work."""
    measure.on_mouse_release(160, 260, arcade.MOUSE_BUTTON_LEFT)
    measure.draw()


def test_no_arcade2_measure_api_remains() -> None:
    """Guard against reintroducing the removed Arcade 2.x symbol."""
    assert hasattr(arcade, "draw_lrbt_rectangle_outline")
    assert not hasattr(arcade, "draw_lrtb_rectangle_outline")
