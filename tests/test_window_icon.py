"""The window must carry the drone icon, and failing to must not be fatal.

Two separate things are checked here, and the second is the one that matters
most.

The icon itself: `GuiSR` has to put it on the window, with the sizes it declares,
because the sizes are pre-rendered files. Getting that wrong is quiet -- the
window opens either way, it just shows a default icon or none.

The failure path: `apply_window_icon` returns a bool rather than raising. An
icon is decoration; a missing file or a window implementation that refuses
`set_icon` must not take a round down with it. A participant whose window never
opens has lost everything, so the degraded paths are pinned as *returning
False*, not as not raising.
"""

import pathlib
import sys

import pytest

# Insert the 'src' directory into sys.path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from swarm_rescue.simulation.drone.drone_abstract import DroneAbstract
from swarm_rescue.simulation.gui_map import window_icon as window_icon_module
from swarm_rescue.simulation.gui_map.closed_playground import ClosedPlayground
from swarm_rescue.simulation.gui_map.gui_sr import GuiSR
from swarm_rescue.simulation.gui_map.map_abstract import MapAbstract
from swarm_rescue.simulation.gui_map.window_icon import (
    ICON_SIZES,
    apply_window_icon,
    available_icon_sizes,
)


class IconDrone(DroneAbstract):
    def define_message_for_all(self):
        return None

    def control(self):
        return {"forward": 0.0, "lateral": 0.0, "rotation": 0.0, "grasper": 0}


class IconMap(MapAbstract):
    """
    The smallest map `GuiSR` accepts.

    Defined here rather than imported from another test module: `tests/` is not
    on `sys.path`, so a cross-test import only resolves by accident of the
    runner's rootdir, and it would break the moment that changes.
    """

    def __init__(self, size=(400, 300)):
        super().__init__(drone_type=IconDrone)
        self._size_area = size
        self._playground = ClosedPlayground(size=self._size_area)
        self._number_drones = 0
        self._drones = []
        self._number_wounded_persons = 0


class RecordingWindow:
    """A window that records what it was handed, and can be told to refuse."""

    def __init__(self, refuse=False):
        self.refuse = refuse
        self.calls = []
        self.sizes = []

    def set_icon(self, *images):
        if self.refuse:
            raise RuntimeError("this window implementation has no icons")
        self.calls.append(images)
        self.sizes = [image.width for image in images]


class TestTheIconFiles:
    """The pre-rendered files, which the whole module is built around."""

    def test_every_declared_size_is_present(self):
        """
        A size is declared, so its file has to exist.

        `available_icon_sizes()` filters on disk precisely so a missing file
        degrades rather than raises -- which also means a typo in
        `ICON_SIZES` would silently ship no icon at all. This is what catches it.
        """
        assert available_icon_sizes() == list(ICON_SIZES)

    @pytest.mark.parametrize("size", ICON_SIZES)
    def test_each_file_is_the_size_it_claims(self, size):
        """Named for its edge length, so it has to be that size.

        Handing pyglet a 128x128 file under the name of the 16x16 lets it pick
        the "wrong" size and scale a scaled image, which is what the four
        separate files exist to avoid.
        """
        from PIL import Image

        path = window_icon_module._icon_path(size)
        with Image.open(path) as image:
            assert image.size == (size, size)

    def test_the_icons_keep_their_transparency(self):
        """
        The drone is drawn on transparency, and an opaque box would show.

        Windows composes the icon against the title bar; a white or black
        rectangle around the drone is the artifact this would produce.
        """
        from PIL import Image

        with Image.open(window_icon_module._icon_path(32)) as image:
            assert image.mode == "RGBA"
            alpha = image.getchannel("A")
            assert alpha.getextrema()[0] == 0, (
                "the icon has no fully transparent pixel, so it is drawn on an "
                "opaque box"
            )

    def test_the_icons_are_small(self):
        """
        They are pre-rendered to be small; that is the reason they exist.

        The source artwork is 1024x1024 and 138 kB. If these files ever grow
        toward it, the resampling step that produced them was skipped.
        """
        import os

        for size in ICON_SIZES:
            path = window_icon_module._icon_path(size)
            assert os.path.getsize(path) < 40 * 1024, (
                f"window_icon_{size}.png is larger than expected for an icon"
            )


