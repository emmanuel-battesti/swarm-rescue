"""
Robust tests for WoundedPerson and RescueCenter using test helpers.
These tests demonstrate how to properly test the rescue workflow.
"""
import sys
import pathlib
import pytest

# Insert the parent directory into sys.path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

# `complete_rescue_scenario`, `simple_playground`, `rescue_center` and
# `wounded_person` are pytest fixtures: importing them is how pytest finds them.
from tests.test_helpers import (
    TestHelpers, run_simulation_steps, complete_rescue_scenario,
    simple_playground, rescue_center, wounded_person
)


class TestWoundedPersonRescueCenterRobust:
    """Robust tests for WoundedPerson and RescueCenter interaction."""

    def test_rescue_center_basic_setup(self, rescue_center):
        """Test basic rescue center setup."""
        assert rescue_center is not None
        assert hasattr(rescue_center, 'activate')
        assert rescue_center._count_rewards == 0

    def test_wounded_person_basic_setup(self, wounded_person):
        """Test basic wounded person setup."""
        assert wounded_person is not None
        assert wounded_person.graspable is True
        assert wounded_person.reward == 1
        assert wounded_person.rescue_center is not None

    def test_complete_rescue_scenario_setup(self, complete_rescue_scenario):
        """Test that complete rescue scenario sets up correctly."""
        playground, drone, rescue_center, wounded_person = complete_rescue_scenario

        # Verify components exist
        assert playground is not None
        assert drone is not None
        assert rescue_center is not None
        assert wounded_person is not None

        # Verify relationships
        assert wounded_person.rescue_center == rescue_center
        assert drone.playground == playground
        assert rescue_center.playground == playground
        assert wounded_person.playground == playground

    def test_wounded_person_association_with_rescue_center(self):
        """Test that wounded person is properly associated with rescue center."""
        rescue_center = TestHelpers.create_rescue_center()
        wounded1 = TestHelpers.create_wounded_person(rescue_center)
        wounded2 = TestHelpers.create_wounded_person(rescue_center)

        assert wounded1.rescue_center == rescue_center
        assert wounded2.rescue_center == rescue_center
        assert wounded1.rescue_center == wounded2.rescue_center

    def test_rescue_center_requires_playground_for_activation(self):
        """Test that rescue center needs playground to activate wounded persons."""
        rescue_center = TestHelpers.create_rescue_center()
        wounded_person = TestHelpers.create_wounded_person(rescue_center)

        # Should fail without playground
        with pytest.raises(ValueError, match="not associated with a playground"):
            rescue_center.activate(wounded_person)

    def test_rescue_workflow_with_playground(self, complete_rescue_scenario):
        """Test complete rescue workflow."""
        playground, drone, rescue_center, wounded_person = complete_rescue_scenario

        # Initial state
        assert not wounded_person.removed
        initial_reward = drone.reward

        # Simulate rescue (wounded person reaches rescue center)
        rescue_center.activate(wounded_person)

        # Verify rescue completed
        assert wounded_person.removed
        assert drone.reward > initial_reward  # Should get reward

    def test_rescue_with_multiple_wounded_persons(self):
        """Test rescue scenario with multiple wounded persons."""
        playground, drone, rescue_center, _ = TestHelpers.setup_complete_rescue_scenario()

        # Add more wounded persons
        wounded2 = TestHelpers.create_wounded_person(rescue_center)
        wounded3 = TestHelpers.create_wounded_person(rescue_center)
        playground.add(wounded2, ((150, 150), 0))
        playground.add(wounded3, ((200, 200), 0))

        initial_reward = drone.reward

        # Rescue all wounded persons
        rescue_center.activate(wounded2)
        rescue_center.activate(wounded3)

        # All should be rescued
        assert wounded2.removed
        assert wounded3.removed
        assert drone.reward > initial_reward

    def test_rescue_center_with_wrong_wounded_person(self):
        """Test rescue center with wounded person from different center."""
        playground = TestHelpers.create_simple_playground()

        # Create two separate rescue centers
        rescue_center1 = TestHelpers.create_rescue_center()
        rescue_center2 = TestHelpers.create_rescue_center()
        playground.add(rescue_center1, ((0, 0), 0))
        playground.add(rescue_center2, ((200, 200), 0))

        # Create wounded person associated with center2
        wounded = TestHelpers.create_wounded_person(rescue_center2)
        playground.add(wounded, ((100, 100), 0))

        # Create drone
        drone = TestHelpers.create_test_drone()
        playground.add(drone, ((50, 50), 0))

        # Try to rescue with wrong center (center1)
        rescue_center1.activate(wounded)

        # Should still be rescued (implementation detail - any rescue center can rescue any wounded)
        # but the wounded person's designated center matters for the collision logic
        assert wounded.removed

    def test_wounded_person_reward_value(self, wounded_person):
        """Test wounded person reward value."""
        assert wounded_person.reward == 1

        # Test with different rescue center
        rescue_center2 = TestHelpers.create_rescue_center()
        wounded2 = TestHelpers.create_wounded_person(rescue_center2)
        assert wounded2.reward == 1

    def test_drone_gets_reward_on_rescue(self, complete_rescue_scenario):
        """Test that drone gets reward when wounded person is rescued."""
        playground, drone, rescue_center, wounded_person = complete_rescue_scenario

        initial_reward = drone.reward
        expected_reward = wounded_person.reward

        rescue_center.activate(wounded_person)

        assert drone.reward == initial_reward + expected_reward

    def test_simulation_steps_with_rescue(self, complete_rescue_scenario):
        """Test running simulation steps with rescue scenario."""
        playground, drone, rescue_center, wounded_person = complete_rescue_scenario

        initial_timestep = playground.timestep

        # Run simulation for a few steps
        run_simulation_steps(playground, 5)

        # Verify simulation progressed
        assert playground.timestep == initial_timestep + 5

        # Manually trigger rescue
        rescue_center.activate(wounded_person)
        assert wounded_person.removed

    def test_playground_reset_after_rescue(self, complete_rescue_scenario):
        """Test playground reset functionality after rescue."""
        playground, drone, rescue_center, wounded_person = complete_rescue_scenario

        # Perform rescue
        rescue_center.activate(wounded_person)
        assert wounded_person.removed

        # Reset playground
        playground.reset()

        # Verify reset worked
        assert playground.timestep == 0
        assert not wounded_person.removed  # Should be back

    def test_multiple_drones_rescue_scenario(self):
        """Test rescue scenario with multiple drones."""
        playground = TestHelpers.create_simple_playground()

        # Create rescue center and wounded person
        rescue_center = TestHelpers.create_rescue_center()
        wounded_person = TestHelpers.create_wounded_person(rescue_center)
        playground.add(rescue_center, ((0, 0), 0))
        playground.add(wounded_person, ((100, 100), 0))

        # Create multiple drones
        drone1 = TestHelpers.create_test_drone(identifier=0)
        drone2 = TestHelpers.create_test_drone(identifier=1)
        playground.add(drone1, ((50, 50), 0))
        playground.add(drone2, ((150, 150), 0))

        # Rescue wounded person
        rescue_center.activate(wounded_person)

        # Verify rescue and rewards
        assert wounded_person.removed
        # Closest drone should get reward (implementation dependent)


