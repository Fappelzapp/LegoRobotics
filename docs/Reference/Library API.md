---
title: Library API
type: reference
status: proposed
updated: 2026-10-28
tags: [lego, spike, api, reference]
---

# Library API

The contract `src/lib/` aims to provide. **Nothing here is implemented yet** unless the file
exists and the session note says so. Reconcile this with the team's incoming drive base code
rather than rewriting that code to match a proposal.

## Principles

- Pure maths modules (`geometry`, `pid`, `odometry`, `grid`) **never import `pybricks`**, so
  `tests/` runs on a laptop.
- Hardware wrappers (`drivebase`, `linefollow`) import `pybricks` and stay thin.
- Units are explicit in every name: `_mm`, `_deg`, `_dps`, `_mms`.

## `config.py`

```python
WHEEL_DIAMETER_MM: float
AXLE_TRACK_MM: float
GEAR_RATIO: float
LEFT_MOTOR_INVERTED: bool
RIGHT_MOTOR_INVERTED: bool

# each value carries a provenance comment: measured / datasheet / guessed
```

## `geometry.py`

```python
wheel_circumference_mm(diameter_mm) -> float
mm_per_motor_deg(diameter_mm, gear_ratio) -> float
motor_deg_for_mm(distance_mm, diameter_mm, gear_ratio) -> float
motor_deg_for_turn(angle_deg, axle_track_mm, diameter_mm, gear_ratio) -> float
wrap_deg(angle_deg) -> float          # to (-180, 180]
arc_pose(x, y, theta_deg, d_mm, dtheta_deg) -> tuple[float, float, float]
```

## `pid.py`

```python
class PID:
    def __init__(self, kp, ki, kd, output_limit, i_limit, deadband=0.0,
                 derivative_on_measurement=True): ...
    def reset(self) -> None: ...
    def update(self, target, measured, dt) -> float: ...
```

Guarantees:

- clamps integral and output separately;
- derivative on measurement, no kick on target steps;
- treats `|error| < deadband` as zero;
- returns `0.0` for `dt <= 0` instead of dividing by zero.

## `odometry.py`

```python
class Pose:
    x_mm: float
    y_mm: float
    theta_deg: float          # clockwise positive

class Odometry:
    def __init__(self, axle_track_mm, start_pose=None): ...
    def reset(self, pose: Pose) -> None: ...
    def update(self, left_mm, right_mm, gyro_deg=None, dt=None) -> Pose: ...
    def pose(self) -> Pose: ...
```

`update` takes **increments** in mm since the previous call. If `gyro_deg` is supplied, it wins
for heading.

## `drivebase.py`

```python
class Drive:
    def straight(self, distance_mm, speed_mms) -> None: ...
    def turn(self, angle_deg, rate_dps) -> None: ...
    def drive(self, speed_mms, turn_rate_dps) -> None: ...
    def stop(self, brake=True) -> None: ...
    def distance_mm(self) -> float: ...
    def angle_deg(self) -> float: ...     # clockwise positive
    def reset(self) -> None: ...
```

This may wrap PyBricks `DriveBase` or drive `Motor` objects directly. Whichever it does, it owns
the only place motor power is written.

## `motion.py`

```python
class Motion:
    def __init__(self, drive, odometry=None, pid_factory=None): ...
    def straight_to(self, distance_mm, speed_mms) -> bool: ...
    def turn_to(self, heading_deg, rate_dps) -> bool: ...
    def hold_heading(self, heading_deg) -> None: ...
```

Each `to` method blocks until settled and returns success. If it returns `False`, the caller
must decide whether to abort — never silently continue to the next mission step.

## `grid.py`

```python
class Grid:
    def __init__(self, resolution_mm, blocked_cells): ...
    def world_to_cell(self, x_mm, y_mm) -> tuple[int, int]: ...
    def cell_to_world(self, i, j) -> tuple[float, float]: ...
    def is_free(self, i, j) -> bool: ...
    def plan(self, start_xy, goal_xy) -> list[tuple[float, float]] | None: ...
```

`plan` returns world-space points, or `None` when unreachable. A\* with 8-connectivity, no
corner cutting, deterministic tie-break.

## `linefollow.py`

```python
class LineFollower:
    def __init__(self, left_sensor, right_sensor, base_speed_mms, gains): ...
    def calibrate(self) -> None: ...
    def follow(self, max_ms=None) -> str: ...    # "line", "lost", "timeout"
```

## Related

- [[docs/Systems/Robot Overview|Robot overview]]
- [[docs/Code Style|Code style]]
- [[docs/Systems/Connected Grid|Connected grid]]
