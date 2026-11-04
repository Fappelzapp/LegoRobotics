---
title: "2026-10-28 PID Refactor and Laptop Simulation"
type: session
status: historical
date: 2026-10-28
updated: 2026-10-28
tags: [lego, spike, session, pid, simulation, research, offline]
---

# 2026-10-28 PID Refactor and Laptop Simulation

> **Superseded layout — 2026-11-04.** The two modules described here
> (`src/lib/competition_config.py`, `src/lib/competition_motion.py`) were folded into a single
> self-contained `src/PID.py`, because that is the only file uploaded to the hub. The claims
> and evidence below are left as recorded; only the file paths are out of date. See
> [[docs/Journal/Sessions/2026-11-04 Single-File PID]].

## Scope

User requested: put the pasted competition program into `PID.py`; remove prints and dead code;
add a 20 ms wait; use DriveBase distance; implement correctness fixes; research efficient laptop
simulation. Work was interrupted by user/model switches and then continued in this session.

`src/PID.py` existed but was **0 bytes** when inspected. It was filled, not replaced over an
existing implementation. Source evidence is the user's chat paste, transcribed to
`docs/Attachments/PID-original-2026-10-28.py.txt` with whitespace/comments abridged. That
transcription is not imported or run.

- Robot revision / installed Pybricks version: unknown. The maintained
  [[docs/Guides/Agent Quickstart]] is not overwritten with inferred hardware facts.
- Transport: **none**. No BLE/USB connection or hub run attempted during this task.
- Permission: code/documentation changes and offline checks only; no physical tuning.
- `src/main.py`, existing scaffold `src/lib/config.py`, and old `src/sim/pybricks` stubs unchanged.

## Observations

### Source / API research, not robot measurements

Primary-source links, detailed comparisons, and correction ledger are maintained in
[[docs/Guides/Laptop Simulation]]. Key findings:

- Published Pybricks v3.6 signature is `DriveBase.drive(speed, turn_rate)` (mm/s, deg/s),
  positive-forward / positive-clockwise. The pasted call had these roles reversed.
- `DriveBase.stop()` coasts; `DriveBase.brake()` is the braking API, not `stop(Stop.BRAKE)`.
- Heading continues beyond ±180°. A wrapped signed difference is needed for shortest-path turns;
  changing the `1800` literal alone is not a complete fix.
- `DriveBase.distance()` is encoder-derived millimetres, not a tape-measure ground distance.
  Wheel diameter, gearing and polarity still matter.
- The original `errsum` **already reset per call**. Earlier explanations saying otherwise were
  wrong. The original lacked a clamp / anti-windup, not a per-call reset.
- Firmware `pbio_servo_run_angle` explicitly says speed and relative-angle signs multiply;
  `run_target` ignores the speed sign. The new module simulator follows that distinction.
- `profile=None` means automatic/default precision profile, not disabled acceleration.
- Source straight raw-motor commands (`links.run(-v)`, `rechts.run(v)`) suggest left
  counterclockwise / right clockwise as physical-forward coordinates. This remains an
  **inference**, not an observed polarity check.

### Local observations — not yet reconciled

- Earlier HTML/session claims about integral reset, timing, motor signs, and route variants are
  retained, with an explicit dated historical banner on the old HTML and a linked correction
  ledger. No previous hub-run evidence was removed.
- Installed `pybricksdev` 2.3.2 does multi-file compilation. An initial
  `from lib import competition_config` compiled successfully but silently omitted the config
  from the bundle. Explicit `import lib.competition_config as config` fixed dependency
  discovery. Final bundle membership is regression-tested, not assumed from compile success.
- This extends the older cautious multi-file discussion in [[docs/Guides/PyBricks Workflow]];
  it is local compiler evidence, not a new hub transport claim.

## Changes and decisions

### Active competition code

- `src/PID.py`: lazy hardware setup; safe laptop import; preserved mission arguments and
  attachment `wait=False` calls; original seven stages with two selectable stage-3 variants.
- `src/lib/competition_config.py`: source constants separated from unrelated scaffold guesses.
  Ports and 62.4 mm / 106 mm geometry come from the paste, **unmeasured**. New acceleration,
  tolerance, settling, timeout and rate-limit values are labelled proposals.
- `src/lib/competition_motion.py`: shared hardware-independent heading/turn/curve loops,
  `wait(20)`, measured dt, wrapped error/measurement derivative, integral/output clamps,
  anti-windup, distance baselines, exceptions/timeouts and braking on exit.
- Removed active unused imports, globals, no-op assignments, legacy curve helpers,
  `ausrichten3`, disabled triple-quoted functions/tests and loop prints.
- Button polling yields and requires fresh press/release; two busy timed raw-motor loops become
  one converted DriveBase straight command plus a timed wait.

**Intentional behavioural migration:**

- Mission `amount` stays in cm; the internal target is `amount * 10` mm. The old 5.56 cm encoder
  multiplier is removed. No claim is made that this preserves physical endpoints.
- Speed is now conventional signed body mm/s; no hidden reversal. Motor polarity is normalised
  using explicitly named unverified guesses.
- Kp=4 / Ki=0 retained from source. Kd=0.02 s is the nominal 20 ms conversion of source per-pass
  1; it is not hub-tuned. Turn gains / motor-speed kick are converted into body angular units.
- All motion helpers brake, including between moves that used to chain. Route timing changes.
- Alignment tolerances/settling replace exact integer equality. Targets such as 360° mean the
  heading equivalent to 0°, not an explicit full rotation.
