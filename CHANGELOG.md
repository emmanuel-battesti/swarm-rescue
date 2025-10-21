# Changelog
All notable changes to this project will be documented in this file.

## [Unreleased]

## [5.1.0] - 2025-01-21

### Added
- Add headless mode for running simulations without GUI
- Add key 'E' to exit the program completely
- Add disappearing walls feature with example implementation
- Add final maps from 2024-2025 competition
- Add new evaluation plan configurations
- Add screen resize and scale functionality (may not work on some maps)
- Add "Create a new map" explanation in README
- Add `stat_saving_enabled` and `video_capture_enabled` options in config files
- Add PyQtGraph dependency for improved visualization
- Add `drone_v2_dead.png` texture for drones in kill zones

### Changed
- **Major change**: Replace matplotlib/pyplot visualization with PyQtGraph for better performance
- Improve drone texture when in kill zone
- Replace `MyMapxxx` naming convention with `Mapxxx` and `my_map` with `the_map`
- Change team number padding from 2 to 3 digits and remove padding in some displays
- Improve implementation with optimizations and caching
- Clean up pymunk.Vec2d vs Tuple usage
- Replace `SrColorWall` with `ColorWall` class
- Replace `SRDisabler` class with `DisablerZone` class
- Use `math.radians` and `math.degrees` instead of manual conversions
- Update README with comprehensive improvements
- Update INSTALL.md documentation
- Move dependencies to pyproject.toml and remove requirements.txt/setup.py
- Change `_display_lidar_graph` to `_should_display_lidar_graph`

### Fixed
- Fix compatibility issues with Ubuntu 20 and Python 3.8
- Fix test_wall.py functionality
- Fix bugs in check_map and my_drone_eval.py
- Improve robustness of explored_map.py to avoid crashes
- Fix wall rendering and collision detection
- Fix _hitpoints calculation bug
- Fix import issues and remove warnings after code inspection
- Correct image_to_map tool functionality
- Various crash prevention improvements
- Remove useless dependencies and clean up project structure

## [5.0.0] - 2025-09-11

### Changed
- Big change: we don't use the library simple-playground anymore. His code is now directly integrated in swarm-rescue. So, swarm-rescue is now independent of simple-playground.
- Simplification of the architecture of the code.
- Change of some function names
- Change of some class names
- Change of some file names
- Change of some directory names

## [4.1.0] - 2025-09-11

### Changed
- Now, some files define the "eval plans" : map name, number of rounds, configuration weight, zones configuration. Those files are in the directory config.

## [4.0.4] - 2025-06-26

### Changed
- Improve image_to_map tool
- Improve measurement tool

### Fixed
- Fixed bug: if the wounded were dropped just before the rescue center, they were not counted when they disappeared inside it
- Added arcade version 2.6.17 in requirements.txt

## [4.0.3] - 2024-12-04

### Added
- Add submission_guidelines.md file.
- Add a script file: create_zip_submission.sh

### Changed
- Minor change to the final report and terminal display

### Fixed
- Correction of a few typos in the README file.

## [4.0.2] - 2024-11-08
### Added
- Add a tool to display info about the computer src/swarm_rescue/tools/opengl_info.py

### Changed
- Update the documentation about installation: INSTALL.md

## [4.0.1] - 2024-10-23
### Added
- Add the maps used for the assessment of the 2023-24 challenge, but add the return zone.
- Add a "main" function in the maps Python file. Permit to just display the map with motionless drones.

### Changed
- Enlarge return area on some maps.
- Update readme.md.
- Rename "playground" to "my_playground" to avoid warning in examples and maps.
- Improvement and simplification of data saving and video record system.

### Fixed
- Fixed bugs with map_random.py.
- Fixed bug in the pdf report.

## [4.0.0] - 2024-10-18

