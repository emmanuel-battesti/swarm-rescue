from enum import IntEnum

from simple_playgrounds.element.elements.modifier import CommunicationDisabler, SensorDisabler

from spg_overlay.drone_sensors import DroneGPS


class EnvironmentType(IntEnum):
    EASY = 0
    NO_COM_ZONE = 1
    NO_GPS_ZONE = 2
    KILL_ZONE = 3


class NoComZone(CommunicationDisabler):
    def __init__(self, **entity_params):
        default_config = {'physical_shape': 'rectangle', 'texture': {'texture_type': 'color', 'color': [230, 0, 126]}}
        entity_params = {**default_config, **entity_params}

        super().__init__(**entity_params)


class NoGpsZone(SensorDisabler):
    def __init__(self, **entity_params):
        default_config = {'physical_shape': 'rectangle', 'texture': {'texture_type': 'color', 'color': [0, 32, 255]}}
        entity_params = {**default_config, **entity_params}

        super().__init__(disabled_sensor_types=DroneGPS, **entity_params)
