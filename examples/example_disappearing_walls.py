"""
Example demonstrating disappearing walls.

This example shows how to create walls that disappear after a specified time,
allowing drones to pass through where the walls were.
"""
import math
import sys
import pathlib

from swarm_rescue.simulation.utils.utils import normalize_angle

# Insert the parent directory of the current file's directory into sys.path.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from typing import List, Type
from swarm_rescue.simulation.elements.disappearing_wall import DisappearingWall, DisappearingBox
from swarm_rescue.simulation.elements.rescue_center import RescueCenter
from swarm_rescue.simulation.elements.wounded_person import WoundedPerson
from swarm_rescue.simulation.gui_map.gui_sr import GuiSR
from swarm_rescue.simulation.gui_map.closed_playground import ClosedPlayground
from swarm_rescue.simulation.gui_map.map_abstract import MapAbstract
from swarm_rescue.simulation.drone.drone_abstract import DroneAbstract
from swarm_rescue.simulation.drone.controller import CommandsDict
from swarm_rescue.simulation.utils.misc_data import MiscData
import random


class MyDroneRandom(DroneAbstract):
    """Simple random drone for demonstration purposes."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.counterStraight = 0
        self.angleStopTurning = random.uniform(-math.pi, math.pi)
        self.counterStopStraight = random.uniform(10, 100)
        self.isTurningLeft = False
        self.isTurningRight = False

    def define_message_for_all(self):
        pass

    def control(self) -> CommandsDict:
        """
        The Drone will move forward and turn for a random angle when an
        obstacle is hit
        """
        command_straight = {"forward": 1.0,
                            "rotation": 0.0}
        command_turn_left = {"forward": 0.0,
                             "rotation": 1.0}
        command_turn_right = {"forward": 0.0,
                              "rotation": -1.0}

        self.counterStraight += 1

        if (not self._is_turning() and
                self.counterStraight > self.counterStopStraight):
            self.angleStopTurning = random.uniform(-math.pi, math.pi)
            diff_angle = normalize_angle(self.angleStopTurning -
                                         self.measured_compass_angle())
            if diff_angle > 0:
                self.isTurningLeft = True
            else:
                self.isTurningRight = True

        diff_angle = normalize_angle(self.angleStopTurning -
                                     self.measured_compass_angle())
        if self._is_turning() and abs(diff_angle) < 0.2:
            self.isTurningLeft = False
            self.isTurningRight = False
            self.counterStraight = 0
            self.counterStopStraight = random.uniform(10, 100)

        if self.isTurningLeft:
            return command_turn_left
        elif self.isTurningRight:
            return command_turn_right
        else:
            return command_straight

    def _is_turning(self):
        return self.isTurningLeft or self.isTurningRight


class MapWithOpeningDoors(MapAbstract):
    """
    A custom map with fixed walls and doors that open progressively.

    The map starts with separate rooms and corridors blocked by doors. As time progresses,
    doors disappear at regular intervals, allowing drones to access new areas with wounded persons.
    This creates a dynamic environment where exploration possibilities expand over time as new
    zones become accessible.
    """

    def __init__(self, drone_type: Type[DroneAbstract], zones_config=()):
        """Initialize the grid map with disappearing walls."""
        super().__init__(drone_type, zones_config)

        # Map parameters
        self._size_area = (800, 500)
        self._number_drones = 4
        self._max_timestep_limit = 1800  # 1 minute at 30 FPS
        self._max_walltime_limit = 60    # 1 minute

        # Create playground
        self._playground = ClosedPlayground(size=self._size_area)

        # Create rescue center and return area
        self._rescue_center = RescueCenter(size=(80, 60))
        self._rescue_center_pos = ((0, 0), 0)
        self._playground.add(self._rescue_center, self._rescue_center_pos)

        # Add wounded persons in areas that become accessible when doors open
        self._wounded_persons_pos = [
            (-300, 0),     # Left room (accessible after left door opens at 150 timesteps)
            (300, 0),      # Right room (accessible after right door opens at 300 timesteps)
            (0, 180),      # Top corridor (accessible after top door opens at 450 timesteps)
            (0, -180),     # Bottom corridor (accessible after bottom door opens at 600 timesteps)
        ]
        self._number_wounded_persons = len(self._wounded_persons_pos)
        self._wounded_persons: List[WoundedPerson] = []

        for i, pos in enumerate(self._wounded_persons_pos):
            wounded_person = WoundedPerson(rescue_center=self._rescue_center)
            self._wounded_persons.append(wounded_person)
            self._playground.add(wounded_person, (pos, 0))

        # Create walls with doors that open progressively
        self._create_walls_with_doors()

        # Create drones
        self._drones_pos = [
            ((0, 0), 0), ((-50, -50), 1.57), ((50, 50), -1.57), ((-50, 50), -3.14)
        ]
        self._drones: List[DroneAbstract] = []

        misc_data = MiscData(
            size_area=self._size_area,
            number_drones=self._number_drones,
            max_timestep_limit=self._max_timestep_limit,
            max_walltime_limit=self._max_walltime_limit
        )

        for i in range(self._number_drones):
            drone = drone_type(identifier=i, misc_data=misc_data)
            self._drones.append(drone)
            self._playground.add(drone, self._drones_pos[i])

    def _create_walls_with_doors(self):
        """Create large fixed walls with doors that open progressively."""
        # Create the main wall structure
        self._add_main_walls()

        # Add doors that open at different times
        self._add_doors(thickness=10)


    def _add_main_walls(self):
        """Add the main permanent walls with gaps for doors."""
        from swarm_rescue.simulation.elements.normal_wall import NormalWall

        # Left room walls - vertical wall with gap for door at center
        wall_left_vertical_top = NormalWall(
            pos_start=(-200, 50),
            pos_end=(-200, 250)
        )
        self._playground.add(wall_left_vertical_top, wall_left_vertical_top.wall_coordinates)

        wall_left_vertical_bottom = NormalWall(
            pos_start=(-200, -250),
            pos_end=(-200, -50)
        )
        self._playground.add(wall_left_vertical_bottom, wall_left_vertical_bottom.wall_coordinates)

        wall_left_top = NormalWall(
            pos_start=(-400, 250),
            pos_end=(-200, 250)
        )
        self._playground.add(wall_left_top, wall_left_top.wall_coordinates)

        wall_left_bottom = NormalWall(
            pos_start=(-400, -250),
            pos_end=(-200, -250)
        )
        self._playground.add(wall_left_bottom, wall_left_bottom.wall_coordinates)

        # Right room walls - vertical wall with gap for door at center
        wall_right_vertical_top = NormalWall(
            pos_start=(200, 50),
            pos_end=(200, 250)
        )
        self._playground.add(wall_right_vertical_top, wall_right_vertical_top.wall_coordinates)

        wall_right_vertical_bottom = NormalWall(
            pos_start=(200, -250),
            pos_end=(200, -50)
        )
        self._playground.add(wall_right_vertical_bottom, wall_right_vertical_bottom.wall_coordinates)

        wall_right_top = NormalWall(
            pos_start=(200, 250),
            pos_end=(400, 250)
        )
        self._playground.add(wall_right_top, wall_right_top.wall_coordinates)

        wall_right_bottom = NormalWall(
            pos_start=(200, -250),
            pos_end=(400, -250)
        )
        self._playground.add(wall_right_bottom, wall_right_bottom.wall_coordinates)

        # Top corridor walls - horizontal wall with even wider gap for door at center
        wall_top_left = NormalWall(
            pos_start=(-400, 100),
            pos_end=(-100, 100)
        )
        self._playground.add(wall_top_left, wall_top_left.wall_coordinates)

        wall_top_right = NormalWall(
            pos_start=(100, 100),
            pos_end=(400, 100)
        )
        self._playground.add(wall_top_right, wall_top_right.wall_coordinates)

        # Bottom corridor walls - horizontal wall with even wider gap for door at center
        wall_bottom_left = NormalWall(
            pos_start=(-400, -100),
            pos_end=(-100, -100)
        )
        self._playground.add(wall_bottom_left, wall_bottom_left.wall_coordinates)

        wall_bottom_right = NormalWall(
            pos_start=(100, -100),
            pos_end=(400, -100)
        )
        self._playground.add(wall_bottom_right, wall_bottom_right.wall_coordinates)

    def _add_doors(self, thickness):
        """Add doors (disappearing walls) that open access to enclosed areas."""

        # Door 1: Left room access (opens after 150 timesteps)
        # This door is part of the left wall, when it disappears, drones can enter left room
        door1 = DisappearingWall(
            pos_start=(-200, -50),
            pos_end=(-200, 50),
            disappear_after_timesteps=150,
            wall_thickness=thickness
        )
        self._playground.add(door1, door1.wall_coordinates)

        # Door 2: Right room access (opens after 300 timesteps)
        # This door is part of the right wall, when it disappears, drones can enter right room
        door2 = DisappearingWall(
            pos_start=(200, -50),
            pos_end=(200, 50),
            disappear_after_timesteps=300,
            wall_thickness=thickness
        )
        self._playground.add(door2, door2.wall_coordinates)

        # Door 3: Top corridor access (opens after 450 timesteps)
        # This door is part of the top wall, when it disappears, drones can enter top corridor
        door3 = DisappearingWall(
            pos_start=(-100, 100),
            pos_end=(100, 100),
            disappear_after_timesteps=450,
            wall_thickness=thickness
        )
        self._playground.add(door3, door3.wall_coordinates)

        # Door 4: Bottom corridor access (opens after 600 timesteps)
        # This door is part of the bottom wall, when it disappears, drones can enter bottom corridor
        door4 = DisappearingWall(
            pos_start=(-100, -100),
            pos_end=(100, -100),
            disappear_after_timesteps=600,
            wall_thickness=thickness
        )
        self._playground.add(door4, door4.wall_coordinates)



def main():
    """
    Main function to run the example with doors that open progressively.

    Watch as doors open in the fixed walls over time:
    - After 150 timesteps: Left wall door opens (access to left room)
    - After 300 timesteps: Right wall door opens (access to right room)
    - After 450 timesteps: Top wall door opens (access to top corridor)
    - After 600 timesteps: Bottom wall door opens (access to bottom corridor)

    Large permanent walls create separate rooms and corridors. Doors open
    progressively to allow drones to access new areas and rescue wounded persons.
    The mission is complete when all 4 wounded persons are brought to the rescue center.
    """
    print("Starting Door Opening Demo")
    print("Timeline:")
    print("   150 timesteps: Left door opens")
    print("   300 timesteps: Right door opens")
    print("   450 timesteps: Top door opens")
    print("   600 timesteps: Bottom door opens")
    print("Mission: Navigate through opening doors to rescue 4 wounded persons!")
    print()

    # Create the map with opening doors
    my_map = MapWithOpeningDoors(drone_type=MyDroneRandom)

    # Create the GUI directly with the map
    gui = GuiSR(the_map=my_map)

    # Run the simulation
    gui.run()

    print("Simulation completed!")
    print(f"Final score: {my_map.compute_score_health_returned()}")


if __name__ == '__main__':
    main()

