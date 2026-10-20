"""The window status bar must stay out of the way of the sensors.

`GuiSR` paints a black band across the top of the window: the map name on the
left, the round progress on the right. It looks like map decoration, and that
is the trap these tests close.

The lidars never look at the window. They read the *uid image*, an offscreen
framebuffer in which every pixel is an entity identifier, rendered by
`TopDownView.update_and_draw_in_framebuffer()`. The window is a separate render
target. So a band drawn from `on_draw()` cannot reach the sensors -- but only
as long as nobody later moves that call into the shared drawing path, or starts
drawing it inside the camera activation with map coordinates.

What is pinned here:

- the band is drawn by `on_draw()` and by nothing else (`draw_status_bar=False`
  removes it, so it is really the bar and not something else that was checked);
- the uid image the sensors read is bit-for-bit identical with and without the
  band, before and after a resize -- the direct expression of "must not
  interfere with the map used for the lidar";
- the sensors therefore return the same readings either way;
- the bar survives being drawn over a letterboxed window, where the scissor box
  is smaller than the window and would clip it away;
- the progress label is right for a normal round, for a round past its limit,
  and for a degenerate limit.
"""

import pathlib
import sys

import arcade
import numpy as np
import pytest

# Insert the 'src' directory into sys.path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from swarm_rescue.simulation.drone.drone_abstract import DroneAbstract
from swarm_rescue.simulation.elements.normal_wall import NormalWall
from swarm_rescue.simulation.elements.rescue_center import RescueCenter
from swarm_rescue.simulation.gui_map.closed_playground import ClosedPlayground
from swarm_rescue.simulation.gui_map.gui_sr import GuiSR
from swarm_rescue.simulation.gui_map.map_abstract import MapAbstract
from swarm_rescue.simulation.gui_map.status_bar import StatusBar
from swarm_rescue.simulation.utils.misc_data import MiscData
from swarm_rescue.simulation.utils.constants import (
    WINDOW_STATUS_BAR_COLOR,
    WINDOW_STATUS_BAR_HEIGHT,
)


class StatusBarDrone(DroneAbstract):
    def define_message_for_all(self):
        return None

    def control(self):
        return {"forward": 0.0, "lateral": 0.0, "rotation": 0.0, "grasper": 0}


class StatusBarMap(MapAbstract):
    """A map with one drone and a wall, so the lidar has rays worth reading.

    Two details make it usable as a fixture for the comparisons below.

    The seed matters: entity uids -- the pixel values the ray sensors read --
    are drawn from the playground's generator, so two instances of an unseeded
    map disagree on every pixel of the uid image. The comparisons are between
    two *separate* views, so without a fixed seed they would report a
    difference that has nothing to do with the band. The seed goes to the
    playground as well as to the map: the uids come from the former.

    The wall matters for the same reason. An empty playground renders a flat
    background, and the uninitialized pixels around it come back with whatever
    the driver left in the texture -- the frame is then not reproducible even
    between two identical runs, and a strict equality check would be measuring
    that noise instead of the band.
    """

    def __init__(self, size=(400, 300), seed=42):
        super().__init__(drone_type=StatusBarDrone, seed=seed)
        self._size_area = size
        self._playground = ClosedPlayground(size=self._size_area, seed=seed)
        self._number_drones = 1
        self._drones = []
        self._number_wounded_persons = 0
        self._max_timestep_limit = 100
        self._max_walltime_limit = 1000

        misc_data = MiscData(
            size_area=self._size_area,
            number_drones=1,
            max_timestep_limit=100,
            max_walltime_limit=1000,
        )
        drone = StatusBarDrone(self._playground, misc_data=misc_data)
        self._drones.append(drone)
        self._playground.add(drone, ((0.0, 0.0), 0.0))

        wall = NormalWall(pos_start=(-120.0, 120.0), pos_end=(120.0, 120.0))
        self._playground.add(wall, wall.wall_coordinates)


def _make_gui(**kwargs):
    return GuiSR(the_map=StatusBarMap(), headless=True, **kwargs)


@pytest.fixture
def gui():
    view = _make_gui()
    try:
        yield view
    finally:
        view.close()


