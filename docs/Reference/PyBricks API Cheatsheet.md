---
title: PyBricks API Cheatsheet
type: reference
status: current
updated: 2026-10-28
tags: [lego, spike, pybricks, api, reference]
---

# PyBricks API Cheatsheet

The calls we actually use. Checked against the PyBricks documentation (v3.6–v4.x) on
2026-10-28, **not** against this team's installed firmware. Verify anything marked **check** on
the hub.

## Imports

```python
from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor, ColorSensor, DistanceSensor, ForceSensor
from pybricks.parameters import Port, Direction, Stop, Color, Axis
from pybricks.robotics import DriveBase
from pybricks.tools import wait, StopWatch
```

Other hubs have their own classes (`InventorHub`, `EssentialHub`, `TechnicHub`). Confirm the
class that matches your hardware.

## Hub

```python
hub = PrimeHub()                      # default top_side=Axis.Z, front_side=Axis.X
hub = PrimeHub(top_side=Axis.Z, front_side=Axis.X)   # match the real mounting

hub.speaker.beep(frequency=500, duration=200)
hub.light.on(Color.GREEN)
hub.display.text("Go")
```

## IMU

```python
hub.imu.heading()          # degrees, 0 at program start, + = clockwise
hub.imu.angular_velocity(Axis.Z)   # deg/s
hub.imu.tilt()             # (pitch, roll) in degrees
hub.imu.reset_heading(0)   # fails if a DriveBase is using the gyro
```

- `heading()` **keeps growing** past 180° and does **not** wrap to `−180`. Normalise it yourself.
- To reset heading while a drive base uses the gyro, call `drive_base.reset(angle=0)` instead.
- On a ramp the flat-surface heading is wrong; the docs mention a 3D option. Do not rely on it
  without testing.

## Motors

```python
motor = Motor(Port.A, positive_direction=Direction.CLOCKWISE)

motor.run(speed)                    # deg/s
motor.run_time(speed, time, then=Stop.HOLD, wait=True)
motor.run_angle(speed, angle, then=Stop.HOLD, wait=True)
motor.run_target(speed, target_angle, then=Stop.HOLD, wait=True)
motor.angle()                      # deg, accumulates
motor.reset_angle(0)
motor.stop()
```

- `positive_direction` sets which physical direction counts as positive.
- Motor angle is **motor** degrees, not wheel degrees.

## DriveBase

```python
drive = DriveBase(left_motor, right_motor, wheel_diameter=56, axle_track=112)
drive.use_gyro(True)               # gyro for straight and turns

drive.settings(
    straight_speed=300,            # mm/s
    straight_acceleration=600,     # mm/s²
    turn_rate=180,                 # deg/s
    turn_acceleration=360,         # deg/s²
)

drive.straight(500)               # mm, + forward
drive.turn(90)                    # deg, + = RIGHT (clockwise)
drive.turn(-90, absolute=False)   # - = left
drive.drive(speed=200, turn_rate=0)          # mm/s, deg/s
drive.stop(Stop.HOLD)

drive.distance()                  # mm since reset
drive.angle()                     # deg, + clockwise
drive.state()                     # (distance, speed, angle, turn_rate)
drive.reset(distance=0, angle=0)
```

Sign rules from the docs:

- Positive distance, radius, and straight speed mean **forward**.
- Positive angle and turn rate mean **turning right** (clockwise).
- `turn(..., absolute=True)` turns to an absolute heading instead of a relative angle.

Advanced: `drive.distance_control` and `drive.heading_control` are PID objects. Use them instead
of layering a second controller on top. **check** the exact attributes on your version.

## Sensors

```python
colour = ColorSensor(Port.C)
colour.color()          # Color enum
colour.reflection()     # 0–100 reflected light
colour.ambient()        # 0–100 ambient light
colour.hsv()            # (h, s, v)

distance = DistanceSensor(Port.D)
distance.distance()     # mm

force = ForceSensor(Port.E)
force.force()           # N
force.pressed()
```

The reflection scale direction (dark high or low) depends on the surface — **measure it**.

## Timing

```python
wait(500)               # ms

timer = StopWatch()
elapsed = timer.time()  # ms
timer.reset()
```

`StopWatch` is the right way to measure `dt` for a PID loop. Do not build one from repeated
`wait(10)` calls and assume 10 ms.

## Version caveats

- `angle()` returns `int` in v3.6 and `float` in later docs. Do not assume sub-degree precision.
- `arc()` exists in recent versions; older ones differ. **check**.
- `use_gyro()` behaviour and gyro calibration options vary by version. **check**.
- The hub's gyro can report e.g. 357° for a physical 360°; `imu.settings(heading_correction=...)`
  compensates. Measure before trusting long turns.

## Related

- [[docs/Reference/SPIKE Hardware|SPIKE hardware]]
- [[docs/Systems/Drive Base|Drive base]]
- [[docs/Guides/PyBricks Workflow|PyBricks workflow]]
