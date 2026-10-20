"""
Test Helpers and Fixtures for Swarm Rescue Testing

This module provides reusable fixtures and helpers to simplify testing
of complex components that require full playground setup.
"""
import sys
import pathlib
import pytest
from typing import Tuple

# Insert the parent directory into sys.path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from swarm_rescue.simulation.gui_map.closed_playground import ClosedPlayground
from swarm_rescue.simulation.elements.wounded_person import WoundedPerson
from swarm_rescue.simulation.elements.rescue_center import RescueCenter
from swarm_rescue.simulation.drone.drone_abstract import DroneAbstract
from swarm_rescue.simulation.utils.misc_data import MiscData
import arcade.window_commands as window_commands


def _ensure_headless_window() -> None:
    try:
        window_commands.get_window()
    except RuntimeError:
        window_commands.set_window(_HeadlessWindow())


class _HeadlessWindow:
    """Minimal fake window class for headless testing."""

    def __init__(self, width: int = 1, height: int = 1):
        self.width = width
        self.height = height
        self.visible = False

    def close(self):
        window_commands.set_window(None)


class MinimalTestDrone(DroneAbstract):
    """Minimal drone implementation for testing purposes."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def define_message_for_all(self):
        """Required method - returns empty message."""
        return {}

    def control(self):
        """Required method - returns no-op commands."""
        return {"forward": 0.0, "rotation": 0.0}


class TestHelpers:
    """Collection of helper methods for testing."""

    @staticmethod
    def create_simple_playground(size: Tuple[int, int] = (400, 400)):
        """
        Create a simple playground for testing.

        Args:
            size: Size of the playground (width, height)

        Returns:
            ClosedPlayground: A basic playground instance
        """
        _ensure_headless_window()
        return ClosedPlayground(size=size)

    @staticmethod
    def create_test_drone(identifier: int = 0,
                         size_area: Tuple[int, int] = (400, 400),
                         max_timestep: int = 1000,
                         max_walltime: int = 60) -> MinimalTestDrone:
        """
        Create a minimal drone for testing.

        Args:
            identifier: Drone ID
            size_area: Area size for misc_data
            max_timestep: Max timesteps for misc_data
            max_walltime: Max wall time for misc_data

        Returns:
            MinimalTestDrone: A test drone instance
        """
        misc_data = MiscData(
            size_area=size_area,
            number_drones=1,
            max_timestep_limit=max_timestep,
            max_walltime_limit=max_walltime
        )
        return MinimalTestDrone(identifier=identifier, misc_data=misc_data)

    @staticmethod
    def create_rescue_center(size: Tuple[int, int] = (80, 60)) -> RescueCenter:
        """
        Create a rescue center for testing.

        Args:
            size: Size of the rescue center

        Returns:
            RescueCenter: A rescue center instance
        """
        return RescueCenter(size=size)

    @staticmethod
    def create_wounded_person(rescue_center: RescueCenter) -> WoundedPerson:
        """
        Create a wounded person for testing.

        Args:
            rescue_center: The rescue center to associate with

        Returns:
            WoundedPerson: A wounded person instance
        """
        return WoundedPerson(rescue_center=rescue_center)

    @staticmethod
    def setup_complete_rescue_scenario():
        """
        Set up a complete rescue scenario with playground, drone, rescue center, and wounded person.

        Returns:
            tuple: (playground, drone, rescue_center, wounded_person)
        """
        # Create playground
        playground = TestHelpers.create_simple_playground()

        # Create rescue center
        rescue_center = TestHelpers.create_rescue_center()
        rescue_center_pos = ((0, 0), 0)
        playground.add(rescue_center, rescue_center_pos)

        # Create wounded person
        wounded_person = TestHelpers.create_wounded_person(rescue_center)
        wounded_pos = ((100, 100), 0)
        playground.add(wounded_person, wounded_pos)

        # Create drone
        drone = TestHelpers.create_test_drone()
        drone_pos = ((50, 50), 0)
        playground.add(drone, drone_pos)

        return playground, drone, rescue_center, wounded_person


class MockDevice:
    """Simple mock device that doesn't require complex setup."""

    def __init__(self, name: str = "mock_device", enabled: bool = True):
        self.name = name
        self._enabled = enabled
        self._anchor = None

    def disable(self):
        """Disable the device."""
        self._enabled = False

    def enable(self):
        """Enable the device."""
        self._enabled = True

    @property
    def enabled(self) -> bool:
        """Check if device is enabled."""
        return self._enabled


