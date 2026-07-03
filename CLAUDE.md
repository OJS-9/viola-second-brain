# Second Brain

Personal agentic second brain for Or, an investment analyst at Viola (VC). Built by following the Dynamous "claude-code-second-brain" workshop, but generated from a personalized PRD — not by copying the reference repo.

## Who the user is

- Beginner programmer: Python, SQL, Flask only. Explain in simple terms; no JS/TS unless asked.
- Timezone: Asia/Jerusalem.

## Critical constraint: cross-platform

Being built on a private MacBook (macOS) but will be moved to and run on a Windows work PC (ThinkPad).

- Write everything in Python with `pathlib` — no shell scripts as core logic.
- Never hardcode absolute paths; derive paths from the project root.
- Any macOS-specific piece (launchd scheduling, notifications) must have a documented Windows equivalent (Task Scheduler) planned.
- No secrets in this folder or in memory files — secrets live in `.env` files that are gitignored.

## Project Structure

- `course-reference/` — the workshop repo (reference material)
- `.claude/skills/create-second-brain-prd/` — generates the personalized build plan
- `my-second-brain-requirements.md` — requirements form (fill before generating PRD)
- `.agent/plans/second-brain-prd.md` — the generated build plan (once created)

## Build workflow

1. Fill out `my-second-brain-requirements.md`.
2. Run `/create-second-brain-prd ./my-second-brain-requirements.md` to generate the PRD.
3. Build phase by phase from the PRD. Pause for the user's approval between phases.
4. After each phase, update this file: new paths, commands, and conventions introduced.

## Completed Phases

- (none yet — workspace setup only)

## Standing goal: backport ideas to the personal agent

The user also runs a personal agent, NanoClaw (`~/projects/nanoclaw_multi_agent`, github.com/OJS-9/nanoclaw_multi_agent), locally and on a VPS. While building this project, when a course pattern or a lesson learned would improve NanoClaw, add it to `backport-ideas.md`. Verify against the NanoClaw codebase before proposing a GitHub issue; get the user's OK before opening one.

## Out of Scope

- `course-reference/` — read-only reference. Never modify it; copy patterns out of it instead.

## Approval Required

The operating loop is: **agent drafts → user approves the specific item → agent executes**.

- Any external action (send email, post, create/update in Notion or other work tools) needs per-item approval first; after approval the agent executes it itself.
- Modifying files outside the vault/workspace: agree on scope and exact change first.
- Never delete anything — no exceptions. Archive or move instead.
- Work/org data access is read-only by default; never make purchases or modify financial data.
- Installing global tools or changing system settings (schedulers, services).
