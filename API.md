# Swarm Rescue — Participant API Reference

This document is the reference for the drone API you are allowed to use in the
Swarm Rescue competition. It describes exactly what you may call from your
drone class, what each call returns, and what the simulator guarantees.

Everything here was read from the source and checked against a running
simulation. Where a value is a tunable constant, the current default is given.

---

## Contents

1. [The golden rule](#1-the-golden-rule)
2. [What you write](#2-what-you-write)
3. [The two methods you must implement](#3-the-two-methods-you-must-implement)
4. [Reading measurements](#4-reading-measurements)
5. [Sensors in detail](#5-sensors-in-detail)
6. [State you may read](#6-state-you-may-read)
7. [Special zones](#7-special-zones)
8. [Grasping](#8-grasping)
9. [Communication](#9-communication)
10. [Sensor accessors](#10-sensor-accessors)
11. [Debugging helpers](#11-debugging-helpers)
12. [What is not part of the API](#12-what-is-not-part-of-the-api)
13. [Reference constants](#13-reference-constants)
14. [Complete example](#14-complete-example)
15. [Before you submit](#15-before-you-submit)
16. [Where to look next](#16-where-to-look-next)
17. [Appendix — how this document was verified](#appendix--how-this-document-was-verified)

---

## 1. The golden rule

**Reason from sensors, never from ground truth.**

Your controller must behave as if it only has noisy, intermittently unavailable
measurements — because in the real competition that is exactly what it has. Read
`measured_gps_position()`, not `true_position()`.

The simulator enforces this. While your `control()` or
`define_message_for_all()` is running, calling a `true_*` accessor raises
`TrueStateAccessError`:

```python
from swarm_rescue.simulation.drone.drone_abstract import TrueStateAccessError
```

The `true_*` accessors stay reachable for debugging, logging, and drawing, and
the reporting code uses them. Reading them to decide what to do is cheating: it
makes the simulated sensor noise pointless.

### Using `true_*` inside `control()` — the debug switch

The guard is **not** global. It is raised only for the duration of your
`control()` and `define_message_for_all()` calls, and lowered again immediately
after. Anywhere else in your code, `true_position()` works normally — including
from a drawing or logging hook. Verified on a live drone:

```
outside control(): is_inside_participant_code() = False
                     true_position() -> [0. 0.]        works
inside control():   is_inside_participant_code() = True
                     true_position() -> TrueStateAccessError
after the block:    is_inside_participant_code() = False   (restored)
```

So for comparing your sensor readings against reality, you need nothing at all —
do it from a hook, which runs outside the guard:

```python
import numpy as np

class MyDrone(DroneAbstract):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._rows = []

    def draw_bottom_layer(self):
        # Runs OUTSIDE the guard: the ground truth is allowed here.
        truth = np.asarray(self.true_position())
        measured = self.measured_gps_position()
        if measured is not None:
            error = float(np.linalg.norm(truth - np.asarray(measured)))
            self._rows.append((self.elapsed_timestep, error))
            print(f"step {self.elapsed_timestep}: gps error {error:.1f} px")
```

Combine that with your own `control()` and `define_message_for_all()` — the hook
is the only part to copy. Measured over 30 steps of a test round, it reports a
per-step error around `7` px, mean `3.15` px: that is the noise you tolerate.

**If you really need it inside `control()`**, set one environment variable:

```bash
SWARM_RESCUE_ALLOW_TRUE_STATE=1 python examples/example_mapping.py
```

Accepted values are `1`, `true`, `yes`, `on` (case-insensitive). Then
`true_position()`, `true_angle()`, `true_velocity()` and
`true_angular_velocity()` work inside your controller, and `control()` can be
written as:

```python
def control(self):
    # Debug only: the exact position, no noise.
    truth = self.true_position()
    print(f"step {self.elapsed_timestep}: at {truth}")
    ...
```

Verified over a full 40-step round: with the variable unset the guard rejected
all 40 calls, and with it set all 40 returned a value. The switch is global, so
it covers a grasped wounded person's `true_position()` too.

Two things to know about the switch:

- **It is off by default and the evaluator never sets it.** It is an environment
  variable, so it cannot be left switched on by accident in a committed file.
  It is a debugging convenience, **not a security boundary**: the guard reads
  `os.environ` on every call, so code that sets the variable itself would
  bypass it. Do not do that. The evaluator controls the scoring run, and a
  controller that reads the ground truth is cheating whatever the guard does;
  your code is there to be read.
- **Turning it off does not remove the noise, only the error message.** Your
  sensors keep their noise and keep returning `None` in the disabling zones.
  Code tuned against `true_position()` will fall apart on real sensor data, so
  use the switch to *understand* a bug, then switch it off and fix the cause.

Draw and log callbacks (`draw_bottom_layer`, `draw_top_layer`) are framework
plumbing: override them for local debugging, but do not rely on them in a
submitted solution.

---

## 2. What you write

Two files matter:

| File | Purpose |
| --- | --- |
| `src/swarm_rescue/solutions/my_drone_XXX.py` | Your drone class. This is your code. |
| `src/swarm_rescue/solutions/my_drone_eval.py` | Wires your class into the evaluation. You only edit the import and the base class. |

`my_drone_eval.py` looks like this:

```python
from swarm_rescue.solutions.my_drone_random import MyDroneRandom


class MyDroneEval(MyDroneRandom):
    pass
```

The same code runs on every drone of the swarm: each drone is a separate
instance of your class, distinguished by `self.identifier`. Never assume a drone
is alone, and never assume an `identifier`.

---

## 3. The two methods you must implement

### `control(self) -> CommandsDict`

Called once per simulation step, at 30 steps per second. This is where your
logic lives.

```python
def control(self) -> CommandsDict:
    command = {
        "forward": 1.0,    # [-1.0, 1.0]  forward / backward
        "lateral": 0.0,    # [-1.0, 1.0]  strafe left / right
        "rotation": -1.0,   # [-1.0, 1.0]  turn one way / the other
        "grasper": 0,      # 0 or 1       open (0) / close (1)
    }
    return command
```

- A key you omit is simply left at its default: `0` for the three continuous
  axes and `0` for the grasper. So the dictionary may be sparse, but returning
  all four is clearer. A key the simulator does not know raises `KeyError` and
  ends the run, so do not invent names.
- `forward`, `lateral` and `rotation` are continuous in `[-1.0, 1.0]`.
  `1.0` is full deflection, `0.0` is neutral. `rotation` is signed: positive
  turns one way, negative the other.
- `grasper` is discrete: `0` opens, `1` closes.
- **Values are not clamped for you.** A value outside its valid range raises a
  `ValueError` inside `control()`, and nothing catches it: the round ends.
  Verified on a live simulation, `{"forward": 2.0, ...}` produced
  `ValueError: Invalid command '2.0' for controller 'forward'`. So a proportional
  controller must clip its own output, e.g.
  `float(np.clip(value, -1.0, 1.0))`. The grasper takes `0` or `1` (Python
  equality means `0.0` and `1.0` are accepted too); anything else raises.
- Returning `2.0` "because it will be normalized" is wrong: there is no
  normalization step. Keep every output in range.

Keep `control()` fast. It runs 30 times per simulated second, for every drone.

### `define_message_for_all(self)`

Returns the payload this drone broadcasts to every neighbor inside
communication range. Return `None` if you do not communicate.

```python
def define_message_for_all(self):
    msg_data = (self.identifier,
                (self.measured_gps_position(),
                 self.measured_compass_angle()))
    return msg_data
```

The return value is opaque to the simulator: it is stored and handed back to the
receivers unchanged. Put whatever your team needs in it, and agree on the layout
across your own drones. Note that anything you send is also sent in the clear to
every other drone in range, so size it deliberately — it is broadcast every step.

---

## 4. Reading measurements

These are the calls a controller should use. All of them are **noisy**, and all
of them can be **disabled** by a special zone, in which case they return `None`.

| Call | Returns | Notes |
| --- | --- | --- |
| `measured_gps_position()` | `np.ndarray` shape `(2,)`, or `None` | Position in pixels, `(x, y)`. |
| `measured_compass_angle()` | `float` in `[-pi, pi]`, or `None` | Heading in radians. |
| `measured_velocity()` | `np.ndarray` shape `(2,)`, or `None` | Pixels **per step** (not per second), from odometer + compass. |
| `measured_angular_velocity()` | `float`, or `None` | Radians **per step** (not per second). |
| `lidar_values()` | `np.ndarray` shape `(181,)`, or `None` | Distance per ray. |
| `lidar_rays_angles()` | `np.ndarray` of angles | Index-aligned with `lidar_values()`. |
| `semantic_values()` | `list` of `Data`, or `None` | What the drone sees, classified. |
| `odometer_values()` | `np.ndarray`, or `None` | Raw odometry. |
| `gps_values()` / `compass_values()` | as above | Same data as the `measured_*` calls. |

**Always handle `None`.** A drone that enters a No GPS zone legitimately gets
`None` from `measured_gps_position()`. Unhandled, this is the single most common
cause of a controller crashing mid-round. A safe pattern:

```python
position = self.measured_gps_position()
if position is None:
    # Sensor disabled: hold still rather than act on stale data.
    return {"forward": 0.0, "lateral": 0.0, "rotation": 0.0, "grasper": 0}
```

### Coordinates

- Units are **pixels** in map space, not meters. `self.size_area` gives the map
  size as `(width, height)`, but it is `None` if the drone was built without
  `MiscData`; treat it as an optional hint, not a guarantee.
- World **+X is right, +Y is up**, matching a standard right-handed frame.
- Angles are in radians, in `[-pi, pi]`.
- **`rotation` is positive counter-clockwise**, i.e. toward the left in this
  frame: `rotation = +1.0` increases the compass angle. That is the convention
  the `bearing = atan2(dy, dx) - heading` steering of section 14 relies on.

---


## 5. Sensors in detail

### Lidar — `lidar_values()` / `lidar_rays_angles()`

A range sensor. Defaults:

| Property | Value |
| --- | --- |
| Rays | `181` |
| Field of view | `360 deg` (full circle) |
| Max range | `300` |

- `lidar_values()[i]` is the distance along ray `i`, in pixels.
- `lidar_rays_angles()[i]` is that ray's angle in radians, **relative to the
  drone's heading**, spanning `-pi` to `+pi`.
- Index `i` pairs the two arrays: a value and its direction.

Verified on a drone with no obstacles: `n=181, first=-3.142, middle=0.000,
last=3.142`. The angles come from `np.linspace(-pi, +pi, 181)`, so index 0 and
index 180 both point straight backwards (`-pi` and `+pi` are the same
direction), and the two ends are therefore the same ray. Reading the array in
order, index 90 points straight ahead, indices `0..90` sweep the **right** side
(negative angles) and `90..180` the **left** side (positive angles). There is no
"behind-left / behind-right" pair at the ends.

Rays that hit nothing report the max range. Since the sensor is noisy, treat a
reading close to `300` as "nothing there", not as an obstacle at 300.

To convert a ray reading into a world point:

```python
import numpy as np

position = self.measured_gps_position()
angle    = self.measured_compass_angle()
distances  = self.lidar_values()
ray_angles = self.lidar_rays_angles()

absolute = ray_angles + angle          # rays are relative to heading
hit_x = position[0] + distances * np.cos(absolute)
hit_y = position[1] + distances * np.sin(absolute)
```

`examples/example_mapping.py` builds an occupancy grid this way.

### Semantic sensor — `semantic_values()`

Tells you *what* you are seeing, not just how far. Defaults: 360 deg field of
view, `200` max range. Returns a list of `Data` named tuples:

| Field | Meaning |
| --- | --- |
| `distance` | Distance in pixels. |
| `angle` | Bearing in radians, relative to heading. |
| `entity_type` | What was hit (see below). |
| `grasped` | Whether the drone has already grasped it. |

In practice `entity_type` is one of `WOUNDED_PERSON`, `RESCUE_CENTER` or
`DRONE` — those are the only three this competition reports.

`TypeEntity.WALL` and `TypeEntity.OTHER` exist in the enum but are never
returned: the semantic sensor deliberately does not report walls, and it reports
no distance or angle for them if it did. **Use the lidar for walls** — treat a
missing `WALL` branch as expected behavior, not as a bug in your code. Verified
by flying next to the walls of `walls_medium_02`: only `DRONE`,
`RESCUE_CENTER` and `WOUNDED_PERSON` were ever observed.

Bearing convention, verified on a flying drone:

| Situation | Reported `angle` |
| --- | --- |
| Straight ahead | `0.0` |
| To the left | positive (about `+1.57`) |
| To the right | negative (about `-1.57`) |
| Behind | about `+/-3.14` |

A single object can be reported at two adjacent angles — two rays hit its two
sides. Deduplicate by distance before acting on a detection.

```python
for data in self.semantic_values() or []:
    if data.entity_type == DroneSemanticSensor.TypeEntity.WOUNDED_PERSON:
        if abs(data.angle) < 0.3:          # roughly straight ahead
            return {"forward": 0.5, "lateral": 0.0,
                    "rotation": 0.0, "grasper": 1}
```

The sensor returns entities only, and only what the drone can actually see. A
rescue center 200 pixels away behind a wall will not be reported.


---

## 6. State you may read

| Member | Type | Meaning |
| --- | --- | --- |
| `drone_health` | `int` | Remaining health. Starts at `40`. |
| `size_area` | `tuple` or `None` | Map size `(width, height)` in pixels, `None` if unavailable. |
| `identifier` | `int` | This drone's index. Unique per round. |
| `grasped_wounded_persons()` | `list` | Wounded persons currently held. |
| `communicators` | `list` | Attached communicators. |

### `drone_health`

Starts at `DRONE_INITIAL_HEALTH = 40`. A collision with a wall or another drone
costs one point, at most once per 30 steps (one simulated second). At zero the
drone is destroyed.

A destroyed drone becomes a wreck. How it behaves depends on the cause of death,
and this matters for your path planning:

- **Destroyed by damage** (`DEATH_BY_DAMAGE`): the wreck is passable and
  invisible to the sensors. Other drones can fly through it and stop seeing it.
- **Destroyed by a kill zone** (`DEATH_BY_KILL_ZONE`): the wreck stays solid and
  stays visible. It remains an obstacle.

Either way the wreck stops communicating: it sends and receives nothing, and it is
not reported in another drone's `communicator.comms_in_range`. So a neighbor that
disappears from your swarm map, but whose wreck you can still see, is a destroyed
drone, not one that merely left the range.

So an area can become physically flyable after a drone dies in a collision, while
a kill-zone wreck is permanent clutter. Verified: health stayed at `40` for a
200-step run with no collisions.

### `position`, `angle`, `velocity`, `angular_velocity` — disabled

These four properties are **traps**, not part of the participant API. Accessing
one raises an `AttributeError` whose message names the accessor to use instead:

| Disabled property | Message points to |
| --- | --- |
| `position` | `measured_gps_position()` |
| `angle` | `measured_compass_angle()` |
| `velocity` | `measured_velocity()` |
| `angular_velocity` | `measured_angular_velocity()` |

For example, `self.position` raises
`AttributeError: self.position is disabled: it would return the exact ground truth. Use self.measured_gps_position() instead.`

This is deliberate: it makes the migration from "true value" to "measured value"
impossible to miss, and it means an old solution that reads `self.position` fails
loudly instead of quietly cheating. Because they are not in `PARTICIPANT_API`,
the naming check of section 12 also flags any solution that still uses them.

---

## 7. Special zones

Zones disable sensors or communication. Your drone must keep working inside them.

| Check | Meaning when `True` |
| --- | --- |
| `semantic_is_disabled()` | Semantic sensor unavailable. |
| `lidar_is_disabled()` | Lidar unavailable. |
| `gps_is_disabled()` | `measured_gps_position()` returns `None`. |
| `compass_is_disabled()` | `measured_compass_angle()` returns `None`. |
| `odometer_is_disabled()` | Odometer unavailable. |
| `communicator_is_disabled()` | No messages sent or received. |

The zone types are `NoGpsZone`, `NoComZone` and `KillZone`.

A kill zone does more than disable: it destroys the drone. Losing the GPS in a No
GPS zone is survivable; losing the drone is not, so treat the boundaries as
obstacles your planner should avoid.

These are also your **diagnostics**. When a sensor returns `None` unexpectedly,
check the corresponding `*_is_disabled()` to tell "the zone took my sensor" apart
from "my code is broken".

---

## 8. Grasping

Grasping and carrying a wounded person is the core objective.

- Command key `"grasper"`: `1` closes, `0` opens.
- Check what you hold with `self.grasped_wounded_persons()`. Empty list means
  holding nothing.
- A wounded person is grasped while the grasper is closed **and** the drone is in
  contact with them. The collision is re-armed every step it lasts, so keeping
  `"grasper": 1` while pushing toward the person works, whether you close on
  approach or after touching. Driving into them with `0` never grasps.
- Carrying slows you down a lot, so plan the return trip for it. Nothing flips a
  `LINEAR_SPEED_RATIO` on your drone: it keeps `LINEAR_SPEED_RATIO = 3.0` all
  the time. The slowdown is physical: the wounded person is a 100 kg body that
  your 50 kg drone now drags along through a pivot joint, with
  `LINEAR_SPEED_RATIO_WOUNDED = 1.0` as the force ratio of *that* body. Measured
  on a straight-line run, terminal speed fell from about `11.4` to `3.6`
  px/step, i.e. roughly a third. Plan the return leg at that speed.

The API gives you the individual pieces; how you sequence them is your design
choice. Three facts that shape it:

- **Closing the grasper does not mean the grasp succeeded.** The command is
  applied whether or not a person was in range. `grasped_wounded_persons()` is
  the only thing that reports what you actually hold, so it — not the command you
  sent — is what tells you whether to start carrying.
- **The list is either empty or holds one person; it is not a count of
  attempts.** A drone can hold one person at a time, and a failed attempt leaves
  it empty exactly like never having tried.
- **A carried person is released by the same command that grabs.** There is no
  separate drop action, and no "release near the center" rule: the simulator
  releases wherever the grasper opens. Delivering is your logic, not the
  simulator's.

`examples/example_semantic_sensor.py` puts these together into a working rescue,
and `examples/example_static_semantic_sensor.py` shows the semantic detections on
their own. Both are reference implementations, not a required structure — your
own controller is free to work in any way you like.


---

## 9. Communication

Drones exchange messages within `RANGE_COMMUNICATION = 250` pixels.

**Sending** is `define_message_for_all()`; its return value is broadcast to every
neighbor in range.

**Receiving** — read `self.communicator.received_messages`, a list of
`(sender_communicator, message)` pairs:

```python
def control(self):
    for sender, msg in self.communicator.received_messages:
        peer_id, (px, py, heading) = msg
        # ... use it
    return {"forward": 0.0, "lateral": 0.0, "rotation": 0.0, "grasper": 0}
```

- The list holds the messages received during the current step, paired with the
  communicator that sent them. `sender.agent` is the sending drone.
- `self.communicators` lists your own attached communicators.
- `communicator.transmission_range` and `communicator.comms_in_range` are
  available if you need the topology.
- Communication is symmetric and unicast-per-pair: you receive each neighbor's
  message once per step, from every neighbor in range.
- Inside a No Com Zone, nothing is sent or received. Check
  `communicator_is_disabled()` before trusting your map of the swarm.

Verified: two drones started 300 pixels apart (beyond the 250 range) exchanged no
messages until they closed the distance, then each received one message per step
(`146` messages each over 200 steps).

A worked example is `src/swarm_rescue/solutions/my_drone_lidar_communication.py`.

---

## 10. Sensor accessors

For each sensor there is an accessor returning the device itself, and a matching
`..._values()` returning the reading.

| Accessor | Device | Values call |
| --- | --- | --- |
| `lidar()` | `DroneLidar` | `lidar_values()` |
| `semantic()` | `DroneSemanticSensor` | `semantic_values()` |
| `gps()` | `DroneGPS` | `gps_values()` |
| `compass()` | `DroneCompass` | `compass_values()` |
| `odometer()` | `DroneOdometer` | `odometer_values()` |

Prefer the `..._values()` calls in a controller: they are the short path and the
one the API is written around. Reach for the device object only when you need
something the short form does not expose, such as `self.lidar().ray_angles`.

---

## 11. Debugging helpers

Two helpers are supported, and both must be off in a submitted solution.

- `self.display()` — draws the lidar graph if enabled.
- `self.display_lidar_graph()` — opens a matplotlib window with the lidar data.

Enable them through the constructor:

```python
super().__init__(display_lidar_graph=True, **kwargs)
```

`examples/example_display_lidar.py` shows the graph, including sensor noise.

---

## 12. What is *not* part of the API

A drone exposes more than you should use. The simulator itself calls `pre_step()`,
`collide_wall()` and the `draw_*` family on every drone it holds, so those cannot
be renamed with a leading underscore, and their existence does not make them
supported.

The supported set is published in code, and a test enforces that it does not
drift:

```python
from swarm_rescue.simulation.drone.drone_abstract import PARTICIPANT_API
```

`PARTICIPANT_API` lists every supported name, methods, and instance attributes
alike (`identifier`, `grasper`, `communicator`, `elapsed_timestep`,
`elapsed_walltime` are assigned in `__init__` and listed there too).

---

## 13. Reference constants

From `swarm_rescue.simulation.utils.constants`:

| Constant | Value | Meaning |
| --- | --- | --- |
| `FRAME_RATE` | `1/30` | Simulated seconds per step (30 steps per second). |
| `DRONE_INITIAL_HEALTH` | `40` | Starting health. |
| `COLLISION_DAMAGE_COOLDOWN_STEPS` | `30` | Steps between two collision damages. |
| `LINEAR_SPEED_RATIO` | `3.0` | Force ratio of the drone's body, free flight. |
| `LINEAR_SPEED_RATIO_WOUNDED` | `1.0` | Force ratio of a wounded person's body (not of the carrying drone). |
| `ANGULAR_SPEED_RATIO` | `0.6` | Angular speed ratio. |
| `RANGE_COMMUNICATION` | `250` | Communication radius in pixels. |
| `RESOLUTION_LIDAR_SENSOR` | `181` | Lidar ray count. |
| `MAX_RANGE_LIDAR_SENSOR` | `300` | Lidar max range. |
| `FOV_LIDAR_SENSOR` | `360` | Lidar field of view, degrees. |
| `RESOLUTION_SEMANTIC_SENSOR` | `35` | Semantic ray count. |
| `MAX_RANGE_SEMANTIC_SENSOR` | `200` | Semantic max range. |
| `FOV_SEMANTIC_SENSOR` | `360` | Semantic field of view, degrees. |
| `DEATH_BY_DAMAGE` | `"damage"` | Death cause: passable, sensor-invisible wreck. |
| `DEATH_BY_KILL_ZONE` | `"kill_zone"` | Death cause: solid, still-visible wreck. |

```python
from swarm_rescue.simulation.utils.constants import (
    DRONE_INITIAL_HEALTH,
    MAX_RANGE_LIDAR_SENSOR,
    RANGE_COMMUNICATION,
)
```

---

## 14. Complete example

A minimal drone that shows every API concept in one place: search with the
semantic sensor, grasp a wounded person, carry it back to the rescue center,
drop it, repeat. It also `None`-checks its sensors and keeps clear of walls with
the lidar.

**Read it as an API demonstration, not a competition-grade controller.** It has
no map, so it has no global plan: it heads for the last place it saw the rescue
center and otherwise sweeps. It flies cleanly and never raises, but whether it
actually completes a rescue depends on the sensor noise — it is not a reliable
solver. Beating that needs the occupancy grid of `examples/example_mapping.py`
plus a real path planner.

```python
import numpy as np

from swarm_rescue.simulation.drone.controller import CommandsDict
from swarm_rescue.simulation.drone.drone_abstract import DroneAbstract
from swarm_rescue.simulation.ray_sensors.drone_semantic_sensor import (
    DroneSemanticSensor,
)


class MyDrone(DroneAbstract):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Last place the rescue center was seen, as (x, y) in map pixels.
        self.center_hint = None

    def define_message_for_all(self):
        # Broadcast id and pose so teammates can coordinate.
        return (self.identifier,
                (self.measured_gps_position(),
                 self.measured_compass_angle()))

    @staticmethod
    def _stop():
        return {"forward": 0.0, "lateral": 0.0, "rotation": 0.0, "grasper": 0}

    def _toward(self, bearing, distance):
        """Turn toward a relative bearing, creep forward if nearly aligned."""
        command = {"forward": 0.0, "lateral": 0.0,
                   "rotation": 0.0, "grasper": 0}
        if abs(bearing) > 0.3:
            command["rotation"] = float(np.clip(bearing, -1.0, 1.0))
        elif distance > 20.0:
            command["forward"] = 0.5
        return command

    def _is_clear_ahead(self, margin=60.0):
        """False when something is close in front of us.

        Lidar rays are relative to the heading, so the rays around the middle of
        the array are the ones pointing forward. A ray reading at the max range
        means "nothing there".
        """
        lidar = self.lidar_values()
        if lidar is None:
            return False
        forward = lidar[80:101]
        return bool(np.min(forward) > margin)

    def _goto(self, target_xy):
        """Steer toward a world point, using the GPS and the compass."""
        position = self.measured_gps_position()
        heading = self.measured_compass_angle()
        if position is None or heading is None:
            return self._stop()
        dx = target_xy[0] - position[0]
        dy = target_xy[1] - position[1]
        distance = float(np.hypot(dx, dy))
        bearing = float(np.arctan2(dy, dx) - heading)
        # Keep the bearing in [-pi, pi] or the turn will take the long way.
        bearing = (bearing + np.pi) % (2 * np.pi) - np.pi
        command = self._toward(bearing, distance)
        if abs(bearing) < 0.3 and not self._is_clear_ahead():
            command["rotation"] = 0.4      # blocked: turn to get around
        return command

    def control(self) -> CommandsDict:
        # Sensors can be switched off by a zone: never act on None.
        semantic = self.semantic_values()
        if semantic is None:
            return self._stop()

        wounded = [d for d in semantic
                   if d.entity_type
                   == DroneSemanticSensor.TypeEntity.WOUNDED_PERSON]
        center = [d for d in semantic
                  if d.entity_type
                  == DroneSemanticSensor.TypeEntity.RESCUE_CENTER]
        # One object can be seen on two adjacent rays: keep the closest.
        wounded.sort(key=lambda d: d.distance)
        center.sort(key=lambda d: d.distance)

        # Remember where the center is each time we see it.
        if center:
            position = self.measured_gps_position()
            heading = self.measured_compass_angle()
            if position is not None and heading is not None:
                absolute = heading + center[0].angle
                self.center_hint = (position[0] + center[0].distance
                                    * float(np.cos(absolute)),
                                    position[1] + center[0].distance
                                    * float(np.sin(absolute)))

        # Carrying: the grasper stays closed for the whole trip.
        if self.grasped_wounded_persons():
            if center:
                command = self._toward(center[0].angle, center[0].distance)
            elif self.center_hint is not None:
                # Center out of sight: head for the last place it was seen,
                # rather than flying blind into the first wall.
                command = self._goto(self.center_hint)
            else:
                command = {"forward": 0.5, "lateral": 0.0,
                           "rotation": 0.4, "grasper": 1}
                if self._is_clear_ahead():
                    command["forward"] = 1.0
                    command["rotation"] = 0.0
                return command
            command["grasper"] = 1
            return command

        if wounded:
            target = wounded[0]
            command = self._toward(target.angle, target.distance)
            command["grasper"] = 1
            # Close the last few pixels whatever the lidar says: the wounded
            # person is itself an obstacle at that range, so braking here would
            # stall the drone just short of the grasp.
            if target.distance > 30.0 and not self._is_clear_ahead(margin=40.0):
                command["forward"] = 0.0
            return command

        # Nothing in sight: sweep slowly to search, staying off the walls.
        command = {"forward": 0.4, "lateral": 0.0,
                   "rotation": 0.3, "grasper": 0}
        if not self._is_clear_ahead():
            command["forward"] = 0.0
        return command
```

---

## 15. Before you submit

Checklist, in the order that catches the most problems:

1. **No `true_*` call in `control()` or `define_message_for_all()`.** It raises.
2. **No `.position` / `.angle` / `.velocity` / `.angular_velocity`.** They raise.
3. **Every sensor read is `None`-checked.** A zone will take each of them away.
4. **No infinite loop or crash inside a zone.** Especially the kill zone.
5. **Every command value in range** (`[-1.0, 1.0]` for the three axes, `0`/`1`
   for the grasper); no unknown keys.
6. **`print(...)` removed**, OpenCV and matplotlib windows off
   (`display_lidar_graph=False`, no `cv2.imshow`).
7. **Runs on a clean checkout** without your local edits.
8. **Runs headless** (`--headless`): your solution must not depend on the window.

Then follow `submission_guidelines.md` for the required files and the naming
convention (`teamXXX_evalstep`), and use `create_zip_submission.sh` to build the
archive.

---

## 16. Where to look next

| Resource | What it shows |
| --- | --- |
| `src/swarm_rescue/solutions/my_drone_random.py` | Lidar usage and basic control. |
| `src/swarm_rescue/solutions/my_drone_lidar_communication.py` | Inter-drone communication. |
| `src/swarm_rescue/solutions/my_drone_motionless.py` | Minimal template. |
| `examples/example_semantic_sensor.py` | Grasping a wounded person and bringing it back. |
| `examples/example_mapping.py` | Building an occupancy grid from the lidar. |
| `examples/example_disablers.py` | Every disabling zone. |
| `examples/example_pid_rotation.py` | PID on orientation. |
| `examples/example_headless.py` | Running without a window. |
| `submission_guidelines.md` | Required files and packaging. |
| `README.md` | Maps, evaluation plan, launcher. |

---

## Appendix — how this document was verified

Behavioral claims here were checked against the running simulator rather than
read off the source alone:

- Command validation: `99.0` and `2.0` both raise
  `ValueError: Invalid command ... for controller ...`, and the exception escapes
  `control()` uncaught, ending the round. Missing keys keep their default; an
  unknown key raises `KeyError`.
- `TrueStateAccessError`: raised when `true_position()` was called inside
  `control()` under `GuiSR`. The guard is installed by the GUI loop, so it is
  active in any real or headless round.
- Sensors: over a 200-step, 2-drone round, `lidar_values()` had length `181` at
  every step and no sensor returned `None` outside a zone.
- Lidar angles: `181` rays spanning `-3.142` to `+3.142`, middle ray `0.000`.
- Semantic bearings, measured on a flying drone: ahead `0.0`, left about `+1.57`,
  right about `-1.57`, behind about `+/-3.14`; a single object reported at two
  adjacent angles.
- Semantic entity types observed: `DRONE`, `RESCUE_CENTER`, `WOUNDED_PERSON`.
- Communication: two drones starting 300 px apart (> the 250 px range) exchanged
  nothing, then one message per step each once in range (146 messages over 200
  steps).
- Health: `40` throughout a collision-free 200-step run.
- `PARTICIPANT_API` membership: every listed name resolves (on the class, or on
  a live drone for the `__init__` attributes), none is private, and
  `true_position` and the four trap properties are deliberately absent — all
  enforced by `tests/test_participant_api.py`.
- The section 14 example was extracted from this document and run as-is. It flies
  without raising on every layout tried (open map, wounded person near the
  center, drone starting at the center, a No GPS zone in between, and a short
  round). Completing the rescue is **not** guaranteed: it delivered the wounded
  person on an open map in one run and did not in another with the same
  starting conditions, because the sensor noise makes it stochastic. It has no
  map and no global planner. Treat it as a working example of the API, not as a
  solution that scores.

---
