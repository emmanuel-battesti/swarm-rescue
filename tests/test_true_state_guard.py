"""
Tests for the ground-truth guard on the drones' controllers.

The participants write `control()` and `define_message_for_all()`. Those must
not read the exact state of the drone (true_position, true_angle,
true_velocity), otherwise the noise of the simulated GPS and compass would be
pointless and every participant would cheat the same way.

The guard is active only while participant code runs, so the rest of the
simulator (drawing, explored map, tests) keeps working with the true state.
"""

import pathlib
import re
import sys

import pytest

# Insert the 'src' and 'examples' directories into sys.path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "examples"))

from swarm_rescue.simulation.drone.drone_abstract import (
    DroneAbstract,
    TrueStateAccessError,
)
from swarm_rescue.simulation.gui_map.closed_playground import ClosedPlayground
from swarm_rescue.simulation.utils.true_state_guard import (
    ALLOW_TRUE_STATE_ENV_VAR,
    true_state_is_allowed,
)

EXAMPLES_DIR = pathlib.Path(__file__).resolve().parent.parent / "examples"


class CheatingDrone(DroneAbstract):
    """A drone that cheats: it reads the ground truth to build its command."""

    def define_message_for_all(self):
        return self.true_position()

    def control(self):
        self.true_position()
        self.true_angle()
        self.true_velocity()
        return {"forward": 0.0, "lateral": 0.0, "rotation": 0.0, "grasper": 0}


class HonestDrone(DroneAbstract):
    """A drone that plays by the rules, using the measured sensors."""

    def define_message_for_all(self):
        return (self.measured_gps_position(), self.measured_compass_angle())

    def control(self):
        self.measured_gps_position()
        self.measured_compass_angle()
        return {"forward": 0.0, "lateral": 0.0, "rotation": 0.0, "grasper": 0}


@pytest.fixture
def playground():
    pg = ClosedPlayground(size=(1200, 800))
    try:
        yield pg
    finally:
        pg.close_window()


def _add(pg, drone, position=(0.0, 0.0)):
    pg.add(drone, initial_coordinates=(position, 0.0))
    return drone


class TestTrueStateIsBlockedInsideControllers:
    def test_true_position_raises_inside_control(self, playground):
        drone = _add(playground, CheatingDrone(playground, angle=0.0))
        with pytest.raises(TrueStateAccessError):
            with drone.participant_code():
                drone.true_position()

    def test_true_angle_raises_inside_control(self, playground):
        drone = _add(playground, CheatingDrone(playground, angle=0.0))
        with pytest.raises(TrueStateAccessError):
            with drone.participant_code():
                drone.true_angle()

    def test_true_velocity_raises_inside_control(self, playground):
        drone = _add(playground, CheatingDrone(playground, angle=0.0))
        with pytest.raises(TrueStateAccessError):
            with drone.participant_code():
                drone.true_velocity()

    def test_true_angular_velocity_raises_inside_control(self, playground):
        """Every ground-truth accessor is guarded, not just the three oldest."""
        drone = _add(playground, CheatingDrone(playground, angle=0.0))
        with pytest.raises(TrueStateAccessError):
            with drone.participant_code():
                drone.true_angular_velocity()

    def test_error_message_names_the_replacement(self, playground):
        """The message must tell the participant what to use instead."""
        drone = _add(playground, CheatingDrone(playground, angle=0.0))
        with pytest.raises(TrueStateAccessError) as excinfo:
            with drone.participant_code():
                drone.true_position()
        assert "measured_gps_position" in str(excinfo.value)

    def test_honest_drone_is_unaffected(self, playground):
        """A drone using the measured sensors must run normally."""
        drone = _add(playground, HonestDrone(playground, angle=0.0))
        with drone.participant_code():
            assert drone.control()["forward"] == 0.0


class WoundedPeeker(DroneAbstract):
    """A drone that cheats through the wounded person it grasps."""

    def define_message_for_all(self):
        return None

    def control(self):
        for person in self.grasped_wounded_persons():
            person.true_position()
            person.true_angle()
        return {"forward": 0.0, "lateral": 0.0, "rotation": 0.0, "grasper": 0}


