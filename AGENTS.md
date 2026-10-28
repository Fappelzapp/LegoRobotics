# Agent Instructions — LegoRobotics

This folder is both an Obsidian vault and a Python/PyBricks workspace. Read this file at the
start of every session and follow it before you finish a task.

**Fast path:** [[docs/Guides/Agent Quickstart]] holds the robot identity, the current
measurements, and the traps that silently produce wrong numbers. Read it before measuring
or tuning anything.

## Hardware honesty rule

There is a physical robot and there is code. Do not blur them.

- **Never claim code ran on a hub unless it did.** Say which transport was used (USB, BLE,
  Pybricks Code) and what the hub printed.
- Code that passes `compileall` or `unittest` is **syntax- and logic-checked only**. It is
  not a robot test.
- When you cannot reach a hub, record `validation: not run — no hub connected` and continue
  with offline checks.
- Never edit `src/` numbers (wheel diameter, gear ratio, PID gains) without saying where the
  number came from: measured, datasheet, or guessed.

## Source precedence

Two machines may edit this vault. Other-machine claims about robot behaviour outrank local
inferences.

- If a local observation contradicts a maintained note, do not overwrite it. Add a dated note
  marked `local observation — not yet reconciled`, link both sides, and leave resolution to
  the originating agent. Use `status: proposed` or `historical`.
- A later file timestamp is **not** evidence of being newer.
- Filesystem facts are the exception: a dead path, moved file, or renamed folder may be fixed
  under *Vault Conventions → Editing*. Fix the reference; leave the claim alone.

## Logging: useful traces, not a transcript

Leave a trace in [[docs/Journal/Agent Log]] when the work is **meaningful**:

- you changed files, gains, or geometry;
- you made a decision later work will rely on;
- you produced a read-only finding worth keeping;
- you corrected an older claim;
- the work is substantial enough to need a session note.

Do **not** log every question, tool call, or typo. Trivial Q&A may be skipped. If unsure, one
short entry beats a paragraph.

The log is a **living document**. Prefer appending, but edit, merge, reorganize, or (rarely)
delete to improve accuracy. Never silently erase the only record of a real test, decision,
rollback instruction, or measurement.

Entry format:

```text
- HH:MM — <agent/session> — <action> — <paths or hub/transport> — <validation>
```

Group under `## YYYY-MM-DD` headings. One entry per task or session, not per tool call.

## Substantial work gets a session note

For a new subsystem, a multi-file change, or an investigation with conclusions:

1. Create `docs/Journal/Sessions/YYYY-MM-DD <Title>.md` from [[docs/Templates/Session Note]].
2. Link it from [[docs/Journal/Index]] and from the log entry.
3. Update the maintained system note and [[docs/Home]] navigation only if behaviour changed.

Pure Q&A and small edits do **not** get a session note. One log line is enough.

## Evidence and honesty

- Do not claim a test passed unless you actually ran it. Record `not run` when you did not.
- State whether a number came from **measurement**, **datasheet**, **inference**, or
  **proposal**.
- Give units. Degrees, millimetres, seconds, and motor degrees are not interchangeable.
- Do not present a proposal as implemented behaviour.
- Follow [[docs/Guides/Vault Conventions]] for status, evidence, and wikilinks.

## Definition of done

- [ ] Log entry added for meaningful work, or a clear reason it was skipped
- [ ] Session note created and indexed if the work was substantial
- [ ] Changed files named in the entry
- [ ] Validation result, or `not run` plus reason, recorded
- [ ] Final response states what changed and what was not verified

## Subagents: cheapest model only

Subagents must run on a **cheap** model. This is a hard cost ceiling inherited from the Roblox
workspace policy, not a preference.

**Allowed:** DeepSeek V4.1 Flash, GLM 5.3 Flash, Minimax 3.1 Flash, Gemini Flash-Lite, and the
nano/mini tier (`gpt-5-nano`, `gpt-5.4-nano`, `gpt-4o-mini`).

**Never:** any **Kimi** model, full-price siblings (`glm-5.3`, `deepseek-v4-pro`,
`mistral-large-*`), or premium routes (`gpt-5.5*`, `gpt-6*`, `gemini-3.1-pro-preview`, and
everything under `openai-subscribed/*`).

Rules of thumb:

1. Pass `model` explicitly on every `spawn_agent` call.
2. If you cannot confirm a model is cheap, do not use it — fall back to DeepSeek V4.1 Flash.
3. `flash`, `nano`, `mini`, and `lite` mark the cheap tier; `pro`, `ultra`, `max`, `codex`,
   and `large` do not.
4. Only an explicit user instruction in that session can override this.
5. Work that needs a frontier model should be done by the parent or reported as too large.

Do not invent prices.

## Scope

Do not commit, push, or create branches unless explicitly asked. Leave user-authored notes
and code alone unless the task requires changing them. For explicit vault-improvement tasks,
editing and reorganizing is allowed; deleting unique evidence still requires care and, when
in doubt, a backup or archive.
