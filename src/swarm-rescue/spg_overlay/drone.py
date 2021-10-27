# Drone est une classe fille de la classe BaseAgent.
# Cette classe est adaptée à la competition avec un certain nombre
# de capteurs pré-définis.
import math
from abc import abstractmethod
from typing import List, Optional, Union

from spg_overlay.drone_sensors import DroneLidar, DroneTouch, DroneSemanticCones
from simple_playgrounds.agents.agents import BaseAgent
from simple_playgrounds.agents.communication import CommunicationDevice
from simple_playgrounds.agents.parts.controllers import External, Keyboard

import matplotlib.pyplot as plt


class DroneAbstract(BaseAgent):
    range_communication = 200

    def __init__(self,
                 controller=External(),
                 identifier: Optional[int] = None,
                 should_display_lidar=False,
                 **kwargs
                 ):
        super().__init__(controller=controller, interactive=True, lateral=True, radius=10, **kwargs)

        self.add_sensor(DroneTouch(anchor=self.base_platform,
                                   min_range=self.base_platform.radius + 1))
        self.add_sensor(DroneSemanticCones(anchor=self.base_platform,
                                           min_range=self.base_platform.radius + 1))

        self.add_sensor(DroneLidar(anchor=self.base_platform,
                                   min_range=self.base_platform.radius + 1))

        self.identifier = identifier
        self._should_display_lidar = should_display_lidar

        if self._should_display_lidar:
            plt.axis([-300, 300, 0, 300])
            plt.ion()

        self.add_communication(CommunicationDevice(self.base_platform, transmission_range=self.range_communication))

    @abstractmethod
    def define_message(self):
        pass

    @abstractmethod
    def control(self):
        pass

    def touch(self):
        return self.sensors[0]

    def semantic_cones(self):
        return self.sensors[1]

    def lidar(self):
        return self.sensors[2]

    def display(self):
        if self._should_display_lidar:
            self.display_lidar()

    def display_lidar(self):
        plt.cla()
        plt.axis([-math.pi/2, math.pi/2, 0, self.lidar().max_range])
        plt.plot(self.lidar().ray_angles, self.lidar().get_sensor_values(), "g.:")
        plt.grid(True)
        plt.draw()
        plt.pause(0.001)