def _uid_image(gui):
    """Render and read back the exact image the ray sensors work from.

    Not `gui.render_uids()`: that is *this* view, which draws real colors.
    The sensors read `playground.uid_view`, a second `TopDownView` whose pixels
    are entity identifiers. Reading the wrong one would have compared the wrong
    surface and found no difference even if the band had leaked into the other.
    """
    # `uid_view` is None until `ray_compute` builds it, so ask for that first.
    # The property builds it lazily: assigning keeps the side effect explicit
    # instead of relying on a bare attribute access with no visible effect.
    _ = gui._playground.ray_compute
    view = gui._playground.uid_view
    assert view is not None
    view.render_uids()
    return np.array(view.read_uid_image())


class TestTheBandIsWindowOnly:
    """The bar is decoration: it belongs to the window and nowhere else."""

    def test_it_is_not_created_when_turned_off(self):
        """`draw_status_bar=False` really removes the band."""
        view = _make_gui(draw_status_bar=False)
        try:
            assert view._status_bar is None
        finally:
            view.close()

    def test_it_is_created_by_default(self, gui):
        """A plain GuiSR shows it: no flag to remember to pass."""
        assert gui._status_bar is not None

    def test_the_name_shown_is_the_map_class_name(self, gui):
        """
        The left label is the map class name.

        That is the identifier the launcher prints and the reports key on, so
        the window cannot claim a different map than the rest of the run.
        """
        assert gui._status_bar._map_name == "StatusBarMap"

    def test_a_frame_with_the_bar_draws(self, gui):
        """The regression test: the band must not break the frame."""
        gui.on_draw()

    def test_several_frames_with_the_bar_draw(self, gui):
        """
        More than one frame.

        The labels are built once and reused, and the percentage is written
        into the right label on each frame. A label rebuilt from stale state, or
        a projector whose viewport never followed the window, only shows up on
        the second call.
        """
        for step in range(5):
            gui._elapsed_timestep = step * 10
            gui.on_draw()

    def test_drawing_the_bar_leaves_the_scissor_enabled(self, gui):
        """
        The bar disables the scissor to reach the window edges, then restores it.

        The window needs that box: it is what preserves the letterbox color
        around the map, and `update_and_draw_in_framebuffer()` relies on it too.
        """
        from pyglet.gl import GL_SCISSOR_TEST, glIsEnabled

        gui.on_draw()
        assert glIsEnabled(GL_SCISSOR_TEST)

    def test_a_degenerate_window_draws_nothing(self, gui):
        """A zero-sized window must not divide by zero or draw out of bounds."""
        gui.on_resize(0, 0)
        gui.on_draw()


class TestTheSensorsCannotSeeIt:
    """The point of the whole exercise: the lidar map is untouched."""

    def test_the_uid_image_is_identical_with_and_without_the_bar(self):
        """
        The same scene, rendered with and without the band, gives the same pixels.

        This is the requirement stated as a measurement rather than as an
        argument: whatever the window shows, the image the lidar reads must be
        the same bytes. Anything drawn into the shared drawing path, or into the
        offscreen framebuffer, would change these arrays and fail here.
        """
        with_bar = _make_gui()
        try:
            with_bar.on_draw()
            image_with = _uid_image(with_bar)
        finally:
            with_bar.close()

        without_bar = _make_gui(draw_status_bar=False)
        try:
            without_bar.on_draw()
            image_without = _uid_image(without_bar)
        finally:
            without_bar.close()

        assert image_with.shape == image_without.shape
        assert np.array_equal(image_with, image_without), (
            "the status bar changed the uid image the lidar reads"
        )

    def test_the_uid_image_is_identical_after_a_resize(self, gui):
        """
        Resizing the window redraws the bar and must not touch the uid image.

        The bar is sized from the window and its projector viewport follows it,
        so a resize is the frame most likely to leak window-space drawing into
        the offscreen render.
        """
        before = _uid_image(gui)

        gui.on_resize(900, 700)
        gui.on_draw()
        after = _uid_image(gui)

        assert np.array_equal(before, after)

    def test_the_lidar_reading_survives_drawing_the_bar(self, gui):
        """
        End to end: drawing the band does not disturb the sensor's reading.

        The pixel comparison above is the strong form of the requirement, but it
        inspects an image whose provenance could one day change. This one asks
        the sensor itself, which is the only consumer the requirement is about.

        Measured *within one view*, across `on_draw()` calls with no step in
        between: the lidar values are refreshed by `playground.step()`, so
        nothing here can move them, and a difference could only come from the
        drawing. Comparing two separate runs instead would be meaningless --
        the readings carry sensor noise and raycasting jitter, so two identical
        configurations differ by several pixels on their own.
        """
        gui._playground.step(all_commands={}, all_messages={})
        drone = gui._playground.agents[0]

        before = np.array(drone.lidar().get_sensor_values()).copy()
        assert before.size > 0, "the lidar returned nothing to compare"

        for _ in range(3):
            gui.on_draw()

        after = np.array(drone.lidar().get_sensor_values()).copy()

        assert np.array_equal(before, after), (
            "the status bar changed what the lidar measures"
        )

    def test_the_recorder_image_does_not_contain_the_band(self, gui):
        """
        The reported screenshot is the offscreen image, so it carries no band.

        Worth pinning: `_last_image` is what the evaluation report shows, and a
        band there would put a claim about the map into the map's own picture.

        Compared *within* one view, before and after `on_draw()`: the display
        framebuffer is only reproducible inside a single instance, so building
        two views and comparing them would be measuring driver noise instead.
        """
        before = gui.get_playground_image().copy()

        gui.on_draw()
        after = gui.get_playground_image().copy()

        assert np.array_equal(before, after), (
            "drawing the status bar changed the image used for the report"
        )


