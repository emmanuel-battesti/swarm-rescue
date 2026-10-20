"""
Integration tests for the drone/grasper rescue workflow that relies on the
public helpers defined in `tests/test_helpers.py`.
"""
import sys
import pathlib

# Insert the src directory so the helpers and simulation modules resolve.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from swarm_rescue.simulation.elements.normal_wall import NormalWall
from tests.test_helpers import TestHelpers


class TestIntegrationRescueWorkflow:
    """Integration-focused smoke tests for rescues via the grasper."""

    def test_drone_grabs_and_rescues_wounded(self):
        playground, drone, rescue_center, wounded = TestHelpers.setup_complete_rescue_scenario()

        # Force grasp readiness, simulate the grasper grabbing the injured person
        drone.grasper._can_grasp = True
        drone.grasper.grasps(wounded)

        assert wounded in drone.grasper.grasped_wounded_persons
        assert drone.grasper in wounded.grasped_by

        initial_reward = drone.reward
        rescue_center.activate(wounded)

        assert wounded.removed
        assert drone.reward == initial_reward + wounded.reward
        assert not drone.grasper.grasped_wounded_persons

    def test_playground_reset_regenerates_walls(self):
        playground, _, _, wounded = TestHelpers.setup_complete_rescue_scenario()

        wall_count_before = sum(
            1 for entity in playground.elements if isinstance(entity, NormalWall)
        )
        assert wall_count_before > 0

        playground.reset()

        wall_count_after = sum(
            1 for entity in playground.elements if isinstance(entity, NormalWall)
        )
        assert wall_count_after == wall_count_before
        assert not wounded.removed


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
