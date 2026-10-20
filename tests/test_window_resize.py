"""
Tests for window resizing functionality in GuiSR.

This module tests:
- The camera viewport keeps the map aspect ratio (letterboxing)
- Resizing the window never forces the window back to a given size
- Resizing the window never changes the framebuffer / recorded size
- Resizing does not affect the simulation (positions, lidar)
"""

import pathlib
import sys

import numpy as np
import pytest
import arcade
import arcade.window_commands as window_commands
from pyglet.math import Vec4

from arcade.camera.projection_functions import (
    generate_orthographic_matrix,
    generate_view_matrix,
)

# Insert the 'src' directory into sys.path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from swarm_rescue.simulation.drone.drone_abstract import DroneAbstract
from swarm_rescue.simulation.gui_map.closed_playground import ClosedPlayground
from swarm_rescue.simulation.gui_map.map_abstract import MapAbstract
from swarm_rescue.simulation.utils.constants import WINDOW_LETTERBOX_COLOR


def _ensure_headless_arcade_window() -> None:
    try:
        window_commands.get_window()
    except RuntimeError:
        arcade.Window(width=1, height=1, visible=False)


class DummyDrone(DroneAbstract):
    def define_message_for_all(self):
        pass

    def control(self):
        return {"forward": 0.0, "lateral": 0.0, "rotation": 0.0, "grasper": 0}


class DummyMap(MapAbstract):
    def __init__(self, size=(1200, 800)):
        super().__init__(drone_type=DummyDrone)
        self._size_area = size
        self._playground = ClosedPlayground(size=self._size_area)
        self._number_drones = 0
        self._drones = []
        self._number_wounded_persons = 0


@pytest.fixture
def mock_map():
    """A simple map usable for GUI tests."""
    return DummyMap()


