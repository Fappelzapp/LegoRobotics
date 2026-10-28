---
title: Laptop Simulation
type: guide
status: current
updated: 2026-10-28
tags: [lego, spike, pybricks, pid, simulation, offline]
---

# Laptop Simulation

## Recommendation: run Python fast, replay the result in the browser

**Use the local virtual-time runner for day-to-day changes.** It runs the actual
`src/PID.py` mission functions and `src/lib/competition_motion.py` controllers. It does not
copy their maths into JavaScript. The browser only replays the resulting samples.

**Evidence:** implemented and checked offline. **Hub validation: not run — no hub connected.**
This is a useful test of software logic under an assumed model, not a prediction of match results.

## Start here — no installation or hub needed

Run these commands from the `LegoRobotics` project root:

```sh
# Calculate the demo; creates the HTML replay AND matching CSV samples.
python3 -m src.sim.run_pid

# Open the interface, not the HTML source text.
xdg-open docs/Attachments/PID-Simulation.html
```

Expected result: a dark **PID Lab** page. Choose a route, press **Play**, and drag the time slider.
The demo starts 15° crooked, drives 50 cm, turns to 90°, then reverses 20 cm.
The path, wrapped heading error, speed commands, encoder distance, and module angles share one
virtual clock. The CSV link downloads the exact data plotted in the page.

Opening the page does **not** connect to Bluetooth, USB, Pybricks Code, or the robot.
Changing replay speed changes only the animation, not the simulated controller's timing.

## Useful experiments

### Replay a real route's code

```sh
python3 -m src.sim.run_pid --route 1
xdg-open docs/Attachments/PID-Simulation.html
```

Routes: `1`, `2`, `3-left`, `3-right`, `4`, `5`, `6`, `7`.
The physical button gates are skipped; the selected route's actual function runs.
Each route starts independently at the local origin, with heading reset as in the program.
This is not a stitched map of all routes on a competition mat.

### Compare four Kp settings without editing robot configuration

```sh
python3 -m src.sim.run_pid --sweep --output docs/Attachments/PID-Gain-Sweep.html
xdg-open docs/Attachments/PID-Gain-Sweep.html
```

Use the route selector to compare demo runs with `Kp = 0, 1, 4, 8`. All use the same model and
20 ms wait. `--kp` and `--kd` are simulation-only overrides. They do not edit hub settings.
`--kd` uses **seconds-based derivative scaling**; the current nominal value is `0.02`, not the
old per-pass `1`.

### Check robustness, not just the ideal case

```sh
python3 -m src.sim.run_pid --slip 0.2 --gyro-drift 0.5 --turn-lag 0.2
```

These are **assumed disturbances**, not measurements:

- `--slip 0.2`: lose 20% of encoder travel at the ground. Encoders still count rotation.
  The robot can meet its encoder target while stopping short on the floor.
- `--gyro-drift 0.5`: assume gyro bias changes by 0.5°/s. The controller can follow a drifting
  sensor without the real pose being correct.
- `--turn-lag 0.2`: assume a 0.2 s turn-rate lag. More lag can expose overshoot.
- `--speed-lag`: assumed forward-speed lag in seconds; default `0.08`.
- `--start-heading`: demo's initial heading error in degrees; default `15`.

Do not tune the real robot solely to make an assumed model's graph look pretty.

### All routes, including the attachment stall

```sh
python3 -m src.sim.run_pid --route all --assume-stall-ms 500 --output docs/Attachments/PID-Routes-Simulation.html
xdg-open docs/Attachments/PID-Routes-Simulation.html
```

**Why the extra flag?** Route 5 calls `modull.run_until_stalled(...)`. A 2D model has no arm,
wall, collision, load, or end stop. Without this flag the runner intentionally stops route 5
with `NotImplementedError`, writes the partial trace, and exits nonzero.
The flag explicitly assumes a stall after 500 ms; it is recorded in that route's report.
It does **not** simulate a real stall or validate the arm.

A Python/control exception also stops the model, appears in the report, and makes the command
exit nonzero. An "offline run completed" label only means the code returned under this model.

## Why this is much faster than the old stubs

| Before: `src/sim/pybricks/` | Now: `src/sim/competition.py` |
| --- | --- |
| `DriveBase.drive()` is a no-op | Drive commands advance encoder distance and gyro heading |
| `wait(1000)` sleeps for a real second | `wait(1000)` advances virtual time by 1000 ms, with no sleep |
| IMU reading is unrelated to wheel motion | Heading and pose follow the same planar model |
| No asynchronous attachment timing | `wait=False` moves continue while other moves/waits run |
| Can import scaffold code, but cannot exercise a feedback loop | Runs the same controller and mission code used by the hub entry point |

The old stubs are retained for existing scaffold tests, not silently redefined as physics.

