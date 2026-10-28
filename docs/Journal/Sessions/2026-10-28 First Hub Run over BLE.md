---
title: "2026-10-28 First Hub Run over BLE"
type: session
status: historical
date: 2026-10-28
updated: 2026-10-28
tags: [lego, spike, session, pybricks, bluetooth]
---

# 2026-10-28 First Hub Run over BLE

## Scope

- Robot: hub advertising as **LegoLabSpike1**, address `EC:03:D9:E4:31:78` (random address).
- Source: `src/main.py`, the placeholder "hello from the hub" program; `src/` unchanged.
- Transport: **BLE**, `pybricksdev` 2.3.2 installed inside `.venv/`.
- Changes allowed: yes — installing a local virtual environment and running the placeholder.

## Observations

- The earlier `B0:B1:13:9B:90:E7` / **SPIKE Prime** device was no longer available. The device in
  use was `LegoLabSpike1` at `EC:03:D9:E4:31:78`.
- `bluetoothctl info` reported: **paired, bonded, trusted, connected**. Modalias
  `bluetooth:v0397p0081d0000` (LEGO vendor `0x0397`).
- It exposes the **Nordic UART Service** (`6e400001-b5a3-f393-e0a9-e50e24dcca9e`), which PyBricks
  firmware uses. A successful `pybricksdev` run confirmed the firmware is PyBricks rather than
  stock LEGO firmware.
- No LEGO USB device was present: `lsusb` listed only the webcam and Bluetooth radio, with no
  `ttyACM*`, `ttyUSB*`, or `/dev/serial/by-id`. `/dev/ttyS0` is the laptop's internal
  `serial8250` UART, not the hub.
- **A connected BLE device stops advertising.** The first `pybricksdev run ble --name
  "LegoLabSpike1"` attempt timed out while the hub was connected. Disconnecting first made the
  hub discoverable again.

## Changes and decisions

- Installed `pybricksdev` 2.3.2 in `.venv/` (gitignored) rather than system-wide.
- Ran the placeholder successfully:

```sh
bluetoothctl disconnect EC:03:D9:E4:31:78
.venv/bin/pybricksdev run ble --name "LegoLabSpike1" src/main.py
```

- Console result: 370 bytes downloaded, then `LegoRobotics scaffold: hello from the hub`.
- Updated [[docs/Guides/Agent Quickstart]] (identity), [[docs/Guides/PyBricks Workflow]]
  (known-good command and the advertising caveat), [[docs/Guides/Validation Checklist]] (one box),
  and [[docs/Backlog]].
- No motor or sensor code was run.

## Validation and limits

- **Hub run: yes**, BLE via `pybricksdev` 2.3.2. Console output captured above.
- The hub disconnected when the program finished; that is expected.
- **Not observed:** the display text, green light, and beep. The agent cannot see the robot.
- **Not tested:** motors, sensors, drive base, PID — none of that code exists yet.
- Offline checks from the earlier session still stand (35 tests).

## Follow-up

- Confirm the exact hub model and PyBricks version ([[docs/Backlog]] item 4).
- Keep the hub disconnected when asking `pybricksdev` to find it, or pass a different transport.
- Import the team's drive base code next.

## Related

- [[docs/Home|Home]]
- [[docs/Journal/Index|Session index]]
- [[docs/Guides/PyBricks Workflow|PyBricks workflow]]
- [[docs/Guides/Validation Checklist|Validation checklist]]
