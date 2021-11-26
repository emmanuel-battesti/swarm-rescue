from typing import List

from simple_playgrounds.agent.actuators import ActuatorDevice
from simple_playgrounds.device.communication import CommunicationDevice
from simple_playgrounds.device.device import Device
from simple_playgrounds.device.sensor import SensorDevice
from simple_playgrounds.common.definitions import ElementTypes
from simple_playgrounds.element.elements.modifier import DeviceDisabler


class KillZone(DeviceDisabler):
    def __init__(self, **entity_params):

        list_disabled: List[type(Device)] = [SensorDevice, CommunicationDevice, ActuatorDevice]

        super().__init__(disabled_device_types=list_disabled,
                         config_key=ElementTypes.SENSOR_DISABLER, **entity_params)

    def modify(self, modified: Device):
        if isinstance(modified, ActuatorDevice):
            modified.part.agent.deactivated = True

        super().modify(modified)
