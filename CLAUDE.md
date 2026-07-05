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

- `SecondBrain/Memory/` — the memory vault (open `SecondBrain/` in Obsidian). Core files: SOUL.md (personality — write-protected), USER.md (profile + platform access map), MEMORY.md (long-term, keep concise), HEARTBEAT.md (proactive-run config, plain-text editable), BOOTSTRAP.md (onboarding — if present, run it), daily/ (append-only logs), companies/, people/ (founders/partners), research/ + research/sources/ (raw material — never modify, cite it), methods/ (living DD SOPs), content/, meetings/, drafts/active|sent|expired/, archive/. A vault `index.md` catalogs pages once content exists (Phase 5).
- `.claude/hooks/` — lifecycle hooks: `session_start_context.py` (SessionStart — injects SOUL/USER/MEMORY/last 2 daily logs), `pre_compact_flush.py` / `session_end_flush.py` (spawn `memory_flush.py` in the background), `block_secrets.py` (PreToolUse — blocks reads/writes/bash that would expose secrets).
- `.claude/scripts/` — standalone `uv` project (Python 3.12+, own `pyproject.toml`/`uv.lock`/`.venv`). `config.py` (paths + Asia/Jerusalem timezone helper), `shared.py` (state, file locking, daily log append, hook logging, retry helper), `memory_flush.py` (background Agent SDK job that distills a conversation excerpt into the daily log).
- `.claude/data/state/` — per-machine operational state (hook execution log, flush dedup state). Gitignored via `.claude/data/`; not synced, regenerable.
- `docs/nanoclaw-lessons.md` — production lessons from Or's personal agent, applied to Phases 5-6.
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

- `uv sync --project .claude/scripts` — first-time setup / after pulling (installs claude-agent-sdk, python-dotenv, tzdata into `.claude/scripts/.venv`).
- `uv run --project .claude/scripts python .claude/scripts/memory_flush.py --context-file <path> --test` — manually test a memory flush without writing to the real daily log.
- `python .claude/hooks/block_secrets.py` (reads a PreToolUse-shaped JSON payload on stdin) — manually test the secrets guard.

## Completed Phases

- **Phase 1 (2026-07-03):** Memory vault created at `SecondBrain/Memory/` with pre-filled SOUL/USER/MEMORY/HEARTBEAT. BOOTSTRAP onboarding completed same day (archived to `archive/`): blunt pushback, English-only email drafts, on-demand drafting (no auto-scan), every-finding notifications, one-pager digest as vault file, cybersecurity thesis profiles in `research/thesis-cybersecurity.md`, IC Deck Structure Notion page as living slide framework. Pending deliveries tracked in USER.md.
- **Phase 2 (2026-07-05):** Hooks wired for context persistence. `.claude/scripts/` is now its own `uv` project (`pyproject.toml` + `uv.lock`, Python 3.12+, deps: `claude-agent-sdk`, `python-dotenv`, `tzdata`). `session_start_context.py` injects SOUL/USER/MEMORY + the last 2 daily logs that exist on disk (not a today/yesterday fallback) at session start. `pre_compact_flush.py` / `session_end_flush.py` extract the tail of the transcript and spawn `memory_flush.py` detached (`subprocess.Popen`, non-blocking) with a `CLAUDE_INVOKED_BY` recursion guard so the Agent SDK's own headless subprocess can't re-trigger the same hooks. `memory_flush.py` dedupes flushes of the same session within 60s (`.claude/data/state/flush-state.json`, lock-protected) and appends distilled notes to the daily log unless the model returns `FLUSH_OK`. `block_secrets.py` (PreToolUse baseline, hardened in Phase 8) blocks reads/writes/bash targeting `.env`, credentials, keys, SSH material. **Interpreter split (deviation from the PRD's illustrative bare-`python`-everywhere example):** `block_secrets.py` runs via bare `python` (zero third-party imports, fires on every tool call, latency matters) while the other 3 hooks route through `uv run --project .claude/scripts python ...` since they import `config.py`, which needs `tzdata`/`python-dotenv` from the venv — bare `python` on PATH isn't guaranteed to be the right interpreter with the right deps. All 4 hooks tested manually on this machine via realistic stdin JSON (incl. Windows-backslash paths) matching the exact `settings.json` invocation.

## Out of Scope

- `course-reference/` — read-only reference. Never modify; copy patterns out instead.

## Approval Required

The operating loop is: **agent drafts → Or approves the specific item → agent executes**.

- Any external action (send email, post, create/update in Notion or other work tools) needs per-item approval first; after approval the agent executes it itself.
- Modifying files outside the vault/workspace: agree on scope and exact change first.
- Never delete anything — no exceptions. Archive or move instead.
- Work/org data access is read-only by default; never make purchases or modify financial data.
- Installing global tools or changing system settings (schedulers, services).
