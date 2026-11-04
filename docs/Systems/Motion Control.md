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

- The hub program and the reusable kit are the same file: `src/PID.py`. Self-contained (imports
  only `math`), because that is the single file uploaded to the hub. It contains no mission for
  any particular field: the settings block sits at the top, and a documented `mission()` at the
  bottom is where the team writes its route. This is both the kit and the current program.
- Separate scaffold: `src/lib/pid.py`. The design discussion below is still a **proposal**,
  not a claim that all the proposed distance/feedforward/settling loops are implemented.
- Competition evidence: source inspection, offline tests, an assumed 2D model, and MicroPython
  compile checks. **Not tuned or run on this robot.**

## Competition program — implemented, offline-checked only

The user's original program was transcribed and refactored on 2026-10-28. The source
transcription is `docs/Attachments/PID-original-2026-10-28.py.txt`. See
[[docs/Guides/Laptop Simulation]] for executable commands, primary sources, assumptions, and
corrections to earlier advice.

| Helper | Implemented behaviour / units |
| --- | --- |
| `motors_pid(stp, speed, amount)` | Absolute heading in deg; signed body speed in mm/s; non-negative distance in **cm** at the legacy mission boundary. Internally uses signed `DriveBase.distance()` deltas in mm, without resetting heading. |
| `ausrichten1/2(stp)` | Absolute heading, wrapped shortest-path error, 2° proposed tolerance, 100 ms proposed settling check, and timeout. |
| `motors_kurve1(target, speed, steering)` | Heading target in deg, signed speed in mm/s, turn-rate magnitude in deg/s (not a steering percentage), with target-selected direction and a timeout. |
| All three | `wait(20)` via shared configuration; `brake()` on normal/error exit. Heading PID uses measured `dt`, derivative on measurement, bounded integral/output, and conditional anti-windup. |

**Behaviour migration, not a drop-in optimization:** the DriveBase call now uses
`drive(speed, turn_rate)`. The inferred left motor direction is normalised so both drive motors
have positive-forward coordinates. The 5.56 cm custom distance multiplier is removed. Every
helper brakes even where source calls previously chained. The speed ramp is now acceleration /
remaining-distance based. Route geometry, timing, and gains need new hardware validation.

- Source constants now measured: **wheel diameter 49.5 mm and axle track 80 mm, measured
  2026-11-04** (were 62.4 mm / 106 mm from the paste). Kp=4, Ki=0 retained from source.
  `MOTOR_TO_BODY_TURN` and all derived turn gains follow the measured geometry.
  The two old errors largely cancelled for rotation (product 1.051 — turns were ~5% fast) but
  not for translation, where only the diameter applies (moves were ~21% short).
- Kd=0.02 s is a derived nominal conversion of the source per-pass 1 at 20 ms, not a tuned gain.
- New limits, tolerance, acceleration, timeout and settling values are labelled proposals in
  configuration. Source turn gains are converted from motor to body angular-speed units.
- Positive speed is forward; positive turn rate is clockwise, including during reverse travel.
- `use_gyro(False)` selects the custom outer gyro heading loop. Native wheel/speed regulation
  remains active; this is a velocity-control cascade, not two absolute heading targets competing.
- Main requires fresh RIGHT then LEFT press/release pairs. `wait_for_start()` in the kit does
  the same for your own mission. Button polling yields rather than busy-spinning.
- `src/main.py` is intentionally unchanged; running it still runs hello world, not competition code.
- **2026-11-04: the seven competition missions were deleted.** They belonged to a retired game
  field. `src/PID.py` is now a mission-free kit: settings, `HeadingPID`, `Motion`, hardware setup,
  the mission-facing wrappers, and an empty `mission()` for the team to fill in. The archive
  `docs/Attachments/PID-original-2026-10-28.py.txt` still holds the original paste.
- Limitation that outlives the missions: `run_until_stalled` is blocking without a timeout, and
  the laptop model refuses to invent contact. Bound any such call you write.

## The three loops (design reference; proposal)

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
