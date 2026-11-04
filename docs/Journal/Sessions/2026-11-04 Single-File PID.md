---
title: "2026-11-04 Single-File PID"
type: session
status: current
date: 2026-11-04
updated: 2026-11-04
tags: [lego, spike, session, pid, packaging]
---

# 2026-11-04 Single-File PID

## Scope

User asked, after seeing the refactor: *"I only want one code."* They upload through Pybricks Code
and did not want a multi-module project or a `lib/` folder. Changes were allowed.

Unchanged: the robot, the firmware version, and every mission argument. No hub was connected, so
no Pybricks version was recorded and no polarity was confirmed.

## Observations

- Pybricks Code has supported multi-file programs since v3.2, and imports are downloaded together
  with the main program, so the earlier layout *would* have worked. The user's preference for one
  file is still the deciding factor, and one file also avoids the open Pybricks bug where
  45–52 KB multi-module programs corrupt over Bluetooth.
- The `lib/` name was a package (a directory), which is the part least likely to survive a flat
  Pybricks Code file list. That alone was enough to stop relying on it.
- `src/sim/competition.py` already reached into `PID.py` for `configure()` and `_motion`, so the
  simulator was never tightly bound to the split.

## Changes and decisions

- `src/PID.py` is now **one self-contained file** (668 lines, imports only `math`):
  - a `SETTINGS` block at the top (formerly `competition_config.py`), same values and same
    evidence comments;
  - `wrap_deg`, `clamp`, `require_finite`;
  - `HeadingPID` and `Motion` (formerly `competition_motion.py`), now reading module constants
    directly instead of a `settings` object;
  - hardware plumbing, mission wrappers, all seven routes, button gating, `main()`.
- Deleted `src/lib/competition_config.py` and `src/lib/competition_motion.py`. Keeping copies
  would have let the simulator test code that no longer runs on the hub.
- `src/lib/geometry.py` stays: it is scaffold shared with `odometry.py`. `wrap_deg` therefore
  exists twice (once for the hub file, once in scaffold). Both are the same four-line function;
  the hub copy must stay because the upload cannot import it.
- `src/sim/run_pid.py`: dropped the config import, reads `program.LOOP_MS`,
  `program.WHEEL_DIAMETER_MM`, `program.AXLE_TRACK_MM`, `program.HEADING_KP`, `program.HEADING_KD`.
- `tests/test_competition.py`: imports `HeadingPID` and `wrap_deg` from `PID`, aliases
  `config = program`, and the bundle test now asserts the bundle is exactly `{'__main__'}`.
- Updated [[docs/Guides/Laptop Simulation]] and [[docs/Systems/Motion Control]]; added a
  superseded banner to [[docs/Journal/Sessions/2026-10-28 PID Refactor and Laptop Simulation]].

### Reusable kit (same day, follow-up request)

User then asked for the code to be *"not built for a specific task but to be used to build for that"*.

- Added `src/PIDBase.py` (485 lines): the same engine, zero match-specific routes, plus a
documented `mission()` entry point, a `wait_for_start()` button gate, and a worked `demo()` route.
  It is the starting point for a new project.
- `src/PID.py` keeps the seven competition routes and is unchanged apart from two comment
  markers.
- The engine block is delimited by `# --- BEGIN/END SHARED ENGINE ---` in **both** files. The
  duplication is deliberate (a template and an instance are different artefacts), so
  `tests/test_pidbase.py` asserts the two blocks are byte-identical and fails on drift.

## Validation and limits

- **Wheel diameter: 49.5 mm, measured** (user report, 2026-11-04). Replaces the 62.4 mm constant
  that came from the paste and was never measured. Applied to the shared engine, so `PID.py` and
  `PIDBase.py` moved together; the drift test confirms the two blocks are still identical.
  Derived turn gains were recomputed from the new ratio at that moment: `TURN_FAST_KP` 2.3349,
  `MIN_TURN_RATE_DPS` 14.0094 — superseded by the track measurement below.
- **Axle track: 80 mm, measured** (user report, 2026-11-04). Replaces 106 mm from the paste.
  Derived values became `MOTOR_TO_BODY_TURN` 0.61875, `TURN_SLOW_KP` 1.8563, `TURN_FAST_KP` 3.0938,
  `MIN_TURN_RATE_DPS` 18.5625.
