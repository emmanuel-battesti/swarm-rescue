"""
`MouseMeasure` must report world coordinates, at any zoom and window size.

The tool used to convert a mouse position by hand:
`world = pixel - playground_size / 2`. That identity only holds for a camera
centered on the origin at zoom 1 -- and it produced a constant offset that grew
every time the window was resized, which is exactly what was reported.

The conversion is the camera's job in arcade 3.x (`Camera2D.unproject`; the
`View.get_world_coordinates` / `get_mouse_pos` helpers of arcade 2.x are gone).
So the tool now takes the conversion as an argument.

`test_mouse_measure_draw.py` covers `draw()` and passed throughout: it asserts
that nothing raises, never that the numbers are right. That is the gap these
tests close -- they aim the mouse at a point whose world position is known and
check what comes back.
"""

import pathlib
import sys

import arcade
import pytest

# Insert the 'src' directory into sys.path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from swarm_rescue.maps.map_intermediate_01 import MapIntermediate01
from swarm_rescue.simulation.drone.drone_motionless import DroneMotionless
from swarm_rescue.simulation.gui_map.gui_sr import GuiSR
from swarm_rescue.simulation.utils.mouse_measure import MouseMeasure

# Zooms chosen to include the nominal 1.0, a zoom in, a zoom out, and an odd
# value: the old formula ignored zoom entirely, so only varied zooms can show a
# regression.
ZOOMS = [1.0, 2.0, 0.5, 3.7]


def _identity(point):
    """A stand-in camera for the unit tests: pixels are world units."""
    return (point[0], point[1])


@pytest.fixture
def gui():
    """A headless GuiSR, which is what owns the camera in real use."""
    the_map = MapIntermediate01(drone_type=DroneMotionless)
    view = GuiSR(
        the_map=the_map, size=(1200, 700), use_mouse_measure=True, headless=True
    )
    try:
        yield view
    finally:
        view.close()


def _world_points_on_integer_pixels(gui, step):
    """
    Yield world points whose screen position is a whole pixel.

    A real mouse reports integer pixels, so a target that lands between two
    pixels could never be aimed at exactly. Only points a mouse could actually
    point at are meaningful here.
    """
    for ix in range(-3, 4):
        for iy in range(-3, 4):
            target = (ix * step * 10.0, iy * step * 10.0)
            screen = gui.camera.project(target)
            if abs(screen.x - round(screen.x)) > 1e-6:
                continue
            if abs(screen.y - round(screen.y)) > 1e-6:
                continue
            yield target, (round(screen.x), round(screen.y))


def _aim(gui, target):
    """Project a world point and hand back the pixel a mouse would report.

    `Camera2D.project` returns fractional pixels, and with an even-sized window
    the map center lands exactly on a half pixel (`599.5, 349.5` for 1200x700):
    the center of the view is always between two pixels. A real mouse can only
    report an integer, so the half pixel has to be rounded away here rather than
    measured and then compared exactly. That rounding is what makes an exact
    comparison fail by 0.5, which is the tolerance the callers below allow for.
    """
    screen = gui.camera.project(target)
    return round(screen.x), round(screen.y)


class TestAimedPointIsRecovered:
    """
    The core property: aim at a known world point, get it back.

    This is the assertion the previous test file could not make.
    """

    @pytest.mark.parametrize("zoom", ZOOMS)
    def test_a_known_point_is_measured_exactly(self, gui, zoom):
        gui.camera.zoom = zoom
        measure = gui._mouse_measure

        for target, screen in _world_points_on_integer_pixels(gui, zoom):
            measure.on_mouse_motion(screen[0], screen[1], 0, 0)

            assert measure.x_mouse == pytest.approx(target[0], abs=1e-6)
            assert measure.y_mouse == pytest.approx(target[1], abs=1e-6)

    def test_the_map_center_is_the_origin(self, gui):
        """
        The point that used to be reported as (-400, -250).

        With the camera on the origin, world (0, 0) must measure as (0, 0).

        One pixel of tolerance, for the half-pixel rounding in `_aim`.
        """
        gui.camera.zoom = 1.0
        measure = gui._mouse_measure
        pixel = _aim(gui, (0.0, 0.0))

        measure.on_mouse_motion(pixel[0], pixel[1], 0, 0)

        assert (measure.x_mouse, measure.y_mouse) == pytest.approx(
            (0.0, 0.0), abs=1.0)

    def test_press_reports_the_aimed_point(self, gui, capsys):
        """`on_mouse_press` prints the position too, so it must be right.

        One pixel of tolerance, for the half-pixel rounding in `_aim`.
        """
        gui.camera.zoom = 1.0
        measure = gui._mouse_measure
        target = (100.0, 50.0)
        pixel = _aim(gui, target)

        measure.on_mouse_press(pixel[0], pixel[1],
                               arcade.MOUSE_BUTTON_LEFT)

        assert (measure.x_mouse, measure.y_mouse) == pytest.approx(
            target, abs=1.0)

    def test_the_measurement_survives_a_resize(self, gui):
        """
        The bug as it was reported: the offset changed with the window.

        The same world point, projected through two different window sizes, must
        still measure the same. Under the old formula it did not.

        One pixel of tolerance, for the half-pixel rounding in `_aim`. The offset
        this guards against was hundreds of pixels, so this still catches it.
        """
        measure = gui._mouse_measure
        target = (0.0, 0.0)

        for width, height in [(1200, 700), (1600, 900), (900, 1400), (700, 500)]:
            gui.on_resize(width, height)
            pixel = _aim(gui, target)
            measure.on_mouse_motion(pixel[0], pixel[1], 0, 0)

            assert (measure.x_mouse, measure.y_mouse) == pytest.approx(
                target, abs=1.0), (
                f"the measurement moved when the window became {width}x{height}")

    def test_a_moved_camera_does_not_shift_the_measurement(self, gui):
        """
        Panning the camera must move what is under the cursor, not the answer.

        With the camera on (137, -42), aiming at the cursor position itself has
        to report that world position.

        One pixel of tolerance, like its siblings. This one used to allow
        nothing at all, which only held while the projection of (0, 0) landed
        on a whole pixel. Once the status band letterboxes the map the
        viewport is offset, the projection falls between two pixels, and
        `round()` in `_aim` costs up to half a pixel -- a quarter of a world
        unit at this zoom. The property under test is that panning does not
        shift the answer, not that the rounding is free.
        """
        gui.camera.zoom = 2.0
        gui.camera.position = (137.0, -42.0)
        measure = gui._mouse_measure
        screen = gui.camera.project((0.0, 0.0))

        measure.on_mouse_motion(round(screen.x), round(screen.y), 0, 0)

        assert (measure.x_mouse, measure.y_mouse) == pytest.approx(
            (0.0, 0.0), abs=1.0)


