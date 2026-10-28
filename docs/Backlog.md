---
title: Backlog
type: backlog
status: current
updated: 2026-10-28
tags: [lego, spike, backlog]
---

# Backlog

Open work with evidence and acceptance criteria. This is **not** a promise of implemented
behaviour. Mark an item done only with a real check; offline checks say so explicitly.

## Now — unblock the robot

| # | Item | Why | Done when |
| --- | --- | --- | --- |
| 1 | Import the team's drive base code into `src/` | Everything else depends on it | Code lives in `src/`, imports cleanly under the offline stubs, `main.py` names it |
| 2 | Record the port map and motor polarity | Wrong ports silently invert one side | [[docs/Guides/Agent Quickstart]] lists every port, motor direction, and sensor |
| 3 | Measure wheel diameter and drive-base track width | Every distance and turn conversion depends on them | Both numbers recorded with method and units; see [[docs/Reference/Drive Optimization]] |
| 4 | Confirm hub model and PyBricks version (firmware is already confirmed as PyBricks) | API differences matter | Model and version strings recorded |
| 5 | Decide the unit convention | Mixed mm/deg/cm causes silent 10× errors | `src/lib/config.py` has one convention, documented |

## Next — control and localisation

| # | Item | Why | Done when |
| --- | --- | --- | --- |
| 6 | Wire distance and heading PID in [[docs/Systems/Motion Control]] | Built-in `DriveBase` is convenient but not exact | Loops exist in `src/lib/`, unit-tested offline, then tuned on the hub |
| 7 | Calibrate odometry | Dead reckoning drifts without measured constants | Drive 1000 mm and spin 360°; error recorded; constants updated |
| 8 | Add gyro-assisted heading | Encoder-only heading drifts on turns | Gyro fused into pose; heading error under target on 4 consecutive turns |
| 9 | Define the field coordinate system | All paths need one origin and one angle convention | [[docs/Systems/Connected Grid]] states origin, axes, units, and sign of positive rotation |

## Later — autonomy

| # | Item | Why | Done when |
| --- | --- | --- | --- |
| 10 | Build the waypoint graph | Missions become paths, not scripts | Nodes and edges in a data file; planner round-trips a path offline |
| 11 | Path following | Grid paths need smooth tracking | Robot follows a 3-waypoint path within target tolerance |
| 12 | Line following | Line-run event | Colour sensor PID tuned; recovers from a bump |
| 13 | Mission scheduler | Runs must be repeatable and restartable | One `missions/` entry point per run; abort/retry without replugging |

## Decisions pending

- **Grid resolution.** Fine enough to avoid gaps, coarse enough for a 1–2 s planner.
- **Tracking wheels or drive encoders.** Drive encoders are free but slip during turns.
- **Gyro use in the drive base.** A built-in `DriveBase` heading loop plus our own would fight.

## Related

- [[docs/Home|Home]]
- [[docs/Guides/Validation Checklist|Validation checklist]]
- [[docs/Systems/Connected Grid|Connected grid]]