### Added
- "Return area" where the drone should return to at the end of the mission.
- Some wounded people can move along a predefined path.
- Drones have access to their health level.
- Drones have access to max timestep limit and elapsed_timestep.
- Drones have access to max walltime limit and elapsed_walltime.
- Drones can detect if they are in the "return area".

### Changed
- Changed drone behavior with elasticity and friction parameters: more friction and elasticity with the walls and other drones.
- Added the health level of the returned drones in the final score calculation and in the pdf report.
- Updated requirements and documentation.
- Indentation and code details.
- Swarm-Rescue is now linked to the *swarm-rescue-v3* version of *simple-playground*.
- The key to activate grasping, on the keyboard, change from G to W.

## [3.2.0] - 2024-04-15

### Changed
- Use drones health percentage instead of drones health value
- If the execution crash, now it continue with the next configuration
- new way to computed reachable pixel in the map to compute the exploration score

### Added
- add title to the window
- add boolean arguments stop_at_first_crash and hide_solution_output
- add border_thickness in ClosedPlayground
- add wall_thickness in NormalWall

## [3.1.0] - 2023-12-05

### Changed
- Improve and update the README.md
- Moved installation instructions to a separate file, INSTALL.md, for easier access and organization.
- Modified image_to_map.py tool
- Add management of collision to all the maps

### Fixed
- Refined the score exploration algorithm to ensure higher accuracy.
- Rectified an issue in the computation of velocity within the function measured_velocity() which was resulting in incorrect outputs.
- Restricted lateral and forward commands to have a maximum norm of 1.0

## [3.0.1] - 2023-10-18

### Fixed
- Import problems in examples

## [3.0.0] - 2023-10-09

### Changed
- A lot of changes !!

## [2.2.3] - 2023-03-20

### Changed
- Change the tool image_to_map.py

### Added
- Add the map of the final !

### Fixed
- Now, round terminates when the time_step exceeds the time_step_limit

## [2.2.2] - 2023-02-07

### Changed
- Walls are no longer detected as OTHER, they are remove from the results of the semantic sensor.
- Improve the generated report. Now, in english.

### Added
- Add a new example for the semantic sensor.

### Fixed
- Drones are correctly detected as DRONE in the results of the semantic sensor.
- Bug fix concerning a random crash.
- Bug fix in the computation of the number of wounded person bring to the rescue center, in the case of multi-grasping.
- Fixed a bug in the calculation of the number of wounded person brought to the rescue center when they are brought by more than one drone.
- Spelling in README.md
- Compatibility with the new version of numpy: numpy.int has been deprecated, use int instead.

## [2.2.1] - 2022-12-15

### Changed
- Cleaning example.
- Disabled forbidden functions: position(), angle(), velocity(), angular_velocity() => generate an exception.

### Added
- Added map_intermediate_02.py !
- In README, added instructions to install the program on Windows10. 
- Added function grasped_entities() in drone_abstract.
- Added function measured_velocity() computed from odometer and compass values in drone_abstract.
- Added function measured_angular_velocity() in drone_abstract.
- Added some tests.

### Fixed
- bug fix: the execution of the code goes through your control() function even if you have activated the use of the keyboard to control the drone.
- there should be no more NaN at the first reading of the sensor data.
- installation bug.

## [2.2.0] - 2022-10-27

### Changed
- Refactoring of the map construction: now, drones are instantiated in the map class.

### Added
- Adding screen recorder tool: not really useful for competitors, but for evaluators. It is disabled by default.

### Fixed
- Fixing bug with macOS: the simulator crashed regularly on macOS. The problem is corrected but at the cost of a decrease in performance on macOS (some calculations done by the GPU are done by the CPU instead)

## [2.1.0] - 2022-10-21

### Changed
- change default GPS noise
- function name:
    - rename *measured_position()* to *measured_gps_position()* in the class *DroneAbstract*
    - rename *measured_angle()* to *measured_compass_angle()* in the class *DroneAbstract*
 - the "no gps zone" still disables the gps sensor and now, it disables also the compass sensor.