- Worth recording: the two wrong constants mostly cancelled for **rotation**
  (106/80 x 49.5/62.4 = 1.051, so turns ran about 5% fast) but not for **translation**, where only
  the diameter applies (moves ran about 21% short). Turns therefore change very little; straight
  moves change a lot. This is arithmetic on declared constants, not a physical measurement.

- `python3 -m compileall src/PID.py src/PIDBase.py` — OK.
- The `timed_straight` test no longer pins the old 108.9085453244 mm/s; it derives the expected
  value from the constant, so a future wheel measurement does not look like a broken conversion.
- `python3 -m unittest discover -s tests` — **82 tests pass** (75 previous + 7 kit tests).
- `src/PIDBase.py` `demo()` runs under the laptop model: signed odometry 200 mm, ends within 3°
  of heading 90, brakes at least once.
- `python3 -m src.sim.run_pid --route 1` — runs, 13.28 virtual seconds in 0.0030 s wall time.
- **validation: not run — no hub connected.** Nothing here confirms that a single-file upload
  runs on the robot, that the port letters are right, or that motor polarity is right.

## Follow-up

### Missions removed (same day, later request)

User: *"Remove all the missions i dont need them i only need the pid, the missions are from a old
simulation gamefield that is no longer useable or active."*

- `src/PID.py` now contains **no missions**: settings, `HeadingPID`, `Motion`, hardware setup, the
  mission-facing wrappers, `wait_for_start()`, a `mission()` the team writes, and `main()`.
  It is 481 lines and imports only `math`.
- `src/PIDBase.py` was deleted; it had become a duplicate of what `src/PID.py` now is. The
  BEGIN/END shared-engine sentinels went with it, and so did `tests/test_pidbase.py` — there is
  no second copy left to drift. The superseded text above is left as the record of that step.
- `src/sim/run_pid.py`: `--route` and `--assume-stall-ms` removed. The runner now executes
  `mission()` from `src/PID.py`, so the simulation always matches whatever the team has written.
- Tests: route-dependent cases removed (route preservation, route 5 stall, all-route completion).
  Added: `mission()` finishes and leaves everything stopped, the kit exposes no `weg*`/`run_route`,
  and the documented commands are callable. **74 tests** now.
- The deleted routes are recoverable from `docs/Attachments/PID-original-2026-10-28.py.txt`.
  `docs/Attachments/PID-Routes-Simulation.*` are historical artefacts and no longer match the code.

### Linter cleanup (same day)

There were never any Python **errors** — the project was already at 0 errors. The complaints were
ruff-style warnings, now all cleared: **0 errors / 0 warnings** for the whole project.

- `wait as hub_wait` combined with `StopWatch` on one line is rejected because ruff runs with
  `combine-as-imports = false`. Fixed by giving the alias its own import line.
- Two non-obvious rules are now commented in the code so they do not get "fixed" back:
  - a comment block directly after the imports needs **one** blank line, not two, or ruff reports
    the import block as unformatted;
  - `tests/test_competition.py` needs `# noqa: I001` because `from tests import _path` must run
    before `import PID` (it puts `src/` on `sys.path`), so that block cannot be sorted.
- Also fixed: `run_pid.py` import order, `%` formatting to an f-string, explicit `check=False` on
  `subprocess.run`, a `dict(...)` literal, nested `with` statements combined, and a parenthesised
  implicit string concatenation.
- The deliberate broad `except Exception` in the runner now carries `# noqa: BLE001` with the
  reason: report any mission failure instead of crashing the report.

## Still open

- Upload `src/PID.py` alone and confirm it starts; then run the wheels-raised polarity check.
- Write a first real `mission()` and measure it, because the distance semantics changed in the
  earlier refactor (see [[docs/Journal/Sessions/2026-10-28 PID Refactor and Laptop Simulation]]).

## Related

- [[docs/Home|Home]]
- [[docs/Journal/Index|Session index]]
- [[docs/Backlog|Backlog]]
- [[docs/Systems/Motion Control]]
