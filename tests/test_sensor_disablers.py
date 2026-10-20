"""
Tests for SensorDisablers with the real constructors and lightweight mocks.
"""
import sys
import pathlib

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from swarm_rescue.simulation.elements.sensor_disablers import (
    DisablerZone,
    NoComZone,
    NoGpsZone,
    KillZone,
    ZoneType,
    disabler_zone_disables_device,
)
from swarm_rescue.simulation.drone.drone_sensors import DroneGPS, DroneCompass
from swarm_rescue.simulation.drone.communicator import Communicator


class MockDevice:
    """Lightweight mock device without arcade dependencies."""

    def __init__(self):
        self.enabled = True

    def disable(self):
        self.enabled = False


class TestZoneType:
    """Enumerations remain stable."""

    def test_zone_type_presence(self):
        assert ZoneType.NO_COM_ZONE != ZoneType.NO_GPS_ZONE
        assert ZoneType.NO_GPS_ZONE != ZoneType.KILL_ZONE
        assert ZoneType.NO_COM_ZONE != ZoneType.KILL_ZONE


class TestDisablerZoneBasic:
    """Smoke tests for DisablerZone.

    These avoid creating any arcade sprites by concentrating on constructor parameters
    and its disable list.
    """

    def test_disabler_zone_custom_classes(self):
        zone = DisablerZone(disable_cls=[MockDevice], size=(10, 10))
        assert MockDevice in zone._disable_cls

    def test_disabler_zone_disable_none(self):
        zone = DisablerZone(disable_cls=[], size=(1, 1))
        assert len(zone._disable_cls) == 0

    def test_disabler_zone_disables_matching_device(self):
        zone = DisablerZone(disable_cls=[MockDevice], size=(2, 2))
        device = MockDevice()
        assert zone.disable(device) is None
        assert not device.enabled


class TestSpecializedZones:
    """Verify the built-in specialized zones configure the expected device lists."""

    def test_no_com_zone_targets_communicator(self):
        zone = NoComZone(size=(20, 20))
        assert Communicator in zone._disable_cls

    def test_no_gps_zone_targets_gps_and_compass(self):
        zone = NoGpsZone(size=(20, 20))
        assert DroneGPS in zone._disable_cls
        assert DroneCompass in zone._disable_cls

    def test_kill_zone_targets_all_devices(self):
        zone = KillZone(size=(20, 20))
        assert len(zone._disable_cls) >= 1


class TestCollisionHandler:
    """Basic sanity check for the collision handler signature."""

    def test_handler_callable(self):
        assert callable(disabler_zone_disables_device)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