- Route 6's 30° alignment followed by a 20° drive target is retained, not silently guessed away.
- Retained limitation: hardware route 5's attachment `run_until_stalled` remains blocking with
  no new timeout. It requires a real end stop and a safe mechanism test.

### Laptop simulation

- `src/sim/competition.py`: virtual clock; planar pose/encoders/gyro; explicit assumed speed and
  turn lags; asynchronous module scheduling; optional slip and gyro drift. No real sleep.
- `src/sim/run_pid.py`: runs the actual PID/mission functions; records Python samples; exports
  standalone HTML replay and CSV. Browser code only replays data, not a second PID algorithm.
- `--route`, `--sweep`, `--kp`, `--kd`, `--slip`, `--gyro-drift`, lag overrides and explicit
  `--assume-stall-ms` experiments. No new Python packages installed.
- Route 5 fails with a useful nonzero error / partial trace without an explicit stall-time
  assumption. The model does not pretend to simulate contact.
- Generated example reports and matching CSV:
  - `docs/Attachments/PID-Simulation.html` / `.csv` — default demo.
  - `docs/Attachments/PID-Routes-Simulation.html` / `.csv` — all 8 variants, assumed 500 ms stall.
  - `docs/Attachments/PID-Gain-Sweep.html` / `.csv` — Kp 0/1/4/8 comparison.
- Researched Gears, official Pybricks Virtual Hub, and Webots. Recommendation: the local runner
  for daily regression work; a calibrated Webots/Gears adapter only when contact/3D questions
  justify it. No drop-in PrimeHub compatibility or third-party simulator install was claimed.

### Documentation and validation files

- `tests/test_competition.py`: controller units/signs/dt, limits, wraparound, failure/braking,
  module concurrency/signs, source-argument preservation, report/CLI and optional compiler bundle.
- `docs/Guides/Laptop Simulation.md`: beginner commands, model limits, primary sources,
  simulator comparison, earlier-claim correction ledger, migration and hardware checklist.
- `docs/Systems/Motion Control.md`: maintained competition implementation, distinct from the
  broader proposed control design.
- `docs/Attachments/PID-Explainer.html`: historical-source banner linking to new replay/guide;
  old text retained rather than silently replacing the earlier claims.
- `README.md`, `docs/Home.md`, `docs/Backlog.md`: actual source/entry point, replay links,
  current offline workflow, and remaining hardware work.
- This session note, `docs/Journal/Index.md`, and `docs/Journal/Agent Log.md` record the work.

## Validation and limits

**validation: not run — no hub connected.** No robot geometry, gains, endpoint, braking, motor
polarity, sensor or attachment performance was measured. Prior hello-world BLE evidence remains
only that prior hello-world run.

Checks actually performed:

1. `python3 -m compileall -q src tests` — passed.
2. `python3 -m unittest discover -s tests -t . -v` — **75 tests passed**, 2.129 s in final run;
   includes 35 original scaffold tests and 40 new competition/simulation tests. Optional local
   compiler dependency-bundle test ran (not skipped) on this laptop.
3. `.venv/bin/pybricksdev compile` — entry point and controller/config compiled offline.
   Parsed final `src/PID.py` ABI-6 bundle: `__main__` (4705 bytes), config (915), motion (2885),
   geometry (736); total **9325 bytes** including module headers. No simulator/stubs bundled.
   This does not validate installed firmware APIs or execute the imports on a hub.
4. All 8 route variants completed in the assumed model with explicit 500 ms attachment stall
   timing. Variant virtual durations: 13.28, 9.09, 26.35, 18.05, 10.28, 6.32, 15.93, 8.14 s.
   These are not measured mission times, and exclude skipped buttons / beep duration.
5. Default demo, gain sweep, and a disturbed demo (`--slip 0.2 --gyro-drift 0.5`) completed.
   One initial timing observation: 4.06 virtual seconds in about 0.0038 s of model calculation;
   excludes interpreter startup, export/render work. Not a performance benchmark.
6. Headless Chrome opened the generated report. Browser probe checked 8-case switching,
   +20 ms step, scrubbing, play/pause labels, controlled playback-clock advancement, reset,
   painted canvas, and no horizontal overflow at observed 1200 px / 500 px viewport widths.
   No JavaScript errors captured. Native real-time playback timing was not benchmarked.
7. Generated HTML tag nesting, active-code absence of `print()`, and new navigation links checked.
   Desktop screenshot inspected; temporary screenshot removed. Original preview PNGs from the
   earlier session left alone.

Limits: no calibrated physical plant, firmware runtime emulation, forces/contact/obstacles,
actual motor saturation, real braking distance, sensor noise, ramps, or real button interaction.
The report's "completed" status means returned under the model, not a successful real mission.

## Follow-up

- Complete [[docs/Backlog]] items 1–4: choose/use the competition entry point explicitly,
  record firmware, check polarity on blocks, measure geometry and short forward/reverse turns.
- Revalidate mission distance/timing after the unit/API/stop changes before considering gain tuning.
- Verify route 5's end stop and decide whether it needs a bounded asynchronous stall manoeuvre.
- Reconcile older explainer/API-cheatsheet claims using the linked correction ledger; retain
  original test/measurement evidence.

## Related

- [[docs/Guides/Laptop Simulation]]
- [[docs/Systems/Motion Control]]
- [[docs/Guides/Agent Quickstart]]
- [[docs/Journal/Sessions/2026-10-28 PID Explainer]]
- [[docs/Journal/Index]]
- [[docs/Home]]
