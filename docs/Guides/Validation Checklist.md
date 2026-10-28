---
title: Validation Checklist
type: guide
status: current
updated: 2026-10-28
tags: [lego, spike, validation]
---

# Validation Checklist

What has been checked, and what still needs a real robot. Update this when a check moves from
proposed to verified. Do not tick a box from an offline test.

## Offline — no hub needed

- [ ] `python3 -m compileall -q src tests` passes.
- [ ] `python3 -m unittest discover -s tests -t . -v` passes.
- [ ] `pybricksdev compile src/main.py` passes (needs `pybricksdev` installed).
- [ ] Every number in `src/lib/config.py` is labelled `measured`, `datasheet`, or `guessed`.
- [ ] No pure-maths module imports `pybricks`.

## On the hub — first contact

- [ ] Hub boots and prints a version banner.
- [x] `main.py` runs and exits without a traceback. — 2026-10-28, BLE, `pybricksdev` 2.3.2; printed `LegoRobotics scaffold: hello from the hub`. Display and beep were not observed by the agent.
- [ ] Each motor can be driven individually in the correct direction.
- [ ] Each sensor returns a plausible value (colour sensor sees its own reflection, gyro reads
      near zero at rest and changes when turned).

## Drive base

- [ ] Straight command of 1000 mm: measured error recorded.
- [ ] Turn command of 90°: measured error recorded, direction correct.
- [ ] Turn command of 360°: no cumulative drift beyond the stated tolerance.
- [ ] Drive 4 × 90° squares: returns near the start (drift documented).
- [ ] Repeat the same straight three times: repeatability recorded.
- [ ] Behaviour at low battery noted, not assumed.

## Motion control

- [ ] Distance PID settles without sustained oscillation.
- [ ] Heading PID holds heading during a straight move.
- [ ] Turn PID overshoot measured and documented.
- [ ] Integral is clamped and the anti-windup behaviour is tested (hold the robot still).
- [ ] Loops behave when the robot is stalled (no runaway integral).

## Odometry and grid

- [ ] Pose from odometry matches a tape-measured pose after a 2 m path.
- [ ] Heading from gyro matches a physical square within the stated tolerance.
- [ ] Planner returns a path between two nodes offline.
- [ ] Robot follows a 3-waypoint path within tolerance.

## Line following

- [ ] Sensor reads dark and light on the real mat.
- [ ] Robot tracks a straight line without oscillating off.
- [ ] Robot recovers after being pushed sideways.
- [ ] Robot handles a right-angle turn or stops explicitly.

## Related

- [[docs/Backlog|Backlog]]
- [[docs/Guides/PyBricks Workflow|PyBricks workflow]]
- [[docs/Systems/Drive Base|Drive base]]
