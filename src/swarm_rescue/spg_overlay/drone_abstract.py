import math
from abc import abstractmethod
from enum import IntEnum
from typing import Optional, Tuple

from spg_overlay.drone_sensors import DroneLidar, DroneTouch, DroneSemanticCones, DroneGPS, DroneVelocity, \
    DroneCompass
from spg_overlay.misc_data import MiscData
from simple_playgrounds.agent.agents import BaseAgent
from simple_playgrounds.device.communication import CommunicationDevice
from simple_playgrounds.agent.controllers import External

import matplotlib.pyplot as plt


class DroneAbstract(BaseAgent):
    """
    This class should be used as a parent class to create your own Drone class.
    It is a BaseAgent class with 3 sensors, 1 sensor of position and 2 mandatory functions define_message() and
    control()
    """

    # 'range_communication' is the radius, in pixels, of the area around the drone in which we will have the other
    # drones with which we can communicate (receive and send messages)
    range_communication = 500

    class SensorType(IntEnum):
        TOUCH = 0
        SEMANTICCONES = 1
        LIDAR = 2
        GPS = 3
        COMPASS = 4
        VELOCITY = 5

    def __init__(self,
                 controller=External(),
                 identifier: Optional[int] = None,
                 misc_data: MiscData = None,
                 should_display_lidar=False,
                 **kwargs
                 ):
        super().__init__(controller=controller, interactive=True, lateral=True, radius=10, **kwargs)

        self.size_area = misc_data.size_area

        self.add_sensor(DroneTouch(anchor=self.base_platform,
                                   min_range=self.base_platform.radius + 1))
        self.add_sensor(DroneSemanticCones(anchor=self.base_platform,
                                           min_range=self.base_platform.radius + 1))

        self.add_sensor(DroneLidar(anchor=self.base_platform,
                                   min_range=self.base_platform.radius + 1))

        self.add_sensor(DroneGPS(anchor=self.base_platform))
        self.add_sensor(DroneCompass(anchor=self.base_platform))
        self.add_sensor(DroneVelocity(anchor=self.base_platform))

        self.identifier = identifier
        self._should_display_lidar = should_display_lidar

        if self._should_display_lidar:
            plt.axis([-300, 300, 0, 300])
            plt.ion()

        self.add_communication(CommunicationDevice(self.base_platform, transmission_range=self.range_communication))

    @abstractmethod
    def define_message(self):
        """
        This function is mandatory in the class you have to create that will inherit from this class.
        You should return want you want to send to all nearest drone.
        For example:
            def define_message(self):
                msg_data = (self.identifier, (self.measured_position(), self.angle))
                return msg_data
        """
        pass

    @abstractmethod
    def control(self):
        """
        This function is mandatory in the class you have to create that will inherit from this class.
        This function should return a command which is a dict with values for the actuators.
        For example:
        command = {self.longitudinal_force: 0.3,
                   self.lateral_force: 0.0,
                   self.rotation_velocity: -1.0,
                   self.grasp: 0,
                   self.activate: 0}
        """
        pass

    def touch(self):
        """
        Give access to the value of the touch sensor.
        """
        return self.sensors[self.SensorType.TOUCH.value]

    def semantic_cones(self):
        """
        Give access to the value of the semantic_cones sensor.
        """
        return self.sensors[self.SensorType.SEMANTICCONES.value]

    def lidar(self):
        """
        Give access to the value of the lidar sensor.
        """
        return self.sensors[self.SensorType.LIDAR.value]

    def touch_is_disabled(self):
        return self.touch().is_disabled()

    def semantic_cones_is_disabled(self):
        return self.semantic_cones().is_disabled()

    def lidar_is_disabled(self):
        return self.lidar().is_disabled()

    def measured_position(self):
        """
        Give the measured position of the drone, in pixels
        You must use this value for your calculation in the control() function, because these values can be altered
        by special areas in the map where the position information can be scrambled.
        """
        return self.sensors[self.SensorType.GPS].sensor_values[0], self.sensors[self.SensorType.GPS].sensor_values[1]

    def measured_angle(self):
        """
        Give the measured orientation of the drone, in radians between 0 and 2Pi.
        You must use this value for your calculation in the control() function.
        """
        return self.sensors[self.SensorType.COMPASS].sensor_values[0]

    def measured_velocity(self):
        """
        Give the measured velocity of the drone, in pixels per second
        You must use this value for your calculation in the control() function.
        """
        return self.sensors[self.SensorType.VELOCITY].sensor_values[0], self.sensors[self.SensorType.VELOCITY].sensor_values[1]

    def measured_angular_velocity(self):
        """
        Give the measured angular velocity of the drone, in radians per second
        You must use this value for your calculation in the control() function.
        """
        return self.sensors[self.SensorType.VELOCITY].sensor_values[2]

    def true_position(self):
        """
        Give the true orientation of the drone, in pixels
        You must NOT use this value for your calculation in the control() function, you should use measured_position()
        instead. But you can use it for debugging or logging.
        """
        return self.position

    def true_angle(self):
        """
        Give the true orientation of the drone, in radians between 0 and 2Pi.
        You must NOT use this value for your calculation in the control() function, you should use measured_angle()
        instead. But you can use it for debugging or logging.
        """
        return self.angle

    def true_velocity(self):
        """
        Give the true velocity of the drone, in pixels per second
        You must NOT use this value for your calculation in the control() function, you should use measured_velocity()
        instead. But you can use it for debugging or logging.
        """
        return self.base_platform.velocity

    def true_angular_velocity(self):
        """
        Give the true angular velocity of the drone, in radians per second
        You must NOT use this value for your calculation in the control() function, you should use measured_angular_velocity()
        instead. But you can use it for debugging or logging.
        """
        return self.base_platform.angular_velocity

    def gps_is_disabled(self):
        return self.sensors[self.SensorType.GPS].is_disabled()

    def compass_is_disabled(self):
        return self.sensors[self.SensorType.COMPASS].is_disabled()

    def display(self):
        if self._should_display_lidar:
            self.display_lidar()

    def display_lidar(self):
        plt.cla()
        plt.axis([-math.pi / 2, math.pi / 2, 0, self.lidar().max_range])
        plt.plot(self.lidar().ray_angles, self.lidar().get_sensor_values(), "g.:")
        plt.grid(True)
        plt.draw()
        plt.pause(0.001)
