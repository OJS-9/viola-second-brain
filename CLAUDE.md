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
- `.claude/scripts/` — standalone `uv` project (Python 3.12+, own `pyproject.toml`/`uv.lock`/`.venv`). `config.py` (paths + Asia/Jerusalem timezone helper), `shared.py` (state, file locking, daily log append, hook logging, retry helper), `memory_flush.py` (background Agent SDK job that distills a conversation excerpt into the daily log), `db.py` (SQLite + FTS5 + sqlite-vec search index), `embeddings.py` (FastEmbed wrapper), `memory_index.py` (chunks + indexes the vault), `memory_search.py` (keyword/semantic/hybrid search CLI). Index data lives in `.claude/data/memory.db` (SQLite, gitignored) and `.claude/data/models/` (FastEmbed model cache, gitignored) — both already covered by the existing `.claude/data/` gitignore rule, no separate entry needed.
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
- `uv run --project .claude/scripts python .claude/scripts/memory_index.py` — index (or re-index) the vault for search. Also `--rebuild` (force full reindex) and `--stats` (print file/chunk/vector counts + db size). First run downloads the ~90MB FastEmbed model to `.claude/data/models/` — expect a wait.
- `uv run --project .claude/scripts python .claude/scripts/memory_search.py "query" [--mode keyword|semantic|hybrid] [--path-prefix <prefix>] [--limit N]` — search the vault. Default mode `hybrid`, default limit 10.

## Completed Phases

- **Phase 1 (2026-07-03):** Memory vault created at `SecondBrain/Memory/` with pre-filled SOUL/USER/MEMORY/HEARTBEAT. BOOTSTRAP onboarding completed same day (archived to `archive/`): blunt pushback, English-only email drafts, on-demand drafting (no auto-scan), every-finding notifications, one-pager digest as vault file, cybersecurity thesis profiles in `research/thesis-cybersecurity.md`, IC Deck Structure Notion page as living slide framework. Pending deliveries tracked in USER.md.
- **Phase 2 (2026-07-05):** Hooks wired for context persistence. `.claude/scripts/` is now its own `uv` project (`pyproject.toml` + `uv.lock`, Python 3.12+, deps: `claude-agent-sdk`, `python-dotenv`, `tzdata`). `session_start_context.py` injects SOUL/USER/MEMORY + the last 2 daily logs that exist on disk (not a today/yesterday fallback) at session start. `pre_compact_flush.py` / `session_end_flush.py` extract the tail of the transcript and spawn `memory_flush.py` detached (`subprocess.Popen`, non-blocking) with a `CLAUDE_INVOKED_BY` recursion guard so the Agent SDK's own headless subprocess can't re-trigger the same hooks. `memory_flush.py` dedupes flushes of the same session within 60s (`.claude/data/state/flush-state.json`, lock-protected) and appends distilled notes to the daily log unless the model returns `FLUSH_OK`. `block_secrets.py` (PreToolUse baseline, hardened in Phase 8) blocks reads/writes/bash targeting `.env`, credentials, keys, SSH material. **Interpreter split (deviation from the PRD's illustrative bare-`python`-everywhere example):** `block_secrets.py` runs via bare `python` (zero third-party imports, fires on every tool call, latency matters) while the other 3 hooks route through `uv run --project .claude/scripts python ...` since they import `config.py`, which needs `tzdata`/`python-dotenv` from the venv — bare `python` on PATH isn't guaranteed to be the right interpreter with the right deps. All 4 hooks tested manually on this machine via realistic stdin JSON (incl. Windows-backslash paths) matching the exact `settings.json` invocation.
- **Phase 3 (2026-07-05):** Local hybrid memory search (keyword + semantic RAG), fully offline. `db.py` is SQLite-only (no Postgres/Protocol/factory abstraction — per `MEMORY.md`'s "2026-07-03 — Local-only, no VPS" decision, since this project has no VPS deployment to justify a dual backend). Schema: `files` (incremental-reindex bookkeeping via sha256 content hash), `chunks` (chunk text + a plain BLOB copy of its embedding), `chunks_fts` (FTS5, trigger-synced from `chunks`), `vec_chunks` (sqlite-vec vec0, `distance_metric=cosine` set explicitly since vec0 defaults to L2). Every embedding is stored twice — once in `vec_chunks`, once as a BLOB on the `chunks` row — so `vector_search()` can fall back to a standalone numpy brute-force `knn()` (vectorized cosine similarity, no sqlite dependency) if sqlite-vec ever fails to load or query on the work PC; this insurance path is unit-tested directly with synthetic vectors, not by forcing sqlite-vec to fail. `memory_search.py`'s `search_hybrid()` implements the PRD's literal min-max normalization algorithm (fetch top `SEARCH_HYBRID_FETCH_K`=20 candidates from each side, min-max normalize each side to 0-1 independently — with an equal-scores/single-candidate edge case defaulting to 1.0 instead of dividing by zero — then combine `0.7*vector + 0.3*keyword`), not the reference implementation's `1/(1+x)` reciprocal scoring. `embeddings.py` wraps FastEmbed (`sentence-transformers/all-MiniLM-L6-v2`, 384-dim) with an explicit `cache_dir` (`.claude/data/models/`) since the library's default is a temp dir. `memory_index.py` chunks markdown into ~400-token/50-token-overlap segments tracking `#`/`##` section titles, incrementally re-indexes only changed files, and sweeps index rows for files no longer on disk (documented in-code as pruning derived cache data, not vault content — doesn't violate "never delete anything"). Confirmed from inside the venv post-install: `sqlite-vec` 0.1.9 does ship a `sqlite_vec-0.1.9-py3-none-win_amd64.whl` on PyPI, and it installed/loaded cleanly. Tested end-to-end against the real 6-file vault: full index (12 chunks/12 vectors), a no-op re-run (all 6 skipped as unchanged), a single-file incremental re-index (editing one file only re-indexed that file, chunk/vector totals otherwise unchanged), and keyword/semantic/hybrid/`--path-prefix` searches all returning sane, correctly-ranked results.

## Out of Scope

- `course-reference/` — read-only reference. Never modify; copy patterns out instead.

## Approval Required

The operating loop is: **agent drafts → Or approves the specific item → agent executes**.

- Any external action (send email, post, create/update in Notion or other work tools) needs per-item approval first; after approval the agent executes it itself.
- Modifying files outside the vault/workspace: agree on scope and exact change first.
- Never delete anything — no exceptions. Archive or move instead.
- Work/org data access is read-only by default; never make purchases or modify financial data.
- Installing global tools or changing system settings (schedulers, services).
