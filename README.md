# Table of Content

- [Welcome to *Swarm-Rescue*](#welcome-to-swarm-rescue)
- [The Competition](#the-competition)
- [Simulation Environment](#simulation-environment)
- [Installation](#installation)
- [Elements of the environment](#elements-of-the-environment)
- [Programming Your Drones](#programming-your-drones)
- [Contact](#contact)

# Welcome to *Swarm-Rescue*

With this project, you will try to save human lives, in simulation... Teach a swarm of drones how to behave to save a maximum of injured people in a minimum of time!

Your job will be to develop your own drone controller. In the competition, each participating team will be evaluated on new, unknown maps. The winner will be determined by a scoring system based on multiple criteria: rescue speed, exploration efficiency, number of injured people saved, remaining health of the drones, and more.

*Swarm-Rescue* is the environment that simulates the drones and that describes the maps used, the drones and the different elements of the map.

[Access to the GitHub repository *Swarm-Rescue*](https://github.com/emmanuel-battesti/swarm-rescue) • [Website](https://emmanuel-battesti.github.io/swarm-rescue-website/) • [Changelog](https://github.com/emmanuel-battesti/swarm-rescue/blob/main/CHANGELOG.md)

The Challenge requires only basic knowledge of *Python* and emphasizes creativity, problem-solving, and algorithmic thinking. Success depends more on innovative approaches to swarm coordination than on advanced programming skills.

# The Competition

## Mission

The objective is simple: explore an unknown area (like the basement of a collapsed building), detect injured people, and guide them to the rescue center.

Each team has a fleet of 10 drones, equipped with sensors and communication devices. Your role is to **program the intelligence of these drones to make them 100% autonomous** by programming them in *Python*.

They will need to collaborate, manage failures, communication losses, and unforeseen events to successfully complete their mission. All development is done **exclusively within this simulation environment**, with maps of increasing complexity.

The final evaluation will be done on several unknown maps designed by the organizers and not available to the contestants. Every proposition will be tested on a same computer and a score related to the performance will be computed.

## Scoring

Depending on the scenario evolution before the final evaluation, the score calculation may be slightly modified.

A mission ends when:
- The maximum simulation timestep is reached (*max timestep limit*).
- The maximum real-world execution time is exceeded (*max walltime limit*, typically 2 to 5 minutes).
When one of the two limits is reached, the game is over. If your algorithm is fast, you will reach the "max timestep limit" first. If your algorithm is too slow, you will reach the "max walltime limit" before the "max timestep limit".

Your score will be calculated based on:
- **✅ Rescued People:** The percentage of injured people brought back to the rescue center.
- **🗺️ Exploration:** The percentage of the map explored.
- **❤️ Drone Health:** The percentage of health points remaining for your drones at the end of the mission.
- **⏱️ Efficiency:** The time remaining if all people are rescued and all the map is explored.

# Simulation Environment

Swarm-Rescue is built on a modified code of the 2D simulation library [**Simple-Playgrounds**](https://github.com/mgarciaortiz/simple-playgrounds) (SPG), which uses the **Pymunk** physics engine and the **Arcade** game engine.

In practical terms, this means:
- Drones and objects have mass and inertia (they don't stop instantly).
- Collisions are handled by the physics engine.
- The simulator manages a perception-action-communication loop at each time step.

# Installation

For installation instructions, please refer to the [`INSTALL.md`](INSTALL.md) file.

# Elements of the environment

## Drones

Drones are a type of **agent** in *Simple-Playgrounds*.
Drones are composed of different body parts attached to a *Base*.

Drones **perceive their surroundings** through two first-person view sensors:
- *Lidar* sensor
- *Semantic* sensor

Drones also have a communication system.

Drones are equipped with sensors that allow them to **estimate their position and orientation**. We have two kinds:
- with absolute measurements: the *GPS* for positions and the magnetic *compass* for orientation.
- with relative measurements: the *odometer* which provides positions and orientation relative to the previous position of the drone.

They are also equipped with life points (or health) that decrease with each collision with the environment or other drones, leading to destruction when reaching zero. When a drone is destroyed, it disappears from the map.
The drone has access to this value with its data attribute *drone_health*.

### Lidar sensor

In the file `src/swarm_rescue/simulation/ray_sensors/drone_lidar.py`, class *DroneLidar*.

It emulates a lidar sensor with the following specifications:

- *fov* (field of view): 360 degrees
- *resolution* (number of rays): 181
- *max range* (maximum range of the sensor): 300 pixels

Gaussian noise has been added to the distance measurements to simulate real-world conditions.
As the *field of view* (fov) is 360°, the first value (at -Pi rad) and the last value (at Pi) should be the same.

You can find an example of lidar use in the `src/swarm_rescue/solutions/my_drone_lidar_communication.py` file.

To visualize lidar sensor data, you need to set the parameter *draw_lidar_rays* of the *GuiSR* class to *True*.

### Semantic sensor

In the file `src/swarm_rescue/simulation/ray_sensors/drone_semantic_sensor.py`, it is described in the class *DroneSemanticSensor*.

The semantic sensor allows to determine the nature of an object, without data processing, around the drone.

- *fov* (field of view): 360 degrees
- *max range* (maximum range of the sensor): 200 pixels
- *resolution*, number of rays evenly spaced across the field of view: 35

As the *fov* is 360°, the first (at -Pi rad) and the last value (at Pi) should be the same.

You can find an example of semantic sensor use in the `examples/example_semantic_sensor.py` file.

For this competition, the semantic sensor can only detect *WoundedPerson*, *RescueCenter* and other *Drones*, but NOT *Walls* (use Lidar for wall detection and avoidance).

Each sensor ray provides a data object with these properties:
- *data.distance*: Distance to the nearest object detected
- *data.angle*: Angle of the ray in radians
- *data.entity_type*: Type of the detected object (WoundedPerson, RescueCenter, Drone)
- *data.grasped*: Boolean indicating if the object is already being grasped

Note: If a wall is detected, both distance and angle will be 0 to prevent usage of wall data through this sensor.

Gaussian noise is applied to the distance measurements to simulate real-world sensor limitations.

To visualize semantic data, you need to set the *draw_semantic_rays* parameter of the *GuiSR* class constructor to *True*.

### GPS sensor

In the file `src/swarm_rescue/simulation/drone/drone_sensors.py`, it is described in the class *DroneGPS*.

This sensor gives the position vector along the horizontal axis and vertical axis.
The position (0, 0) is at the center of the map.
Noise has been added to the data to make it look like GPS noise. This is not just gaussian noise but noise that follows an autoregressive model of order 1.

If you want to enable the visualization of the noises, you need to set the *enable_visu_noises* parameter of the *GuiSR* class constructor to *True*.

### Compass sensor

In the file `src/swarm_rescue/simulation/drone/drone_sensors.py`, it is described in the class *DroneCompass*.

This sensor gives the orientation of the drone.
The orientation increases with a counter-clockwise rotation of the drone. The value is between -Pi and Pi.
Noise has been added to the data to make it look like Compass noise. This is not just gaussian noise but noise that follows an autoregressive model of order 1.

If you want to enable the visualization of the noises, you need to set the *enable_visu_noises* parameter of the *GuiSR* class constructor to *True*.

### Odometer sensor

In the file `src/swarm_rescue/simulation/drone/drone_sensors.py`, it is described in the class *DroneOdometer*.

This sensor provides relative positioning data through an array with three key measurements:
- `dist_travel`: Distance traveled during the last timestep (in pixels)
- `alpha`: Relative angle of the current position with respect to the previous frame (in radians)
- `theta`: Orientation variation (rotation) during the last timestep (in radians)

These measurements are all relative to the drone's previous position. By integrating these odometry readings over time, you can estimate the drone's current position when absolute positioning (GPS) is unavailable.

This capability is essential when navigating through GPS-denied areas on the map, such as No-GPS zones.

Angles, alpha and theta, increase with a counter-clockwise rotation of the drone. Their value is between -Pi and Pi.
Gaussian noise was added separately to the three parts of the data to make them look like real noise.

![odometer values](img/odom.png)

If you want to enable the visualization of the noises, you need to set the parameter *enable_visu_noises* parameter of the *GuiSR* class constructor to *True*. It will show also a demonstration of the integration of odometer values, by drawing the estimated path.

### Communication

Drones can exchange information with nearby teammates through the communication system:
* Each drone can communicate with all other drones within 250 pixels.
* Messages are sent and received at each simulation timestep.
* You can define custom message content through the `define_message_for_all()` method
* Received messages are available through the `received_messages` attribute

You can find a practical example of drone communication in `src/swarm_rescue/solutions/my_drone_lidar_communication.py`.

### Actuators

At each time step, you must provide values for your actuators.

You have 3 values to control your drone's movement:
- *forward*: A float value between -1 and 1. This applies force in the longitudinal direction.
- *lateral*: A float value between -1 and 1. This applies force in the lateral direction.
- *rotation*: A float value between -1 and 1. This controls the rotation speed.

To interact with the world, you can *grasp* certain *graspable* objects. To rescue a *wounded person*, you must:
1. Approach them
2. *Grasp* them by setting the *grasper* value to 1
3. Transport them to the rescue center
4. Release them by setting the *grasper* value to 0

The *grasper* actuator is binary:
- 0: Released (not carrying anything)
- 1: Grasped (carrying an object)

When a wounded person is grasped by a drone, they become "transparent" to the drone's sensors. This design allows the drone to navigate more easily without having its sensors obstructed by the carried person.

You can find examples of actuator use in almost all files in `examples/` and `src/swarm_rescue/solutions/`.

## Playground

Drones act and perceive in a *Playground*.

A *playground* is composed of scene elements, which can be fixed or movable. A drone can grasp certain scene elements.
The playground with all its elements, except for the drones, is called a "Map" within this *Swarm-Rescue* repository.

### Coordinate System

The playground uses a standard Cartesian coordinate system:

* The position `(x, y)` :
  - Origin (0,0) is at the center of the map.
  - `x`: Horizontal position (positive values to the right)
  - `y`: Vertical position (positive values upward)

* The orientation `theta`:
  - Measured in radians between -π and π
  - Increases with counter-clockwise rotation
  - At `theta` = 0, the drone faces right (positive x-axis)

* Map Dimensions:
  - Maps have a size [width, height], with width along x-axis and height along y-axis
  - All measurements are in pixels

## Wounded Person

A *Wounded Person* appears as a yellow character on the map and represents an injured individual requiring rescue.

**Rescue Process:**
1. Detect the wounded person (using the semantic sensor)
2. Approach them
3. Grasp them (set `grasper = 1`)
4. Transport them to the rescue center
5. Release them at the rescue center (set `grasper = 0`)

**Types of Wounded Persons:**
- **Static** (majority): Remain in fixed positions
- **Dynamic**: Move along predetermined paths, following these behaviors:
  - Move back and forth along their defined route
  - If dropped by a drone somewhere off their path, they will move in a straight line attempting to rejoin their original route
  - May be more challenging to rescue due to their movement

A practical example of grasping a wounded person can be found in `examples/example_semantic_sensor.py`.

You can find an example of some dynamic wounded persons in the `examples/example_moving_wounded.py` file.

## The Rescue Center

The *Rescue Center* is a red element on the map where the drones have to bring the *Wounded Person*.

A reward is given to a drone each time it gives a *Wounded Person* to the *Rescue Center*.

You can find an example of rescue center used in the `examples/example_semantic_sensor.py` file.

## The Return Area

The *Return Area* is a blue area on the map where the drones should stay at the end of the mission.
Part of the final score is calculated with this zone: the percentage of health points of the drones that return to this return area at the end of the mission compared to the health points of the drones at the beginning of the mission.
If there is no *Return Area* in the map, then the score is calculated with the percentage of health points of all drones in the map.

This return area is not visible to any sensor, but the boolean data attribute *is_inside_return_area* gives information about whether the drone is inside the return area or not.
The *Return Area* is always near the *Rescue Center* and the drones always start the mission from this area.

## Special zones

There are zones that alter the abilities of the drones. They can also call the *disablers*. They are invisible to sensors!
- **No-Communication Zone (transparent yellow):** Cuts off all radio communication.
- **No-GPS Zone (transparent gray):** The GPS and compass no longer work. Rely on the odometer!
- **Kill Zone (or deactivation zone) (transparent pink):** Instantly destroys any drone that enters it.

# Programming Your Drones

## Code Architecture

Your code is located in the `src/swarm_rescue/solutions` directory. You will only need to modify files in this folder.

An important file is `src/swarm_rescue/solutions/my_drone_eval.py`. This is where you will tell the simulator which drone class to use: the MyDroneEval class must inherit from your drone class.

`src/swarm_rescue/launcher.py` is the main program file to launch a swarm of drones using your code. This file executes everything needed to perform the evaluation.

It will launch the 10 drones that you have customized in the map that you want, make it run and give the final score.

## Your Drone's Brain

You must create a class that inherits from `DroneAbstract`. This class is your drone's "brain." It must implement two crucial methods:

1.  `define_message_for_all()`: This is where you define the information the drone will send to its neighbors.
2.  `control()`: This is the core of your logic. This method is called at each time step and must return the actuator commands (move, turn, etc.).

**Golden Rule:** In your code, use **only** sensor data (e.g., `measured_gps_position()`) and not the true simulation values (e.g., `true_position()`). This is essential to prepare for the actual competition conditions where ground truth is not available.

## Useful Directories

- `src/swarm_rescue/solutions`: **Your code.** Examples are provided here.
- `src/swarm_rescue/maps`: The available simulation maps.
- `examples/`: Standalone example scripts to understand each feature (controlling a drone with the keyboard, visualizing Lidar, etc.).
- `src/swarm_rescue/tools`: Tools, for example, to create a map from an image.
- `src/swarm_rescue/simulation`: The core of the simulator. **Do not modify these files.**

## Evaluation Plan

### What is the Evaluation Plan?

The evaluation plan defines which scenarios your drones will be tested on. It is fully configurable via a YAML file, allowing you to specify which maps, special zones, and how many rounds to run for each scenario—without changing any Python code.

**Why use it?**
- Evaluators can easily test your solution on many scenarios.
- You can test your own code on custom maps and conditions.
- Output options (reports, videos) are controlled from the same file.

---

### YAML Configuration Structure

Your main configuration file (e.g., `config/default_eval_plan.yml`) should look like this:

```yaml
stat_saving_enabled: true        # Save statistics and generate PDF report (true/false)
video_capture_enabled: false     # Enable video recording of the mission (true/false)

evaluation_plan:
  - map_name: MapIntermediate01
    nb_rounds: 2
    config_weight: 1
    zones_config: []
  - map_name: MapIntermediate02
    nb_rounds: 1
    config_weight: 1
    zones_config: []
  - map_name: MapMedium01
    nb_rounds: 1
    config_weight: 1
    zones_config: []
  - map_name: MapMedium01
    nb_rounds: 1
    config_weight: 1
    zones_config: [NO_COM_ZONE, NO_GPS_ZONE, KILL_ZONE]
  - map_name: MapMedium02
    nb_rounds: 1
    config_weight: 1
    zones_config: [NO_COM_ZONE, NO_GPS_ZONE, KILL_ZONE]
```

**Top-level fields:**
- `stat_saving_enabled`: Save statistics and generate a PDF report (`true`/`false`)
- `video_capture_enabled`: Record a video of the mission (`true`/`false`)

The generation of statistics reports and mission videos in the ~/results_swarm_rescue directory is primarily intended for the competition evaluator.
You can enable or disable report and video generation using the 'stat_saving_enabled' and 'video_capture_enabled' fields below.

**evaluation_plan:**
A list of scenarios, each with:
- `map_name`: The map to use (see `src/swarm_rescue/maps`)
- `nb_rounds`: How many times to repeat this scenario
- `config_weight`: Importance in the final score
- `zones_config`: List of special zones to activate:
  - `NO_COM_ZONE`: Disables drone communication
  - `NO_GPS_ZONE`: Disables GPS positioning  
  - `KILL_ZONE`: Destroys drones that enter
  - Empty list `[]`: No special zones active

### Quick Start: Running an Evaluation

1. Edit your YAML file as needed.
2. Run the launcher with your config:
   ```bash
   python src/swarm_rescue/launcher.py --config config/my_eval_plan.yml
   ```
3. Results (reports/videos) will appear in `~/results_swarm_rescue` if enabled.

**Note:**
Generated reports and videos are for the evaluator's use.

### Running in Headless Mode (No Display)

The simulator supports **headless mode**, which is essential for running evaluations on remote servers without a display or GPU.

#### Basic Usage

Add the `--headless` (or `-H`) flag to run without opening a window:

```bash
python src/swarm_rescue/launcher.py --headless --config config/my_eval_plan.yml
```

**Important:** This command works if you already have an X11 server running (even if hidden). The `--headless` flag tells arcade not to show the window, but it still needs an X11 display to create the OpenGL context.

#### Running on Servers Without Display

If you're on a server without X11 or if you encounter OpenGL/display errors, use `xvfb-run` to create a virtual framebuffer:

```bash
# Install xvfb (if needed)
sudo apt-get install xvfb

# Run with virtual display
xvfb-run -s "-screen 0 1920x1080x24" python src/swarm_rescue/launcher.py --headless --config config/my_eval_plan.yml
```

This allows the simulator to create OpenGL contexts even without a physical display, enabling video capture and rendering in headless environments.

### API: EvalConfig and EvalPlan

You can also create evaluation plans programmatically:

```python
from swarm_rescue.simulation.reporting.evaluation import EvalConfig, EvalPlan
from swarm_rescue.simulation.elements.sensor_disablers import ZoneType

# Create an easy scenario
easy_config = EvalConfig(map_name="MyMapEasy01")

# Scenario with all special zones
hard_config = EvalConfig(
    map_name="MapMedium01",
    zones_config=(ZoneType.NO_COM_ZONE, ZoneType.NO_GPS_ZONE, ZoneType.KILL_ZONE),
    nb_rounds=3,
    config_weight=2
)

# Add scenarios to a plan
plan = EvalPlan()
plan.add(easy_config)
plan.add(hard_config)
```
You can see examples of evaluation plan created programmatically in the main() fonction of the files:
- src/swarm_rescue/maps/map_final_2023_24_01.py
- src/swarm_rescue/maps/map_final_2023_24_02.py 
- src/swarm_rescue/maps/map_final_2023_24_03.py
- src/swarm_rescue/maps/map_final_2024_25_01.py
- src/swarm_rescue/maps/map_final_2024_25_02.py
- src/swarm_rescue/maps/map_final_2024_25_03.py

### Pre-configured Evaluation Plans

The `config/` directory contains ready-to-use evaluation plan YAML files for different competition scenarios:

**Competition-specific configurations:**
- `final_2024_25_eval_plan.yml` - Latest 2024-2025 final maps (MapFinal_2024_25_01/02/03)
- `final_2023_24_eval_plan.yml` - 2023-2024 final maps (MapFinal_2023_24_01/02/03) 
- `final_2022_23_eval_plan.yml` - 2022-2023 final map (MapFinal2022_23)
- `intermediate_eval_plan.yml` - Training maps (MapIntermediate01/02)

**Usage examples:**
```bash
# Test on latest 2024-2025 competition maps
python src/swarm_rescue/launcher.py --config config/final_2024_25_eval_plan.yml

# Train on intermediate difficulty maps
python src/swarm_rescue/launcher.py --config config/intermediate_eval_plan.yml

# Test on previous year's final maps
python src/swarm_rescue/launcher.py --config config/final_2023_24_eval_plan.yml
```

Each configuration includes scenarios with progressive difficulty:
- Basic scenarios (no special zones) for algorithm validation
- Individual special zone challenges (NO_COM_ZONE, NO_GPS_ZONE, KILL_ZONE)

Statistics saving and video capture are enabled by default in these configurations for detailed performance analysis.

## Code in detail

### Directory *simulation*

As its name indicates, the folder `src/swarm_rescue/simulation` contains the software for the simulator. It contains six subdirectories:
- *drone*: definition of the drone, its sensors and actuators.
- *elements*: definition of the different elements of the environment (walls, wounded persons, rescue center, return area, etc.).
- *gui_map*: graphical interface, keyboard management, playground, etc.
- *ray_sensors*: ray sensors (lidar, semantic sensor, etc.) and the shaders used for the sensors.
- *reporting*: tools to compute the score and create a PDF evaluation report.
- *utils*: various functions and useful tools.

The files it contains must *not* be modified.

An important file is `src/swarm_rescue/simulation/gui_map/gui_sr.py` which contains the class *GuiSR*. To use the keyboard to navigate drone "#0", set the `use_keyboard` parameter in the *GuiSR* constructor to `True`. To enable visualization of noises for debugging, set `enable_visu_noises=True`; it also draws the estimated odometry path.

### Directory *maps*

This directory `src/swarm_rescue/maps` contains the maps used by the drones. New maps may be added as new missions are developed. You can also create your own maps based on existing ones.

Every map file contains a main function, allowing the file to be executed directly to observe the map. In this case, the map is run with stationary drones. The parameter `use_mouse_measure` is set to `True` so the measuring tool is active when clicking on the screen.

Each map must inherit from the class *MapAbstract*.

### Directory *solutions*

This directory `src/swarm_rescue/solutions` will contain your solutions. The code currently there serves as example implementations with simple behavior. Use it as inspiration and go beyond: write code that defines your drones and how they interact with the environment.

Each Drone must inherit from the class *DroneAbstract*. You have 2 mandatory member functions: `define_message_for_all()` to define the message sent between drones, and `control()` to return the action to perform at each time step.

Keep in mind that the same code runs on each of the 10 drones. Each drone is an instance of your Drone class.

For your computations in `control()`, use only the sensor and communication data, without directly accessing internal members. In particular, do not use the true `position` and `angle` variables; instead use `measured_gps_position()` and `measured_compass_angle()` to get the drone’s position and orientation. These values are noisy (more realistic) and may be altered by special zones.

The true position of the drone can be accessed via `true_position()` and `true_angle()` (or directly with the variables `position` and `angle`), BUT this is only for debugging or logging.

Example implementations are provided in `src/swarm_rescue/solutions` to help you get started:
- `my_drone_random.py` - Demonstrates basic lidar sensor usage and actuator control
- `my_drone_lidar_communication.py` - Shows how to implement inter-drone communication with lidar
- `my_drone_motionless.py` - A minimal implementation of a stationary drone (useful as a starting template)

### Directory *examples*

In the `examples/` folder at the root of the repository, you will find stand-alone programs to help you understand key concepts. In particular:
- `example_display_lidar.py` shows a visualization of the lidar on a graph, with noise.
- `example_com_disabler.py` demonstrates communication between drones and the effect of *No Com Zone* and *Kill Zone*. When communication is possible, a line is drawn between two drones.
- `example_disablers.py` illustrates each disabling zone.
- `example_gps_disablers.py` demonstrates the effect of *No GPS Zone* and *Kill Zone*. The green circle is the GPS position; the red circle is the odometry-only estimate.
- `example_keyboard.py` shows how to use the keyboard for development or debugging. Usable keys include: Up/Down (forward/backward), Left/Right (turn), Shift+Left/Right (lateral), W (grasp), L (lidar rays), S (semantic rays), P (GPS position), C (communication), M (print messages), Q (quit), R (reset).
- `example_mapping.py` shows how to create an occupancy map.
- `example_pid_rotation.py` controls orientation with a PID.
- `example_pid_translation.py` controls translation with a PID.
- `example_return_area.py` uses `is_inside_return_area` to detect whether the drone is inside the return area.
- `example_semantic_sensor.py` shows semantic sensor and actuators, grasping a wounded person and bringing it back to the rescue area.
- `example_static_semantic_sensor.py` illustrates semantic sensor rays with other drones and wounded persons.
- `random_drones.py` shows many drones flying randomly in empty space.
- `random_drones_intermediate_1.py` shows random flying in `map_intermediate_01`.

### Directory *tools*

In `src/swarm_rescue/tools`, you may find utilities to create maps, make measurements, etc. Notably:
- `image_to_map.py` builds a map from a black and white image.
- `check_map.py` shows a map without drones; clicking prints coordinates—useful for designing or modifying a map.

## Submission

At the end of the competition, submit your solution to your evaluator. The evaluator will use the same software to assess your solution.

Provide only:
- The code to run your simulated drone, which must come from the `src/swarm_rescue/solutions` directory.
- The file `team_info.yml`, filled in correctly.
- The list of any new dependencies required to run your drone.

## Various tips

### Exiting an execution

- To exit elegantly after launching a map, press `Q` in the simulation window (exits current round).
- To exit the entire program immediately, press `E` in the simulation window (exits all rounds).

### Enable some visualizations

The `GuiSR` class can be constructed with the following parameters (defaults shown):
- `draw_zone`: True. Draws special zones (no com zone, no gps zone, killing zone).
- `draw_lidar_rays`: False. Draws lidar rays.
- `draw_semantic_rays`: False. Draws semantic sensor rays.
- `draw_gps`: False. Draws the GPS position.
- `draw_com`: False. Displays the communication range and links between communicating drones.
- `print_rewards`: False.
- `print_messages`: False.
- `use_keyboard`: False.
- `use_mouse_measure`: False. Click to print the mouse position.
- `enable_visu_noises`: False.
- `filename_video_capture`: None to disable; otherwise the output video filename.

### Print FPS performance in the terminal

Display the program's FPS in the console at regular intervals by changing the global variable at the top of `src/swarm_rescue/simulation/gui_map/gui_sr.py`: `DISPLAY_FPS = True`. 
See `src/swarm_rescue/simulation/utils/fps_display.py` for details.

### Show your own display

In *DroneAbstract*, you can override two functions to draw overlays:
- `draw_top_layer()`: draw on top of all layers.
- `draw_bottom_layer()`: draw below all other layers.

For example, draw the drone identifier by calling `self.draw_identifier()` inside `draw_top_layer()`.

### Create a new map

Creating custom maps is useful to reproduce specific scenarios, stress-test parts of your algorithm, and compare strategies under controlled conditions.
It also lets you prototype challenges (wall layouts, wounded placements, and special zones) before the final evaluation on unknown maps.

To add a new map you must create and add two files in `src/swarm_rescue/maps`:
- `map_<name>.py` — defines the Map class (inherits from `MapAbstract`). In the `__init__` of your Map class paste the initialization lines printed by `image_to_map.py` (for example `self._size_area`, `self._rescue_center`, `self._rescue_center_pos`, `self._wounded_persons_pos`) so the map parameters exactly match the conversion. Implement `build_playground()` to set drones' start positions and to call helper functions that add walls/boxes.
- `walls_<name>.py` — contains the helper functions generated by `image_to_map.py` (the script writes `generated_code.py`). Copy the generated helper functions (for example `add_walls(playground)` and `add_boxes(playground)`) into `walls_<name>.py` and import them from `map_<name>.py`.

Step-by-step workflow

1. Draw your map as a PNG image with clear, consistent colors:
   - Walls: pure black (RGB 0,0,0), ~10 px thick for robust detection.
   - Wounded persons: bright yellow (recommended RGB 255,255,0), about 25–40 px diameter.
   - Rescue center: pure red (RGB 255,0,0).
2. Edit `img_path` in `src/swarm_rescue/tools/image_to_map.py` to point to your PNG and run the script. The tool is interactive and shows intermediate images with OpenCV (`cv2.imshow`); press any key to advance (`cv2.waitKey(0)`). On success it will:
   - write a `generated_code.py` that contains helper functions (walls/boxes), and
   - print a few Python initialization lines in the console.
3. Copy the helper functions from `generated_code.py` into a new file `src/swarm_rescue/maps/walls_<name>.py`.
4. COPY the initialization lines printed in the console into the `__init__` of your `Map` class in `src/swarm_rescue/maps/map_<name>.py`. Important: copy these exact assignments so your map parameters match the converter output:
   - `self._size_area`
   - `self._rescue_center`
   - `self._rescue_center_pos`
   - `self._wounded_persons_pos`
   These values ensure the map dimensions, rescue center placement and wounded persons coordinates are identical to the conversion (the console output from `image_to_map.py` is authoritative).
5. Implement `build_playground()` in `map_<name>.py` to:
   - import and call the helper functions from `walls_<name>.py` to add walls/boxes,
   - define drones' starting area/positions (the converter does not create drone starts automatically),
   - add any return area or extra elements required by your scenario.
6. Validate visually using `src/swarm_rescue/tools/check_map.py` (displays the map without drones and prints coordinates when clicking). After visual validation, run a short simulation to smoke-test the map:
```bash
python3 src/swarm_rescue/launcher.py --config config/my_eval_plan.yml
```
Notes & troubleshooting
- Exact variables to copy: when you run `image_to_map.py` the console output contains the Python lines to paste into your `map_<name>.py`. In particular copy the assignments for `self._size_area`, `self._rescue_center`, `self._rescue_center_pos`, and `self._wounded_persons_pos` into your Map class `__init__`.
- Color detection: `image_to_map.py` detects yellow hues for wounded persons and red for the rescue center using HSV/luma thresholds. If detection fails for a particular shade (for instance yellow vs green), tweak the thresholds inside `src/swarm_rescue/tools/image_to_map.py` (adjust yellow/green thresholds there). The README intentionally points to the tool for color tuning rather than enumerating many variants.
- Drone start positions: the converter does not set drone starting positions. Add them explicitly in `map_<name>.py` — see existing `map_*.py` examples for idiomatic patterns.
- Small elements and thickness: keep walls reasonably thick in the source PNG (~8–12 px) to avoid fragmentation during detection.
- Final check: after creating both files (`map_<name>.py`, `walls_<name>.py`) and validating with `check_map.py`, run a short simulation to validate the map in situ.

# Getting Started

Welcome to Swarm-Rescue! This section will help you quickly set up and run your first simulation with a custom drone controller.

## Installation

Follow [INSTALL.md](INSTALL.md) to set up your environment, install dependencies, and troubleshoot common issues. Supported platforms include Ubuntu (recommended) and Windows (with WSL2 or Git Bash).

## Quick Start Example

Once installed, you can launch a default simulation with:

```bash
python3 src/swarm_rescue/launcher.py
```

## Minimal Drone Controller Example

Here is a minimal example of a custom drone controller.
Create a new file in the `src/swarm_rescue/solutions/` directory, e.g., `my_great_drone.py`, and add the following code:

```python
from swarm_rescue.simulation.drone.drone_abstract import DroneAbstract

class MyGreatDrone(DroneAbstract):
    def control(self):
        # Simple forward motion at each step
        return {
            "forward": 1.0,  # Move forward at full speed
            "lateral": 0.0,  # No sideways movement
            "rotation": 0.0,  # No rotation
            "grasper": 0      # Don't grasp anything
        }

    def define_message_for_all(self) -> None:
        # Define message content for communication with other drones
        pass
```

Then, modify `src/swarm_rescue/solutions/my_drone_eval.py` to use your new drone:
```python
from swarm_rescue.solutions.my_great_drone import MyGreatDrone
class MyDroneEval(MyGreatDrone):
    pass
```

Now, run the launcher again to see your drone in action!
```bash
python3 src/swarm_rescue/launcher.py
```

# Project Structure Overview

```
private-swarm-rescue/
├── src/
│   └── swarm_rescue/
│       ├── launcher.py
│       ├── solutions/
│       │   ├── my_drone_eval.py
│       │   ├── my_drone_lidar_communication.py
│       │   ├── my_drone_motionless.py
│       │   ├── my_drone_random.py
│       │   └── team_info.yml
│       ├── simulation/
│       │   ├── drone/
│       │   │   ├── drone_sensors.py
│       │   │   └── drone_abstract.py
│       │   ├── ray_sensors/
│       │   │   ├── drone_lidar.py
│       │   │   └── drone_semantic_sensor.py
│       │   ├── gui_map/
│       │   │   └── gui_sr.py
│       │   └── ...
│       ├── maps/
│       └── tools/
├── examples/
├── config/
├── tests/
├── INSTALL.md
├── README.md
└── pyproject.toml
```

# Contact

If you have questions about the code, propose improvements or report bugs, you can contact:
emmanuel . battesti at ensta . fr