**One local offline timing observation:** a 4.06 s virtual demo took about 0.0038 s of Python
model calculation on this laptop. That excludes HTML/CSV export, browser rendering, interpreter
startup, and real hardware. It is not a repeatable performance benchmark or a robot measurement.

The efficient workflow is: calculate headlessly, record once, replay as often as needed.
Do not animate every experiment in real time. Run parameter comparisons against identical
conditions, and rerun with disturbances before drawing conclusions.

## What is really simulated?

- Body linear speed and clockwise angular rate, in mm/s and deg/s.
- Continuous planar pose and encoder distance; an exact constant-twist arc is used per step.
- Illustrative first-order speed/turn lags (`0.08` / `0.12` s by default).
- At most 20 ms per integration step; `StopWatch` uses this same virtual clock.
- Relative motor-angle commands and overlapping `wait=False` timing, at constant assumed speed.
- Optional lost ground travel and gyro-bias drift.

**Not simulated:** firmware's internal motor controllers, exact motor limits, battery state,
mass/inertia/contact forces, tyre deformation, real braking distance, mat obstacles, ramps,
colour/ultrasonic sensors, attachment geometry, or real button interaction. The brake is idealised
as instantaneous. Motor polarity is assumed correct. There is no noise distribution fitted to data.

This means a good graph cannot prove motor polarity, rolling diameter, traction, endpoint
accuracy, or mission success. Those require a real hub and measurements.

## Other simulators — researched 2026-10-28

| Option | Best use | Compatibility / cost in effort |
| --- | --- | --- |
| **This virtual-time runner** | Fast regression tests, timeout/sign/unit bugs, parameter comparisons, path inspection | Already implemented, Python standard library only. Same mission/control functions. Simplified assumed plant, not firmware emulation. |
| **Gears / GearsBot** | Accessible browser-based 3D robotics and contact experiments | Official wiki documents Pybricks/ev3dev support and mostly EV3-based components. I have **not** established drop-in support for this PrimeHub/pupdevices/IMU program. Expect an adapter and robot configuration; do not assume all Pybricks versions/APIs match. |
| **Pybricks Virtual Hub** | Firmware/API-level development and compatibility testing | Official firmware repo has a virtual-hub build/test target. Changelog says the old Unix variant was replaced by a simulated embedded hub. This is developer infrastructure, not a ready-made SPIKE robot + competition-field simulator. Not built or evaluated in this task. |
| **Webots** | A model with wheels, mechanisms, obstacles, contact and sensor geometry | Supports Python controllers and fast/headless workflows. Reusing our controller needs a Webots backend implementing our small device interface, plus a physical robot model. No native drop-in Pybricks compatibility has been verified here. More setup; useful only when the extra physics answers a concrete question. |

**Recommendation:** use the local runner now; consider Webots when you need to answer an arm/contact
question that this model cannot. Gears is a good lower-setup 3D experiment if its API adapter is
acceptable. A complex uncalibrated 3D robot is not automatically more accurate than a small model.

### Primary sources

