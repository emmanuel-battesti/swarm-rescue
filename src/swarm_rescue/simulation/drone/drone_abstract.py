import math
from abc import abstractmethod
from contextlib import contextmanager
from enum import IntEnum, auto
from typing import TYPE_CHECKING, Optional, Union

import arcade
import numpy as np
import pymunk

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
from swarm_rescue.simulation.collision_handlers import get_colliding_entities
from swarm_rescue.simulation.utils.constants import (
    COLLISION_DAMAGE_COOLDOWN_STEPS,
    DEATH_BY_DAMAGE,
    DEATH_WRECK_ALPHA_HIDDEN,
    DEATH_WRECK_ALPHA_SOLID,
    DRONE_INITIAL_HEALTH,
    RANGE_COMMUNICATION,
)
from swarm_rescue.simulation.utils.misc_data import MiscData
from swarm_rescue.simulation.utils.true_state_guard import (
    # `TrueStateAccessError` is unused here but re-exported on purpose: this
    # module is where participants look for the error raised by
    # `true_position()` / `true_angle()` in their own controllers. Do not let a
    # linter drop it without adding an `__all__` entry.
    TrueStateAccessError,
    check_true_state_access,
    participant_code as _participant_code,
)
from swarm_rescue.simulation.utils.utils import normalize_angle

if TYPE_CHECKING:
    # Only used to annotate *local* variables inside the collision handlers,
    # which are never evaluated at runtime (PEP 526). Importing the
    # presentation package eagerly would make the model depend on it for
    # nothing. See the same note in elements/rescue_center.py.
    from swarm_rescue.simulation.gui_map.playground import Playground


# Public surface of this module.
#
# `TrueStateAccessError` is exported on purpose: it is the error participants
# see when their controller reads `true_position()`, and their own code has to
# be able to name it. A linter must not drop it.
__all__ = [
    "DroneAbstract",
    "TrueStateAccessError",
    "drone_collision_wall",
    "drone_collision_drone",
    "PARTICIPANT_API",
]


# The API a participant is meant to use, and the only one that stays
# supported. Everything else reachable on a drone -- `draw_gps`,
# `collide_wall`, `pre_step`, ... -- is internal plumbing that a solution has
# no reason to call, and that this class is free to change.
#
# Why write it down instead of relying on the leading underscore? Because most
# of the internal members do *not* have one: `Playground` calls `pre_step()`,
# `collide_wall()` and `display()` on every drone it holds, so they cannot be
# renamed without touching the framework. The convention alone therefore says
# nothing about what is contract.
#
# Class members and instance attributes live in the same set on purpose: from a
# participant's point of view there is no difference between `self.drone_health`
# and `self.identifier`, and splitting them into two lists only gave two places
# to forget. Some names here are defined on the class, the rest are assigned in
# `__init__`, so the existence test checks the class first and falls back to a
# live instance.
#
# `tests/test_participant_api.py` checks that every name listed here exists and
# is public, and that the set does not drift silently.
PARTICIPANT_API = frozenset({
    # --- to be implemented by the participant ---
    "control",
    "define_message_for_all",
    # --- sensor accessors ---
    "semantic",
    "lidar",
    "gps",
    "compass",
    "odometer",
    "semantic_values",
    "lidar_values",
    "lidar_rays_angles",
    "gps_values",
    "compass_values",
    "odometer_values",
    # --- measurements (noisy, this is what a controller should read) ---
    "measured_gps_position",
    "measured_compass_angle",
    "measured_velocity",
    "measured_angular_velocity",
    # --- state a controller may reasonably read ---
    "drone_health",
    "size_area",
    # --- disabling zones ---
    "semantic_is_disabled",
    "lidar_is_disabled",
    "gps_is_disabled",
    "compass_is_disabled",
    "odometer_is_disabled",
    "communicator_is_disabled",
    # --- grasping ---
    "grasped_wounded_persons",
    "grasper",
    # --- communication ---
    "communicators",
    "communicator",
    # --- instance attributes assigned in __init__ ---
    "identifier",
    "elapsed_timestep",
    "elapsed_walltime",
    # --- debug helpers, documented in the README ---
    "display",
    "display_lidar_graph",
})