class TestDistances:
    """
    A translation must not change a distance.

    Worth its own class: the offset was constant, so the distance between two
    points came out right while both endpoints were wrong. A test that only
    checked distances would have missed the bug.
    """

    def test_the_distance_is_independent_of_the_offset(self, gui):
        gui.camera.zoom = 1.0
        measure = gui._mouse_measure

        start_pixel = _aim(gui, (0.0, 0.0))
        end_pixel = _aim(gui, (30.0, 40.0))

        measure.on_mouse_motion(start_pixel[0], start_pixel[1], 0, 0)
        measure.on_mouse_press(start_pixel[0], start_pixel[1],
                               arcade.MOUSE_BUTTON_LEFT)
        measure.on_mouse_motion(end_pixel[0], end_pixel[1], 0, 0)

        dx = measure.x_mouse - measure.x_mouse_prev
        dy = measure.y_mouse - measure.y_mouse_prev

        # One pixel of tolerance: each end was snapped to a whole pixel by
        # `_aim`, so the delta can be off by up to one. The offset this guards
        # against was hundreds of pixels.
        assert dx == pytest.approx(30.0, abs=1.0), f"dx={dx}"
        assert dy == pytest.approx(40.0, abs=1.0), f"dy={dy}"

    def test_the_distance_holds_at_any_zoom(self, gui):
        gui.camera.zoom = 3.7
        measure = gui._mouse_measure

        start_pixel = _aim(gui, (0.0, 0.0))
        end_pixel = _aim(gui, (37.0, 37.0))

        measure.on_mouse_motion(start_pixel[0], start_pixel[1], 0, 0)
        measure.on_mouse_press(start_pixel[0], start_pixel[1],
                               arcade.MOUSE_BUTTON_LEFT)
        measure.on_mouse_motion(end_pixel[0], end_pixel[1], 0, 0)

        dx = measure.x_mouse - measure.x_mouse_prev
        dy = measure.y_mouse - measure.y_mouse_prev

        assert dx == pytest.approx(37.0, abs=1.0), f"dx={dx}"
        assert dy == pytest.approx(37.0, abs=1.0), f"dy={dy}"


class TestTheToolRefusesToGuess:
    def test_a_missing_conversion_is_refused(self):
        """
        Without a conversion the tool cannot be trusted.

        Failing at construction is the point: a tool that quietly measures in
        the wrong unit is worse than one that refuses to start.
        """
        with pytest.raises(ValueError, match="screen_to_world"):
            MouseMeasure(screen_to_world=None)

    def test_a_non_callable_conversion_is_refused(self):
        with pytest.raises(ValueError, match="screen_to_world"):
            MouseMeasure(screen_to_world=(800, 500))

    def test_the_identity_conversion_is_accepted(self):
        """The unit tests below rely on a trivial stand-in being allowed."""
        measure = MouseMeasure(screen_to_world=_identity)

        measure.on_mouse_motion(12.0, -7.0, 0, 0)

        assert (measure.x_mouse, measure.y_mouse) == (12.0, -7.0)


class TestTheOldFormulaIsGone:
    def test_no_half_map_offset_remains(self):
        """
        A guard against the formula coming back.

        The bug was a one-line arithmetic shortcut, so it can come back as one.
        """
        measure_source = (
            pathlib.Path(__file__).resolve().parent.parent
            / "src" / "swarm_rescue" / "simulation" / "utils" / "mouse_measure.py"
        ).read_text(encoding="utf-8")

        assert "_playground_size[0] / 2" not in measure_source
        assert "_playground_size[1] / 2" not in measure_source
