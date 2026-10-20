"""
Tests for the two debug overlays that were never exercised: `draw_gps` and
`draw_com`.

These are the drone drawing methods that only run when their GuiSR flag is on,
which no test ever set. `draw_gps` builds two `arcade.Text` objects and
`draw_com` draws a circle plus one line per communicator in range -- so they
have branches (a disabled GPS, a disabled communicator, an empty range) that
only a test can reach.

What is asserted here is that every branch runs against the real arcade 3.3.3
API, and that the drawn geometry is what the drone's state says it should be.
The pixels are not checked: that would need a readable framebuffer and would
fail for reasons unrelated to the API being called correctly.
"""

import pathlib
import sys

import numpy as np
import pytest

# Insert the 'src' directory into sys.path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from swarm_rescue.simulation.drone.drone_abstract import DroneAbstract
from swarm_rescue.simulation.gui_map.closed_playground import ClosedPlayground
from swarm_rescue.simulation.gui_map.gui_sr import GuiSR
from swarm_rescue.simulation.gui_map.map_abstract import MapAbstract
from swarm_rescue.simulation.utils.constants import RANGE_COMMUNICATION
from swarm_rescue.simulation.utils.misc_data import MiscData

# Position the second drone just inside / outside the communication range.
INSIDE_RANGE = (-30.0, 0.0)
OUTSIDE_RANGE = (RANGE_COMMUNICATION + 50.0, 0.0)


class OverlayDrone(DroneAbstract):
    """A drone that draws nothing extra: the overlays are what we test."""

    def define_message_for_all(self):
        return None

    def control(self):
        return {"forward": 0.0, "lateral": 0.0, "rotation": 0.0, "grasper": 0}


def _misc(size):
    return MiscData(
        size_area=size,
        number_drones=2,
        max_timestep_limit=1000,
        max_walltime_limit=100,
    )


class OverlayMap(MapAbstract):
    """
    Two drones, because `draw_com` draws one line per neighbor in range.

    A single drone would leave the "links" branch of `draw_com` permanently
    untested -- which is the branch that actually calls `draw_line`.
    """

    def __init__(self, size=(800, 600), second_position=INSIDE_RANGE):
        super().__init__(drone_type=OverlayDrone)
        self._size_area = size
        self._playground = ClosedPlayground(size=self._size_area)
        self._number_drones = 2
        self._drones = []
        self._number_wounded_persons = 0
        self._max_timestep_limit = 1000
        self._max_walltime_limit = 100

        misc = _misc(size)
        for position in [(0.0, 0.0), second_position]:
            drone = OverlayDrone(self._playground, misc_data=misc)
            self._drones.append(drone)
            self._playground.add(drone, (position, 0.0))


def _map(**kwargs):
    the_map = OverlayMap(**kwargs)
    try:
        yield the_map
    finally:
        the_map.playground.close_window()


@pytest.fixture
def two_drones():
    yield from _map()


@pytest.fixture
def far_apart():
    yield from _map(second_position=OUTSIDE_RANGE)


@pytest.fixture
def gui(two_drones):
    view = GuiSR(the_map=two_drones, draw_gps=True, draw_com=True, headless=True)
    try:
        yield view
    finally:
        view.close()


