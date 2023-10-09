import math
from abc import abstractmethod
from enum import IntEnum, auto
from typing import Optional, Union

import arcade
import numpy as np

from spg.agent.agent import Agent
from spg.agent.communicator.communicator import Communicator
from spg.agent.interactor import GraspMagnet
from spg.element import PhysicalElement, ColorWall
from spg.playground import Playground, get_colliding_entities

from spg_overlay.entities.drone_base import DroneBase
from spg_overlay.entities.drone_distance_sensors import DroneLidar, DroneSemanticSensor
from spg_overlay.entities.drone_sensors import DroneGPS, DroneCompass, DroneOdometer
from spg_overlay.entities.normal_wall import NormalWall, NormalBox
from spg_overlay.utils.constants import DRONE_INITIAL_HEALTH, RANGE_COMMUNICATION
from spg_overlay.utils.misc_data import MiscData

import matplotlib.pyplot as plt

from spg_overlay.utils.timer import Timer
from spg_overlay.utils.utils import normalize_angle


def drone_collision_wall(arbiter, _, data):
    playground: Playground = data["playground"]
    (part, _), (element, _) = get_colliding_entities(playground, arbiter)

    assert isinstance(part, DroneBase)
    assert isinstance(element, PhysicalElement) or isinstance(element, DroneBase)

    # CollisionTypes.PART
    drone = part.agent

    if isinstance(element, NormalWall) or isinstance(element, ColorWall) or isinstance(element, NormalBox):
        drone.collide_wall()

    if isinstance(element, Agent) or isinstance(element, DroneBase):
        drone.collide_drone()

    return True


def drone_collision_drone(arbiter, _, data):
    playground: Playground = data["playground"]
    (my_part, _), (other_part, _) = get_colliding_entities(playground, arbiter)

    assert isinstance(my_part, DroneBase)
    assert isinstance(other_part, DroneBase)

    # CollisionTypes.PART
    my_drone = my_part.agent

    if isinstance(other_part, Agent) or isinstance(other_part, DroneBase):
        my_drone.collide_drone()

    return True