### Added
- add odometer sensor (see README.md for more information)
- remove velocity sensor (whose data can be replaced by a calculation on the odometry data)
- visualization of the noises on gps sensor, compass sensor and odometer sensor.

### Fixed
- improve code: typing, comments, documentation
- fix small bugs

## [2.0.0] - 2022-10-10

### Changed
- New version of simple-playgrounds. A lot of changes !!
- The interface is now more beautiful and faster.

## [1.5.2] - 2022-09-08

### Fixed
- Spelling correction in the README and comments of the code

## [1.5.1] - 2022-02-28

### Changed
- The radius, around the drones, of space that is considered explored, increases from 100 to 200

### Fixed
- Bug fix in the calculation of the explored area.

## [1.5.0] - 2022-02-15

### Changed
- *launcher.py* file is reformatted
- The evaluation report file is improved
- Information displayed in the console is improved

### Added

### Fixed
- The package *pathlib* has been changed to *pathlib2*, because *pathlib* is not maintained anymore.

## [1.4.1] - 2022-02-10

### Fixed
- Bug fix in *launcher.py* in function reset()

## [1.4.0] - 2022-02-04

### Changed
- *launcher.py* will now run the code following the competition evaluation rules (tests without special zones and with each zone activated)
- Special zones can now be activated/deactivated in the maps
- The starting points of the drones are not random anymore. The position of all drones now displays a square.

