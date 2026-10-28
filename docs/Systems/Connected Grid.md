---
title: Connected Grid
type: system
status: proposed
updated: 2026-10-28
tags: [lego, spike, navigation, grid]
---

# Connected Grid

The field map: a grid of reachable cells joined into a graph, plus named waypoints and a planner
that turns *"go from here to there"* into a path the drive base can execute.

> [!note] Two different "grids"
> This note is about **robot navigation**. The vault also has a graph of linked notes (see
> [[docs/Home|Home]]); that is documentation, not field geometry. Do not mix them.

## Responsibility

- Define the field coordinate system and resolution.
- Store obstacles, waypoints, and edges.
- Plan a path between waypoints.
- Hand a list of poses to [[docs/Systems/Motion Control]].
- Not responsible for motor control or PID tuning.

## Source and evidence

- Source: `src/lib/grid.py` (scaffold), data under `src/lib/` or `missions/`
- Context: proposal
- Evidence: design only; **no planner has run and no path has been driven**
- Verified: not yet

## Coordinate system

- Origin `(0, 0, 0)` at a fixed, documented field corner — **not** wherever the robot starts.
- `+X` toward the far end of the field, `+Y` to the **right** when facing `+X`.
- `θ` in degrees, **clockwise** from `+X` (PyBricks convention).
- Units: **millimetres**. Angles: **degrees**.
- The robot's pose is `(x, y, θ)` from [[docs/Systems/Odometry and Localization]].

Write the origin and axis directions on a diagram in `docs/Attachments/` before coding. A wrong
origin makes every path wrong in the same way, which is hard to spot.

## Resolution

| Choice | Consequence |
| --- | --- |
| Coarse (50 mm) | Fewer cells, fast planner, paths too blocky for tight missions |
| Medium (25 mm) | Good default; roughly a wheel-width per cell |
| Fine (10 mm) | Smoother paths, more memory and planner time on a hub |

Proposal: start at **25 mm**, revisit after measuring the robot's real footprint. The robot's
radius, not its bounding box, sets the inflation margin.

## Two layers

1. **Occupancy layer** — which cells are blocked (field walls, fixed obstacles, keep-out zones).
2. **Waypoint layer** — named poses that matter to missions (`start`, `home`, `mission_a`), with
   edges allowed between them.

A pure occupancy grid is flexible; a pure waypoint graph is simple and fast. Use **both**:
waypoints for mission logic, the grid for the route between them.

## Data model

```python
GRID = {
    "resolution_mm": 25,
    "origin_mm": (0, 0),
    "blocked": {(i, j), ...},          # cell indices, not millimetres
    "waypoints": {
        "start": (0, 0, 0),
        "home": (600, 0, 0),
    },
}
```

Rules:

- Store cells as **integer indices**; convert to millimetres only at the boundary.
- Inflate blocked cells by the robot's radius so the planner keeps clearance.
- Keep the data in one file and load it; do not hard-code coordinates inside missions.

## Planning

- **A\*** on the 8-connected grid.
- Step cost `1` orthogonally, `√2` diagonally.
- Heuristic: Euclidean distance to the goal. It is admissible with those costs.
- **No corner cutting**: a diagonal move requires both adjacent orthogonal cells to be free.
- Tie-break deterministically so the same query returns the same path.

If the goal is unreachable, return `None` and let the mission abort cleanly — never drive a
partial path and hope.

## Executing a path

Two options:

| Strategy | Behaviour | Use when |
| --- | --- | --- |
| **Turn–drive–turn** | Stop at each waypoint, rotate, drive | Precision matters; simplest to debug |
| **Pure pursuit** | Follow a lookahead point smoothly | Speed matters and the path is smooth |

Start with turn–drive–turn. It reuses `turn()` and `straight()` from
[[docs/Systems/Drive Base]], so a planner bug shows up as a wrong path, not as a control bug.

For pure pursuit, with lookahead distance `Ld` and heading error `α` to the lookahead point:

```text
curvature = 2 · sin(α) / Ld
ω         = v · curvature
```

Then convert `v` and `ω` to wheel speeds with the inverse kinematics in
[[docs/Systems/Drive Base]].

## Tolerances

| Quantity | Proposal | Why |
| --- | --- | --- |
| Position tolerance | 20 mm | Below this, odometry error dominates |
| Heading tolerance | 3° | Enough for sensors to see their target |
| Waypoint timeout | 5 s | Prevents a hung run from ending the match |

Tolerances are **proposals** until measured.

## Failure modes

| Symptom | Likely cause |
| --- | --- |
| Path hugs walls | Blocked cells not inflated by robot radius |
| Path cuts a corner and clips an obstacle | Missing no-corner-cutting rule |
| Robot reaches waypoints but drifts | Odometry error, not the planner |
| Planner slow on the hub | Grid too fine, or A* reopening nodes without a closed set |
| Path valid but impossible to drive | Turn radius smaller than the robot can achieve |

## Validation

- Offline: planner returns the expected path on a hand-drawn map; unreachable goal returns
  `None`; diagonal corner-cutting is rejected.
- Hub: **not run — no hub connected**.
- Required next: drive a 3-waypoint path and record the final pose error.

## Related

- [[docs/Systems/Odometry and Localization|Odometry]]
- [[docs/Systems/Drive Base|Drive base]]
- [[docs/Systems/Motion Control|Motion control]]
- [[docs/Backlog|Backlog]]