- [Pybricks DriveBase v3.6](https://docs.pybricks.com/en/v3.6.0/robotics.html):
  `drive(speed, turn_rate)`, mm/s then deg/s; `distance()` in mm; `stop()` coasts;
  `brake()` brakes; `reset()` can change heading when gyro use is enabled.
- [PrimeHub IMU v3.6](https://docs.pybricks.com/en/v3.6.0/hubs/primehub.html):
  heading is clockwise-positive and does not wrap at ±180°; readiness and reset restrictions.
- [Timing tools](https://docs.pybricks.com/en/stable/tools/index.html): wait and StopWatch use ms.
- [Motor API v3.6](https://docs.pybricks.com/en/v3.6.0/pupdevices/motor.html):
  positive-direction setup, precision profile, and `wait=False`.
- [Pybricks firmware servo source](https://github.com/pybricks/pybricks-micropython/blob/master/lib/pbio/src/servo.c):
  `pbio_servo_run_angle` explicitly documents that speed and angle signs multiply.
  This differs from `run_target`, where the speed sign is ignored.
- [Gears official wiki](https://github.com/QuirkyCort/gears/wiki): supported languages, components,
  Pybricks limitations and physics goals.
- [Pybricks virtual-hub test script](https://github.com/pybricks/pybricks-micropython/blob/master/test-virtualhub.sh)
  and [firmware changelog](https://github.com/pybricks/pybricks-micropython/blob/master/CHANGELOG.md).
- [Webots installation / headless workflow](https://www.cyberbotics.com/doc/guide/installation-procedure)
  and [user interface / simulation time](https://cyberbotics.com/doc/guide/the-user-interface).

These establish documented/API behaviour, not the unknown installed firmware version on this hub.

## Corrections to the earlier explanation

> **Local observation — not yet reconciled with the original explainer.** The old
> [[docs/Attachments/PID-Explainer.html|HTML explainer]] and
> [[docs/Journal/Sessions/2026-10-28 PID Explainer|its session note]] are retained as historical
> evidence. The points below correct the earlier chat advice/code-reading claims, without
> presenting new hardware observations.

| Earlier claim | Correction and evidence |
| --- | --- |
| `errsum` was never reset | It was a local variable set to zero on every original function call. Missing clamping, not missing per-call reset, was the issue. Source inference. |
| `stop(Stop.BRAKE)` is the DriveBase braking API | The documented call is `brake()`. `stop()` has no stop-mode argument and coasts. Datasheet. |
| A 20 ms wait fixes timing without changing tuning | A wait changes loop dynamics and can require retuning. It is a minimum pause, not an exact 50 Hz schedule. The new derivative/integral use measured elapsed time. |
| The derivative is stronger at a higher loop rate | For a given physical error rate, a per-pass difference is smaller with a shorter period. The old effective derivative coefficient is approximately `kd * dt`; the integral's per-second accumulation grows with loop frequency. |
| `DriveBase.distance()` removes gearing/calibration dependence | It removes duplicated conversion code; geometry and any configured gear train still have to be correct. Encoder distance is not a ground measurement. |
| Every PID call originally had a stop; missing stops are necessarily bugs | Many calls intentionally chain or lead directly into other actions. The refactor deliberately brakes every helper for bounded behaviour; that changes timing and cannot be advertised as behaviour-preserving. |
| The timed opposite-sign raw motor blocks are spins | Under the motor polarity inferred from the source they are straight moves. The replacement converts motor deg/s to body mm/s once. Inference; physical polarity still unverified. |
| `profile=None` disables the motor ramp | It selects an automatic/default precision profile; it does not mean no acceleration profile. Datasheet. |
| `abs(heading)` fixes wraparound | Absolute value loses left/right information and is not angle normalisation. Use a wrapped signed difference. |
| All displayed route variants run one after another | Route 3 selects **one** of two variants via a double press. There are seven stages and eight possible variant functions, not eight stages in one run. |

The native `DriveBase` motor/speed controllers are not removed. The custom outer heading loop
commands their body turn-rate setpoint. The code disables built-in gyro heading use for this
custom loop; this is not an instruction to disable all internal motor regulation.

## Before putting the refactor on the real robot

1. Back up the original program; the transcription is in `docs/Attachments/PID-original-2026-10-28.py.txt`.
2. Record the installed Pybricks version and verify all four ports. Keep the robot raised and
   attachments clear. The inferred mapping is left E counterclockwise, right A clockwise;
   modules F/B clockwise. This is **not measured**.
3. In a separate bounded smoke test, verify that positive drive speed moves both wheels forward,
   and positive turn rate means clockwise. Do not start a full mission to discover a sign error.
4. On a clear mat, measure a slow 10 cm move and a small turn, then a reverse move. The source
   62.4 mm / 106 mm constants are unmeasured. Do not try to tune away bad geometry.
5. Recheck every route distance and timing. With this refactor `amount=21` requests **210 mm** of
   encoder travel. Under a hypothetical 62.4 mm direct-drive wheel, the old 5.56 cm formula would
   have counted about 235.7 mm instead. That arithmetic is not a physical measurement.
6. Retune only after the API/sign/unit checks. Kp=4 and Ki=0 are retained from source;
   Kd=0.02 is a nominal 20 ms unit conversion of the old per-pass 1, **not** a tuned gain.
7. Confirm the stall/end stop for route 5. Its retained hardware `run_until_stalled` command is
   blocking and has no added timeout. The drive/alignment/curve timeouts do not bound that call.

Use [[docs/Guides/PyBricks Workflow]] for transport. `src/PID.py` is the competition entry point;
`src/main.py` remains the safe hello-world program. Do not add `src/sim` to a hub upload.

### Check the local dependency bundle without uploading

```sh
# Optional: uses the already installed local pybricksdev compiler, not a hub.
.venv/bin/pybricksdev compile src/PID.py
```

**Local observation — not yet reconciled with the older multi-file caveat in
[[docs/Guides/PyBricks Workflow]].** Installed `pybricksdev` 2.3.2 uses
`compile_multi_file` even for its `compile` command. The final `src/PID.py` bundle was parsed
offline and contains `__main__`, `lib.competition_config`, `lib.competition_motion`, and
`lib.geometry` (9325 bytes in this check), with no simulator or Pybricks stubs.

An initial `from lib import competition_config` import silently omitted that dependency from
the bundle. Explicit dotted imports fixed it. A regression test checks bundle membership when
the optional local compiler is installed. This check does **not** execute any hub API or prove
compatibility with the installed firmware. No upload/run was performed.

## Related

- [[docs/Systems/Motion Control|Motion control and behaviour changes]]
- [[docs/Guides/Agent Quickstart|Known and unknown hardware facts]]
- [[docs/Reference/PID Tuning|PID tuning reference]]
- [[docs/Journal/Index|Session evidence]]
