---
title: Agent Quickstart
type: guide
status: current
updated: 2026-10-28
tags: [lego, spike, agent, quickstart]
---

# Agent Quickstart

One page: what the robot is, which numbers we actually know, and the traps that produce wrong
answers. Read this before measuring, tuning, or editing `src/`.

## Identity

| Field | Value | Source |
| --- | --- | --- |
| Team / robot name | **TODO** | not recorded yet |
| Hub model | **TODO** — SPKI 6 (Prime), SPKI 7 (Inventor), or Essential | not recorded |
| Robot Bluetooth name | **LegoLabSpike1**, address `EC:03:D9:E4:31:78` (random) | connected and used 2026-10-28 |
| Other device seen | **SPIKE Prime**, `B0:B1:13:9B:90:E7` | BLE scan, not used |
| Hub firmware | **PyBricks** — proved by a successful `pybricksdev` run and the Nordic UART Service | 2026-10-28 |
| PyBricks version | **TODO** | read in Pybricks Code |
| Event(s) | **TODO** | not recorded |
| Drive motors | **TODO** — model, port, direction | not recorded |
| Drive wheel diameter | **TODO** mm | must be measured |
| Drive-base track width | **TODO** mm | must be measured |

Anything marked TODO is **unknown**, not "probably fine". Do not invent a value to make code
run; use a clearly named `GUESS_*` constant and log it.

## Ports

| Port | Device | Direction / note |
| --- | --- | --- |
| A | Drive motor | side unknown; positive direction unverified |
| B | — | |
| C | — | |
| D | — | |
| E | Drive motor | side unknown; positive direction unverified |
| F | — | |

## Unit traps

These are the errors that look like broken code but are wrong numbers.

| Trap | What happens | Guard |
| --- | --- | --- |
| Motor angle vs. wheel distance | `Motor.angle()` is **motor degrees**, not wheel degrees or mm | Convert through gear ratio and wheel diameter in one place |
| Wheel diameter vs. radius | Distances become 2× too long or short | Name it `wheel_diameter_mm`; never `wheel_radius` without checking |
| Heading sign | Positive rotation may be clockwise in your convention | Write the convention down; test a known turn |
| Track width | Measured to the **outside** of the wheels inflates turn error | Measure centre-to-centre of the contact patches |
| Degrees vs. radians | A `math` call expecting radians given degrees | Keep degrees at API edges, radians only inside trig |
| `DriveBase` built-in loops | Our heading PID and the built-in one fight | Disable or bypass the built-in loop before adding ours |
| Battery voltage | Speed drops as the battery drains; tuned gains drift | Tune on a charged battery; re-check at low charge |
| Wheel slip | Encoders count rotation the floor never saw | Limit acceleration; calibrate on the real mat |

## How to measure the two critical numbers

**Wheel diameter (mm).** Mark a point on the tyre and the floor. Roll the robot forward exactly
10 wheel revolutions in a straight line. Measure the distance in mm. Diameter = distance ÷ (10π).
Repeat three times; use the mean and record the spread.

**Track width (mm).** Put a mark at the centre of each drive wheel's floor contact. Measure
between the marks. This is the value used in turn kinematics, not the robot's outer width.

Record both in [[docs/Systems/Drive Base]] with the method and date. A datasheet value is a
starting point; the measured value wins.

## Where things live

| You want | Go to |
| --- | --- |
| Tune a loop | [[docs/Reference/PID Tuning]] |
| Fix drift or slip | [[docs/Reference/Drive Optimization]] |
| Add a grid path | [[docs/Systems/Connected Grid]] |
| Run code on the hub | [[docs/Guides/PyBricks Workflow]] |
| Check what is still untested | [[docs/Guides/Validation Checklist]] |

## Related

- [[docs/Home|Home]]
- [[docs/Guides/Vault Conventions|Vault conventions]]
- [[docs/Systems/Robot Overview|Robot overview]]