class TestTheBandNeverHidesTheMap:
    """The band reserves its room instead of covering the map.

    The failure this exists to prevent: the band is drawn across the whole
    window *after* the map, so if the camera still letterboxed the map against
    the full window height, the band would sit on top of the map's upper rows.
    Nothing would raise -- the band would simply eat them, and the rows would be
    gone from the window while still being present in the uid image the sensors
    read, which is exactly the kind of silent divergence that is hard to spot.
    """

    @pytest.mark.parametrize("width,height", [
        (1920, 1000),  # letterboxed on both sides
        (1200, 800),   # exactly the map aspect ratio
        (800, 1200),   # taller than the map
        (640, 480),
        (1000, 400),   # very wide
    ])
    def test_the_map_starts_below_the_band(self, gui, width, height):
        """`viewport.top` must not reach into the band."""
        gui.on_resize(width, height)
        viewport = gui.camera.viewport

        band_bottom = height - gui._status_bar.effective_height(height)
        assert viewport.top <= band_bottom + 1e-6, (
            f"the map reaches y={viewport.top} but the band starts its map-free "
            f"zone at y={band_bottom} (window {width}x{height})"
        )

    def test_the_map_is_still_centered_in_the_area_below_the_band(self, gui):
        """
        Reserving the strip must not push the map against the bottom edge.

        The letterbox is symmetric *within the area left over*, so the band
        does not silently become a top-heavy layout: half the slack above the
        map and half below it, measured from the band.
        """
        gui.on_resize(1920, 1000)
        viewport = gui.camera.viewport
        band_bottom = 1000 - gui._status_bar.effective_height(1000)

        left_gap = viewport.left
        right_gap = 1920 - viewport.right
        assert left_gap == pytest.approx(right_gap, abs=1.0)

        # Below the map, and between the map and the band.
        bottom_gap = viewport.bottom
        top_gap = band_bottom - viewport.top
        assert bottom_gap == pytest.approx(top_gap, abs=1.0)

    def test_the_band_reserves_nothing_when_turned_off(self):
        """Without the band the map is letterboxed against the whole window.

        The pre-existing behavior, pinned so the reservation cannot leak into
        the no-band case.
        """
        view = _make_gui(draw_status_bar=False)
        try:
            view.on_resize(1920, 1000)
            assert view.camera.viewport.top == pytest.approx(1000, abs=1.0)
        finally:
            view.close()

    def test_the_map_keeps_at_least_one_row_in_a_tiny_window(self, gui):
        """
        A window shorter than the band gives the room to the map.

        `Camera2D.unproject` divides by the viewport size, so a zero-sized
        viewport would make `screen_to_world` -- and with it the mouse tool --
        raise `ZeroDivisionError`. The band is decoration; when the two cannot
        both fit, the map wins.
        """
        gui.on_resize(400, 10)
        viewport = gui.camera.viewport

        assert viewport.height > 0
        assert viewport.width > 0

    def test_the_reservation_matches_what_is_painted(self, gui):
        """
        The reserved height and the painted height are the same number.

        They come from `StatusBar.effective_height` on both sides, and this is
        what makes the guarantee structural rather than a coincidence of two
        clamps happening to agree today: if one side were changed without the
        other, the band would grow back over the map with every test above still
        passing.
        """
        for height in (1000, 300, 40, 10):
            assert gui._reserved_top_height(height) == \
                gui._status_bar.effective_height(height)

    def test_the_painted_band_stops_where_the_map_starts(self, gui):
        """
        Intercept the real draw call and compare it with the viewport.

        The other tests in this class compare numbers that describe the
        layout; this one checks the rectangle actually handed to the GPU, which
        is the thing that would cover the map.

        The window is resized for real, not only through `on_resize()`: the
        band reads `window.width` / `window.height`, and `on_resize()` moves
        the camera viewport alone, so a camera-only resize would compare a
        1200x800 band against a viewport laid out for a different size.
        """
        import swarm_rescue.simulation.gui_map.status_bar as status_bar_module

        gui._playground.window.set_size(1200, 800)
        gui.on_resize(1200, 800)

        drawn = []
        original = status_bar_module.arcade.draw_lrbt_rectangle_filled

        def spy(**kwargs):
            drawn.append(kwargs)
            return original(**kwargs)

        status_bar_module.arcade.draw_lrbt_rectangle_filled = spy
        try:
            gui.on_draw()
        finally:
            status_bar_module.arcade.draw_lrbt_rectangle_filled = original

        assert len(drawn) == 1, "the band was not drawn exactly once"
        rect = drawn[0]
        viewport = gui.camera.viewport

        # `bottom` is the lowest row of the band; it must be at or above the
        # top of the map.
        assert rect["bottom"] >= viewport.top - 1e-6
        assert rect["top"] == pytest.approx(800)
        assert rect["left"] == 0
        assert rect["right"] == pytest.approx(1200)


