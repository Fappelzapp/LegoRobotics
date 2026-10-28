---
title: Agent Logging
type: guide
status: current
updated: 2026-10-28
tags: [documentation, workflow]
---

# Agent Logging

The log is a **trace of meaningful work**, not a transcript. It answers: *what changed, what was
decided, and how was it checked?*

## Log when

- you changed code, gains, geometry, or configuration;
- you made a decision later work will rely on;
- you produced a read-only finding worth keeping;
- you corrected an older claim;
- the work deserves a session note.

## Skip when

- the user asked a quick question and nothing changed;
- you only ran a search or read a file;
- you retried a command after a typo.

## Format

```text
## 2026-10-28

- 14:05 — agent/zed — imported drive base, added offline tests — src/lib/, tests/ — offline: 12 tests pass; hub: not run
```

One entry per task or session. Merge duplicates. Keep units and validation state.

## Session notes

Create `docs/Journal/Sessions/YYYY-MM-DD <Title>.md` when the work is a new subsystem, a
multi-file change, or an investigation with conclusions. Then:

1. Link it from [[docs/Journal/Index]].
2. Link it from the log entry.
3. Update the maintained system note only if behaviour changed.

## Related

- [[docs/Journal/Agent Log|Agent log]]
- [[docs/Journal/Index|Session index]]
- [[docs/Guides/Vault Conventions|Vault conventions]]
