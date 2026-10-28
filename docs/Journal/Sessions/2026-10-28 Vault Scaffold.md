---
title: "2026-10-28 Vault Scaffold"
type: session
status: historical
date: 2026-10-28
updated: 2026-10-28
tags: [lego, spike, session, vault]
---

# 2026-10-28 Vault Scaffold

## Scope

- Robot: not present in this tree; the team's drive base code had not arrived.
- Source: empty vault containing only `.obsidian/`.
- Context: laptop only. No hub was connected, so no robot behaviour was observed.
- Changes allowed: yes — creating the vault and offline harness was the task.

## Observations

- The vault opened at `/home/fabian/Documents/LegoRobotics` with `.obsidian/` and no notes.
- Python 3.14.4 is available. `pyserial` is installed. `pybricksdev` is not installed.
- No serial device (`/dev/ttyACM*`, `/dev/ttyUSB*`) was present and no LEGO/Nordic USB device
  was visible.
- Bluetooth is powered on with no known devices; no hub was paired.
- The sibling Roblox workspace at `~/Documents/Roblox/Rojo Instances/Test World` supplied the
  conventions this vault follows: status vocabulary, session notes, living agent log, Bases
  dashboard, and the cheapest-model subagent rule.

## Changes and decisions

- Created `README.md`, `AGENTS.md`, the `docs/` tree, Bases views, and core Templates files.
- Adopted **PyBricks sign conventions**: +Y right, heading and turns positive **clockwise**,
  matching `DriveBase.turn()` and `hub.imu.heading()`. This corrected an earlier draft that used
  a counter-clockwise math convention and would have required a sign flip at every boundary.
- Chose one unit convention per layer: millimetres at the drive/odometry boundary, degrees for
  angles, mm/s and deg/s for speeds.
- Split future code into pure-maths modules (testable offline) and thin hardware wrappers.
- Added reference material on PID, drive optimisation, hardware, and the API, all marked as
  proposals or documentation-derived rather than measured.

## Validation and limits

- Offline: `python3 -m compileall -q src tests` passed and `python3 -m unittest discover -s tests -t .`
  ran **35 tests, all passing**. `src/main.py` also imports and runs through the `src/sim/`
  stubs on the "hello from the hub" path.
- Hub: **not run — no hub connected**. No claim is made about how the robot drives.
- The API cheatsheet was checked against PyBricks documentation, not against the installed
  firmware. Version-sensitive calls are marked **check**.

## Follow-up

- Import the team's drive base code and reconcile it with [[docs/Reference/Library API]].
- Fill in the identity table in [[docs/Guides/Agent Quickstart]].
- Measure wheel diameter and track width.
- Track the rest in [[docs/Backlog]].

## Related

- [[docs/Home|Home]]
- [[docs/Journal/Index|Session index]]
- [[docs/Backlog|Backlog]]
