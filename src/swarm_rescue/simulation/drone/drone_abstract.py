import math
from abc import abstractmethod
from enum import IntEnum, auto
from typing import Optional, Union

import arcade
import matplotlib.pyplot as plt
import numpy as np
import pymunk
import pyqtgraph
from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication

from swarm_rescue.simulation.drone.agent import Agent
from swarm_rescue.simulation.drone.communicator import Communicator
from swarm_rescue.simulation.drone.controller import CommandsDict
from swarm_rescue.simulation.drone.drone_base import DroneBase
from swarm_rescue.simulation.drone.grasper import Grasper
from swarm_rescue.simulation.ray_sensors.drone_lidar import DroneLidar
from swarm_rescue.simulation.ray_sensors.drone_semantic_sensor import DroneSemanticSensor
from swarm_rescue.simulation.drone.drone_sensors import DroneGPS, DroneCompass, DroneOdometer
from swarm_rescue.simulation.elements.normal_wall import NormalWall, NormalBox
from swarm_rescue.simulation.elements.physical_element import PhysicalElement
from swarm_rescue.simulation.gui_map.collision_handlers import get_colliding_entities
from swarm_rescue.simulation.gui_map.playground import Playground
from swarm_rescue.simulation.utils.constants import DRONE_INITIAL_HEALTH, RANGE_COMMUNICATION
from swarm_rescue.simulation.utils.misc_data import MiscData
from swarm_rescue.simulation.utils.timer import Timer
from swarm_rescue.simulation.utils.utils import normalize_angle


def drone_collision_wall(arbiter: pymunk.Arbiter, _, data) -> bool:
    """
    Handles collision between a drone and a wall or box.

    Args:
        arbiter (pymunk.Arbiter): The collision arbiter.
        _ : Unused.
        data: Dictionary containing the playground.

    Returns:
        bool: True to continue processing the collision.
    """
    playground: Playground = data["playground"]
    drone_base, element = get_colliding_entities(playground, arbiter)

    assert isinstance(drone_base, DroneBase)
    assert (isinstance(element, PhysicalElement)
            or isinstance(element, DroneBase))

    # CollisionTypes.DRONE
    my_drone = drone_base.agent

    if (isinstance(element, NormalWall) or
            isinstance(element, NormalBox)):
        my_drone.collide_wall()

    return True


def drone_collision_drone(arbiter: pymunk.Arbiter, _, data) -> bool:
    """
    Handles collision between two drones.

    Args:
        arbiter (pymunk.Arbiter): The collision arbiter.
        _ : Unused.
        data: Dictionary containing the playground.

    Returns:
        bool: True to continue processing the collision.
    """
    playground: Playground = data["playground"]
    drone_base, other_drone_base = get_colliding_entities(playground, arbiter)

    assert isinstance(drone_base, DroneBase)
    assert isinstance(other_drone_base, DroneBase)

    # CollisionTypes.DRONE
    my_drone = drone_base.agent

    if isinstance(other_drone_base, Agent) or isinstance(other_drone_base, DroneBase):
        my_drone.collide_drone()

    return True


