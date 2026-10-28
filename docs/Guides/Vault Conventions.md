---
title: Vault Conventions
type: guide
status: current
updated: 2026-10-28
tags: [documentation, workflow]
---

# Vault Conventions

## Keep one maintained account of each subsystem

Use [[docs/Home|Home]] as the only project hub. `docs/Systems/` owns current overviews;
`docs/Reference/` holds detailed APIs and tables. A session may record past values, but should
link to the maintained note rather than claim its values remain current forever.

- **Systems:** responsibility, actual source location, behaviour, config, limitations, evidence.
- **Reference:** detailed API or data; avoid duplicating the overview.
- **Sessions:** dated observations and decisions. Preserve what happened.
- **Backlog:** unresolved work, evidence, and acceptance criteria. Not promises.
- **Inbox:** temporary intake; promote into a maintained note or dated session after review.

## Status and evidence

Use frontmatter `type`, `status`, `updated`, and `tags`. Add `verified` only for a real check.

| Status | Meaning |
| --- | --- |
| `current` | Maintained note checked against the stated source |
| `historical` | Prior observations, superseded implementation, or unavailable source |
| `proposed` | Planned behaviour or work; not implemented or not run |
| `retired` | Feature removed from the active implementation |
| `template` | Structure only; never evidence |

## Evidence vocabulary

Every behavioural claim should say which of these it rests on:

- **measured** — taken from the physical robot or a stopwatch/tape measure;
- **datasheet** — from LEGO or PyBricks documentation;
- **inference** — reasoned from code or geometry, not observed;
- **proposal** — designed, not built;
- **hub run** — code actually executed on a hub, with the transport named;
- **offline test** — `compileall`/`unittest` only. Never implies robot behaviour.

## Claims and measurements

- Record units. Millimetres, motor degrees, and seconds are not interchangeable.
- Give the sample size, battery state, and surface for any performance claim.
- Separate configured constants, measured values, and proposals.
- Do not turn an offline pass into a claim that the robot drives correctly.

## Links and note creation

- Use full vault-relative wikilinks without `.md`, e.g. `[[docs/Systems/Drive Base]]`.
- In tables, escape the alias separator: `[[docs/Systems/Drive Base\|Drive base]]`.
- Add a link to the relevant index and at least one related note.
- New unsorted notes go to `docs/Inbox/`; attachments to `docs/Attachments/`.
- The core Templates plugin reads `docs/Templates/`.

## Editing, merging, and deleting

The default is to append, but notes are living documents.

- **Edit** for corrections, broken links, duplicate headings, and stale navigation.
- **Merge** duplicate hubs instead of maintaining two versions of one claim.
- **Delete** only noise, duplicates, or obsolete scaffolding. Never delete the only record of a
  real test, decision, rollback instruction, or measurement.
- **Preserve provenance.** If a claim was wrong, say what changed and why.

## Live views

`docs/Bases/*.base` define the tables embedded in [[docs/Dashboard|Dashboard]]. They read
frontmatter directly, so keeping `status`, `updated`, `type`, and `tags` accurate keeps the
tables accurate. Do not maintain a second handwritten index of the same rows.

## Related

- [[docs/Home|Home]]
- [[docs/Dashboard|Dashboard]]
- [[docs/Backlog|Backlog]]
- [[docs/Journal/Index|Session index]]