class TestWoundedPersonsAreProtectedToo:
    """A grasped wounded person must be as protected as the drone itself."""

    @pytest.fixture
    def wounded(self, playground):
        from swarm_rescue.simulation.elements.rescue_center import RescueCenter
        from swarm_rescue.simulation.elements.wounded_person import WoundedPerson

        center = RescueCenter(size=(100, 100))
        playground.add(center, initial_coordinates=((0.0, 0.0), 0.0))
        person = WoundedPerson(center)
        playground.add(person, initial_coordinates=((200.0, 0.0), 0.0))
        return person

    def test_wounded_true_position_raises_inside_control(self, playground, wounded):
        drone = _add(playground, HonestDrone(playground, angle=0.0))
        with pytest.raises(TrueStateAccessError):
            with drone.participant_code():
                wounded.true_position()

    def test_wounded_true_angle_raises_inside_control(self, playground, wounded):
        drone = _add(playground, HonestDrone(playground, angle=0.0))
        with pytest.raises(TrueStateAccessError):
            with drone.participant_code():
                wounded.true_angle()

    def test_wounded_true_state_works_outside_control(self, playground, wounded):
        """The simulator itself must keep using it freely."""
        assert wounded.true_position() is not None
        assert isinstance(wounded.true_angle(), float)

    def test_env_var_also_unlocks_the_wounded_person(
            self, playground, wounded, monkeypatch):
        """The guard is global, so the override has to be global too.

        A controller reaches the wounded person it carries, and that person's
        `true_position` is guarded by the same function. Lifting the guard for
        the drone but not for its cargo would be a confusing half-measure.
        """
        drone = _add(playground, HonestDrone(playground, angle=0.0))
        monkeypatch.setenv(ALLOW_TRUE_STATE_ENV_VAR, "1")
        with drone.participant_code():
            assert wounded.true_position() is not None

    def test_wounded_internal_updates_are_not_blocked(self, playground, wounded):
        """pre_step() reads the true state to move the person: not blocked."""
        wounded.pre_step()
        assert wounded.pose is not None

    def test_a_cheating_controller_is_stopped_through_the_wounded(self, playground, wounded):
        """The realistic cheat: read the grasped person's exact position.

        The drone really grasps the person first, otherwise the controller
        would never reach it and the test would pass for the wrong reason.
        """
        drone = _add(playground, WoundedPeeker(playground, angle=0.0))
        # Real grasp: the grasper only accepts one once the command is applied.
        drone.receive_commands(
            {"forward": 0.0, "lateral": 0.0, "rotation": 0.0, "grasper": 1}
        )
        drone.apply_commands()
        drone.grasper.grasps(wounded)
        assert drone.grasped_wounded_persons(), "the grasp should have succeeded"

        with pytest.raises(TrueStateAccessError):
            with drone.participant_code():
                drone.control()


class TestTrueStateStaysAvailableElsewhere:
    def test_true_position_works_outside_the_controller(self, playground):
        """Debugging, logging and the evaluation must keep working."""
        drone = _add(playground, HonestDrone(playground, angle=0.0))
        assert drone.true_position() is not None
        assert isinstance(drone.true_angle(), float)
        assert drone.true_velocity() is not None

    def test_guard_is_restored_after_the_block(self, playground):
        """Leaving the block must give the true state back."""
        drone = _add(playground, HonestDrone(playground, angle=0.0))
        with drone.participant_code():
            pass
        assert drone.true_position() is not None

    def test_guard_is_restored_even_if_the_controller_raises(self, playground):
        """A faulty drone must not lock the true state away for the whole run."""
        drone = _add(playground, HonestDrone(playground, angle=0.0))
        with pytest.raises(ValueError):
            with drone.participant_code():
                raise ValueError("controller bug")
        assert drone.true_position() is not None

    def test_nested_blocks_restore_the_previous_state(self, playground):
        drone = _add(playground, HonestDrone(playground, angle=0.0))
        with drone.participant_code():
            with drone.participant_code():
                pass
            # The inner block must not have cleared the outer one.
            with pytest.raises(TrueStateAccessError):
                drone.true_position()
        assert drone.true_position() is not None