def drone_collision_wall(arbiter: pymunk.Arbiter, _, data) -> bool:
    """
    Handle a collision between a drone and a wall or box.

    Args:
        arbiter (pymunk.Arbiter): The collision arbiter.
        _: Unused.
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
    assert isinstance(my_drone, DroneAbstract)

    if (isinstance(element, NormalWall) or
            isinstance(element, NormalBox)):
        my_drone.collide_wall()

    return True


def drone_collision_drone(arbiter: pymunk.Arbiter, _, data) -> bool:
    """
    Handle a collision between two drones.

    Args:
        arbiter (pymunk.Arbiter): The collision arbiter.
        _: Unused.
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
    assert isinstance(my_drone, DroneAbstract)

    if isinstance(other_drone_base, Agent) or isinstance(other_drone_base, DroneBase):
        my_drone.collide_drone()

    return True


class DroneAbstract(Agent):
    """
    Abstract base class for drones in the simulation.

    Subclass this class to implement your own Drone. It inherits from Agent
    and provides the functionality required to control a drone in a simulated
    environment. It is a BaseAgent with three sensors, one position sensor,
    and two mandatory methods: define_message_for_all() and control().

    Example usage:
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

        # Instantiate the custom drone
        drone = MyDrone()

        # Access sensor values and other functionality
        gps_position = drone.measured_gps_position()
        lidar_values = drone.lidar()
        grasped_wounded_persons = drone.grasped_wounded_persons()

        # Control the drone
        command = drone.control()

    Attributes:
        identifier (int): The identifier of the drone.
        _should_display_lidar_graph (bool): Whether to display lidar data with matplotlib.
        size_area (tuple): The size of the area in which the drone operates.
        communicator (Communicator): The communicator used for inter-drone communication.
        _steps_since_last_damage (int): Steps elapsed since the last collision
            damage. Throttles the collision damages, in steps and not in seconds
            of real time.
        _drone_health (int): Health of the drone, reduced on collisions.
        is_inside_return_area (bool): Whether the drone is inside the return area.
        elapsed_timestep (int): Number of timesteps since the beginning.
        elapsed_walltime (float): Elapsed wall time in seconds since the beginning.
    """

    class SensorType(IntEnum):
        """
        Enumeration of the drone's sensor types.
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
            misc_data (Optional[MiscData]): Miscellaneous data, including the area size.
            display_lidar_graph (bool): Whether to display lidar data graphically.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(interactive=True, lateral=True, radius=10, **kwargs)

        if identifier is None:
            identifier = id(self)

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
            # Lazy and tolerant imports: avoid ImportError on CI (no EGL)
            try:
                from PySide6.QtWidgets import QApplication
                from PySide6.QtCore import QCoreApplication
                import pyqtgraph

                # Store the QCoreApplication class for later use in display_lidar_graph
                self._QCoreApplication = QCoreApplication

                self._app = QApplication.instance()
                if self._app is None:
                    self._app = QApplication([])
                self._win = pyqtgraph.GraphicsLayoutWidget(title="Lidar Measurements")
                self._win.resize(600, 400)
                self._plot = self._win.addPlot(title="Lidar measurements")
                self._plot.setLabel('left', 'Distance')
                self._plot.setLabel('bottom', 'Angle (rad)')
                self._plot.setXRange(-math.pi, math.pi)
                self._plot.setYRange(0, self.lidar().max_range)
                angles = [0] * 100
                distances = [0] * 100
                self._curve = self._plot.plot(angles, distances, pen='g', symbol='o')
                self._win.show()
            except Exception:
                # Graphical environment unavailable; degrade gracefully
                self._app = None
                self._win = None
                self._plot = None
                self._curve = None
                self._QCoreApplication = None

        # Steps elapsed since the last collision damage. This counter is driven
        # by the simulation steps (see `pre_step`), never by the wall clock, so
        # that a drone takes the same damage for the same trajectory whether the
        # run is windowed, headless, fast or slow.
        self._steps_since_last_damage = 0
        self._drone_health = DRONE_INITIAL_HEALTH

        # Why the drone died, and when. None means it is alive.
        self._death_cause: Optional[str] = None
        self._death_timestep: int = -1

        self.is_inside_return_area = False

        # 'elapsed_timestep' is the number of timesteps since the beginning
        self.elapsed_timestep = 0
        # 'elapsed_walltime' is the elapsed time (in seconds) since the beginning
        self.elapsed_walltime = 0

    @property
    def size_area(self) -> Optional[tuple]:
        """
        Return the size of the area in which the drone operates.

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

    @property
    def drone_health(self) -> int:
        """
        Return the current health of the drone.

        Returns:
            int: The drone's health.
        """
        return self._drone_health

    @property
    def is_dead(self) -> bool:
        """
        Whether this drone is destroyed.

        A dead drone stays on the map: its wreck remains where it fell and is
        still drawn after the explosion.

        Returns:
            bool: True if the drone is dead.
        """
        return self._death_cause is not None

    @property
    def death_cause(self) -> Optional[str]:
        """
        Why the drone died: `DEATH_BY_DAMAGE`, `DEATH_BY_KILL_ZONE`, or None.

        The cause is not cosmetic. A drone that ran out of health is a wreck
        that lies in nobody's way and that the sensors no longer see, while a
        drone caught by a kill zone keeps blocking and stays in their image.

        Returns:
            Optional[str]: The cause of death, or None if it is alive.
        """
        return self._death_cause

    @property
    def death_timestep(self) -> int:
        """
        The step at which the drone died, or -1 while it is alive.

        Returns:
            int: The step of death.
        """
        return self._death_timestep

    def die(self, cause: str) -> None:
        """
        Destroy the drone, and apply what that cause means physically.

        Args:
            cause (str): `DEATH_BY_DAMAGE` or `DEATH_BY_KILL_ZONE`.
        """
        if self.is_dead:
            return

        self._death_cause = cause
        self._death_timestep = self.elapsed_timestep

        # How opaque the wreck is drawn follows the cause: a wreck the sensors
        # cannot see is drawn see-through, one they can still see stays solid.
        wreck_alpha = (DEATH_WRECK_ALPHA_HIDDEN if cause == DEATH_BY_DAMAGE
                       else DEATH_WRECK_ALPHA_SOLID)
        self.base.start_death_animation(wreck_alpha)

        # A drone out of health has fallen where it is: it is not in the
        # way, and the others do not see it. A drone caught by a kill
        # zone keeps its body in the physical space and stays in the sensors'
        # image, so neither call below is made for it.
        if cause == DEATH_BY_DAMAGE:
            playground = self._playground
            assert playground is not None
            playground.make_passable(self)
            playground.hide_from_sensors(self)

    @abstractmethod
    def define_message_for_all(self):
        """
        Mandatory method to be implemented in any subclass of this class.

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
        Mandatory method to be implemented in any subclass of this class.

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
        Return the wounded persons currently grasped by the drone.

        Returns:
            list: List of grasped wounded persons.
        """
        return self.grasper.grasped_wounded_persons

    def communicator_is_disabled(self) -> bool:
        """
        Return whether the drone's communicator is disabled.

        `True` when a No Com Zone switched it off for the current step, and also
        when the drone is destroyed. This is the meaning the API gives the call
        -- "no messages sent or received" -- and it is what `draw_com()` reads to
        decide whether to draw links, so a wreck must report `True` here or it
        would still be shown talking to the drones that are still alive.

        The per-step `_disabled` flag alone is not enough: a drone destroyed by
        damage is taken out of the space (see `die`), so no disabling zone keeps
        touching its communicator and the flag goes back to `False` on the next
        `pre_step`. `is_switched_off` is the flag that covers both reasons.

        Returns:
            bool: True if disabled or the drone is destroyed, False otherwise.
        """
        return self.communicator.is_switched_off

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
        Return whether the semantic sensor is disabled.

        Returns:
            bool: True if disabled, False otherwise.
        """
        return self.semantic().is_disabled()

    def lidar_is_disabled(self) -> bool:
        """
        Return whether the lidar sensor is disabled.

        Returns:
            bool: True if disabled, False otherwise.
        """
        return self.lidar().is_disabled()

    def gps_is_disabled(self) -> bool:
        """
        Return whether the GPS sensor is disabled.

        Returns:
            bool: True if disabled, False otherwise.
        """
        return self.gps().is_disabled()

    def compass_is_disabled(self) -> bool:
        """
        Return whether the compass sensor is disabled.

        Returns:
            bool: True if disabled, False otherwise.
        """
        return self.compass().is_disabled()

    def odometer_is_disabled(self) -> bool:
        """
        Return whether the odometer sensor is disabled.

        Returns:
            bool: True if disabled, False otherwise.
        """
        return self.odometer().is_disabled()

    def semantic_values(self):
        """
        Return the current values from the semantic sensor.

        Returns:
            Any: Sensor values.
        """
        return self.semantic().get_sensor_values()

    def lidar_values(self):
        """
        Return the current values from the lidar sensor.

        Returns:
            Any: Sensor values.
        """
        return self.lidar().get_sensor_values()

    def lidar_rays_angles(self):
        """
        Return the angles of the lidar rays.

        Returns:
            Any: Ray angles.
        """
        return self.lidar().ray_angles

    def gps_values(self):
        """
        Return the current values from the GPS sensor.

        Returns:
            Any: Sensor values.
        """
        return self.gps().get_sensor_values()

    def compass_values(self):
        """
        Return the current values from the compass sensor.

        Returns:
            Any: Sensor values.
        """
        return self.compass().get_sensor_values()

    def odometer_values(self):
        """
        Return the current values from the odometer sensor.

        Returns:
            Any: Sensor values.
        """
        return self.odometer().get_sensor_values()

    def measured_gps_position(self) -> Union[np.ndarray, None]:
        """
        Return the measured position of the drone, in pixels, as provided by
        the GPS sensor.

        This value may be used for calculations inside the control() function.
        Note that it can be altered by special areas of the map where position
        information is scrambled.

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
        Return the measured orientation of the drone, in radians within the
        range [-Pi, Pi], as provided by the compass sensor.

        This value may be used for calculations inside the control() function.
        Note that it can be altered by special areas of the map where position
        information is scrambled.

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
        Return the measured 2D velocity of the drone, in pixels per simulation
        step.

        The velocity is computed from the odometer values and the compass
        angle. This value must be used for calculations inside the control()
        function.

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
        Get the measured angular velocity of the drone, in radians per
        simulation step.
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
        Disabled: use measured_gps_position() instead.

        Raises:
            AttributeError: always. This property exists only to turn a stale
                ground-truth read into a loud failure instead of a silent
                cheat; the replacement accessor is named in the message.
        """
        raise AttributeError(
            "self.position is disabled: it would return the exact ground "
            "truth. Use self.measured_gps_position() instead."
        )

    @property
    def angle(self):
        """
        Disabled: use measured_compass_angle() instead.

        Raises:
            AttributeError: always. See `position`.
        """
        raise AttributeError(
            "self.angle is disabled: it would return the exact ground truth. "
            "Use self.measured_compass_angle() instead."
        )

    @property
    def velocity(self):
        """
        Disabled: use measured_velocity() instead.

        Raises:
            AttributeError: always. See `position`.
        """
        raise AttributeError(
            "self.velocity is disabled: it would return the exact ground "
            "truth. Use self.measured_velocity() instead."
        )

    @property
    def angular_velocity(self):
        """
        Disabled: use measured_angular_velocity() instead.

        Raises:
            AttributeError: always. See `position`.
        """
        raise AttributeError(
            "self.angular_velocity is disabled: it would return the exact "
            "ground truth. Use self.measured_angular_velocity() instead."
        )

    @contextmanager
    def participant_code(self):
        """
        Mark the enclosed block as participants' controller code.

        Convenience wrapper around
        swarm_rescue.simulation.utils.true_state_guard.participant_code, so
        that a single drone can guard its own controller. The guard is
        simulation-wide, so wrapping the whole loop instead is equivalent and
        covers the wounded persons the controllers can reach too.

        Yields:
            None.
        Raises:
            TrueStateAccessError: If a ground-truth accessor is called inside.
        """
        with _participant_code():
            yield

    def true_position(self) -> np.ndarray:
        """
        Get the true position of the drone, in pixels.
        You must NOT use this value for your calculation in the control()
        function, you should use measured_gps_position() instead. But you can
        use it for debugging or logging.
        Calling it from control() or define_message_for_all() raises
        TrueStateAccessError.
        Returns:
            np.ndarray: The true position.
        """
        check_true_state_access("true_position", "measured_gps_position()")
        return np.array(self.base._pm_body.position)

    def true_angle(self) -> float:
        """
        Get the true orientation of the drone, in radians between -Pi and Pi.
        You must NOT use this value for your calculation in the control()
        function, you should use measured_compass_angle() instead. But you can
        use it for debugging or logging.
        Calling it from control() or define_message_for_all() raises
        TrueStateAccessError.
        Returns:
            float: The true angle.
        """
        check_true_state_access("true_angle", "measured_compass_angle()")
        return float(normalize_angle(self.base._pm_body.angle))

    def true_velocity(self) -> np.ndarray:
        """
        Get the true velocity of the drone in 2D, in pixels per simulation step.
        You must NOT use this value for your calculation in the
        control() function, you should use GPS, Compass or odometry data
        instead. But you can use it for debugging or logging.
        Calling it from control() or define_message_for_all() raises
        TrueStateAccessError.
        """
        check_true_state_access("true_velocity", "the odometry")
        return np.array(self.base._pm_body.velocity)

    def true_angular_velocity(self) -> float:
        """
        Get the true angular velocity of the drone, in radians per simulation
        step.
        You must NOT use this value for your calculation in the control()
        function, you should use GPS, Compass or odometry data instead. But you
        can use it for debugging or logging.
        Calling it from control() or define_message_for_all() raises
        TrueStateAccessError.
        """
        check_true_state_access(
            "true_angular_velocity", "measured_angular_velocity()"
        )
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
        if self.lidar_values() is not None and getattr(self, '_curve', None) is not None:
            angles = self.lidar().ray_angles
            distances = self.lidar().get_sensor_values()
            self._curve.setData(angles, distances)
            # Only call processEvents if QCoreApplication was successfully imported
            if getattr(self, '_QCoreApplication', None) is not None:
                try:
                    self._QCoreApplication.processEvents()
                except Exception:
                    # Best-effort: ignore if processing events fails
                    pass

    def draw_gps(self) -> None:
        """
        Draw the GPS position and the true position of the drone on the
        playground.
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

        pt = true_pt

        # Create Text objects
        gps_text = arcade.Text(txt_gps, float(pt[0]) + 10, float(pt[1]) + 10, (128, 128, 128), 10)
        truth_text = arcade.Text(txt_truth, float(pt[0]) + 10, float(pt[1]) + 25, (128, 128, 128), 10)

        # Draw the Text objects
        gps_text.draw()
        truth_text.draw()

    def draw_com(self) -> None:
        """
        Draw the communication range and the links to other drones on the
        playground.
        """
        pt = self.true_position()

        color = (128, 128, 128)
        if self.communicator_is_disabled():
            color = (200, 200, 200)
        arcade.draw_circle_outline(
            center_x=float(pt[0]),
            center_y=float(pt[1]),
            radius=RANGE_COMMUNICATION,
            color=color,
            border_width=1,
            num_segments=-1,
        )

        # in_transmission_range
        if not self.communicator_is_disabled():
            for com in self.communicator.comms_in_range:
                if not com.agent.communicator_is_disabled():
                    pt2 = com.agent.true_position()
                    arcade.draw_line(
                        start_x=float(pt[0]),
                        start_y=float(pt[1]),
                        end_x=float(pt2[0]),
                        end_y=float(pt2[1]),
                        color=(128, 128, 128),
                        line_width=2,
                    )

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
        pt1 = (self.true_position() + np.array([offset, offset]))
        str_id = str(self.identifier)
        font_size = 10
        id_text = arcade.Text(
            text=str_id,
            x=float(pt1[0]),
            y=float(pt1[1]),
            color=color,
            font_size=font_size,
        )
        id_text.draw()

    def _apply_collision_damage(self) -> None:
        """
        Remove one health point, at most once per
        `COLLISION_DAMAGE_COOLDOWN_STEPS` steps, and destroy the drone if it
        reaches zero.

        The cooldown is counted in simulation steps, not in seconds of real
        time, so the damage a drone takes depends only on its trajectory and
        not on how fast the machine runs the simulation.

        One single cooldown is shared by `collide_wall` and `collide_drone`, so
        that bouncing between a wall and another drone costs the drone a single
        health point per cooldown.
        """
        if self._steps_since_last_damage < COLLISION_DAMAGE_COOLDOWN_STEPS:
            return

        self._steps_since_last_damage = 0
        self._drone_health -= 1

        if self._drone_health <= 0:
            # The drone stays on the map as a wreck: passable, and out of the
            # sensors' image. See `die`.
            self.die(DEATH_BY_DAMAGE)

    def collide_wall(self) -> None:
        """
        Handle a collision with a wall and reduce the drone's health.
        """
        self._apply_collision_damage()

    def collide_drone(self) -> None:
        """
        Handle a collision with another drone and reduce the drone's health.
        """
        self._apply_collision_damage()

    def reset(self) -> None:
        """
        Reset the drone to its initial state, restoring full health so that a
        previously destroyed drone can operate normally again.
        """
        super().reset()
        self._drone_health = DRONE_INITIAL_HEALTH
        self._steps_since_last_damage = 0
        # Alive again, and able to collide and to be seen: the consequences of
        # the death are undone with it.
        self._death_cause = None
        self._death_timestep = -1
        self.base.reset_death_animation()
        playground = self._playground
        assert playground is not None
        playground.restore_collision_and_sensors(self)

    def pre_step(self) -> None:
        """
        Prepare the drone for a new simulation step.
        """
        self.is_inside_return_area = False
        # Advances the collision damage cooldown. `SimulationStepper` calls this
        # on every agent once per step, before the physics, which is what makes
        # the counter a step counter.
        self._steps_since_last_damage += 1
        super().pre_step()