class TestLetterboxedWindow:
    """On a letterboxed window the scissor box is smaller than the window."""

    def test_the_bar_draws_on_a_letterboxed_window(self, gui):
        """
        The window is not the map aspect ratio, so the scissor clips the edges.

        The band spans the full window width, so without disabling the scissor
        it would lose its ends here -- and this is the *default* window shape
        whenever the user resizes, so it is not an exotic case.
        """
        gui.on_resize(1000, 400)
        gui.on_draw()

    def test_the_viewport_is_smaller_than_the_window(self, gui):
        """Precondition: the clipping the bar has to survive is real."""
        gui.on_resize(1000, 400)
        viewport = gui.camera.viewport
        assert viewport.width < 1000 or viewport.height < 400

    def test_the_bar_follows_a_resize(self, gui):
        """
        Both labels are rebuilt for the new width.

        The right one is anchored to the right edge: after a widening resize it
        has to sit at the new edge, not at the x it was built for. The window is
        resized for real here -- `on_resize()` only moves the camera viewport,
        the bar reads `window.width`, so resizing the camera alone would leave
        the band where it was and prove nothing.
        """
        gui._playground.window.set_size(600, 400)
        gui.on_resize(600, 400)
        gui.on_draw()

        gui._playground.window.set_size(1400, 400)
        gui.on_resize(1400, 400)
        gui.on_draw()

        assert gui._status_bar._labels_window_size == (1400, 400)
        assert gui._status_bar._right_text.x == pytest.approx(1400 - 10, abs=1.0)