class DroneAbstract(Agent):
    """
    The DroneAbstract class is a parent class that should be used to create custom Drone classes. It inherits from the
    Agent class and provides functionality for controlling a drone in a simulated environment.
    It is a BaseAgent class with 3 sensors, 1 sensor of position and 2 mandatory functions define_message() and
    control()

    Example Usage
        # Create a custom Drone class that inherits from DroneAbstract
        class MyDrone(DroneAbstract):
            def define_message_for_all(self):
                # Define the message to be sent to other drones
                msg_data = (self.identifier, (self.measured_gps_position(), self.measured_compass_angle()))
                return msg_data

            def control(self):
                # Define the control command for the drone
                command = {"forward": 1.0, "lateral": 0.0, "rotation": -1.0, "grasper": 0}
                return command

        # Create an instance of the custom drone class
        drone = MyDrone()

        # Access sensor values and other functionalities
        gps_position = drone.measured_gps_position()
        lidar_values = drone.lidar()
        grasped_entities = drone.grasped_entities()

        # Control the drone
        command = drone.control()

    Fields
        RANGE_COMMUNICATION: The radius, in pixels, of the area around the drone in which it can communicate with
        other drones.
        SensorType: An enumeration of different sensor types.
        identifier: The identifier of the drone.
        _display_lidar_graph: A flag indicating whether the lidar sensor data should be displayed on matplotlib graph.
         It is slow.
        size_area: The size of the area in which the drone operates.
        communicator: The communicator object used for communication with other drones.
        timer_collision_wall_or_drone: A timer used to track collision events.
        drone_health: The health of the drone, which is reduced upon collision events.
    """

    class SensorType(IntEnum):
        SEMANTIC = 0
        LIDAR = auto()
        GPS = auto()
        COMPASS = auto()
        ODOMETER = auto()

    def __init__(self,
                 identifier: Optional[int] = None,
                 misc_data: MiscData = None,
                 display_lidar_graph=False,
                 **kwargs
                 ):
        super().__init__(interactive=True, lateral=True, radius=10, **kwargs)

        if identifier is None:
            identifier = id(self)

        base = DroneBase()
        self.add(base)

        grasp = GraspMagnet(base, max_grasped=1)
        self.base.add(grasp)

        self._half_size_array = None
        self._size_area = None
        if misc_data:
            self.size_area = misc_data.size_area

        self.base.add(DroneSemanticSensor(playground=self.playground, invisible_elements=self._parts))
        self.base.add(DroneLidar(invisible_elements=self._parts))

        self.base.add(DroneGPS())
        self.base.add(DroneCompass())
        self.base.add(DroneOdometer())

        self.identifier = identifier
        self._display_lidar_graph = display_lidar_graph

        if self._display_lidar_graph:
            plt.figure(self.SensorType.LIDAR)
            plt.axis((-300, 300, 0, 300))
            plt.ion()

        self.communicator = Communicator(transmission_range=RANGE_COMMUNICATION)
        self.base.add(self.communicator)

        self.timer_collision_wall_or_drone = Timer(start_now=True)
        self.drone_health = DRONE_INITIAL_HEALTH

    @property
    def size_area(self):
        return self._size_area

    @size_area.setter
    def size_area(self, value):
        self._size_area = value
        if value is not None:
            self._half_size_array = np.array(self._size_area) / 2
        else:
            self._half_size_array = None

    @abstractmethod
    def define_message_for_all(self):
        """
        This function is mandatory in the class you have to create that will inherit from this class.
        You should return want you want to send to all nearest drones.
        For example:
            def define_message_for_all(self):
                msg_data = (self.identifier, (self.measured_gps_position(), self.measured_compass_angle()))
                return msg_data
        """
        pass

    @abstractmethod
    def control(self):
        """
        This function is mandatory in the class you have to create that will inherit from this class.
        This function should return a command which is a dict with values for the actuators.
        For example:
        command = {"forward": 1.0,
                   "lateral": 0.0,
                   "rotation": -1.0,
                   "grasper": 0}
        """
        pass

    def grasped_entities(self):
        """ Returns the entities currently grasped by the drone."""
        return self.base.grasper.grasped_entities

    def communicator_is_disabled(self):
        """Returns whether the communicator of the drone is disabled."""
        return self.communicator._disabled

    def semantic(self):
        """
        Give access to the value of the semantic sensor.
        """
        return self.sensors[self.SensorType.SEMANTIC]

    def lidar(self):
        """
        Give access to the value of the lidar sensor.
        """
        return self.sensors[self.SensorType.LIDAR]

    def gps(self):
        """
        Give access to the value of the gps sensor.
        """
        return self.sensors[self.SensorType.GPS]

    def compass(self):
        """
        Give access to the value of the compass sensor.
        """
        return self.sensors[self.SensorType.COMPASS]

    def odometer(self):
        """
        Give access to the value of the gps sensor.
        """
        return self.sensors[self.SensorType.ODOMETER]

    def semantic_is_disabled(self):
        return self.semantic().is_disabled()

    def lidar_is_disabled(self):
        return self.lidar().is_disabled()

    def gps_is_disabled(self):
        return self.gps().is_disabled()

    def compass_is_disabled(self):
        return self.compass().is_disabled()

    def odometer_is_disabled(self):
        return self.odometer().is_disabled()

    def semantic_values(self):
        return self.semantic().get_sensor_values()

    def lidar_values(self):
        return self.lidar().get_sensor_values()

    def lidar_rays_angles(self):
        return self.lidar().ray_angles

    def gps_values(self):
        return self.gps().get_sensor_values()

    def compass_values(self):
        return self.compass().get_sensor_values()

    def odometer_values(self):
        return self.odometer().get_sensor_values()

    def measured_gps_position(self) -> Union[np.ndarray, None]:
        """
        Give the measured position of the drone, in pixels. The measurement comes from the GPS sensor.
        You can use this value for your calculation in the control() function. These values can be altered
        by special areas in the map where the position information can be scrambled.
        """
        if self.gps_is_disabled():
            return None

        gps_values = self.gps_values()
        if gps_values is not None:
            return np.array([gps_values[0], gps_values[1]])
        else:
            return None

    def measured_compass_angle(self) -> Union[float, None]:
        """
        Give the measured orientation of the drone, in radians between 0 and 2Pi. The measurement comes from the compass
        sensor. You can use this value for your calculation in the control() function. These values can be altered
        by special areas in the map where the position information can be scrambled.
        """
        if self.compass_is_disabled():
            return None

        if self.compass_values() is not None:
            return self.compass_values()
        else:
            return None

    def measured_velocity(self) -> Union[np.ndarray, None]:
        """
        Give the measured velocity of the drone in the two dimensions, in pixels per second
        You must use this value for your calculation in the control() function.
        """
        odom = self.odometer_values()
        angle = self.compass_values()
        if odom and angle:
            speed = odom[0]
            vx = speed * math.cos(angle)
            vy = speed * math.sin(angle)
            return np.array([vx, vy])
        else:
            return None

    def measured_angular_velocity(self) -> Union[float, None]:
        """
        Give the measured angular velocity of the drone, in radians per second
        You must use this value for your calculation in the control() function.
        """
        odometer = self.odometer_values()
        if odometer:
            return odometer[2]
        else:
            return None

    @property
    def position(self):
        raise Exception('Function Disabled')

    @property
    def angle(self):
        raise Exception('Function Disabled')

    @property
    def velocity(self):
        raise Exception('Function Disabled')

    @property
    def angular_velocity(self):
        raise Exception('Function Disabled')

    def true_position(self) -> np.ndarray:
        """
        Give the true position of the drone, in pixels
        You must NOT use this value for your calculation in the control() function, you should use
        measured_gps_position() instead. But you can use it for debugging or logging.
        """
        return np.array(self.base._pm_body.position)

    def true_angle(self) -> float:
        """
        Give the true orientation of the drone, in radians between 0 and 2Pi.
        You must NOT use this value for your calculation in the control() function, you should use
        measured_compass_angle() instead. But you can use it for debugging or logging.
        """
        return normalize_angle(self.base._pm_body.angle)

    def true_velocity(self) -> np.ndarray:
        """
        Give the true velocity of the drone in the two dimensions, in pixels per second
        You must NOT use this value for your calculation in the control() function, you should use GPS, Compass or
        odometry data instead. But you can use it for debugging or logging.
        """
        return np.array(self.base._pm_body.velocity)

    def true_angular_velocity(self) -> float:
        """
        Give the true angular velocity of the drone, in radians per second
        You must NOT use this value for your calculation in the control() function, you should use GPS, Compass or
        odometry data instead. But you can use it for debugging or logging.
        """
        return self.base._pm_body.angular_velocity

    def display(self):
        if self._display_lidar_graph:
            self.display_lidar_graph()

    def display_lidar_graph(self):
        if self.lidar_values() is not None:
            plt.figure(self.SensorType.LIDAR)
            plt.cla()
            plt.axis((-math.pi, math.pi, 0, self.lidar().max_range))
            plt.plot(self.lidar().ray_angles, self.lidar_values(), "g.:")
            plt.grid(True)
            plt.draw()
            plt.pause(0.001)

    def draw_gps(self):
        """Draws the GPS position of the drone on the playground."""

        true_pt = self.true_position()
        gps_pt = self.measured_gps_position()

        if gps_pt is not None:
            txt_gps = "GPS: ({0:.1f}, {1:.1f})".format(gps_pt[0], gps_pt[1])
        else:
            txt_gps = "GPS: None"
        txt_truth = "Truth: ({0:.1f}, {1:.1f})".format(true_pt[0], true_pt[1])

        pt = true_pt + self._half_size_array

        arcade.draw_text(txt_gps, pt[0] + 10, pt[1] + 10, [128, 128, 128], 10)
        arcade.draw_text(txt_truth, pt[0] + 10, pt[1] + 25, [128, 128, 128], 10)

    def draw_com(self):
        """Draws the communication range of the drone on the playground."""
        pt = self.true_position() + self._half_size_array

        # arcade.draw_circle_outline(pt[0], pt[1], RANGE_COMMUNICATION, [128, 128, 128], 5, -1)
        # for r in range(RANGE_COMMUNICATION - 60, RANGE_COMMUNICATION, 20):
        color = [128, 128, 128]
        if self.communicator_is_disabled():
            color = [200, 200, 200]
        arcade.draw_circle_outline(pt[0], pt[1], RANGE_COMMUNICATION, color, 1, -1)

        # in_transmission_range
        if not self.communicator_is_disabled():
            for com in self.communicator.comms_in_range:
                if not com.agent.communicator_is_disabled():
                    pt2 = com.agent.true_position() + self._half_size_array
                    arcade.draw_line(pt[0], pt[1], pt2[0], pt2[1], [128, 128, 128], 2)

    def draw_bottom_layer(self):
        pass

    def draw_top_layer(self):
        pass

    def draw_identifier(self):
        color = (64, 64, 64)
        offset = 10
        pt1 = self.true_position() + self._half_size_array + np.array([offset, offset])
        str_id = str(self.identifier)
        font_size = 10
        arcade.draw_text(str_id,
                         pt1[0],
                         pt1[1],
                         color,
                         font_size)

    def collide_wall(self):
        """Handles collision with walls and reduces drone health."""
        if self.timer_collision_wall_or_drone.get_elapsed_time() > 1.0:
            self.drone_health -= 1
            self.timer_collision_wall_or_drone.restart()
            # print("Drone {} collides a wall, drone_health = {}".format(self.identifier,
            #                                                            self.drone_health))

        if self.drone_health <= 0:
            print(f"Drone {self.identifier} destroyed, too much collision !")
            if not self.removed:
                self.base.grasper._release_grasping()
                self._playground.remove(self)

    def collide_drone(self):
        """Handles collision with other drones and reduces drone health."""
        if self.timer_collision_wall_or_drone.get_elapsed_time() > 1.0:
            self.drone_health -= 1
            self.timer_collision_wall_or_drone.restart()
            # print("Drone {} collides a drone, drone_health = {}".format(self.identifier,
            #                                                             self.drone_health))

        if self.drone_health <= 0:
            print(f"Drone {self.identifier} destroyed, too much collision !")
            if not self.removed:
                self.base.grasper._release_grasping()
                self._playground.remove(self)
