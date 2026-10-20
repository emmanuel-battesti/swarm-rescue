"""
A frame of the simulation must actually be drawable.

`DroneAbstract.draw_identifier()` passed `start_x`/`start_y` to `arcade.Text`.
Those are the arcade 2.x parameter names; arcade 3.x renamed them to `x`/`y`,
so every call raised `TypeError`. It was only ever seen by someone launching an
example, because the suite had a double blind spot:

- no test called any of the drone's `draw_*` methods;
- the one test that did call `GuiSR.on_draw()` neutralized the drawing first
  (`monkeypatch.setattr(gui, "draw", lambda: None)`), because it was checking
  the `clear()` calls and not the rendering.

So "296 tests green" and "`random_drones.py` crashes on startup" were both
true at the same time. These tests close the gap: they draw a real frame, with
every visualization enabled, and let the exceptions through.

A note on what this does *not* check: the pixels. Asserting on the rendered
image would need a readable framebuffer and a known font, and would fail for
reasons unrelated to the API being called correctly. What is checked here is
that every drawing path runs end to end against the real arcade 3.3.3 API.
"""

import pathlib
import sys

import pytest

# Insert the 'src' directory into sys.path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from swarm_rescue.simulation.drone.drone_abstract import DroneAbstract
from swarm_rescue.simulation.gui_map.closed_playground import ClosedPlayground
from swarm_rescue.simulation.gui_map.gui_sr import GuiSR
from swarm_rescue.simulation.gui_map.map_abstract import MapAbstract
from swarm_rescue.simulation.utils.misc_data import MiscData


class DrawableDrone(DroneAbstract):
    """
    A drone that does nothing but is present to be drawn.

    `draw_top_layer` calls `draw_identifier` on purpose. It is an empty hook in
    the base class, so the identifier is only ever drawn by a drone that asks
    for it -- which is exactly what `examples/random_drones.py` does, and why
    a bare drone would not have reproduced the crash.
    """

    def define_message_for_all(self):
        return None

    def control(self):
        return {"forward": 0.0, "lateral": 0.0, "rotation": 0.0, "grasper": 0}

    def draw_top_layer(self):
        self.draw_identifier()


class DrawableMap(MapAbstract):
    """The smallest map `GuiSR` accepts: one drone, no wounded, no zones."""

    def __init__(self, size=(800, 600)):
        super().__init__(drone_type=DrawableDrone)
        self._size_area = size
        self._playground = ClosedPlayground(size=self._size_area)
        self._number_drones = 1
        self._drones = []
        self._number_wounded_persons = 0
        self._max_timestep_limit = 1000
        self._max_walltime_limit = 100

        # A drone needs `MiscData.size_area` to know where the map bounds are,
        # which is what `_half_size_array` is derived from. Every `draw_*`
        # method offsets its text by that array, so a drone built without it
        # would fail here for a reason that has nothing to do with the drawing.
        misc_data = MiscData(
            size_area=self._size_area,
            number_drones=1,
            max_timestep_limit=1000,
            max_walltime_limit=100,
        )
        drone = DrawableDrone(self._playground, misc_data=misc_data)
        self._drones.append(drone)
        self._playground.add(drone, ((0.0, 0.0), 0.0))


@pytest.fixture
def drawable_map():
    the_map = DrawableMap()
    try:
        yield the_map
    finally:
        the_map.playground.close_window()


@pytest.fixture
def gui(drawable_map):
    """
    A GuiSR with **every** visualization on.

    The flags matter: `draw_gps()` and `draw_com()` are skipped entirely when
    they are off, so a default GuiSR never reaches them. A regression in those
    two would hide just as well as the identifier one did.
    """
    view = GuiSR(
        the_map=drawable_map,
        draw_gps=True,
        draw_com=True,
        draw_lidar_rays=True,
        headless=True,
    )
    try:
        yield view
    finally:
        view.close()


class TestAFrameCanBeDrawn:
    def test_one_frame_runs_without_raising(self, gui):
        """
        The regression test.

        Before the fix this raised, from `draw_identifier()`:
        `TypeError: Text.__init__() missing 2 required positional arguments`.
        """
        gui.on_draw()

    def test_several_consecutive_frames_run(self, gui):
        """
        Not one frame.

        The drone moves between frames, so a Text built from a stale position,
        or a sprite list mutated while it is iterated, only shows up on the
        second or third call.
        """
        for _ in range(5):
            gui._playground.step(all_commands={}, all_messages={})
            gui.on_draw()

    def test_the_drone_layer_draws_on_its_own(self, gui):
        """
        `draw_top_layer` is the last thing `GuiSR.draw()` does per drone.

        Isolate it so a failure points at the drone rather than at the view.
        """
        drone = gui._playground.agents[0]
        drone.draw_top_layer()


class TestEveryVisualizationRuns:
    """
    One test per drawing entry point.

    Grouped rather than lumped into the frame test above: when one of them
    breaks, the name of the failing test is the diagnosis.
    """

    def test_draw_identifier(self, gui):
        """Was the actual bug: `arcade.Text(start_x=..., start_y=...)`."""
        gui._playground.agents[0].draw_identifier()

    def test_draw_gps(self, gui):
        """Two more `arcade.Text` calls, built positionally."""
        gui._playground.agents[0].draw_gps()

    def test_draw_com(self, gui):
        """A circle outline plus a line per communicator in range."""
        gui._playground.agents[0].draw_com()

    def test_draw_bottom_layer(self, gui):
        gui._playground.agents[0].draw_bottom_layer()

    def test_draw_top_layer(self, gui):
        gui._playground.agents[0].draw_top_layer()


class TestDrawGpsEdgeCase:
    def test_draw_gps_survives_a_missing_gps_reading(self, gui):
        """
        `draw_gps` prints "GPS: None" when the reading is unavailable.

        That branch builds a Text too, so it needs the same guarantee as the
        normal one -- and it is the branch that never runs in a nominal test.
        A GPS killed by a special zone is the real way to get there.
        """
        drone = gui._playground.agents[0]
        drone.gps().disable()
        assert drone.measured_gps_position() is None

        drone.draw_gps()

    def test_draw_identifier_follows_the_drone(self, gui):
        """
        The text position comes from the true position.

        A drone that has been moved must not leave its label behind, so the
        call has to be re-runnable after a step rather than once at build time.
        """
        drone = gui._playground.agents[0]

        drone.draw_identifier()
        drone._playground.step(all_commands={}, all_messages={})
        drone.draw_identifier()
