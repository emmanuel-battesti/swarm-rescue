"""
Tests focusing on the publicly available behaviors of WoundedPerson and RescueCenter.
These avoid reaching into private internals and rely on scenarios that can actually run.
"""
import sys
import pathlib
import pytest

# Ensure the src directory is importable.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from tests.test_helpers import TestHelpers
from swarm_rescue.simulation.elements.wounded_person import WoundedPerson
from swarm_rescue.simulation.elements.rescue_center import (
    RescueCenter, wounded_rescue_center_collision
)


class TestWoundedPersonBasics:
    """Verify the core attributes that a wounded person exposes."""

    def test_wounded_person_initialization(self):
        rescue_center = RescueCenter(size=(80, 60))
        wounded = WoundedPerson(rescue_center=rescue_center)

        assert wounded.rescue_center == rescue_center
        assert wounded.graspable
        assert wounded.reward == 1
        assert wounded.linear_ratio > 0

    def test_wounded_person_has_controllers(self):
        rescue_center = RescueCenter(size=(80, 60))
        wounded = WoundedPerson(rescue_center=rescue_center)

        assert hasattr(wounded, "forward_controller")
        assert hasattr(wounded, "lateral_controller")
        assert wounded.forward_controller.name == "forward"
        assert wounded.lateral_controller.name == "lateral"

    def test_wounded_person_path_behaviors(self):
        rescue_center = RescueCenter(size=(80, 60))
        wounded = WoundedPerson(rescue_center=rescue_center)

        assert hasattr(wounded, "path")
        assert hasattr(wounded, "reverse")
        assert hasattr(wounded, "goal_index")
        assert hasattr(wounded, "set_path")


class TestRescueCenterBasics:
    """Check the observable behaviors of a rescue center."""

    def test_activate_requires_playground(self):
        rescue_center = RescueCenter(size=(80, 60))
        wounded = WoundedPerson(rescue_center=rescue_center)

        with pytest.raises(ValueError, match="not associated with a playground"):
            rescue_center.activate(wounded)

    def test_activate_removes_wounded_and_rewards(self):
        playground, drone, rescue_center, wounded = TestHelpers.setup_complete_rescue_scenario()

        initial_reward = drone.reward
        rescue_center.activate(wounded)

        assert wounded.removed
        assert drone.reward > initial_reward


class TestCollisionHandler:
    """Simple sanity check for the collision handler signature."""

    def test_collision_handler_callable(self):
        assert callable(wounded_rescue_center_collision)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
