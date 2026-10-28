---
title: Line Following
type: system
status: proposed
updated: 2026-10-28
tags: [lego, spike, line-following, pid]
---

# Line Following

Colour-sensor tracking for the line event: follow a dark line on a light mat using reflected
light as the measurement.

## Responsibility

- Read the colour sensor(s) and compute a line error.
- Convert that error into a steering correction.
- Not responsible for the whole run; missions call it and decide when to stop.

## Source and evidence

- Source: `src/lib/linefollow.py` (scaffold)
- Context: proposal; no sensor calibration has been done
- Evidence: standard reflected-light PID, **not measured**
- Verified: not yet

## Sensor facts

- Reflected light is a 0–100 scale: higher usually means lighter. Verify on the real mat; the
  direction can surprise you.
- Ambient light and mat gloss affect the reading. Calibrate on the competition surface, not a
  desk.
- A single sensor gives position error but no direction. Two sensors give a sign and are more
  robust; use two if the event allows it.

## Error signal

**One sensor** (target = the edge you want to sit on):

```text
error = reflection − LINE_TARGET
```

**Two sensors** (one each side of the line):

```text
error = reflection_left − reflection_right
```

Two sensors are symmetric around the line, so `error = 0` means centred, whichever way the
mat's reflectance shifts.

## Control

```text
turn_rate = kP·error + kD·(error − previous) / dt + kI·integral
```

- Output is a **turn rate**, applied differentially:
  `v_L = base − turn_rate`, `v_R = base + turn_rate`.
- Keep the base speed low enough that the robot can actually turn between samples.
- Integral is usually unnecessary and is the first thing to remove if the robot weaves.
- Clamp the correction so a lost line does not command a spin.

## Loss of line

Define it explicitly:

- if the reading stays outside a band for `LOST_MS`, stop or run a recovery;
- recovery: back up briefly, re-scan, or turn toward the last known side;
- never keep driving on the last correction indefinitely.

## Calibration

1. Place the sensor over the dark line, record the reading.
2. Place it over the light mat, record the reading.
3. Set `LINE_TARGET` between them, nearer the dark edge if following an edge.
4. Test at the planned base speed; readings change with speed on glossy mats.

## Validation

- Offline: error and correction maths unit-tested, including clamping.
- Hub: **not run — no hub connected**.
- Required next: calibrate on the real mat, then a straight line and a recovery test.

## Related

- [[docs/Systems/Motion Control|Motion control]]
- [[docs/Reference/PID Tuning|PID tuning]]
- [[docs/Reference/SPIKE Hardware|SPIKE hardware]]
- [[docs/Backlog|Backlog]]
