---
title: LegoRobotics — Home
aliases: [Lego Robotics Home, SPIKE Home, Project Hub]
type: index
status: current
updated: 2026-10-28
tags: [lego, spike, index]
---

# LegoRobotics — Home

Documentation for our **LEGO SPIKE Prime** competition robot and the PyBricks code that drives
it. This folder is both an Obsidian vault and a Python source tree.

> [!important] Read the evidence label
> **Current** means checked against the stated source; use its `verified` date. **Historical**
> means retained session evidence, not a fresh test. **Proposed** means designed but not
> implemented or not run on a hub. Offline tests never imply robot behaviour. See
> [[docs/Guides/Vault Conventions|vault conventions]].

> [!tip] New here?
> Read [[docs/Guides/Agent Quickstart|Agent quickstart]] first — robot identity, current
> measurements, and the traps that silently produce wrong numbers. Then use
> [[docs/Dashboard|Dashboard]] for live tables.

## Start here

- [[docs/Guides/Agent Quickstart|Agent quickstart]] — one page: identity, numbers, traps.
- [[docs/Dashboard|Dashboard]] — live Bases views of systems, sessions, and vault health.
- [[docs/Backlog|Backlog]] — actionable work with evidence and acceptance criteria.
- [[docs/Guides/Validation Checklist|Validation checklist]] — what still needs a real robot test.
- [[docs/Journal/Agent Log|Agent log]] — living trace of meaningful work.
- [[docs/Journal/Index|Session index]] — dated evidence, not current instructions.

## Systems

| Note | Status and scope |
| --- | --- |
| [[docs/Systems/Robot Overview\|Robot overview]] | Proposed; subsystem map and source layout |
| [[docs/Systems/Drive Base\|Drive base]] | Proposed; geometry, motors, kinematics, calibration |
| [[docs/Systems/Motion Control\|Motion control]] | Proposed; PID loops for distance, heading, and turns |
| [[docs/Systems/Odometry and Localization\|Odometry]] | Proposed; pose estimation from encoders + gyro |
| [[docs/Systems/Connected Grid\|Connected grid]] | Proposed; field coordinates, waypoint graph, path planning |
| [[docs/Systems/Line Following\|Line following]] | Proposed; colour-sensor PID for the line-run event |

## Reference

- [[docs/Reference/PID Tuning|PID tuning]] — terms, discrete form, tuning order, failure modes.
- [[docs/Reference/Drive Optimization|Drive optimisation]] — traction, gearing, calibration, error budget.
- [[docs/Reference/SPIKE Hardware|SPIKE hardware]] — hub, motors, sensors, ports, units.
- [[docs/Reference/PyBricks API Cheatsheet|PyBricks API cheatsheet]] — the calls we actually use.
- [[docs/Reference/Library API|Library API]] — what each module in `src/lib/` promises.
- [[docs/Attachments/PID-Explainer|PID explainer (interactive HTML)]] — click-through simulator for `motors_pid()`, annotated source, distance arithmetic, and ten review checks. Opens in the browser; no hub needed.

## Guides

- [[docs/Guides/PyBricks Workflow|PyBricks workflow]] — laptop → hub, and how to verify.
- [[docs/Guides/Vault Conventions|Vault conventions]] — status, evidence, links, editing.
- [[docs/Guides/Agent Logging|Agent logging]] — what counts as meaningful.
- [[docs/Code Style|Code style]] — Python conventions for hub code.

## Layout

| Folder | Purpose |
| --- | --- |
| `docs/Systems/` | One maintained overview per subsystem |
| `docs/Reference/` | Detailed APIs, tuning tables, hardware facts |
| `docs/Guides/` | Workflows, conventions, validation |
| `docs/Journal/Sessions/` | Dated observations and decisions |
| `docs/Bases/` | Live Bases views behind the Dashboard |
| `docs/Templates/` | Core Templates plugin files |
| `docs/Inbox/` | Temporary intake; promote after review |
| `docs/Attachments/` | Images and data files |
| `src/` | Hub code: `main.py`, `lib/`, `missions/` |
| `src/sim/` | Offline `pybricks` stubs |
| `tests/` | Offline unit tests |
