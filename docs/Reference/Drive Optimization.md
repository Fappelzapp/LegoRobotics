---
title: Drive Optimization
type: reference
status: proposed
updated: 2026-10-28
tags: [lego, spike, drivebase, optimization, reference]
---

# Drive Optimisation

How to make the drive base **faster and more repeatable** without trading away accuracy.
In competition robotics, repeatability usually beats peak speed.

## The metric that matters

Measure both, always:

1. **Run time** — seconds for the same mission.
2. **Repeatability** — spread of the final pose over several runs.

A robot that is 0.5 s faster but misses a mission 1 in 3 runs is slower in the score. Optimise
repeatability first; then remove time that costs no accuracy.

## Mechanical

### Mass and balance

- Remove unused structure. Mass costs acceleration and increases wheel slip under braking.
- Put the centre of mass **low and between the drive wheels**. Weight over the driven wheels
  improves traction; weight at the ends increases inertia and pitching.
- Keep the battery and hub low. Long lever arms amplify vibration and backlash.

### Traction

- Rubber tyres on a clean mat grip better than hard plastic. Clean the tyres; dust is a real
  cause of drift.
- Wider contact patches help, but only if the load is actually on them.
- Traction limit is roughly `a_max ≈ μ · g`. `μ` depends on the surface; do not assume a number
  without testing.

### Wheels and gearing

- **Wheel diameter** trades speed for torque and resolution: larger wheels are faster, but each
  encoder degree covers more ground and acceleration is harder.
- **Gear ratio** `G = motor revs / wheel rev`. Higher `G` = more torque, less speed. Lower `G` =
  faster, less torque and worse low-speed control.
- Estimate free speed:

```text
v_max = (π · D · motor_rpm) / (60 · G)
```

- Avoid gearing so tall that the robot cannot accelerate without slipping, or so short that the
  top speed is far below what the mission needs.

### Structure

- Brace the drive axles. Flex changes the effective track width and makes turns inconsistent.
- Minimise backlash in gears and axle joints; backlash is a dead zone your PID cannot see.
- Route cables so they cannot snag or pull on a sensor mid-run.
- Keep the robot symmetric; an offset mass curves every straight move.

## Motion profile

- **Acceleration limit.** Ramping speed avoids wheel slip, which corrupts odometry and wastes
  time in correction. A trapezoidal profile (accelerate, cruise, decelerate) is usually better
  than a step command.
- **Turn while driving** when the path allows it. Stopping at every waypoint costs time.
- **Avoid unnecessary stops.** Each stop adds settle time and a chance for backlash.
- **Smooth the path.** A grid path with 90° corners is slow; a diagonal or smoothed path is
  faster, if clearance allows.

## Calibration constants

Every constant below feeds distance and heading. Wrong values cannot be tuned away.

| Constant | Effect if wrong | How to measure |
| --- | --- | --- |
| Wheel diameter | Fixed distance scale error | Roll 10 revolutions |
| Track width | Fixed turn scale error | Centre-to-centre of contact patches |
| Gear ratio | Distance and speed scale error | Count teeth; verify with motor angle |
| Gyro scale/bias | Heading drift | Reset at rest; compare with a physical square |
| Wheel balance | Robot curves | Swap wheels side to side and compare |

Store per-side scale factors if the wheels differ: `LEFT_SCALE`, `RIGHT_SCALE`, both `1.0` when
the robot is healthy.

## Error budget

Track where error comes from so you fix the biggest term first.

| Source | Typical order | Grows with | Fix |
| --- | --- | --- | --- |
| Wheel diameter error | 0.5–2 % of distance | distance | Calibrate |
| Track width error | 1–3 % of angle | number of turns | Calibrate |
| Slip during acceleration | Unbounded | acceleration | Ramp speed |
| Slip during turns | Unbounded | turn rate | Slow turns, or gyro |
| Heading drift | Accumulates | time and distance | Gyro + re-localise |
| Backlash | Fixed offset | direction changes | Mechanical fix, or avoid reversals |

These orders of magnitude are **guidance**, not measurements from this robot.

## Sensor fusion

- Use **encoders for translation** and the **gyro for rotation**. This is the highest-value
  fusion on a SPIKE robot.
- Re-zero the gyro at rest before each run.
- Re-localise at known features (walls, lines) when the field allows it.
- Do not trust a single sensor to detect a stall; combine commanded power with near-zero
  measured motion.

## Power and battery

- Motor power is not torque. At low battery, the same command gives less speed and the robot
  looks "weak", not "mistuned".
- Charge before tuning and before matches. Record the charge state with every gain set.
- Avoid long stalls: they heat motors and drain the battery, and they wind up the integral.

## Software-level wins

1. **Feedforward** — see [[docs/Reference/PID Tuning]].
2. **Fixed loop period** — predictable `dt` makes gains meaningful.
3. **Early exit** — stop when within tolerance, not after a fixed time.
4. **Precompute** — convert paths to wheel distances once, not every loop iteration.
5. **No printing in loops** — it dominates the period.
6. **Restartable missions** — a failed run should not need a replug.

## Measurement protocol

For any claimed improvement:

1. State the metric (time, final error, spread over N runs).
2. Run at least 3 trials, ideally 5.
3. Keep the battery and surface the same across trials.
4. Record the code revision and the constants used.
5. Do not compare a new run against an old one with different firmware or tyres.

## Related

- [[docs/Systems/Drive Base|Drive base]]
- [[docs/Reference/PID Tuning|PID tuning]]
- [[docs/Systems/Odometry and Localization|Odometry]]
- [[docs/Backlog|Backlog]]
