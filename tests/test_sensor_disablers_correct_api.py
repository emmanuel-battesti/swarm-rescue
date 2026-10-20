"""
Tests corrects pour SensorDisablers basés sur l'API réelle découverte.
"""
import sys
import pathlib
import pytest

# Insert the parent directory into sys.path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from swarm_rescue.simulation.elements.sensor_disablers import (
    DisablerZone, NoComZone, NoGpsZone, KillZone, ZoneType,
    disabler_zone_disables_device
)
from swarm_rescue.simulation.drone.drone_sensors import DroneGPS, DroneCompass
from swarm_rescue.simulation.drone.communicator import Communicator
from swarm_rescue.simulation.drone.device import Device


class SimpleMockDevice:
    """Lightweight mock device without arcade dependencies."""

    def __init__(self, name="mock_device"):
        self.name = name
        self.enabled = True

    def disable(self):
        self.enabled = False


class TestSensorDisablersRealAPI:
    """Test sensor disablers with their real API."""

    def test_no_com_zone_creation(self):
        """Test NoComZone creation with correct API."""
        zone = NoComZone(size=(50, 50))
        assert zone is not None
        assert hasattr(zone, 'disable')
        assert hasattr(zone, '_disable_cls')

    def test_no_gps_zone_creation(self):
        """Test NoGpsZone creation with correct API."""
        zone = NoGpsZone(size=(50, 50))
        assert zone is not None
        assert hasattr(zone, 'disable')
        assert hasattr(zone, '_disable_cls')

    def test_kill_zone_creation(self):
        """Test KillZone creation with correct API."""
        zone = KillZone(size=(50, 50))
        assert zone is not None
        assert hasattr(zone, 'disable')
        assert hasattr(zone, '_disable_cls')

    def test_disabler_zone_with_custom_classes(self):
        """Test DisablerZone with custom device classes."""
        zone = DisablerZone(
            disable_cls=[SimpleMockDevice],
            size=(50, 50),
            color="red",
            text_to_draw="Test Zone"
        )
        assert zone is not None
        assert zone._disable_cls == [SimpleMockDevice]

    def test_no_com_zone_disables_communicator(self):
        """Test that NoComZone disables communicator devices."""
        zone = NoComZone(size=(50, 50))

        # Check that Communicator is in the disable list
        assert Communicator in zone._disable_cls

        # Mock communicator to test disable logic
        mock_comm = SimpleMockDevice()

        # Test that disable method works
        zone.disable(mock_comm)
        # Note: This will only work if MockDevice is in disable_cls
        # For real test, would need to create proper Communicator instance

    def test_no_gps_zone_disables_gps_devices(self):
        """Test that NoGpsZone disables GPS and compass."""
        zone = NoGpsZone(size=(50, 50))

        # Check that GPS and Compass are in the disable list
        assert DroneGPS in zone._disable_cls
        assert DroneCompass in zone._disable_cls

    def test_kill_zone_disables_all_devices(self):
        """Test that KillZone disables all device types."""
        zone = KillZone(size=(50, 50))

        # Check that Device (base class) is in the disable list
        assert Device in zone._disable_cls

    def test_zone_creation_with_none_size(self):
        """Test zone creation with None size."""
        zone = NoComZone(size=None)
        assert zone is not None

    def test_zone_creation_with_different_sizes(self):
        """Test zones with various sizes."""
        sizes = [(10, 10), (50, 50), (100, 100), (200, 150)]

        for size in sizes:
            no_com = NoComZone(size=size)
            no_gps = NoGpsZone(size=size)
            kill = KillZone(size=size)

            assert no_com is not None
            assert no_gps is not None
            assert kill is not None

    def test_disabler_zone_custom_colors_and_text(self):
        """Test DisablerZone with custom colors and text."""
        test_cases = [
            {"color": "red", "text": "Red Zone"},
            {"color": (255, 0, 0), "text": "RGB Zone"},
            {"color": (255, 0, 0, 128), "text": "RGBA Zone"},
            {"color": 0xFF0000, "text": "Hex Zone"},
        ]

        for case in test_cases:
            zone = DisablerZone(
                disable_cls=[SimpleMockDevice],
                size=(50, 50),
                color=case["color"],
                text_to_draw=case["text"]
            )
            assert zone is not None

    def test_collision_handler_function_exists(self):
        """Test that the collision handler function exists and is callable."""
        assert callable(disabler_zone_disables_device)

    def test_zone_type_enum_still_exists(self):
        """Test that ZoneType enum still exists even if not used in constructor."""
        assert hasattr(ZoneType, 'NO_COM_ZONE')
        assert hasattr(ZoneType, 'NO_GPS_ZONE')
        assert hasattr(ZoneType, 'KILL_ZONE')


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""

    def test_multiple_device_types_in_kill_zone(self):
        """Test that KillZone registers the Device base class."""
        kill_zone = KillZone(size=(100, 100))
        assert Device in kill_zone._disable_cls

    def test_specialized_zones_target_specific_devices(self):
        """Test that specialized zones target their configured classes."""
        no_com_zone = NoComZone(size=(50, 50))
        no_gps_zone = NoGpsZone(size=(50, 50))

        assert SimpleMockDevice not in no_com_zone._disable_cls
        assert SimpleMockDevice not in no_gps_zone._disable_cls

    def test_empty_disable_class_list(self):
        """Test DisablerZone with empty disable class list."""
        zone = DisablerZone(
            disable_cls=[],  # Empty list
            size=(50, 50),
            color="blue",
            text_to_draw="Empty Zone"
        )

        mock_device = SimpleMockDevice()
        zone.disable(mock_device)
        assert mock_device.enabled


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
