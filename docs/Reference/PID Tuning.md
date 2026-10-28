---
title: PID Tuning
type: reference
status: proposed
updated: 2026-10-28
tags: [lego, spike, control, pid, reference]
---

# PID Tuning

Everything needed to reason about and tune the three loops in [[docs/Systems/Motion Control]]
without guessing. Values here are **starting points**, not measurements from this robot.

> [!tip] Prefer pictures?
> [[docs/Attachments/PID-Explainer|The interactive PID explainer]] walks the same ideas with a
> simulator, the team's own `motors_pid()` annotated line by line, and a plain-language glossary of
> the German variable names. Good for onboarding; it is not evidence about the real robot.

## Mental model

A PID controller looks at **how wrong we are** and turns that into **how hard to push**.

| Term                 | Reacts to                   | Effect                        | Too much                    | Too little               |
| -------------------- | --------------------------- | ----------------------------- | --------------------------- | ------------------------ |
| **P** — proportional | current error               | immediate push, like a spring | oscillation, overshoot      | sluggish, never arrives  |
| **I** — integral     | error accumulated over time | removes steady offset         | windup, slow oscillation    | permanent offset remains |
| **D** — derivative   | how fast error is closing   | damping, brakes early         | noise amplification, jitter | overshoot, ringing       |

The output is a sum:

```text
output = P + I + D
```

## Discrete form

```python
error = target - measured
integral = clamp(integral + error * dt, -i_limit, i_limit)
derivative = (measured - previous) / dt
output = kp * error - kd * derivative + ki * integral
previous = measured
```

Why the signs:

- For a constant target, `d(error)/dt = -d(measured)/dt`, so differentiating the **measurement**
  with a minus sign is the same derivative without the kick caused by a step in the target.
- `dt` must be the real elapsed time. A fixed nominal `dt` is acceptable only if the loop is
  actually consistent.

## Clamping

Three separate clamps, all required:

1. **Output** — never command more than the motors can deliver.
2. **Integral** — never let the accumulator grow while the robot is stuck.
3. **Error** (optional) — for heading, normalise to `(-180, 180]` first.

A common bug: clamping only the output. The integral keeps accumulating behind the clamp and
the robot lurches when the error finally reverses.

## Feedforward beats feedback

If you know roughly what output a speed needs, supply it and let PID correct the rest:

```text
output = kS * sign(target_speed) + kV * target_speed + PID(error)
```

- `kS` is the smallest power that breaks static friction.
- `kV` maps speed to power.
- Benefits: less lag, smaller gains, less overshoot, more consistent across battery levels.

## Tuning sequence

Tune **one loop at a time**, and only after the geometry is calibrated
([[docs/Systems/Drive Base]]). Wrong wheel diameter or track width makes every gain wrong.

### Step 1 — P only

Set `ki = 0`, `kd = 0`.

- Start with a `kp` that produces roughly half output for a full-scale error.
- Increase until the response is crisp but just begins to oscillate.
- Reduce to about **70 %** of that value.

Expected result: reaches near the target, may overshoot slightly, may leave a small offset.

### Step 2 — D

- Raise `kd` until overshoot disappears and the approach feels "braked".
- If the robot buzzes, jitters, or the motors whine at rest, `kd` is too high **or** the
  measurement is noisy. Reduce, or filter the measurement.
- `kd` is sensitive to `dt`; retune if the loop period changes.

Expected result: clean arrival with little overshoot.

### Step 3 — I (last, small)

- Add `ki` only if a repeatable offset remains.
- Start very small. Watch for a slow hunt or a growing oscillation.
- Verify anti-windup by **holding the robot still** for a few seconds, then releasing it. It must
  not lurch.

Expected result: offset removed without changing the shape of the response.

## Starting-gain heuristics

Useful when you have no data at all:

- **P:** choose `kp` so the maximum expected error maps to ~50 % motor power. If a 90° turn uses
  `kp = 0.5`, a 90° error commands 45 %. Then tune up.
- **D:** often `kd ≈ kp · 0.05 … 0.2` **in seconds**, i.e. `kd` has units of `kp × time`. If your
  loop uses `dt` in seconds and error in degrees, this keeps the magnitude sane.
- **I:** start at `ki = kp / 10` **per second** or smaller, then reduce if it hunts.

These are dimensional rules of thumb, not magic numbers. The robot decides.

## Diagnosing the response

| What you see                    | Likely cause                                | First change                                |
| ------------------------------- | ------------------------------------------- | ------------------------------------------- |
| Slow, never reaches target      | P too low, or too much friction             | Raise `kp`, add `kS` feedforward            |
| Overshoots then comes back      | D too low or P too high                     | Raise `kd`, then trim `kp`                  |
| Oscillates forever              | P too high, D too low                       | Lower `kp`, raise `kd`                      |
| Buzzes or jitters at standstill | D amplifying noise, or deadband missing     | Lower `kd`, add deadband                    |
| Stops short consistently        | Deadband too wide, or P too low near target | Narrow deadband, add small `ki`             |
| Slow drift away from target     | Integral missing, or mechanical bias        | Small `ki`, check wheel alignment           |
| Lurches after being blocked     | Integral windup                             | Clamp integral, reset on stall              |
| Works cold, fails warm          | Battery sag or tyre temperature             | Retune at realistic charge; add feedforward |

## Heading and turn specifics

- **Turn loop:** error is an angle. Normalise it. A 350° error is really −10°.
- **Heading loop:** target is a fixed heading; the robot should hold it while driving straight.
  If the drive base already corrects heading internally, disable one of them.
- **Turn direction:** a sign error looks like a stable robot that turns the wrong way, then
  fights itself. Test with a small angle first.

## Sampling and noise

- Sample as fast as the loop allows. For SPIKE drive motors, 5–20 ms is typical.
- Do not `print()` in the loop; it dominates the period.
- If a sensor is noisy, lower `kd` before adding a filter. A filter adds phase lag, which the
  derivative then amplifies.
- Record `dt` during a run. If it varies widely, the gains are tuning a moving target.

## Battery and consistency

Motor output for a given power depends on voltage. Practical rules:

- Tune on a **charged** battery, then re-check at the charge level you expect in a match.
- Prefer feedforward + moderate gains over large gains that only work at full charge.
- If the event allows, run the same mission twice at different charge levels and compare.

## What to record

For each loop, record:

- gains (`kp`, `ki`, `kd`), output and integral limits, deadband;
- target and measured values with units;
- overshoot (deg or mm), settling time (s), steady-state error;
- battery state and surface;
- date and code revision.

Put the numbers in `src/lib/config.py` with a `measured` label, and the story in a session note.

## Related

- [[docs/Systems/Motion Control|Motion control]]
- [[docs/Reference/Drive Optimization|Drive optimisation]]
- [[docs/Systems/Line Following|Line following]]
- [[docs/Attachments/PID-Explainer|Interactive PID explainer]]
