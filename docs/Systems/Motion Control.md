---
title: Motion Control
type: system
status: proposed
updated: 2026-10-28
tags: [lego, spike, control, pid]
---

# Motion Control

The closed loops that make the drive base go where it is told: distance, heading, and turn.
Deep tuning reference: [[docs/Reference/PID Tuning]].

## Responsibility

- Turn a target (mm or degrees) into motor power over time.
- Own the PID gains and the stop/settle logic.
- Not responsible for deciding *where* to go; that is [[docs/Systems/Connected Grid]].

## Source and evidence

- Source: `src/lib/motion.py`, `src/lib/pid.py` (scaffold)
- Context: proposal; classical PID plus feedforward
- Evidence: standard control theory, **not tuned on this robot**
- Verified: not yet

## The three loops

| Loop | Measurement | Target | Output |
| --- | --- | --- | --- |
| Distance | `drive.distance()` (mm) | mm | common motor power |
| Heading | gyro or `drive.angle()` (deg) | deg | differential power |
| Turn | `drive.angle()` (deg) | deg | opposed powers, sign by error |

Keep them **separate**. Running a distance loop and a heading loop that both write motor power
is fine only if the outputs are summed once, at the end. Do not let two controllers each call
`motor.run()` with their own value.

## Discrete PID

```text
error      = target − measured
integral  += error · dt            # clamp to ±I_LIMIT
derivative = (measured − previous) / dt
output     = kP·error − kD·derivative + kI·integral
```

Notes:

- `dt` comes from the loop, never from a global clock read inside the maths.
- The derivative uses the **measurement**, so a step in the target does not produce a kick.
  The minus sign is because `d(error)/dt = −d(measured)/dt` for a constant target.
- Clamp `output` to the motor's usable range. Clamp `integral` separately; clamping the output
  alone still lets the integral wind up.
- Normalise heading error to `(−180, 180]` **before** the PID, not after.
- Positive heading, turn, and correction mean **right** (clockwise), matching PyBricks. A
  positive differential output therefore slows the right wheel and speeds up the left.
- Add a deadband: below `±DEADBAND`, treat the error as zero so the robot does not buzz.

## Feedforward

A pure PID always lags a moving target. Add a model term:

```text
output = kS·sign(v) + kV·v + PID(...)
```

- `kS` overcomes static friction — the minimum power that moves the robot.
- `kV` converts a desired speed into power.
- The PID then only corrects the model's error.

For turns, the same idea with a turn-specific `kS`/`kV`, because scrubbing four wheels sideways
costs more than rolling two forward.

## Stop and settle

A move is done when **both** hold:

1. `|error| < TOLERANCE` for `SETTLE_MS` (e.g. 150 ms), not just once;
2. speed is below `STOP_SPEED`.

Then brake (`Stop.BRAKE`) or hold. A single-sample check stops early on a noisy measurement.

## Tuning order

1. `kP` only. Raise until the response is brisk but starts to oscillate; back off ~30 %.
2. `kD` to damp the overshoot. Raise until noise appears, then back off.
3. `kI` last and small, only if a steady offset remains.
4. Re-check at a low battery — gains that work at full charge may be sluggish later.

Record the battery state with every gain set.

## Loop rate

- Aim for a fixed loop period (e.g. 10 ms) and measure the real `dt`.
- PyBricks motor/sensor reads are fast, but `print()` is not. Never print inside the loop.
- If the loop takes longer than expected, lower the work per iteration rather than widening the
  tolerance.

## Interaction with the built-in `DriveBase`

PyBricks `DriveBase.straight()`/`turn()` already run internal controllers and may use the gyro.
Choose one of:

- **Use the built-in controller** for simple moves, and keep our PID for custom paths.
- **Bypass it** (drive the motors directly) and own the whole loop.

Do not run both on the same motors. Document the choice in `config.py`.

## Validation

- Offline: PID class tested for clamping, anti-windup, derivative sign, and `dt` handling.
- Hub: **not run — no hub connected**.
- Required next: tune distance then heading, record overshoot and settling time.

## Related

- [[docs/Reference/PID Tuning|PID tuning]]
- [[docs/Systems/Drive Base|Drive base]]
- [[docs/Systems/Odometry and Localization|Odometry]]
- [[docs/Backlog|Backlog]]