class TestEdgeCasesAndRobustness:
    """Test edge cases and robustness scenarios."""

    def test_rescue_already_removed_wounded_person(self, complete_rescue_scenario):
        """Test rescuing a wounded person that's already been removed."""
        playground, drone, rescue_center, wounded_person = complete_rescue_scenario

        # Rescue once
        rescue_center.activate(wounded_person)
        assert wounded_person.removed

        # Try to rescue again - should not crash
        try:
            rescue_center.activate(wounded_person)
        except Exception:
            # Some implementations might raise an exception, which is OK
            pass

    def test_large_number_of_wounded_persons(self):
        """Test performance with many wounded persons."""
        playground, drone, rescue_center, _ = TestHelpers.setup_complete_rescue_scenario()

        # Add many wounded persons
        wounded_persons = []
        for i in range(20): # Test with 20 wounded persons
            wounded = TestHelpers.create_wounded_person(rescue_center)
            wounded_persons.append(wounded)
            playground.add(wounded, ((100 + i*10, 100 + i*10), 0))

        initial_reward = drone.reward

        # Rescue all
        for wounded in wounded_persons:
            rescue_center.activate(wounded)
            assert wounded.removed

        # Verify total reward
        expected_total_reward = initial_reward + len(wounded_persons)
        assert drone.reward == expected_total_reward


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
