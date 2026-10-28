---
title: SPIKE Hardware
type: reference
status: proposed
updated: 2026-10-28
tags: [lego, spike, hardware, reference]
---

# SPIKE Hardware

Hardware facts we code against. Model-specific numbers marked **verify** have not been checked
against this team's hub and must not be treated as measured.

## Hub

The SPIKE hub is a small computer: it runs PyBricks, holds the program, and provides the IMU,
display, speaker, and Bluetooth.

| Feature | Notes |
| --- | --- |
| Ports | Six labelled **A–F** on the Prime hub. **Verify** the count on your model |
| Display | 5×5 light matrix |
| Speaker | Simple tones and beeps |
| IMU | 3-axis gyro + accelerometer, built in |
| Radio | Bluetooth (used by Pybricks Code and `pybricksdev`) |
| Wired | USB for power/charging and, depending on firmware, program transfer |
| Power | Rechargeable battery pack |

The hub model changes the PyBricks import. Prime uses `PrimeHub`; other hubs have their own
classes. Confirm the class that matches your hardware before writing code.

## Motors

| Motor | Character | Use for |
| --- | --- | --- |
| Large Angular Motor | More torque, lower free speed | Drive wheels |
| Medium Angular Motor | Lighter, faster, less torque | Attachments and arms |

- Motor angle is reported in **degrees** of the motor shaft.
- Speed is **degrees per second** (`run`) or a **percentage** (`dc`).
- `positive_direction` and `Direction.CLOCKWISE`/`COUNTERCLOCKWISE` set the sign convention.
- Gearing between motor and wheel means motor degrees are **not** wheel degrees. Convert in one
  place; see [[docs/Systems/Drive Base]].

## Sensors

| Sensor | Measurement | PyBricks call |
| --- | --- | --- |
| Colour / light | Reflected light 0–100, colour enum, ambient, HSV | `.reflection()`, `.color()`, `.ambient()`, `.hsv()` |
| Distance (ultrasonic) | Distance in mm | `.distance()` |
| Force | Newtons, pressed state | `.force()`, `.pressed()` |

Any device can physically connect to any port, but the PyBricks class must match the device.
A colour sensor constructed as a `ForceSensor` will not behave.

## Units summary

| Quantity | Unit |
| --- | --- |
| Motor angle | degrees |
| Motor speed | degrees/second, or % for duty cycle |
| DriveBase distance | millimetres |
| DriveBase angle | degrees |
| DriveBase straight speed | millimetres/second |
| DriveBase turn rate | degrees/second |
| Colour reflection | 0–100 (scale direction must be verified on the mat) |
| Distance sensor | millimetres |
| Force | newtons |

Do not convert inside a controller. Convert at the boundary and keep one unit per layer.

## Handling

- Connect and disconnect devices with the hub idle. Hot-plugging during a motor command can
  produce confusing errors.
- Charge before a tuning session; voltage affects every speed.
- Keep the hub away from metal debris near the ports.
- Do not stall motors for long; it heats them and wastes battery.

## What to verify on the real hub

- [ ] Exact hub model and PyBricks import class.
- [ ] Firmware and PyBricks version strings.
- [ ] Port count and labels.
- [ ] Motor model and which port each drive motor uses.
- [ ] Sensor models and ports.
- [ ] Whether USB program transfer works with the installed firmware.

Record the answers in [[docs/Guides/Agent Quickstart]] and remove the `verify` flags here.

## Related

- [[docs/Guides/PyBricks Workflow|PyBricks workflow]]
- [[docs/Reference/PyBricks API Cheatsheet|PyBricks API cheatsheet]]
- [[docs/Systems/Drive Base|Drive base]]