class TestAllowTrueStateEnvVar:
    """`ALLOW_TRUE_STATE_ENV_VAR` is a deliberate, opt-in debugging switch.

    A participant sometimes needs to see what their controller is really acting
    on. Rather than editing the simulator -- easy to forget to revert -- the
    guard can be lifted from the environment. Two properties matter and are
    pinned here: the switch must be OFF unless explicitly asked for, and it must
    actually work when asked for. The second is easy to get wrong, because
    `drone_abstract.py` imports `check_true_state_access` by value, so patching
    the guard module's own attribute would have no effect on it.
    """

    def test_guard_is_on_by_default(self, playground):
        """The evaluation must never be able to run with the guard off."""
        assert not true_state_is_allowed(), (
            f"{ALLOW_TRUE_STATE_ENV_VAR} leaked into the test environment"
        )
        drone = _add(playground, CheatingDrone(playground, angle=0.0))
        with pytest.raises(TrueStateAccessError):
            with drone.participant_code():
                drone.true_position()

    @pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "on", " 1 "])
    def test_truthy_values_lift_the_guard(self, playground, monkeypatch, value):
        monkeypatch.setenv(ALLOW_TRUE_STATE_ENV_VAR, value)
        assert true_state_is_allowed()
        drone = _add(playground, CheatingDrone(playground, angle=0.0))
        with drone.participant_code():
            assert drone.true_position() is not None

    @pytest.mark.parametrize("value", ["", "0", "false", "no", "off", "maybe"])
    def test_falsy_values_keep_the_guard(self, playground, monkeypatch, value):
        """A typo must not silently disable the check."""
        monkeypatch.setenv(ALLOW_TRUE_STATE_ENV_VAR, value)
        assert not true_state_is_allowed()
        drone = _add(playground, CheatingDrone(playground, angle=0.0))
        with pytest.raises(TrueStateAccessError):
            with drone.participant_code():
                drone.true_position()

    def test_switch_unset_again_restores_the_guard(self, playground, monkeypatch):
        """The switch must not survive the end of the debugging session."""
        drone = _add(playground, CheatingDrone(playground, angle=0.0))
        monkeypatch.setenv(ALLOW_TRUE_STATE_ENV_VAR, "1")
        with drone.participant_code():
            assert drone.true_position() is not None
        monkeypatch.delenv(ALLOW_TRUE_STATE_ENV_VAR)
        with pytest.raises(TrueStateAccessError):
            with drone.participant_code():
                drone.true_position()


def _control_body(source: str) -> str:
    """Extract the body of control() from a source file.

    Stops at the next method definition, and drops comment lines: the point is
    to check the code that actually runs, not a neighboring draw_*() helper
    nor a comment that merely mentions the forbidden accessors.
    """
    lines = source.splitlines()
    start = next(
        i for i, line in enumerate(lines) if line.strip().startswith("def control(")
    )
    body = []
    for line in lines[start + 1:]:
        # A new `def` (however indented) means control() is over.
        if re.match(r"^\s*def\s", line):
            break
        if line.strip().startswith("#"):
            continue
        body.append(line)
    return "\n".join(body)


class TestExamplesDoNotCheat:
    """The shipped examples must model the behavior we ask for."""

    def test_pid_rotation_example_uses_measured_sensors(self):
        # `encoding="utf-8"`, not the locale encoding: the examples are UTF-8,
        # and the Windows runner's locale is cp1252, which would silently mangle
        # their accented characters. These two particular files are pure ASCII,
        # so this is the same rule as the other source-reading tests rather than
        # a fix for an observed failure here.
        source = (EXAMPLES_DIR / "example_pid_rotation.py").read_text(encoding="utf-8")
        control = _control_body(source)
        assert "true_position()" not in control
        assert "true_angle()" not in control
        assert "measured_compass_angle()" in control

    def test_pid_translation_example_uses_measured_sensors(self):
        source = (EXAMPLES_DIR / "example_pid_translation.py").read_text(encoding="utf-8")
        control = _control_body(source)
        assert "true_position()" not in control
        assert "true_angle()" not in control
        assert "measured_gps_position()" in control

    def test_pid_rotation_example_runs(self):
        from example_pid_rotation import MyDronePid, MyMap
        from swarm_rescue.simulation.gui_map.gui_sr import GuiSR

        gui = GuiSR(the_map=MyMap(drone_type=MyDronePid), headless=True)
        try:
            for _ in range(5):
                gui._playground.step(all_commands={}, all_messages={})
        finally:
            gui.close()

    def test_pid_translation_example_runs(self):
        from example_pid_translation import MyDronePidTranslation, MyMap
        from swarm_rescue.simulation.gui_map.gui_sr import GuiSR

        gui = GuiSR(the_map=MyMap(drone_type=MyDronePidTranslation), headless=True)
        try:
            for _ in range(5):
                gui._playground.step(all_commands={}, all_messages={})
        finally:
            gui.close()
