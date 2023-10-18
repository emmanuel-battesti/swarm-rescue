# Changelog
All notable changes to this project will be documented in this file.

## [Unreleased]

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
- Compatibility with the new version of numpy : numpy.int has been deprecated, use int instead.

## [2.2.1] - 2022-12-15

### Changed
- Cleaning example.
- Disabled forbidden functions : position(), angle(), velocity(), angular_velocity() => generate an exception.

### Added
- Added map_intermediate_02.py !
- In README, added instructions to install the program on Windows10. 
- Added function grasped_entities() in drone_abstract.
- Added function measured_velocity() computed from odometer and compass values in drone_abstract.
- Added function measured_angular_velocity() in drone_abstract.
- Added some tests.

### Fixed
- bug fix : the execution of the code goes through your control() function even if you have activated the use of the keyboard to control the drone.
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
    - rename *measured_angle()* to *measured_compass_angle()*  in the class *DroneAbstract*
 - the "no gps zone"  still disables the gps sensor and now, it disables also the compass sensor.

### Added
- add odometer sensor (see README.md for more information)
- remove velocity sensor (whose data can be replaced by a calculation on the odometry data)
- visualization of the noises on gps sensor, compass sensor and odometer sensor.

### Fixed
- improve code : typing, comments, documentation
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
- New map : MyMapCompet02
- Teams should now fill the team_info.yml file in the solutions/ directory
- *launcher.py* now produces a pdf report of the performances in the *~/results_swarm_rescue/* directory according to the challenge evaluation rules

### Fixed


## [1.3.0] - 2022-01-27

### Changed
- Change fov of the *DroneLidar* from 180° to 360°, but we keep 90 rays.
- Split the sensor *DronePosition* in 2 sensors : *DroneGPS*, for only the position in pixels, and *DroneCompass*, for only the orientation of the drone in radians. Thus, the no-GPS zone will only apply to *DroneGP*S sensor, the orientation is still available.
- In the no-GPS zone, the measured position was always (0, 0). Now, it is (NaN, NaN).

### Added
- There are new functions in the class DroneAbstract to known if a sensor is disabled:
    - *touch_is_disabled()*
    - *semantic_cones_is_disabled()*
    - *lidar_is_disabled()*
    - *gps_is_disabled()*
    - *compass_is_disabled()*
    - but no *communication_is_disabled()*...
- Now, drone have a velocity sensor *DroneVelocity* and the functions : *measured_velocity()*, *measured_angular_velocity()*, *true_velocity()*, *true_angular_velocity()*

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

[Unreleased]: https://github.com/emmanuel-battesti/swarm-rescue/compare/v3.0.1...HEAD
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