class TestCameraViewport:
    """The camera viewport is the letterboxed map area."""

    def test_viewport_keeps_map_aspect_ratio(self, mock_map):
        """The viewport ratio must match the map ratio, whatever the window."""
        from swarm_rescue.simulation.gui_map.gui_sr import GuiSR

        gui = GuiSR(the_map=mock_map, headless=True)
        try:
            expected = 1200 / 800  # map aspect ratio
            for width, height in [(1920, 1080), (1000, 1000), (800, 1200), (640, 480)]:
                gui.on_resize(width, height)
                viewport = gui.camera.viewport
                assert viewport.height > 0
                ratio = viewport.width / viewport.height
                assert ratio == pytest.approx(expected, rel=1e-6)
        finally:
            gui.close()

    def test_viewport_fits_inside_window(self, mock_map):
        """The map area must never exceed the window size."""
        from swarm_rescue.simulation.gui_map.gui_sr import GuiSR

        gui = GuiSR(the_map=mock_map, headless=True)
        try:
            for width, height in [(1920, 1080), (1000, 1000), (800, 1200)]:
                gui.on_resize(width, height)
                viewport = gui.camera.viewport
                assert viewport.width <= width + 1e-6
                assert viewport.height <= height + 1e-6
        finally:
            gui.close()

    def test_viewport_is_centered(self, mock_map):
        """
        The letterbox is symmetric: the map is centered in the area it has.

        The area is the window minus the status band, not the whole window --
        the band reserves its rows so it never covers the map, and centering
        against the full height would push the map down under it.
        """
        from swarm_rescue.simulation.gui_map.gui_sr import GuiSR

        gui = GuiSR(the_map=mock_map, headless=True)
        try:
            width, height = 1920, 1000
            gui.on_resize(width, height)
            viewport = gui.camera.viewport
            band = gui._reserved_top_height(height)
            left_gap = viewport.left
            right_gap = width - viewport.right
            bottom_gap = viewport.bottom
            top_gap = height - band - viewport.top
            assert left_gap == pytest.approx(right_gap, abs=1.0)
            assert bottom_gap == pytest.approx(top_gap, abs=1.0)
        finally:
            gui.close()

    def test_the_map_is_never_under_the_status_band(self, mock_map):
        """
        The viewport must stop at the bottom of the band.

        The band is painted after the map, over the whole window width, so a
        viewport reaching into its rows would have them painted over. The
        scissor is the only thing that could stop it, and the scissor *is* the
        viewport -- so this is the check that keeps the two consistent.
        """
        from swarm_rescue.simulation.gui_map.gui_sr import GuiSR

        gui = GuiSR(the_map=mock_map, headless=True)
        try:
            for width, height in [(1920, 1080), (1000, 1000), (800, 1200),
                                  (640, 480), (400, 400), (1920, 30)]:
                gui.on_resize(width, height)
                band_bottom = height - gui._reserved_top_height(height)
                assert gui.camera.viewport.top <= band_bottom + 1e-6
        finally:
            gui.close()

    def test_world_origin_is_at_the_center_of_the_map_area(self, mock_map):
        """
        The world point (0, 0) must be displayed at the center of the map area,
        not at a corner, whatever the window size and the letterbox.

        "Center of the map area", not "center of the window": the status band
        takes the top rows, so the center of what is left is half a band lower
        than the window center. See `test_viewport_is_centered`.

        The matrices are combined the way the GPU does it
        (projection @ view) to get the actual rendered position.
        """
        from swarm_rescue.simulation.gui_map.gui_sr import GuiSR

        gui = GuiSR(the_map=mock_map, headless=True)
        try:
            # The camera projection is centered on the origin
            # (`LRBT(-w/2, w/2, -h/2, h/2)`) and `update_sprite` puts a sprite at
            # its world position, so the world (0, 0) is projected as (0, 0).
            # This test used to offset it by (view_width/2, view_height/2)
            # first, which was right while `update_sprite` still converted world
            # coordinates to view pixels and wrong as soon as it stopped.
            for width, height in [(1200, 800), (1920, 1080), (1000, 1000),
                                  (800, 1200), (640, 480), (400, 400)]:
                gui.on_resize(width, height)

                projection = generate_orthographic_matrix(
                    gui.camera.projection_data, gui.camera.zoom)
                view = generate_view_matrix(gui.camera.view_data)
                ndc = projection @ view @ Vec4(0.0, 0.0, 0.0, 1.0)

                viewport = gui.camera.viewport
                screen_x = viewport.left + (0.5 * ndc.x + 0.5) * viewport.width
                screen_y = viewport.bottom + (0.5 * ndc.y + 0.5) * viewport.height

                band = gui._reserved_top_height(height)
                assert screen_x == pytest.approx(width / 2, abs=1.0)
                assert screen_y == pytest.approx((height - band) / 2, abs=1.0)
        finally:
            gui.close()

    def test_scissor_follows_viewport(self, mock_map):
        """
        The scissor box clips the drawing to the map area, so it must always
        match the viewport: otherwise the map would overflow in the letterbox.
        """
        from swarm_rescue.simulation.gui_map.gui_sr import GuiSR

        gui = GuiSR(the_map=mock_map, headless=True)
        try:
            for width, height in [(1920, 1080), (1000, 1000), (800, 1200), (640, 480)]:
                gui.on_resize(width, height)
                assert gui.camera.scissor == gui.camera.viewport
        finally:
            gui.close()

    def test_projection_is_not_modified_by_resize(self, mock_map):
        """
        The projection defines the map area: it must stay tied to the map
        size and never follow the window, otherwise the map would be
        distorted.
        """
        from swarm_rescue.simulation.gui_map.gui_sr import GuiSR

        gui = GuiSR(the_map=mock_map, headless=True)
        try:
            projection_before = gui.camera.projection
            for width, height in [(1920, 1080), (640, 480), (1000, 1000)]:
                gui.on_resize(width, height)
                assert gui.camera.projection == projection_before
        finally:
            gui.close()

    def test_resize_with_zero_size_is_ignored(self, mock_map):
        """A degenerate window size must not corrupt the camera."""
        from swarm_rescue.simulation.gui_map.gui_sr import GuiSR

        gui = GuiSR(the_map=mock_map, headless=True)
        try:
            gui.on_resize(1280, 720)
            viewport_before = gui.camera.viewport
            gui.on_resize(0, 0)
            assert gui.camera.viewport == viewport_before
        finally:
            gui.close()

    @pytest.mark.parametrize("size", [
        (1200, 800),   # even, the common case
        (800, 500),
        (1113, 750),   # odd width: MapMedium02
        (1819, 1350),  # odd width: MapFinal2022_23
        (801, 501),    # odd both ways
    ])
    def test_projection_is_symmetric_for_any_map_size(self, size):
        """The projection must be centered on the origin, even for odd sizes.

        Regression test. The bounds used to be written `-width // 2`, which
        Python evaluates as `(-width) // 2`: for an odd width that floors one
        pixel further left, so the projection spanned an extra pixel on the
        left and its center sat at -0.5. Every map with an odd width was then
        drawn half a pixel left of center -- visible on MapMedium02, the second
        map of the default evaluation plan.

        The check is on the symmetry of the bounds rather than on the rendering,
        because the fault is a half-pixel shift that no pixel comparison would
        reliably catch.
        """
        from swarm_rescue.simulation.gui_map.gui_sr import GuiSR

        gui = GuiSR(the_map=DummyMap(size=size), headless=True)
        try:
            projection = gui.camera.projection
            left, right, bottom, top = (
                projection.left, projection.right,
                projection.bottom, projection.top,
            )
            assert left == -right, f"projection decalee en x: {projection}"
            assert bottom == -top, f"projection decalee en y: {projection}"
        finally:
            gui.close()

    @pytest.mark.parametrize("size", [
        (800, 500),    # MapIntermediate01
        (1200, 500),   # MapIntermediate02
        (1660, 1122),  # MapMedium01
        (1113, 750),   # MapMedium02
        (1819, 1350),  # MapFinal2022_23
        (1700, 1100),  # every MapFinal 2023-2025
    ])
    def test_camera_sits_at_the_world_origin(self, size):
        """The camera must be at (0, 0), not at the center of the window.

        Regression test. `arcade.Camera2D` places itself at
        `(half_width, half_height)` of the viewport that existed when it was
        constructed, which is right for its own convention -- a projection
        running from 0 to the window size, where the world origin sits in the
        bottom-left corner. This view uses a *centered* projection, so that
        default shifted the whole map by half a window: on MapMedium01 (window
        830x561) the map was drawn about (415, 280) px from where it belonged.

        The assertion is on `camera.position` rather than on the rendered
        position of the origin, because that is what actually differs: under
        the test fixture the window is 1x1, so the unfixed camera lands on
        (0.5, 0.5) instead of (415, 280.5), and a rendered check with a
        half-pixel tolerance would pass either way. Checking the invariant also
        keeps the test honest if the fixture's window size changes.
        """
        from swarm_rescue.simulation.gui_map.gui_sr import GuiSR

        gui = GuiSR(the_map=DummyMap(size=size), headless=True)
        try:
            assert gui.camera.position == pytest.approx((0.0, 0.0), abs=1e-6)
        finally:
            gui.close()

    @pytest.mark.parametrize("size", [
        (1660, 1122),  # MapMedium01
        (1700, 1100),
    ])
    def test_world_origin_is_centered_in_a_real_size_window(self, size):
        """Same invariant, checked through what is drawn.

        `test_camera_sits_at_the_world_origin` pins the cause; this one pins the
        visible effect, so the test suite fails if a future change breaks the
        centering in some other way.
        """
        from swarm_rescue.simulation.gui_map.gui_sr import GuiSR

        gui = GuiSR(the_map=DummyMap(size=size), headless=True)
        try:
            # Force the size the window would really have, then let the camera
            # recompute its viewport the way a resize does.
            gui.on_resize(size[0] // 2, size[1] // 2)

            projection = generate_orthographic_matrix(
                gui.camera.projection_data, gui.camera.zoom)
            view = generate_view_matrix(gui.camera.view_data)
            ndc = projection @ view @ Vec4(0.0, 0.0, 0.0, 1.0)

            viewport = gui.camera.viewport
            screen_x = viewport.left + (0.5 * ndc.x + 0.5) * viewport.width
            screen_y = viewport.bottom + (0.5 * ndc.y + 0.5) * viewport.height

            # Centered in the *viewport*, whose origin is `left`/`bottom` and is
            # not zero once the window is letterboxed. Comparing against
            # `viewport.width / 2` instead -- which is what this used to do --
            # only held while the map filled the window from the corner; the
            # status band guarantees it never does again.
            assert screen_x == pytest.approx(
                viewport.left + viewport.width / 2, abs=0.5)
            assert screen_y == pytest.approx(
                viewport.bottom + viewport.height / 2, abs=0.5)
        finally:
            gui.close()


class TestInitialWindowSize:
    """The window opens at most at 1366x768, whatever the map size."""

    @pytest.mark.parametrize("size", [
        (800, 500),
        (1200, 800),
        (1819, 1350),
        (1700, 1100),
        (3840, 2160),
        (3000, 600),
    ])
    def test_default_size_is_capped_and_keeps_aspect_ratio(self, size):
        from swarm_rescue.simulation.gui_map.gui_sr import GuiSR
        from swarm_rescue.simulation.utils.constants import (
            MAX_WINDOW_WIDTH,
            MAX_WINDOW_HEIGHT,
        )

        width, height = GuiSR._scaled_window_size(size, None)
        assert width <= MAX_WINDOW_WIDTH
        assert height <= MAX_WINDOW_HEIGHT
        assert width == pytest.approx(size[0] * min(
            1.0,
            MAX_WINDOW_WIDTH / size[0],
            MAX_WINDOW_HEIGHT / size[1],
        ), abs=1)
        assert height / width == pytest.approx(size[1] / size[0], rel=1e-2)

    def test_a_map_smaller_than_the_cap_keeps_its_size(self):
        from swarm_rescue.simulation.gui_map.gui_sr import GuiSR

        assert GuiSR._scaled_window_size((800, 500), None) == (800, 500)

    def test_explicit_scale_is_still_capped(self):
        from swarm_rescue.simulation.gui_map.gui_sr import GuiSR
        from swarm_rescue.simulation.utils.constants import (
            MAX_WINDOW_WIDTH,
            MAX_WINDOW_HEIGHT,
        )

        width, height = GuiSR._scaled_window_size((1200, 800), 2.0)
        assert width <= MAX_WINDOW_WIDTH
        assert height <= MAX_WINDOW_HEIGHT
        assert GuiSR._scaled_window_size((1200, 800), 0.5) == (600, 400)

    def test_window_is_resizable_after_startup(self, mock_map):
        from swarm_rescue.simulation.gui_map.gui_sr import GuiSR

        gui = GuiSR(the_map=mock_map, headless=True)
        try:
            assert gui._playground.window._resizable
        finally:
            gui.close()


class TestWindowIsNeverForced:
    """Resizing must never take control of the window size back."""

    def test_on_resize_does_not_call_set_size(self, mock_map, monkeypatch):
        """
        This is the core of the letterbox behavior: the window keeps the size
        the user asked for, we never call `set_size` to force the ratio back.
        """
        from swarm_rescue.simulation.gui_map.gui_sr import GuiSR

        gui = GuiSR(the_map=mock_map, headless=True)
        try:
            calls = []
            monkeypatch.setattr(
                gui._playground.window, "set_size",
                lambda *a: calls.append(a),
            )
            for width, height in [(1920, 1080), (1000, 1000), (640, 900)]:
                gui.on_resize(width, height)
            assert calls == []
        finally:
            gui.close()

    def test_view_size_is_unchanged_by_resize(self, mock_map):
        """
        The view (and its framebuffer) keeps the map size: this is what keeps
        the recorded video resolution stable.
        """
        from swarm_rescue.simulation.gui_map.gui_sr import GuiSR

        gui = GuiSR(the_map=mock_map, headless=True)
        try:
            size_before = gui._size
            for width, height in [(1920, 1080), (1000, 1000), (640, 900)]:
                gui.on_resize(width, height)
                assert gui._size == size_before
        finally:
            gui.close()

    def test_framebuffer_size_is_unchanged_by_resize(self, mock_map):
        """The offscreen framebuffer used for recording keeps its size."""
        from swarm_rescue.simulation.gui_map.gui_sr import GuiSR

        gui = GuiSR(the_map=mock_map, headless=True)
        try:
            fbo_size_before = gui._fbo.size
            for width, height in [(1920, 1080), (1000, 1000), (640, 900)]:
                gui.on_resize(width, height)
                assert gui._fbo.size == fbo_size_before
        finally:
            gui.close()

    def test_resize_allowed_while_recording(self, mock_map, tmp_path):
        """
        Recording is no longer blocked on resize: the framebuffer no longer
        changes size, so there is no FFmpeg size mismatch to avoid.
        """
        from swarm_rescue.simulation.gui_map.gui_sr import GuiSR

        video_file = tmp_path / "test_recording.avi"
        gui = GuiSR(
            the_map=mock_map,
            filename_video_capture=str(video_file),
            headless=True,
        )
        try:
            size_before = gui._size
            fbo_size_before = gui._fbo.size
            gui.on_resize(1000, 1000)
            assert gui._size == size_before
            assert gui._fbo.size == fbo_size_before
        finally:
            gui.close()


class TestLetterboxColor:
    """The area outside the map shows the letterbox color."""

    def test_letterbox_color_is_gray(self):
        """The letterbox color should be a neutral gray, not pure black."""
        red, green, blue = WINDOW_LETTERBOX_COLOR[:3]
        assert red == green == blue
        assert 0 < red < 255

    def test_map_area_keeps_playground_background(self, mock_map, monkeypatch):
        """
        The letterbox must not swallow the playground background color.

        on_draw() clears the whole window with the letterbox color, then
        re-clears only the map area (the viewport) with the playground
        background, so the map keeps its own light background.
        """
        from swarm_rescue.simulation.gui_map.gui_sr import GuiSR

        gui = GuiSR(the_map=mock_map, headless=True)
        try:
            width, height = 1600, 800
            gui.on_resize(width, height)

            clears = []
            monkeypatch.setattr(
                gui, "clear", lambda **kwargs: clears.append(kwargs))
            monkeypatch.setattr(gui, "draw", lambda: None)
            gui.on_draw()

            # 1) the whole window is cleared with the letterbox color
            assert len(clears) == 2
            assert clears[0]["color"] == WINDOW_LETTERBOX_COLOR
            assert clears[0].get("viewport") is None

            # 2) the map area is restored to the playground background
            assert clears[1]["color"] == gui._background
            assert gui._background != WINDOW_LETTERBOX_COLOR

            # and the map area is the viewport, which fits in the window
            viewport = clears[1]["viewport"]
            assert viewport is not None
            x, y, vp_width, vp_height = viewport
            assert 0 <= x and 0 <= y
            assert x + vp_width <= width
            assert y + vp_height <= height
        finally:
            gui.close()


class TestResizeDoesNotAffectSimulation:
    """Resizing is purely visual: the simulation state is untouched."""

    def test_resize_does_not_change_simulation_state(self):
        """
        Strictest check: resizing must leave the simulation state bit for bit
        identical. No step is performed between the two measurements, so any
        difference could only come from the resize itself.
        """
        from swarm_rescue.simulation.gui_map.gui_sr import GuiSR
        from swarm_rescue.maps.map_intermediate_01 import MapIntermediate01
        from swarm_rescue.simulation.drone.drone_motionless import DroneMotionless

        my_map = MapIntermediate01(drone_type=DroneMotionless)
        gui = GuiSR(the_map=my_map, size=(1920, 1080), headless=True)
        try:
            for _ in range(10):
                gui._playground.step(all_commands={}, all_messages={})

            # 'true_position' is used because the GPS sensor adds noise on each
            # reading, which would make the comparison unreliable.
            initial_positions = [d.true_position() for d in my_map.drones]
            initial_lidar = np.array(my_map.drones[0].lidar().get_sensor_values())

            for width, height in [(1280, 720), (800, 600), (1600, 1200), (400, 400)]:
                gui.on_resize(width, height)

            final_positions = [d.true_position() for d in my_map.drones]
            final_lidar = np.array(my_map.drones[0].lidar().get_sensor_values())

            for before, after in zip(initial_positions, final_positions):
                assert np.array_equal(after, before)
            assert np.array_equal(final_lidar, initial_lidar)
        finally:
            gui.close()

    def test_simulation_keeps_running_after_resize(self):
        """
        After a resize the simulation must still run normally: stepping keeps
        working, and a motionless drone drifts no more than a run without any
        resize (the residual drift comes from the physics engine integration).
        """
        from swarm_rescue.simulation.gui_map.gui_sr import GuiSR
        from swarm_rescue.maps.map_intermediate_01 import MapIntermediate01
        from swarm_rescue.simulation.drone.drone_motionless import DroneMotionless

        def _drift_after_steps(resize_each_step):
            my_map = MapIntermediate01(drone_type=DroneMotionless)
            gui = GuiSR(the_map=my_map, size=(1920, 1080), headless=True)
            try:
                for _ in range(10):
                    gui._playground.step(all_commands={}, all_messages={})
                start = my_map.drones[0].true_position()
                for i in range(15):
                    if resize_each_step:
                        gui.on_resize(1280 + i, 720 + i)
                    gui._playground.step(all_commands={}, all_messages={})
                return float(np.linalg.norm(my_map.drones[0].true_position() - start))
            finally:
                gui.close()

        drift_with_resize = _drift_after_steps(True)
        drift_without_resize = _drift_after_steps(False)

        # Resizing must not add any drift of its own.
        assert drift_with_resize == pytest.approx(drift_without_resize, abs=1.0)


class TestOffscreenRenderingIsIndependentFromWindow:
    """The offscreen views (used for ray sensors) must not depend on the window.

    Arcade's ``Window._on_resize()`` resets the *global* viewport to the new
    window size. Any offscreen rendering that does not set its own viewport and
    projection is then drawn with that leftover state, which stretches the image
    and makes ray sensors report hits on the wrong objects.
    """

    @staticmethod
    def _simulate_real_resize(gui, width, height):
        """Reproduce what a real user window resize does to the GL state."""
        # This is literally arcade's Window._on_resize() behavior.
        gui._playground.ctx.viewport = (0, 0, width, height)
        # ... and our own letterbox handling.
        gui.on_resize(width, height)

    def test_id_view_image_is_independent_from_window_size(self):
        """The uid image rendered offscreen must not change when resized."""
        from swarm_rescue.simulation.gui_map.gui_sr import GuiSR
        from swarm_rescue.maps.map_intermediate_01 import MapIntermediate01
        from swarm_rescue.simulation.drone.drone_motionless import DroneMotionless

        my_map = MapIntermediate01(drone_type=DroneMotionless)
        gui = GuiSR(the_map=my_map, size=(1920, 1080), headless=True)
        try:
            gui._playground.step(all_commands={}, all_messages={})
            uid_view = gui._playground.ray_compute.uid_provider

            def render():
                uid_view.render_uids()
                return uid_view.read_uid_image().copy()

            reference = render()
            # Sanity check: the reference is not a blank image, otherwise the
            # comparison below would be meaningless.
            assert (reference.sum(axis=2) > 0).sum() > 0

            for width, height in [(1280, 720), (800, 1200), (1000, 1000), (640, 480)]:
                self._simulate_real_resize(gui, width, height)
                assert np.array_equal(render(), reference), (
                    f"the uid image changed after a resize to {width}x{height}"
                )
        finally:
            gui.close()

    def test_lidar_hitpoints_are_independent_from_window_size(self):
        """Ray sensors must keep reporting the very same hits after a resize."""
        from swarm_rescue.simulation.gui_map.gui_sr import GuiSR
        from swarm_rescue.maps.map_intermediate_01 import MapIntermediate01
        from swarm_rescue.simulation.drone.drone_motionless import DroneMotionless

        my_map = MapIntermediate01(drone_type=DroneMotionless)
        gui = GuiSR(the_map=my_map, size=(1920, 1080), headless=True)
        try:
            gui._playground.step(all_commands={}, all_messages={})
            ray_compute = gui._playground.ray_compute

            def hitpoints():
                ray_compute.update_sensors()
                return [
                    np.array(sensor._hitpoints, copy=True)
                    for sensor in ray_compute._sensors
                ]

            reference = hitpoints()
            assert reference, "no ray sensor was registered"
            # Sanity check: the drone really sees something, otherwise the
            # comparison below would be meaningless.
            assert any(np.isfinite(h).any() for h in reference)

            for width, height in [(1280, 720), (800, 1200), (1000, 1000), (640, 480)]:
                self._simulate_real_resize(gui, width, height)
                current = hitpoints()
                for index, (before, after) in enumerate(zip(reference, current)):
                    assert np.array_equal(before, after, equal_nan=True), (
                        f"sensor {index} changed its hitpoints after a resize "
                        f"to {width}x{height}"
                    )
        finally:
            gui.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