class DroneAbstract(Agent):
    """
    Abstract base class for drones in the simulation.

    This class should be used as a parent class to create your own Drone classes.
    It inherits from the Agent class and provides
    functionality for controlling a drone in a simulated environment.
    It is a BaseAgent class with 3 sensors, 1 sensor of position and 2
    mandatory functions define_message() and control().

    Example Usage
        # Create a custom Drone class that inherits from DroneAbstract
        class MyDrone(DroneAbstract):
            def define_message_for_all(self):
                # Define the message to be sent to other drones
                msg_data = (self.identifier, (self.measured_gps_position(),
                self.measured_compass_angle()))
                return msg_data

            def control(self) -> CommandsDict:
                # Define the control command for the drone
                command = {"forward": 1.0, "lateral": 0.0, "rotation": -1.0,
                "grasper": 0}
                return command

        # Create an instance of the custom drone class
        drone = MyDrone()

        # Access sensor values and other functionalities
        gps_position = drone.measured_gps_position()
        lidar_values = drone.lidar()
        grasped_wounded_persons = drone.grasped_wounded_persons()

        # Control the drone
        command = drone.control()

     Attributes:
        identifier (int): The identifier of the drone.
        _should_display_lidar_graph (bool): Whether to display lidar data with matplotlib.
        size_area (tuple): The size of the area in which the drone operates.
        communicator (Communicator): The communicator object for inter-drone communication.
        _timer_collision_wall_or_drone (Timer): Timer for collision events.
        _drone_health (int): Health of the drone, reduced on collisions.
        is_inside_return_area (bool): Whether the drone is inside the return area.
        elapsed_timestep (int): Number of timesteps since the beginning.
        elapsed_walltime (float): Elapsed wall time in seconds since the beginning.
    """

    class SensorType(IntEnum):
        """
        Enumeration of sensor types for the drone.
        """
        SEMANTIC = 0
        LIDAR = auto()
        GPS = auto()
        COMPASS = auto()
        ODOMETER = auto()

    def __init__(
        self,
        identifier: Optional[int] = None,
        misc_data: Optional[MiscData] = None,
        display_lidar_graph: bool = False,
        **kwargs
    ):
        """
        Initialize the DroneAbstract.

        Args:
            identifier (Optional[int]): Unique identifier for the drone.
            misc_data (Optional[MiscData]): Miscellaneous data, including area size.
            display_lidar_graph (bool): Whether to display lidar data graphically.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(interactive=True, lateral=True, radius=10, **kwargs)

        if identifier is None:
            identifier = id(self)

        self._half_size_array = None
        self._size_area = None
        self._misc_data = misc_data
        if misc_data:
            self.size_area = misc_data.size_area

        self.add_base(DroneBase())
        self.grasper = Grasper(self.base, max_grasped=1)
        self.base.add_device(self.grasper)
        self.base.add_device(self.grasper.grasp_controller)

        self.base.add_device(DroneSemanticSensor(playground=self.playground,
                                                 invisible_elements=self.base))
        self.base.add_device(DroneLidar(invisible_elements=self.base))

        self.base.add_device(DroneGPS())
        self.base.add_device(DroneCompass())
        self.base.add_device(DroneOdometer())

        self.communicator = (
            Communicator(transmission_range=RANGE_COMMUNICATION))
        self.base.add_device(self.communicator)

        self.identifier = identifier
        self._should_display_lidar_graph = display_lidar_graph

        if self._should_display_lidar_graph:
            self._app = QApplication.instance()  # Use QApplication directly
            if self._app is None:
                self._app = QApplication([])
            self._win = pyqtgraph.GraphicsLayoutWidget(title="Lidar Measurements")
            self._win.resize(600, 400)
            self._plot = self._win.addPlot(title="Lidar measurements")
            self._plot.setLabel('left', 'Distance')
            self._plot.setLabel('bottom', 'Angle (rad)')
            self._plot.setXRange(-math.pi, math.pi)
            self._plot.setYRange(0, self.lidar().max_range)
            angles = [0] * 100  # Exemple : 100 points avec des angles à 0
            distances = [0] * 100  # Exemple : 100 points avec des distances à 0
            self._curve = self._plot.plot(angles, distances, pen='g', symbol='o')
            self._win.show()

        self._timer_collision_wall_or_drone = Timer(start_now=True)
        self._drone_health = DRONE_INITIAL_HEALTH

        self.is_inside_return_area = False

        # 'elapsed_timestep' is the number of timesteps since the beginning
        self.elapsed_timestep = 0
        # 'elapsed_walltime' is the elapsed time( in seconds) since the
        # beginning
        self.elapsed_walltime = 0

    @property
    def size_area(self) -> Optional[tuple]:
        """
        Returns the size of the area in which the drone operates.

        Returns:
            Optional[tuple]: The size of the area.
        """
        return self._size_area

    @size_area.setter
    def size_area(self, value: Optional[tuple]) -> None:
        """
        Set the size of the area in which the drone operates.

        Args:
            value (Optional[tuple]): The size of the area.
        """
        self._size_area = value
        if value is not None:
            self._half_size_array = np.array(self._size_area) / 2
        else:
            self._half_size_array = None

    @property
    def drone_health(self) -> int:
        """
        Returns the current health of the drone.

        Returns:
            int: The drone's health.
        """
        return self._drone_health

    @abstractmethod
    def define_message_for_all(self):
        """
        This function is mandatory in the class you have to create that will
        inherit from this class.
        Define the message to be sent to all nearby drones.
        For example:
            def define_message_for_all(self):
                msg_data = (self.identifier, (self.measured_gps_position(),
                self.measured_compass_angle()))
                return msg_data
        Returns:
            Any: The message to send.
        """
        pass

    @abstractmethod
    def control(self) -> CommandsDict:
        """
        This function is mandatory in the class you have to create that will
        inherit from this class.
        Define the control command for the drone.
        For example:
        command = {"forward": 1.0,
                   "lateral": 0.0,
                   "rotation": -1.0,
                   "grasper": 0}
        Returns:
            CommandsDict: Dictionary of actuator commands.
        """
        pass

    def grasped_wounded_persons(self):
        """
        Returns the wounded persons currently grasped by the drone.

        Returns:
            list: List of grasped wounded persons.
        """
        return self.grasper.grasped_wounded_persons

    def communicator_is_disabled(self) -> bool:
        """
        Returns whether the communicator of the drone is disabled.

        Returns:
            bool: True if disabled, False otherwise.
        """
        return self.communicator._disabled

    def semantic(self):
        """
        Access the semantic sensor.

        Returns:
            DroneSemanticSensor: The semantic sensor.
        """
        return self.sensors[self.SensorType.SEMANTIC]

    def lidar(self):
        """
        Access the lidar sensor.

        Returns:
            DroneLidar: The lidar sensor.
        """
        return self.sensors[self.SensorType.LIDAR]

    def gps(self):
        """
        Access the GPS sensor.

        Returns:
            DroneGPS: The GPS sensor.
        """
        return self.sensors[self.SensorType.GPS]

    def compass(self):
        """
        Access the compass sensor.

        Returns:
            DroneCompass: The compass sensor.
        """
        return self.sensors[self.SensorType.COMPASS]

    def odometer(self):
        """
        Access the odometer sensor.

        Returns:
            DroneOdometer: The odometer sensor.
        """
        return self.sensors[self.SensorType.ODOMETER]

    def semantic_is_disabled(self) -> bool:
        """
        Returns whether the semantic sensor is disabled.

        Returns:
            bool: True if disabled, False otherwise.
        """
        return self.semantic().is_disabled()

    def lidar_is_disabled(self) -> bool:
        """
        Returns whether the lidar sensor is disabled.

        Returns:
            bool: True if disabled, False otherwise.
        """
        return self.lidar().is_disabled()

    def gps_is_disabled(self) -> bool:
        """
        Returns whether the GPS sensor is disabled.

        Returns:
            bool: True if disabled, False otherwise.
        """
        return self.gps().is_disabled()

    def compass_is_disabled(self) -> bool:
        """
        Returns whether the compass sensor is disabled.

        Returns:
            bool: True if disabled, False otherwise.
        """
        return self.compass().is_disabled()

    def odometer_is_disabled(self) -> bool:
        """
        Returns whether the odometer sensor is disabled.

        Returns:
            bool: True if disabled, False otherwise.
        """
        return self.odometer().is_disabled()

    def semantic_values(self):
        """
        Get the current values from the semantic sensor.

        Returns:
            Any: Sensor values.
        """
        return self.semantic().get_sensor_values()

    def lidar_values(self):
        """
        Get the current values from the lidar sensor.

        Returns:
            Any: Sensor values.
        """
        return self.lidar().get_sensor_values()

    def lidar_rays_angles(self):
        """
        Get the angles of the lidar rays.

        Returns:
            Any: Ray angles.
        """
        return self.lidar().ray_angles

    def gps_values(self):
        """
        Get the current values from the GPS sensor.

        Returns:
            Any: Sensor values.
        """
        return self.gps().get_sensor_values()

    def compass_values(self):
        """
        Get the current values from the compass sensor.

        Returns:
            Any: Sensor values.
        """
        return self.compass().get_sensor_values()

    def odometer_values(self):
        """
        Get the current values from the odometer sensor.

        Returns:
            Any: Sensor values.
        """
        return self.odometer().get_sensor_values()

    def measured_gps_position(self) -> Union[np.ndarray, None]:
        """
        Get the measured position of the drone, in pixels. The measurement
        comes from the GPS sensor.
        You can use this value for your calculation in the control() function.
        These values can be altered by special areas in the map where the
        position information can be scrambled.
        Returns:
            Union[np.ndarray, None]: The measured position, or None if unavailable.
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
        Get the measured orientation of the drone, in radians between -Pi and
        Pi. The measurement comes from the compass sensor. You can use this
        value for your calculation in the control() function. These values can
        be altered by special areas in the map where the position information
        can be scrambled.
        Returns:
            Union[float, None]: The measured angle, or None if unavailable.
        """
        if self.compass_is_disabled():
            return None

        if self.compass_values() is not None:
            return self.compass_values()
        else:
            return None

    def measured_velocity(self) -> Union[np.ndarray, None]:
        """
        Get the measured velocity of the drone in 2D, in pixels per second.
        You must use this value for your calculation in the control() function.
        Returns:
            Union[np.ndarray, None]: The measured velocity, or None if unavailable.
        """
        odom = self.odometer_values()
        angle_compass = self.compass_values()
        if odom is not None and angle_compass is not None:
            speed = odom[0]
            alpha = odom[1]
            vx = speed * math.cos(angle_compass + alpha)
            vy = speed * math.sin(angle_compass + alpha)
            return np.array([vx, vy])
        else:
            return None

    def measured_angular_velocity(self) -> Union[float, None]:
        """
        Get the measured angular velocity of the drone, in radians per second.
        You must use this value for your calculation in the control() function.
        Returns:
            Union[float, None]: The measured angular velocity, or None if unavailable.
        """
        odometer = self.odometer_values()
        if odometer is not None:
            return odometer[2]
        else:
            return None

    @property
    def position(self):
        """
        Disabled: Use measured_gps_position() instead.
        """
        raise Exception('Function Disabled')

    @property
    def angle(self):
        """
        Disabled: Use measured_compass_angle() instead.
        """
        raise Exception('Function Disabled')

    @property
    def velocity(self):
        """
        Disabled: Use measured_velocity() instead.
        """
        raise Exception('Function Disabled')

    @property
    def angular_velocity(self):
        """
        Disabled: Use measured_angular_velocity() instead.
        """
        raise Exception('Function Disabled')

    def true_position(self) -> np.ndarray:
        """
        Get the true position of the drone, in pixels.
        You must NOT use this value for your calculation in the control()
        function, you should use measured_gps_position() instead. But you can
        use it for debugging or logging.
        Returns:
            np.ndarray: The true position.
        """
        return np.array(self.base._pm_body.position)

    def true_angle(self) -> float:
        """
        Get the true orientation of the drone, in radians between -Pi and Pi.
        You must NOT use this value for your calculation in the control()
        function, you should use measured_compass_angle() instead. But you can
        use it for debugging or logging.
        Returns:
            float: The true angle.
        """
        return normalize_angle(self.base._pm_body.angle)

    def true_velocity(self) -> np.ndarray:
        """
        Get the true velocity of the drone in 2D, in pixels per second.
        You must NOT use this value for your calculation in the
        control() function, you should use GPS, Compass or odometry data
        instead. But you can use it for debugging or logging.
        """
        return np.array(self.base._pm_body.velocity)

    def true_angular_velocity(self) -> float:
        """
        Get the true angular velocity of the drone, in radians per second.
        You must NOT use this value for your calculation in the control()
        function, you should use GPS, Compass or odometry data instead. But you
        can use it for debugging or logging.
        """
        return self.base._pm_body.angular_velocity

    def display(self) -> None:
        """
        Display lidar graph if enabled.
        """
        if self._should_display_lidar_graph:
            self.display_lidar_graph()

    def display_lidar_graph(self) -> None:
        """
        Display the lidar sensor data using matplotlib.
        """
        if self.lidar_values() is not None:
            angles = self.lidar().ray_angles
            distances = self.lidar().get_sensor_values()
            self._curve.setData(angles, distances)
            QCoreApplication.processEvents()

    def draw_gps(self) -> None:
        """
        Draw the GPS and true position of the drone on the playground.
        """

        true_pt = self.true_position()
        gps_pt = self.measured_gps_position()

        if gps_pt is not None:
            txt_gps = ("GPS: ({0:.1f}, {1:.1f})"
                       .format(gps_pt[0], gps_pt[1]))
        else:
            txt_gps = "GPS: None"
        txt_truth = ("Truth: ({0:.1f}, {1:.1f})"
                     .format(true_pt[0], true_pt[1]))

        pt = true_pt + self._half_size_array

        # Create Text objects
        gps_text = arcade.Text(txt_gps, float(pt[0]) + 10, float(pt[1]) + 10, (128, 128, 128), 10)
        truth_text = arcade.Text(txt_truth, float(pt[0]) + 10, float(pt[1]) + 25, (128, 128, 128), 10)

        # Draw the Text objects
        gps_text.draw()
        truth_text.draw()

    def draw_com(self) -> None:
        """
        Draw the communication range and links to other drones on the playground.
        """
        pt = self.true_position() + self._half_size_array

        # arcade.draw_circle_outline(pt[0], pt[1], RANGE_COMMUNICATION,
        # [128, 128, 128], 5, -1)
        # for r in range(RANGE_COMMUNICATION - 60, RANGE_COMMUNICATION, 20):
        color = [128, 128, 128]
        if self.communicator_is_disabled():
            color = [200, 200, 200]
        arcade.draw_circle_outline(float(pt[0]), float(pt[1]),
                                   RANGE_COMMUNICATION, color,
                                   1, -1)

        # in_transmission_range
        if not self.communicator_is_disabled():
            for com in self.communicator.comms_in_range:
                if not com.agent.communicator_is_disabled():
                    pt2 = com.agent.true_position() + self._half_size_array
                    arcade.draw_line(float(pt[0]), float(pt[1]),
                                     float(pt2[0]), float(pt2[1]),
                                     [128, 128, 128],
                                     2)

    def draw_bottom_layer(self) -> None:
        """
        Draw elements on the bottom layer (override as needed).
        """
        pass

    def draw_top_layer(self) -> None:
        """
        Draw elements on the top layer (override as needed).
        """
        pass

    def draw_identifier(self) -> None:
        """
        Draw the drone's identifier on the playground.
        """
        color = (64, 64, 64)
        offset = 10
        pt1 = (self.true_position() + self._half_size_array +
               np.array([offset, offset]))
        str_id = str(self.identifier)
        font_size = 10
        id_text = arcade.Text(str_id,
                              pt1[0],
                              pt1[1],
                              color,
                              font_size)
        id_text.draw()

    def collide_wall(self) -> None:
        """
        Handle collision with walls and reduce drone health.
        """
        if self._timer_collision_wall_or_drone.get_elapsed_time() > 1.0:
            self._drone_health -= 1
            self._timer_collision_wall_or_drone.restart()
            # print("Drone {} collides a wall, drone_health = {}"
            # .format(self.identifier, self._drone_health))

        if self._drone_health <= 0:
            print(f"Drone {self.identifier} destroyed, too much collision !")
            if not self.removed:
                self.grasper._release_grasping()
                self._playground.remove(self)

    def collide_drone(self) -> None:
        """
        Handle collision with other drones and reduce drone health.
        """
        if self._timer_collision_wall_or_drone.get_elapsed_time() > 1.0:
            self._drone_health -= 1
            self._timer_collision_wall_or_drone.restart()
            # print("Drone {} collides a drone, drone_health = {}"
            # .format(self.identifier,self._drone_health))

        if self._drone_health <= 0:
            print(f"Drone {self.identifier} destroyed, too much collision !")
            if not self.removed:
                self.grasper._release_grasping()
                self._playground.remove(self)

    def pre_step(self) -> None:
        """
        Prepare the drone for a new simulation step.
        """
        self.is_inside_return_area = False
        super().pre_step()