class MockTexture:
    """Mock texture for testing without graphics dependencies."""

    def __init__(self, width: int = 32, height: int = 32):
        self.width = width
        self.height = height
        self.hit_box_points = [(0, 0), (width, 0), (width, height), (0, height)]

    def get_hit_box(self):
        """Return hit box points."""
        return self.hit_box_points


@pytest.fixture
def simple_playground():
    """Pytest fixture for a simple playground."""
    return TestHelpers.create_simple_playground()


@pytest.fixture
def test_drone():
    """Pytest fixture for a test drone."""
    return TestHelpers.create_test_drone()


@pytest.fixture
def rescue_center():
    """Pytest fixture for a rescue center."""
    return TestHelpers.create_rescue_center()


@pytest.fixture
def wounded_person(rescue_center):
    """Pytest fixture for a wounded person."""
    return TestHelpers.create_wounded_person(rescue_center)


@pytest.fixture
def complete_rescue_scenario():
    """Pytest fixture for complete rescue scenario setup."""
    return TestHelpers.setup_complete_rescue_scenario()


@pytest.fixture
def mock_device():
    """Pytest fixture for a mock device."""
    return MockDevice()


# Utility functions for common test assertions
def assert_playground_state(
    playground, expected_elements: int | None = None, expected_agents: int | None = None
):
    """
    Assert playground is in expected state.

    Args:
        playground: The playground to check
        expected_elements: Expected number of elements (defaults to current count)
        expected_agents: Expected number of agents (defaults to current count)
    """
    actual_elements = len(playground.elements)
    actual_agents = len(playground.agents)

    if expected_elements is not None:
        assert actual_elements == expected_elements, \
            f"Expected {expected_elements} elements, got {actual_elements}"
    if expected_agents is not None:
        assert actual_agents == expected_agents, \
            f"Expected {expected_agents} agents, got {actual_agents}"


def assert_drone_position_near(drone, expected_pos: Tuple[float, float], tolerance: float = 1.0):
    """
    Assert drone is near expected position within tolerance.

    Args:
        drone: The drone to check
        expected_pos: Expected (x, y) position
        tolerance: Allowed distance tolerance
    """
    actual_pos = drone.true_position()
    distance = ((actual_pos[0] - expected_pos[0])**2 + (actual_pos[1] - expected_pos[1])**2)**0.5
    assert distance <= tolerance, f"Drone at {actual_pos}, expected near {expected_pos}"


def assert_wounded_rescued(wounded_person):
    """
    Assert that wounded person has been rescued (removed from playground).

    Args:
        wounded_person: The wounded person to check
    """
    assert wounded_person.removed, "Wounded person should be marked as removed after rescue"


def run_simulation_steps(playground, steps: int = 10):
    """
    Run simulation for specified number of steps.

    Args:
        playground: The playground to step
        steps: Number of simulation steps to run
    """
    for _ in range(steps):
        playground.step()


# Example usage and test template
def test_example_using_helpers():
    """Example test showing how to use the test helpers."""
    # Using helper methods
    playground, drone, rescue_center, wounded_person = TestHelpers.setup_complete_rescue_scenario()

    # Verify initial state (the playground ships with several pre-built walls, so
    # only assert agents)
    assert_playground_state(playground, expected_agents=1)
    assert not wounded_person.removed

    # Run simulation
    run_simulation_steps(playground, 5)

    # Basic assertions
    assert playground.timestep == 5


if __name__ == "__main__":
    # Run the example test
    test_example_using_helpers()
    print("Test helpers are working correctly!")
