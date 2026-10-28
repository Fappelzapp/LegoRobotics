---
title: Code Style
type: guide
status: current
updated: 2026-10-28
tags: [lego, spike, python, style]
---

# Code Style

Conventions for code that runs on the SPIKE hub (`src/`) and tests that run on a laptop
(`tests/`). MicroPython is smaller and slower than desktop Python; favour plain code.

## Hard constraints

- **No third-party packages on the hub.** Only `pybricks` and the standard MicroPython modules.
  If a module cannot be imported in Pybricks Code, it does not ship.
- **No `microbit`, `machine`, or `time` hacks** where a PyBricks call exists. They behave
  differently on the hub.
- **Keep the import surface tiny.** Every imported module costs hub memory.
- **Avoid deep recursion and large literals.** MicroPython has little RAM and no tail calls.

## Naming and layout

- `snake_case` for functions and variables, `PascalCase` for classes, `UPPER_CASE` for
  configuration constants.
- One responsibility per module. `lib/` holds reusable logic; `missions/` holds run scripts;
  `main.py` selects a mission.
- Put every tunable number in `src/lib/config.py` with a comment saying
  `measured`, `datasheet`, or `guessed`. See [[docs/Guides/Agent Quickstart]].
- Units belong in the name: `wheel_diameter_mm`, `turn_rate_dps`, `loop_dt_ms`.

## Numbers and units

- PyBricks motor angles are **degrees**; distances in the `DriveBase` API are
  **millimetres**. Do not mix them silently.
- Store heading in degrees, normalise to `(-180, 180]` at module boundaries.
- Prefer integer millimetres for positions unless sub-millimetre precision is measured and
  needed.

## Control code

- Every PID loop takes `dt` explicitly. Never rely on a global clock inside the loop.
- Clamp the integral term and the output; document both limits.
- Differentiate the **measurement**, not the error, to avoid a derivative kick when the
  target steps.
- One loop, one unit: a distance loop outputs mm/s, a heading loop outputs deg/s, a turn loop
  outputs deg/s. Do not chain unit conversions inside the loop body.

## Offline compatibility

`src/` must import on a laptop for tests. Import hub-only modules behind the stubs in
`src/sim/`, or split pure maths into modules that never import `pybricks`.

- Pure geometry, PID, and path planning: **no `pybricks` import**.
- Hardware wrappers: import `pybricks`, live next to them, and stay thin.

## Comments

Comment intent, constraints, and surprises — not restatements of the code. A comment is
warranted when it records *why a number is what it is*, or a hardware quirk that will bite
the next person.

## Related

- [[docs/Guides/Vault Conventions|Vault conventions]]
- [[docs/Reference/PyBricks API Cheatsheet|PyBricks API cheatsheet]]
- [[docs/Guides/Validation Checklist|Validation checklist]]
