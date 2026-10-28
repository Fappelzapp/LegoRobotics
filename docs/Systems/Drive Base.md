---
title: Drive Base
type: system
status: proposed
updated: 2026-10-28
tags: [lego, spike, drivebase, geometry]
---

# Drive Base

The two-wheel differential drive: geometry, motor polarity, and the straight/turn primitives
everything else builds on.

## Responsibility

- Own the physical constants: wheel diameter, track width, gear ratio, motor polarity.
- Convert **millimetres** and **degrees** into motor commands.
- Provide `straight`, `turn`, and `arc` primitives.
- Not responsible for path planning, PID tuning policy, or mission logic.

## Source and evidence

- Source: `src/lib/config.py`, `src/lib/drivebase.py` (scaffold; team's implementation pending)
- Context: proposal and standard differential-drive kinematics
- Evidence: textbook geometry, **not measured**
- Verified: not yet — wheel diameter and track width are unmeasured

## Coordinate and sign convention

We follow the **PyBricks convention** so platform calls need no sign flip:

- **+X** forward, **+Y** to the robot's **right**, **θ clockwise** from +X (compass/bearing).
- Positive `turn()` and positive `θ` mean turning **right**. This matches `DriveBase.turn()` and
  `hub.imu.heading()`.
- Positive motor power drives the robot forward, after polarity correction.
- Left motor is on −Y, right motor on +Y.

Do not mix conventions in one file. If imported code uses the opposite sign, convert once at
its boundary and note it here.

## Constants

| Constant | Meaning | Value | Source |
| --- | --- | --- | --- |
| `WHEEL_DIAMETER_MM` | Drive wheel diameter | TODO | measure |
| `AXLE_TRACK_MM` | Centre-to-centre distance between drive wheels | TODO | measure |
| `GEAR_RATIO` | Motor revolutions per wheel revolution | TODO | count teeth |
| `LEFT_MOTOR_INVERTED` | Mirror the left motor's sign | TODO | test on hub |
| `RIGHT_MOTOR_INVERTED` | Mirror the right motor's sign | TODO | test on hub |

A datasheet value is a starting point. The measured value wins, and the method is recorded in
[[docs/Guides/Agent Quickstart]].

## Kinematics

Wheel circumference:

```text
C = π · D
```

Distance travelled per **motor** degree (with gear ratio `G` = motor revs per wheel rev):

```text
mm_per_motor_deg = (π · D) / (360 · G)
```

Wheel distance for a rotation of `θ` degrees about the robot centre:

```text
wheel_distance_mm = (θ · π / 180) · (L / 2)
```

Velocity form, with `v` in mm/s and `ω` in rad/s, **clockwise positive**:

```text
v_L = v + ω · L / 2
v_R = v − ω · L / 2
```

and the inverse, used by odometry:

```text
v   = (v_L + v_R) / 2
ω   = (v_L − v_R) / L
```

## Primitives

| Command | Inputs | Output |
| --- | --- | --- |
| `straight(distance_mm, speed_mm_s)` | signed distance | both motors matched |
| `turn(angle_deg, rate_dps)` | signed angle, **positive = right** | wheels opposed |
| `arc(radius_mm, angle_deg, speed)` | signed radius/angle | inner wheel slower |
| `stop(brake=True)` | — | motors hold or coast |

`straight` and `turn` should be implemented as **closed-loop** commands (see
[[docs/Systems/Motion Control]]), not fixed-duration motor runs. Open-loop timing is acceptable
only for a first smoke test.

## Calibration

1. **Wheel diameter.** 10 wheel revolutions, measure ground distance, `D = distance / (10π)`.
2. **Track width.** Mark the floor contact centre of each wheel, measure across.
3. **Gear ratio.** Count teeth, or rotate the wheel 10 times and read the motor angle.
4. **Polarity.** Drive each motor +20 % with the robot raised; confirm forward.
5. **Repeatability.** Run `straight(1000)` three times and record the spread.

## Failure modes

| Symptom | Likely cause |
| --- | --- |
| Distances consistently 2× off | Radius used where diameter belongs, or vice versa |
| Robot curves on a straight command | One motor inverted, wheel sizes differ, or weight offset |
| Turns under/over-rotate by a fixed ratio | Track width or gear ratio wrong |
| Turns drift more as the run goes on | Wheel slip, battery sag, or no heading feedback |
| One side stalls at low power | Speed below the motor's minimum; raise the floor or add feedforward |

## Validation

- Offline: geometry functions unit-tested against hand-computed values.
- Hub: **not run — no hub connected**.
- Required next: measure diameter and track width, then record errors for 1000 mm and 90°.

## Related

- [[docs/Systems/Motion Control|Motion control]]
- [[docs/Systems/Odometry and Localization|Odometry]]
- [[docs/Reference/Drive Optimization|Drive optimisation]]
- [[docs/Guides/Agent Quickstart|Agent quickstart]]
