# Changelog
All notable changes to this project will be documented in this file.

## [Unreleased]
### Fixed
- Samll bug in CHANGELOG.md

## [1.1.0] - 2021-11-18
### Added
- A MiscData objet should be passed as a parameter of the drone contructor. MiscData will contains miscellaneous data for the drone. For now, it contains only the dimension of the playground.
- This file, CHANGELOG.md

### Changed
- README.md updated
- Increase range of communication sensor from 200 to 500
- Now a semantic sensor DroneSemanticCones sends for each cone: the distance, the angle, the type of object and a boolean if it is grasped. It no longer sends the object itself.

### Fixed
- Bug fix in map_random

## [1.0.0] - 2021-11-05

### Added
- Keep track of what was visited in the map with ExploredMap class
- Class to compute the final score: score_manager.py
- Add example files

### Changed
- Change of API in SPG
- Remove warnings and bugs
- Change texture of wounded persons, rescue center and walls

## [0.9.0] - 2021-10-27
### Changed
- First real version

## [0.0.0] - 2021-10-19
### Added
- Initial commit

[Unreleased]: https://github.com/embaba/swarm-rescue/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/embaba/swarm-rescue/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/embaba/swarm-rescue/compare/v0.9.0...v1.0.0
[0.9.0]: https://github.com/embaba/swarm-rescue/compare/v0.0.0...v0.9.0
[0.0.0]: https://github.com/embaba/swarm-rescue/releases/tag/v0.0.0

