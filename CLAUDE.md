# Second Brain

Personal agentic second brain for Or, an investment analyst at Viola Ventures (VC). Built phase-by-phase from `.agent/plans/second-brain-prd.md` — generated from a personalized PRD, not copied from the reference repo.

## Who the user is

- Beginner programmer: Python, SQL, Flask only. Explain in simple terms; no JS/TS unless asked.
- Timezone: Asia/Jerusalem. Languages: Hebrew + English.

## Critical constraint: cross-platform

Being built on a private MacBook (macOS) but will be moved to and run on a Windows work PC (ThinkPad).

- Write everything in Python with `pathlib` — no shell scripts as core logic. Never hardcode absolute paths.
- Never use macOS system Python (can't load SQLite extensions) — use uv-managed Python 3.12+.
- Any macOS-specific piece (launchd, osascript notifications) must have a documented Windows equivalent (Task Scheduler, toast).
- No secrets in the vault or memory files — secrets live in gitignored `.env` files. This repo must never get a public remote; work data stays local.

## Key paths

- `SecondBrain/Memory/` — the memory vault (open `SecondBrain/` in Obsidian). Core files: SOUL.md (personality — write-protected), USER.md (profile + platform access map), MEMORY.md (long-term, keep concise), HEARTBEAT.md (proactive-run config, plain-text editable), BOOTSTRAP.md (onboarding — if present, run it), daily/ (append-only logs), companies/, research/, methods/ (living DD SOPs), content/, meetings/, drafts/active|sent|expired/, archive/.
- `.agent/plans/second-brain-prd.md` — the build plan (source of truth for phases)
- `course-reference/` — workshop repo, read-only reference
- `backport-ideas.md` — improvements to propose for NanoClaw (personal agent)

## Vault conventions

- Daily logs: `daily/YYYY-MM-DD.md`, append-only, timestamped entries.
- Company/research notes carry YAML frontmatter (type, created, status, sources).
- Factual claims tagged **[verified]** (2 independent sources) or **[unverified]**.
- Archive, never delete: obsolete files move to `archive/` (or `drafts/expired/`).

## Build workflow

1. Build phase-by-phase from the PRD. Pause for Or's approval between phases.
2. After each phase: update this file (paths, Build Commands, conventions) + mark Completed Phases + update the PRD if reality diverged.
3. When a course pattern would improve NanoClaw, add it to `backport-ideas.md`.

## Build Commands

- (placeholder — populated as phases land; if a command isn't listed here, the agent doesn't know it exists)

## Completed Phases

- **Phase 1 (2026-07-03):** Memory vault created at `SecondBrain/Memory/` with pre-filled SOUL/USER/MEMORY/HEARTBEAT from the requirements interview. BOOTSTRAP.md covers only remaining gaps (tone, drafting criteria, digest prefs, asset locations) — run it conversationally if present.

## Out of Scope

- `course-reference/` — read-only reference. Never modify; copy patterns out instead.

## Approval Required

The operating loop is: **agent drafts → Or approves the specific item → agent executes**.

- Any external action (send email, post, create/update in Notion or other work tools) needs per-item approval first; after approval the agent executes it itself.
- Modifying files outside the vault/workspace: agree on scope and exact change first.
- Never delete anything — no exceptions. Archive or move instead.
- Work/org data access is read-only by default; never make purchases or modify financial data.
- Installing global tools or changing system settings (schedulers, services).
