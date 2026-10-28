---
title: PyBricks Workflow
type: guide
status: current
updated: 2026-10-28
tags: [lego, spike, pybricks, workflow]
---

# PyBricks Workflow

How code gets from this laptop onto the SPIKE hub, and how to know whether it actually ran.
**Code on disk is not code on the robot.** Only a hub run is a hub run.

## Choose a transport

| Route | Use when | Requirements |
| --- | --- | --- |
| **Pybricks Code** (`code.pybricks.com`) | Normal development, especially multi-file projects | Browser with Web Bluetooth; hub with Pybricks firmware |
| **`pybricksdev` over BLE** | Scripting, automation, editor integration | `pybricksdev`, Bluetooth, hub awake |
| **`pybricksdev` over USB** | Wired connection | Documented for LEGO official firmware; may not work with Pybricks firmware depending on version — test it, don't assume |

Pybricks Code is the safe default. `pybricksdev` is convenient but is described by its own
maintainers as a developer tool rather than a supported end-user product.

## Install `pybricksdev` (once)

`pybricksdev` requires Python 3.10 or newer. This machine has Python 3.14.

```sh
# Recommended: isolated install
pipx install pybricksdev

# Or inside a virtual environment
python3 -m venv .venv && . .venv/bin/activate
pip install pybricksdev
```

On Linux, USB access needs udev rules:

```sh
pybricksdev udev | sudo tee /etc/udev/rules.d/99-pybricksdev.rules
```

## Run a program

```sh
# BLE, first hub found
pybricksdev run ble src/main.py

# BLE, a named hub (use when several are nearby)
pybricksdev run ble --name "Pybricks Hub" src/main.py

# Compile only — catches syntax errors without a hub
pybricksdev compile src/main.py
```

### Known-good on this robot (2026-10-28)

```sh
# A hub that is already connected stops advertising, so pybricksdev cannot
# find it. Drop the existing link first; pybricksdev reconnects on its own.
bluetoothctl disconnect <hub-bluetooth-address>

.venv/bin/pybricksdev run ble --name "LegoLabSpike1" src/main.py
```

Result: 370 bytes downloaded, then `LegoRobotics scaffold: hello from the hub` on the
console. The hub disconnects when the program finishes. This proves the BLE path works; it does
not prove any motor behaviour.

**Multi-file projects:** Pybricks Code uploads the whole project, so `src/lib/` imports work
there. `pybricksdev run` sends a program to the hub; do not assume it transfers a directory of
modules. Confirm the behaviour on your version before relying on it — if it does not, either
import through the single file Pybricks Code builds, or keep the shipped entry point
self-contained.

## Before you press run

1. **Wheels off the floor** for any first run of a new drive routine.
2. Battery charged. Gains tuned at low battery behave differently.
3. Hub awake and not connected to another device.
4. Know the expected result — "left motor turns forward for 1 s" beats "it should work".

## What counts as evidence

| Evidence | Means |
| --- | --- |
| `python3 -m compileall src` | Syntax only |
| `python3 -m unittest discover -s tests` | Logic and geometry, under stubs |
| `pybricksdev compile` | MicroPython compile, no hardware |
| Hub run via BLE/USB | Real execution; record transport and printed output |
| Observed movement | Real behaviour; record distance/angle and how it was measured |

Never write "tested" for the first three. Write **offline test** or **compile check**.

## Reporting a hub run

Record in the session note or log entry:

- transport (Pybricks Code / BLE / USB) and hub name;
- the exact file that ran;
- the console output, including tracebacks;
- what the robot did, with measured units if anything moved.

## Related

- [[docs/Guides/Validation Checklist|Validation checklist]]
- [[docs/Reference/SPIKE Hardware|SPIKE hardware]]
- [[docs/Systems/Drive Base|Drive base]]