class TestTheProgressLabel:
    """`progress_label` is pure, so it is checked directly."""

    def test_it_reports_the_percentage_of_the_limit(self):
        assert StatusBar.progress_label(50, 200) == "25.0 % (50/200 timesteps)"

    def test_it_is_clamped_at_one_hundred(self):
        """
        The step counter is incremented before the limit is checked, so a round
        stopped by its limit can read one step over it. The bar must show 100 %,
        not 100.5 %.
        """
        label = StatusBar.progress_label(201, 200)
        assert label.startswith("100.0 %")

    def test_it_survives_a_zero_limit(self):
        """A map declaring a limit of 0 must not divide by zero."""
        assert StatusBar.progress_label(0, 0) == "0.0 % (0/0 timesteps)"

    def test_it_survives_a_negative_limit(self):
        """Defensive: a negative limit must not divide by zero either."""
        assert "%" in StatusBar.progress_label(5, -10)

    def test_it_returns_nothing_when_there_is_no_limit(self):
        """A map declaring neither limit has no progress to show."""
        assert StatusBar.progress_label(50, None) is None

    def test_it_shows_the_walltime_alongside_the_steps(self):
        label = StatusBar.progress_label(50, 200, elapsed_walltime=42.4,
                                         max_walltime_limit=600)
        assert label == "25.0 % (50/200 timesteps) - 42s/600s"

    def test_it_shows_only_the_declared_limit(self):
        """Each half is omitted when its own limit is missing."""
        assert (StatusBar.progress_label(50, None, elapsed_walltime=42.0,
                                         max_walltime_limit=600)
                == "42s/600s")
        assert (StatusBar.progress_label(50, 200, elapsed_walltime=42.0,
                                         max_walltime_limit=None)
                == "25.0 % (50/200 timesteps)")

    def test_it_clamps_the_walltime_to_its_limit(self):
        """The wall clock is read before the limit is checked."""
        label = StatusBar.progress_label(0, 200, elapsed_walltime=700.0,
                                         max_walltime_limit=600)
        assert label.endswith("600s/600s")

    def test_it_shows_the_rescued_count(self):
        label = StatusBar.progress_label(0, 200, rescued_number=3,
                                         total_wounded_persons=7)
        assert label.endswith("3/7 wounded")

    def test_it_hides_the_rescued_count_without_wounded_persons(self):
        """No wounded person, no rescue center: `0/0 wounded` says nothing."""
        assert StatusBar.progress_label(0, 200, rescued_number=0,
                                        total_wounded_persons=0
                                        ) == "0.0 % (0/200 timesteps)"
        assert StatusBar.progress_label(0, 200, rescued_number=0,
                                        total_wounded_persons=None
                                        ) == "0.0 % (0/200 timesteps)"

    def test_it_clamps_the_rescued_count_to_the_total(self):
        """The reward counter cannot push the display past the total."""
        label = StatusBar.progress_label(0, 200, rescued_number=9,
                                         total_wounded_persons=7)
        assert label.endswith("7/7 wounded")

    def test_it_moves_as_the_round_progresses(self, gui):
        """The label follows the round rather than being frozen at build time."""
        gui._elapsed_timestep = 0
        gui.on_draw()
        first = gui._status_bar._right_text.text

        gui._elapsed_timestep = 50
        gui.on_draw()
        assert gui._status_bar._right_text.text != first

    def test_a_reset_puts_the_counters_back_on_the_bar(self, gui):
        """
        Pressing R restarts the round, so the bar restarts with it.

        The counters belong to the view, not to the playground, so
        `Playground.reset()` alone would leave the previous round's steps and
        rescued count on the bar. This goes through `on_key_press`, the path the
        player actually takes.
        """
        gui._elapsed_timestep = 80
        gui._rescued_number = 5
        gui._elapsed_walltime = 900.0
        gui.on_draw()
        assert "80/100" in gui._status_bar._right_text.text

        gui.on_key_press(arcade.key.R, 0)
        gui.on_draw()

        label = gui._status_bar._right_text.text
        assert "0/100" in label
        assert "5/" not in label
        assert gui._elapsed_walltime < 900.0

    def test_the_right_side_stays_empty_without_a_limit(self, gui):
        """A map with no limit at all shows no progress on the right."""
        gui.on_draw()
        assert gui._status_bar._right_text.text != ""

        gui._max_timestep_limit = None
        gui._max_walltime_limit = None
        gui.on_draw()
        assert gui._status_bar._right_text.text == ""

    def test_no_rescue_count_without_rescue_center(self, gui):
        """The fixture has no rescue center and no wounded: nothing to count."""
        gui.on_draw()
        assert "wounded" not in gui._status_bar._right_text.text

    def test_the_rescue_count_appears_when_rescuable(self):
        """A map with a rescue center and wounded persons shows the counter."""

        class MapWithWounded(StatusBarMap):
            def __init__(self):
                super().__init__()
                self._number_wounded_persons = 2
                center = RescueCenter(size=(60, 60))
                self._playground.add(center, ((0.0, -100.0), 0))

        view = GuiSR(the_map=MapWithWounded(), headless=True)
        try:
            view._rescued_number = 1
            view.on_draw()
            assert "1/2 wounded" in view._status_bar._right_text.text
        finally:
            view.close()


class TestTheBandConstants:
    """The band has to be dark and wide enough to read as a band."""

    def test_the_fill_is_darker_than_the_letterbox(self):
        """
        It must not read as more letterbox.

        `WINDOW_LETTERBOX_COLOR` is (64, 64, 64); a bar at that level would be
        indistinguishable from the frame around the map.
        """
        from swarm_rescue.simulation.utils.constants import (
            WINDOW_LETTERBOX_COLOR,
        )

        assert sum(WINDOW_STATUS_BAR_COLOR) < sum(WINDOW_LETTERBOX_COLOR)

    def test_the_band_has_a_usable_thickness(self):
        """A band thinner than a line of text would clip its own labels."""
        assert WINDOW_STATUS_BAR_HEIGHT >= 14