### Added
- New map: MyMapCompet02
- Teams should now fill the team_info.yml file in the solutions/ directory
- *launcher.py* now produces a pdf report of the performances in the *~/results_swarm_rescue/* directory according to the challenge evaluation rules

### Fixed


## [1.3.0] - 2022-01-27

### Changed
- Change fov of the *DroneLidar* from 180° to 360°, but we keep 90 rays.
- Split the sensor *DronePosition* in 2 sensors: *DroneGPS*, for only the position in pixels, and *DroneCompass*, for only the orientation of the drone in radians. Thus, the no-GPS zone will only apply to *DroneGP*S sensor, the orientation is still available.
- In the no-GPS zone, the measured position was always (0, 0). Now, it is (NaN, NaN).

### Added
- There are new functions in the class DroneAbstract to known if a sensor is disabled:
    - *touch_is_disabled()*
    - *semantic_cones_is_disabled()*
    - *lidar_is_disabled()*
    - *gps_is_disabled()*
    - *compass_is_disabled()*
    - but no *communication_is_disabled()*...
- Now, drone have a velocity sensor *DroneVelocity* and the functions: *measured_velocity()*, *measured_angular_velocity()*, *true_velocity()*, *true_angular_velocity()*

### Fixed

## [1.2.0] - 2021-11-26
### Added
- Add member variable *display* in the class *Launcher*. If *False*, the map is not shown.
- Add the file *spg_overlay/fps_display.py* which contains *FpsDisplay* class. This class prints the FPS.
- Add noise to *Position* sensor that follows an autoregressive model of order 1
- Add gaussian noise to *lidar* sensor, *semantic* sensor and *touch* sensor.
- Add *number_drones* in the MiscData class. Now, drones have access to this value.
- Add "no communication zone", "no gps zone", "kill zone" in map_compet_01.py

### Changed
- Change the resolution of the *DroneLidar* from 180 rays to 90 rays to improve overall speed.
- Change the resolution of the *DroneTouch* from 36 sensors to 12 sensors to improve overall speed.

## [1.1.0] - 2021-11-18
### Added
- A MiscData object should be passed as a parameter of the drone constructor. MiscData will contain miscellaneous data for the drone. For now, it contains only the dimension of the playground.
- This file, CHANGELOG.md

### Changed
- README.md updated
- Increase the range of communication sensor from 200 to 500
- Now a semantic sensor DroneSemanticCones sends for each cone: the distance, the angle, the type of object and a boolean if it is grasped. It no longer sends the object itself.

### Fixed
- Bug fix in map_random

## [1.0.0] - 2021-11-05

### Added
- Keep track of what was visited on the map with ExploredMap class
- Class to compute the final score: score_manager.py
- Add example files

### Changed
- Change of API in SPG
- Remove warnings and bugs
- Change the texture of wounded persons, rescue center and walls

## [0.9.0] - 2021-10-27
### Changed
- First real version

## [0.0.0] - 2021-10-19
### Added
- Initial commit

[Unreleased]: https://github.com/emmanuel-battesti/swarm-rescue/compare/v5.1.0...HEAD
[5.1.0]: https://github.com/emmanuel-battesti/swarm-rescue/compare/v5.0.0...v5.1.0
[5.0.0]: https://github.com/emmanuel-battesti/swarm-rescue/compare/v4.1.0...v5.0.0
[4.1.0]: https://github.com/emmanuel-battesti/swarm-rescue/compare/v4.0.4...v4.1.0
[4.0.4]: https://github.com/emmanuel-battesti/swarm-rescue/compare/v4.0.3...v4.0.4
[4.0.3]: https://github.com/emmanuel-battesti/swarm-rescue/compare/v4.0.2...v4.0.3
[4.0.2]: https://github.com/emmanuel-battesti/swarm-rescue/compare/v4.0.1...v4.0.2
[4.0.1]: https://github.com/emmanuel-battesti/swarm-rescue/compare/v4.0.0...v4.0.1
[4.0.0]: https://github.com/emmanuel-battesti/swarm-rescue/compare/v3.2.0...v4.0.0
[3.2.0]: https://github.com/emmanuel-battesti/swarm-rescue/compare/v3.1.0...v3.2.0
[3.1.0]: https://github.com/emmanuel-battesti/swarm-rescue/compare/v3.0.1...v3.1.0
[3.0.1]: https://github.com/emmanuel-battesti/swarm-rescue/compare/v3.0.0...v3.0.1
[3.0.0]: https://github.com/emmanuel-battesti/swarm-rescue/compare/v2.2.3...v3.0.0
[2.2.3]: https://github.com/emmanuel-battesti/swarm-rescue/compare/v2.2.2...v2.2.3
[2.2.2]: https://github.com/emmanuel-battesti/swarm-rescue/compare/v2.2.1...v2.2.2
[2.2.1]: https://github.com/emmanuel-battesti/swarm-rescue/compare/v2.2.0...v2.2.1
[2.2.0]: https://github.com/emmanuel-battesti/swarm-rescue/compare/v2.1.0...v2.2.0
[2.1.0]: https://github.com/emmanuel-battesti/swarm-rescue/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/emmanuel-battesti/swarm-rescue/compare/v1.5.2...v2.0.0
[1.5.2]: https://github.com/emmanuel-battesti/swarm-rescue/compare/v1.5.1...v1.5.2
[1.5.1]: https://github.com/emmanuel-battesti/swarm-rescue/compare/v1.5.0...v1.5.1
[1.5.0]: https://github.com/emmanuel-battesti/swarm-rescue/compare/v1.4.1...v1.5.0
[1.4.1]: https://github.com/emmanuel-battesti/swarm-rescue/compare/v1.4.0...v1.4.1
[1.4.0]: https://github.com/emmanuel-battesti/swarm-rescue/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/emmanuel-battesti/swarm-rescue/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/emmanuel-battesti/swarm-rescue/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/emmanuel-battesti/swarm-rescue/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/emmanuel-battesti/swarm-rescue/compare/v0.9.0...v1.0.0
[0.9.0]: https://github.com/emmanuel-battesti/swarm-rescue/compare/v0.0.0...v0.9.0
[0.0.0]: https://github.com/emmanuel-battesti/swarm-rescue/releases/tag/v0.0.0

