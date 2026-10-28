---
title: Odometry and Localization
type: system
status: proposed
updated: 2026-10-28
tags: [lego, spike, odometry, localization]
---

# Odometry and Localization

Where the robot thinks it is: pose `(x, y, θ)` in millimetres and degrees, updated from wheel
rotation and the gyro.

## Responsibility

- Integrate wheel motion into a pose.
- Fuse the gyro for heading.
- Provide `get_pose()` and `reset_pose(x, y, θ)`.
- Not responsible for planning; that is [[docs/Systems/Connected Grid]].

## Source and evidence

- Source: `src/lib/odometry.py` (scaffold)
- Context: proposal; dead reckoning
- Evidence: standard differential-drive integration, **not measured**
- Verified: not yet

## Pose convention

Same as [[docs/Systems/Drive Base]]: +X forward, +Y right, **θ clockwise** in degrees. This is
the PyBricks convention, so `drive.angle()` and `hub.imu.heading()` need no sign flip.
`reset_pose` sets a known start, usually the field origin.

## Update step

Read left and right wheel travel `dL`, `dR` in mm since the last update. With track width `L`:

```text
d      = (dL + dR) / 2
dθ_rad = (dL − dR) / L
```

With clockwise positive, the **left** wheel travelling farther than the right means the robot
turned right. Check this sign against a known 90° turn before trusting a path.

**Straight or near-straight** (`|dθ|` tiny):

```text
x += d · cos(θ + dθ/2)
y += d · sin(θ + dθ/2)
θ += dθ
```

**Exact arc** (signed radius `R = d / dθ`):

```text
x += R · (sin(θ + dθ) − sin(θ))
y += −R · (cos(θ + dθ) − cos(θ))
θ += dθ
```

Use the exact form when `|dθ|` is above a small threshold; the midpoint approximation is fine
for short steps.

## Using the gyro for heading

- Prefer the gyro's angle as `θ` and use encoders only for translation. Encoder heading is
  corrupted by wheel slip, especially during turns.
- Reset the gyro while the robot is still. Motion during reset leaves an offset.
- Treat a slowly growing heading offset as **bias**, not as a reason to widen the tolerance.

## Error sources

| Source | Effect | Mitigation |
| --- | --- | --- |
| Wheel slip | Under-counts travel; worst during acceleration and turns | Limit acceleration; calibrate on the real mat |
| Track width error | Turn angle wrong in a fixed ratio | Measure centre-to-centre |
| Wheel diameter error | Distance wrong in a fixed ratio | Measure over 10 revolutions |
| Unequal wheel wear | Robot curves; heading drifts | Replace tyres; trim with a per-side scale |
| Backlash | Small dead zone at direction changes | Avoid reversing inside a path, or add a compensation constant |
| Sampling gaps | Integration misses motion | Fixed `dt`; log the real loop period |
| Gyro drift | Heading slowly walks | Re-zero at rest; square up against a wall or line |

Dead reckoning error **grows without bound**. A 1 % distance error is 10 mm per metre, and
heading error compounds it. Plan to re-localise.

## Re-localisation

- **Start pose reset** before every run.
- **Wall squaring**: drive slowly into a known wall to align heading, then reset `θ`.
- **Line reference**: use a colour sensor crossing a known line to correct one axis.
- **Two-wall corner**: align both axes when the field geometry allows it.

## Validation

- Offline: integration tested against hand-computed arcs and a pure rotation.
- Hub: **not run — no hub connected**.
- Required next: 2 m path, compare pose with a tape measure; record error and direction.

## Related

- [[docs/Systems/Drive Base|Drive base]]
- [[docs/Systems/Connected Grid|Connected grid]]
- [[docs/Reference/Drive Optimization|Drive optimisation]]
