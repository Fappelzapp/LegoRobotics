# LegoRobotics

Obsidian vault and Python/**PyBricks** workspace for our LEGO SPIKE Prime competition robot.

> [!note] Status — 2026-10-28
> The vault structure, conventions, and offline Python harness exist. The robot's drive base
> code is **not in this tree yet**; the team is supplying it. The placeholder `src/main.py` has
> been run on the hub over BLE — hello world only, no robot movement. See
> [[docs/Guides/Validation Checklist]] for what still needs a real robot test.

## Working with me

**I have ADHD and need clear, structured explanations.**

When explaining something to me:

- Lead with the answer or recommendation, then the supporting detail.
- Put the "so what" at the top and in headings; don't bury it in long prose.
- Use short sentences, short paragraphs, and one idea per paragraph.
- Prefer bullets, tables, and numbered steps over walls of text.
- Define terms and avoid unexplained jargon or acronyms.
- Break work into small steps and state the expected result of each.
- Call out decisions, tradeoffs, and next actions explicitly.

## Start here

| If you want to… | Open |
| --- | --- |
| Get oriented in 60 seconds | [[docs/Guides/Agent Quickstart]] |
| Know what exists and what changed | [[docs/Dashboard]] |
| Know what is left to do | [[docs/Backlog]] |
| Understand the drive base | [[docs/Systems/Drive Base]] |
| Tune a controller | [[docs/Reference/PID Tuning]] |
| Understand the field grid | [[docs/Systems/Connected Grid]] |
| See what agents did | [[docs/Journal/Agent Log]] |

Vault home: [[docs/Home]]. Agent rules: [[AGENTS]].

## What this repository is — and is not

- **Is:** a Markdown vault you open in Obsidian, a Python source tree for the hub, an offline
  test harness that never touches LEGO hardware, and a decision log.
- **Is not:** a simulator of the physical robot. Offline tests prove logic and geometry; they do
  not prove traction, gear backlash, battery sag, or sensor noise.

## Layout

| Folder | Purpose |
| --- | --- |
| `docs/Home.md` | The only project hub |
| `docs/Systems/` | One maintained note per robot subsystem |
| `docs/Reference/` | PID, drive optimisation, hardware, PyBricks API |
| `docs/Guides/` | Workflows, conventions, validation |
| `docs/Journal/` | Agent log and dated session notes |
| `docs/Bases/` | Obsidian Bases views behind the Dashboard |
| `docs/Templates/` | Core Templates plugin files |
| `docs/Inbox/` | Unsorted notes land here first |
| `src/` | Hub code: `main.py`, `lib/`, `missions/` |
| `src/sim/` | `pybricks` stubs so `src/` imports on a laptop |
| `tests/` | Offline unit tests (pure Python) |

## Quick start (offline, no hub)

```sh
# 1. Syntax-check everything
python3 -m compileall -q src tests

# 2. Run the offline tests
python3 -m unittest discover -s tests -t . -v
```

Both commands run on a plain laptop. Neither talks to a hub.

## Talking to the hub

PyBricks code runs **on the SPIKE hub**, not on this laptop. Two routes:

1. **Pybricks Code** (browser IDE, Web Bluetooth) — the normal route, especially for multi-file
   projects. No install needed.
2. **`pybricksdev`** (Python CLI) — can flash/run over USB or BLE from this machine once
   installed. Not installed here as of 2026-10-28; see [[docs/Guides/PyBricks Workflow]].

## Inspiration

The vault layout, status vocabulary, session-note discipline, and Bases dashboard are adapted
from the Roblox workspace vault at `~/Documents/Roblox/Rojo Instances/Test World` (the "Roblox
Projekt"). Keep the two consistent where it costs nothing; do not copy Roblox-specific content.