class TestApplyWindowIcon:
    """What actually reaches the window."""

    def test_it_hands_over_every_size(self):
        """All four, in order, so pyglet can pick the one the WM asks for."""
        window = RecordingWindow()

        assert apply_window_icon(window) is True
        assert window.sizes == list(ICON_SIZES)

    def test_it_is_called_once_by_the_view(self):
        """
        `GuiSR.__init__` is what sets it up.

        Not called through `set_caption()`: that is a public method a caller may
        invoke repeatedly, and re-decoding four PNGs on every caption change
        would be a surprising cost.
        """
        import swarm_rescue.simulation.gui_map.gui_sr as gui_sr_module

        seen = []
        original = gui_sr_module.apply_window_icon

        def spy(window):
            result = original(window)
            seen.append(result)
            return result

        gui_sr_module.apply_window_icon = spy
        try:
            view = GuiSR(the_map=IconMap(), headless=True)
            try:
                assert len(seen) == 1
                assert seen[0] is True
            finally:
                view.close()
        finally:
            gui_sr_module.apply_window_icon = original

    def test_a_window_that_refuses_is_not_fatal(self):
        """
        Returns False instead of raising.

        Some headless and EGL window implementations reject `set_icon`. The
        simulation has to run anyway: the icon is decoration, and a participant
        whose window never opens has lost the whole round.
        """
        window = RecordingWindow(refuse=True)

        assert apply_window_icon(window) is False

    def test_a_window_with_no_icon_method_is_not_fatal(self):
        """A stub window (as used in some tests) simply has nothing to set."""
        assert apply_window_icon(object()) is False

    def test_a_missing_file_is_not_fatal(self, monkeypatch):
        """
        No icon file on disk must not raise.

        Pinned by emptying the list rather than by moving files around, so the
        test cannot leave the checkout in a broken state if it fails midway.
        """
        monkeypatch.setattr(window_icon_module, "available_icon_sizes",
                            lambda: [])
        assert apply_window_icon(RecordingWindow()) is False

    def test_one_unreadable_file_does_not_discard_the_others(self, monkeypatch):
        """
        A single bad file costs that size, not the whole icon.

        Skipping is deliberate: giving up would leave the window with no icon at
        all because one of four files is corrupt.
        """
        real_load = window_icon_module.pyglet.image.load
        calls = []

        def flaky_load(path):
            calls.append(path)
            if "window_icon_32.png" in path:
                raise OSError("corrupt file")
            return real_load(path)

        monkeypatch.setattr(window_icon_module.pyglet.image, "load", flaky_load)
        window = RecordingWindow()

        assert apply_window_icon(window) is True
        assert window.sizes == [s for s in ICON_SIZES if s != 32]
        assert len(calls) == len(ICON_SIZES)

    def test_every_file_unreadable_is_not_fatal(self, monkeypatch):
        """Nothing loadable is still just a missing icon, not a crash."""
        def always_fail(path):
            raise OSError("corrupt file")

        monkeypatch.setattr(window_icon_module.pyglet.image, "load", always_fail)
        assert apply_window_icon(RecordingWindow()) is False


class TestTheIconDoesNotAffectTheSimulation:
    """The icon is window furniture, like the status band."""

    def test_the_view_still_draws_with_an_icon(self):
        """
        `set_icon` sits between the window setup and `show_view()`; it must not
        disturb either.
        """
        view = GuiSR(the_map=IconMap(), headless=True)
        try:
            view.on_draw()
            view.on_resize(800, 600)
            view.on_draw()
        finally:
            view.close()

    def test_the_caption_still_works_afterwards(self):
        """
        `set_caption` is public API and is often called right after construction.

        It must keep working with the icon in place.
        """
        view = GuiSR(the_map=IconMap(), headless=True)
        try:
            view.set_caption("a caption")
        finally:
            view.close()