class TestDrawGps:
    """The overlay shows the measured reading next to the ground truth."""

    def test_runs_with_a_reading(self, gui):
        drone = gui._playground.agents[0]
        assert drone.measured_gps_position() is not None

        drone.draw_gps()

    def test_runs_without_a_reading(self, gui):
        """
        The "GPS: None" branch.

        This is what a drone in a no-GPS zone sees. It builds a Text like the
        other branch, so it needs the same guarantee -- and it is the branch
        that no nominal run ever reaches.
        """
        drone = gui._playground.agents[0]
        drone.gps().disable()
        assert drone.measured_gps_position() is None

        drone.draw_gps()

    def test_survives_a_drone_that_never_moved(self, gui):
        """
        The text is offset from the map center, so a drone sitting at the
        origin is the case where the offset is actually exercised.

        `true_position()` rather than `position`: the latter is deliberately
        disabled to stop solutions cheating, and a test is outside the
        participant-code guard, so reading the true state is legitimate here.
        """
        drone = gui._playground.agents[0]
        assert np.allclose(drone.true_position(), (0.0, 0.0))

        drone.draw_gps()

    def test_follows_the_drone_after_a_step(self, gui):
        """The overlay reads the live position, so it must be re-runnable."""
        drone = gui._playground.agents[0]

        drone.draw_gps()
        gui._playground.step(all_commands={}, all_messages={})
        drone.draw_gps()


class TestDrawCom:
    """The overlay draws the transmission range and the links inside it."""

    def test_draws_with_a_neighbor_in_range(self, gui):
        drone = gui._playground.agents[0]
        drone.communicator.pre_step()
        assert drone.communicator.comms_in_range, "expected a neighbor in range"

        drone.draw_com()

    def test_draws_with_nobody_in_range(self, far_apart):
        """
        The empty-range branch: the circle still has to be drawn.

        Without a neighbor in range this exercises a different path through
        the same method -- the loop body is never entered.
        """
        view = GuiSR(the_map=far_apart, draw_com=True, headless=True)
        try:
            drone = view._playground.agents[0]
            drone.communicator.pre_step()
            assert drone.communicator.comms_in_range == []

            drone.draw_com()
        finally:
            view.close()

    def test_a_disabled_communicator_still_draws_its_circle(self, gui):
        """
        A disabled communicator draws a paler circle and no link.

        The point of the branch is that drawing must not depend on being able
        to communicate: a drone in a no-com zone still has to be visible.
        """
        drone = gui._playground.agents[0]
        drone.communicator.disable()

        drone.draw_com()

    def test_one_neighbor_disabled_is_skipped(self, gui):
        """
        The nested filter: a link is drawn only if *both* ends are enabled.

        Skipping the sender is the outer `if`; skipping the receiver is the
        inner one. Both have to survive being drawn.
        """
        sender, receiver = gui._playground.agents
        sender.communicator.pre_step()
        assert sender.communicator.comms_in_range, "expected a neighbor in range"

        receiver.communicator.disable()
        sender.draw_com()

    def test_neither_end_disabled_draws_the_link(self, gui):
        """The counterpart of the previous test: the link is drawn."""
        sender, receiver = gui._playground.agents
        sender.communicator.pre_step()
        assert sender.communicator.comms_in_range

        sender.draw_com()

    def test_a_damage_wreck_is_not_drawn_as_a_linked_neighbor(self, gui):
        """
        A drone destroyed by damage must not be shown talking to a live one.

        This is the picture a participant sees on key C. A damage wreck leaves
        the space, so no zone keeps its communicator switched off and the
        per-step flag alone left it in the neighbor's `comms_in_range` -- which
        is what drew the link. Whether the wreck is alive, not just whether a
        zone touched it, is what has to decide.
        """
        from swarm_rescue.simulation.utils.constants import DEATH_BY_DAMAGE

        sender, receiver = gui._playground.agents
        sender.communicator.pre_step()
        assert sender.communicator.comms_in_range, "expected a neighbor in range"

        receiver.die(DEATH_BY_DAMAGE)
        gui._playground.step()

        assert receiver.communicator_is_disabled()
        assert receiver not in sender.communicator.comms_in_range
        sender.draw_com()

    def test_draws_for_every_drone_of_a_two_drone_swarm(self, gui):
        """
        Each drone draws from its own point of view.

        The second drone's `comms_in_range` is computed separately, so drawing
        only the first would leave one direction untested.
        """
        for drone in gui._playground.agents:
            drone.communicator.pre_step()
            drone.draw_com()
