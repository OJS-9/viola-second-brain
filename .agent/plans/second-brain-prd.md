# Or's Second Brain — Build Plan (PRD)

**Generated:** 2026-07-03
**For:** Or, Investment Analyst at Viola Ventures
**Summary:** A local, cross-platform (macOS → Windows) agentic second brain that acts as a due-diligence sidekick — researching companies, generating slides from Or's framework, keeping Notion tasks in sync, drafting email replies, and delivering a weekly cybersecurity / AI-infra / defense-tech digest. Operating mode: **Advisor with execute-on-approval** — the agent drafts, Or approves the specific item, the agent executes.

---

## Global conventions (apply to every phase)

- **Language:** Python 3.12+ only, managed with `uv`. All paths via `pathlib`, derived from the project root — never hardcoded. No shell scripts as core logic.
- **Cross-platform rule:** built and tested on macOS now; must run unchanged on Windows (work ThinkPad). Every OS-specific piece (scheduler, notifications, file locking) needs both implementations or a documented Windows path.
- **Python gotcha (macOS):** never use Apple's system Python — it can't load SQLite extensions (needed in Phase 3). Use uv-managed or python.org/Homebrew Python.
- **Secrets:** in `.claude/scripts/.env` (gitignored). The LLM never sees tokens — Python modules authenticate and pass only data (API key isolation).
- **Timezone:** Asia/Jerusalem everywhere (heartbeat active hours, calendar queries, digest scheduling).
- **Approval loop:** agent drafts → Or approves the specific item → agent executes. No external write (email send, Notion create/update outside its own areas, posts) without per-item approval. **Never delete anything** — archive/move instead.
- **Claude auth:** the Agent SDK inherits Claude Code's login. On the work PC this is Viola's Claude subscription — leave `ANTHROPIC_API_KEY` unset in all scheduler environments so jobs bill the subscription, not an API key.
- **After every phase:** update `CLAUDE.md` (new paths, build commands, conventions) and mark the phase in "Completed Phases". If a command isn't in CLAUDE.md, the agent doesn't know it exists.

---

## Phase 1: Foundation (Memory Layer)

**What:** Create the memory vault — a folder of markdown files that is the brain's long-term memory, viewable in Obsidian.

**Key files:**
```
SecondBrain/Memory/
  SOUL.md            # personality: concise analyst-brief tone, advisor mode, boundaries
  USER.md            # Or's profile: role, platforms, drafting criteria, account IDs (no secrets)
  MEMORY.md          # long-term facts, decisions, lessons — stays concise
  BOOTSTRAP.md       # first-run onboarding conversation script (deletes itself when done)
  HEARTBEAT.md       # checklist of what heartbeat runs monitor
  index.md           # catalog of every vault page, updated on every ingest (NanoClaw lesson)
  daily/             # append-only daily logs YYYY-MM-DD.md
  meetings/          # meeting notes and decisions
  companies/         # one file per startup in play (deal flow context)
  people/            # one file per founder/partner/ecosystem contact (NanoClaw lesson)
  research/          # DD research notes + sector research (cyber, AI infra, defense-tech)
  research/sources/  # raw material (articles, exports, decks) — read-only once saved; notes cite it
  methods/           # Or's DD flow SOPs — living documents (see Phase 5)
  content/           # slide outlines, event content, digest archive
  drafts/active|sent|expired/   # email draft lifecycle (Phase 6)
```

- Vault root `SecondBrain/` sits inside the project; open it as an Obsidian vault (Obsidian is the viewer — everything works without it).
- BOOTSTRAP.md drives a one-time interactive onboarding (communication style, drafting criteria, digest preferences) to fill USER.md/SOUL.md/HEARTBEAT.md; picks up where it left off if interrupted.
- Rewrite root `CLAUDE.md` for the operational system: key paths, conventions above, "Build Commands" section (placeholder now, filled as phases land), Completed Phases.

**Dependencies:** none. **Complexity: Low.**

**Personalization:** folder set mirrors Or's memory categories (meetings, companies, research, methods, content, team context inside USER.md). SOUL.md encodes the advisor loop and "be the smartest in the room" digest mission.

---

## Phase 2: Hooks (Context Persistence)

**What:** Wire Claude Code lifecycle hooks so every session starts with memory loaded and ends with an intelligent summary saved.

**Key files:** `.claude/hooks/session_start_context.py`, `pre_compact_flush.py`, `session_end_flush.py`; `.claude/scripts/memory_flush.py`, `shared.py`; hook config in `.claude/settings.json`.

**Implementation notes (researched, July 2026):**
- Hook config lives in `.claude/settings.json` (committed); machine-specific interpreter overrides in `settings.local.json`. Use **exec form** for cross-platform: `{"type": "command", "command": "python", "args": ["${CLAUDE_PROJECT_DIR}/.claude/hooks/session_start_context.py"]}` — no shell involved, identical on Mac/Windows (ensure `python` on PATH via uv).
- Hooks receive JSON on stdin: `session_id`, `transcript_path`, `cwd`, event fields. SessionStart injects context by printing `{"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "..."}}`; register it for matchers `startup`, `resume`, AND `compact` (re-inject after compaction).
- SessionStart reads SOUL.md + USER.md + MEMORY.md + last 2 daily logs + BOOTSTRAP.md if present (onboarding trigger).
- SessionEnd/PreCompact get `transcript_path` (conversation JSONL) — they spawn `memory_flush.py` **detached** (`subprocess.Popen`) and exit immediately; also mark hooks `"async": true`.
- `memory_flush.py`: Agent SDK background job, `tools=[]` (pure reasoning — note: `tools`, not `allowed_tools`, is the capability restriction), `setting_sources=[]`, `max_turns=1`. Distills decisions/lessons/facts from the transcript into bullet points appended to the daily log. Dedup: skip if same session flushed <60s ago.
- **Recursion guard:** every SDK job sets `os.environ["CLAUDE_INVOKED_BY"] = "<job>"`; SessionEnd/PreCompact hooks read it and exit 0 if set — otherwise SDK exits trigger new flushes infinitely.
- `shared.py`: `file_lock()` (`msvcrt` Windows / `fcntl` Unix), `with_retry()` (exponential backoff for API calls), atomic writes (`.tmp` + `os.replace`). Everything that appends to daily logs or state files uses the lock.

**Implementation note (built 2026-07-05):** built as planned, with one deliberate deviation from the bare-`python`-everywhere illustrative example above. `block_secrets.py` runs via plain `{"command": "python", ...}` — it's zero-dependency stdlib (`json`/`re`/`sys` only) and fires on every single tool call, so skipping `uv run`'s startup overhead matters for latency. The other 3 hooks (`session_start_context.py`, `pre_compact_flush.py`, `session_end_flush.py`) import `config.py`, which needs `tzdata` and `python-dotenv` from the `.claude/scripts` venv — relying on bare `python` on PATH to be the right interpreter with the right packages installed is fragile (which Python is "on PATH" varies by shell/machine/uv-shim state). Those 3 route through `{"command": "uv", "args": ["run", "--project", "${CLAUDE_PROJECT_DIR}/.claude/scripts", "python", ...]}` instead — still no shell, still identical on Mac/Windows, just resolves to the project's own venv deterministically. `"async": true` was added to the PreCompact/SessionEnd hook entries per the plan; it was accepted by Claude Code's settings schema without error (not rejected as an unknown key), though its concrete effect wasn't separately isolated from the hooks' own detached-`Popen`-and-exit-0 behavior, which independently guarantees non-blocking execution regardless.

**Dependencies:** Phase 1. **Complexity: Medium.**

---

## Phase 3: Memory Search (Hybrid RAG)

**What:** Local hybrid search over the vault — semantic + keyword — so the brain can find "that founder call about ARR" without exact words.

**Key files:** `.claude/scripts/db.py`, `embeddings.py`, `memory_index.py`, `memory_search.py`. Index DB at `.claude/data/memory.db` (gitignored, regenerable).

**Implementation notes (researched):**
- **FastEmbed** (v0.8.x): `sentence-transformers/all-MiniLM-L6-v2`, 384-dim, ~90MB one-time download, ONNX/CPU (no PyTorch). Set `cache_dir` explicitly (project `.claude/data/models/`) — default is the temp dir.
- **sqlite-vec** (v0.1.9): pip wheels for macOS arm64 AND Windows x64. Load via `sqlite_vec.load(db)` after `enable_load_extension(True)`. vec0 table: `embedding float[384] distance_metric=cosine` (default is L2 — set cosine explicitly). Brute-force scan is <10ms at our scale.
- **FTS5** external-content table for keywords; `rank` is *negative* BM25 (lower = better) — negate before normalizing. Wrap query terms in quotes to dodge FTS5 syntax errors.
- **Hybrid merge in Python:** top-20 from each side → min-max normalize each score set to 0–1 → `0.7 * vector + 0.3 * keyword` → top-N. 
- **Incremental indexing:** files table with relative path + mtime + sha256; re-embed only changed files; sweep index rows for files that no longer exist (index is derived data — pruning it doesn't violate no-delete).
- **Insurance:** put KNN behind a tiny interface (`knn(vec, k)`) with a numpy brute-force fallback (7MB RAM, <5ms at 5K chunks) in case sqlite-vec misbehaves on the work PC.
- CLI: `memory_search.py "query" [--mode hybrid|keyword|semantic] [--path-prefix drafts/sent] [--limit N]`, `memory_index.py --rebuild|--stats`.

**Dependencies:** Phase 1 (vault exists). **Complexity: Medium.**

**Implementation note (built 2026-07-05):** built SQLite-only — no Postgres, no `Protocol`/factory abstraction, no `DATABASE_URL` — per `MEMORY.md`'s "2026-07-03 — Local-only, no VPS" decision; a dual-backend abstraction would add complexity with no deployment target to justify it, and this user (Or) is a Python/SQL/Flask beginner who benefits from a simpler, single-path module. Hybrid scoring implements the literal min-max normalization algorithm described above (fetch top `SEARCH_HYBRID_FETCH_K`=20 from each side, min-max normalize each side to 0-1 independently with an equal/single-candidate edge case defaulting to 1.0 rather than dividing by zero, then `0.7*vector + 0.3*keyword`) rather than a reciprocal `1/(1+x)` scoring scheme, matching this document's spec exactly. The KNN insurance fallback was built as specified: every chunk's embedding is stored twice (once in the `vec_chunks` vec0 table, once as a plain BLOB column on `chunks`), and `vector_search()` catches any exception from the vec0 MATCH query and falls back to a standalone, vectorized numpy `knn()` (cosine similarity via one matrix dot-product, no sqlite dependency) — verified directly with hand-built synthetic vectors (a near-parallel vector correctly outranked an orthogonal one) rather than by forcing sqlite-vec itself to fail. The sqlite-vec Windows wheel claim checked out: `sqlite-vec` 0.1.9 ships `sqlite_vec-0.1.9-py3-none-win_amd64.whl` on PyPI, confirmed present in `uv.lock` and installed/loading cleanly from inside the `.claude/scripts` venv on this machine.

---

## Phase 4: Integrations

**What:** Python modules per platform, one pattern: dataclass → auth → query functions → context formatter → CLI subcommand. Registry detects which are configured; unified CLI `query.py <platform> <cmd>`.

**Key files:** `.claude/scripts/integrations/registry.py`, `integration_template.py`, `notion_api.py`, `nimble_api.py`, `outlook_api.py`, `gcal_api.py`; CLI at `.claude/skills/direct-integrations/scripts/query.py`.

### 4.1 Notion (first — center of gravity)

- **Auth:** internal integration token (`ntn_...`) in `.env`. **Viola dependency:** only workspace owners can create integrations, and enterprise workspaces can restrict connections to an approved list — may need an admin. **Dev path:** build against Or's personal Notion workspace on the Mac now; swap the token on the work PC later. **If the work token is blocked:** fall back to the Notion Claude connector (same no-IT route as Outlook/Affinity) for on-session use, keeping the API module for whatever workspace the token can reach.
- **SDK:** `notion-client` (ramnes/notion-sdk-py) v3.x. Pin `Notion-Version: 2025-09-03`.
- **Critical post-2025 API model:** databases are containers; rows+schema live in **data sources**. Resolve once at startup: database ID (from URL, 32-hex before `?v=`) → `databases.retrieve` → `data_source_id`; cache it. Query via `data_sources.query` with filters/sorts; create pages with `parent={"type": "data_source_id", ...}`.
- **Operations needed:** query tasks DB (open tasks, due dates) · create/update task pages (status property: values must already exist; `select` auto-creates, `status` does not) · create digest/DD report pages · append markdown-converted blocks.
- **Needs a small markdown→blocks converter** (headings, bullets, paragraphs) — Notion has no markdown input. Respect limits: 100 blocks per append, 2000 chars per rich_text, page_size ≤ 100, ~3 req/s (honor `Retry-After` on 429; SDK has a retry option).
- Writes follow the approval loop: task status updates and page creations in the agent's own areas (digest pages, DD notes) are pre-approved by convention recorded in USER.md; anything touching shared team pages needs per-item approval.

### 4.2 Nimbleway web research (second — no work accounts needed)

- **Auth:** `Authorization: Bearer <API key>` (key from Account Settings → API Keys). Base: `https://sdk.nimbleway.com`. (Legacy `api.webit.live`/Basic-auth docs are outdated — ignore.)
- **`POST /v1/search`** — the digest workhorse: `{"query", "focus": "news", "time_range": "week", "max_results": 10, "search_depth": "lite"}` → results with title/description/url. `deep` also fetches page content (+1 credit/page) — prefer `lite` + targeted extract.
- **`POST /v1/extract`** — DD reading: `{"url", "formats": ["markdown"], "render": false}` → clean markdown at `data.markdown`. Default `render: false`; retry with `render: true` (driver vx8) only when markdown comes back thin. Client timeout 120s.
- **SERP** (`/v1/serp`, `search_engine: "google_search"|"google_news"`) available for precise queries; always pass `no_html: true`.
- **Retries:** on 429 (honor `retry_after`), 5xx, and 555 (render timeout) with backoff via `shared.with_retry()`; never retry 400/402 (out of credits). Rate limits (83 req/s) are a non-issue.
- Key is on Viola's Nimble account — log credit usage per run so costs are visible.

### 4.3 Outlook mail + calendar — via the Claude connector (no IT ticket)

- **Decision (Or, 2026-07-03):** use the Outlook mail/calendar connectors attached to Or's Claude account — the same no-IT route Affinity already uses — instead of registering a Microsoft Graph app.
- **How it works:** connector tools (read inbox/threads, read calendar, create drafts) are available in Claude Code / Claude Desktop sessions, and to Agent SDK sessions that load the user's MCP config (`setting_sources=["user"]` or explicit `mcp_servers`).
- **The approval loop still holds:** agent reads a thread → writes the reply as a draft (connector draft tools where available; otherwise a markdown draft in `drafts/active/`) → Or approves → agent sends/finalizes.
- **Known limitation — test early in Phase 6:** connectors are OAuth'd through the Claude app, so **headless scheduled runs may not reach them.** If the heartbeat can't use connectors, email/calendar triage becomes an on-session flow: a `morning-triage` command that runs when Or opens Claude (or once a day via the SessionStart hook) instead of background polling. The Notion + Nimble parts of the heartbeat are unaffected (API-based).
- **Documented fallback only if connectors prove insufficient:** a direct Microsoft Graph app (single-tenant public client; delegated Mail.Read/ReadWrite/Send + Calendars.Read; `msal`+`requests` with `SerializableTokenCache`; createReply → PATCH → approve → `/send`; `calendarView` with `Prefer: outlook.timezone="Israel Standard Time"`). Full recipe goes in `docs/graph-fallback.md`. It costs one IT consent ticket — which is exactly why it's the fallback.

### 4.4 Google Calendar, personal (read-only, alongside 4.3)

- Desktop OAuth (`google-auth-oauthlib`), scope `calendar.readonly`, token.json refresh pattern.
- **Gotcha to dodge on day one:** leave the consent screen in "Testing" and refresh tokens die every 7 days. **Publish the app to Production** (ignore verification; it's personal use) → tokens last indefinitely.
- `events().list(calendarId="primary", timeMin/timeMax RFC3339 with offset, singleEvents=True, orderBy="startTime")`.

### 4.5 Affinity — keep exactly as it works today

The existing Claude Code connection + founder-classification skill. No Python module, no IT involvement. Just document it in USER.md/HEARTBEAT.md so DD flows know to call it, and keep usage read-only.

### 4.6 Snowflake — no direct connection (IT won't approve it). Use the data-drop pattern

- Or exports query results himself (Snowsight → Download CSV/XLSX, or from the BI tool) into `SecondBrain/data-drops/`.
- The agent detects new files, parses them with pandas, uses them read-only in analysis, then moves them to `data-drops/processed/` (moved, never deleted).
- Zero credentials, zero IT surface — the read-only boundary is physical. Recurring needs (e.g., weekly portfolio metrics) become a documented 30-second export habit in HEARTBEAT.md.

**Dependencies:** Phase 2 (shared.py). **Complexity: Medium per integration.**

---

## Phase 5: Skills (Starter Pack)

**What:** Teach the agent Or's ways of working as reusable skills.

**Key files:** `.claude/skills/<name>/SKILL.md` (+ `scripts/`, `references/`).

1. **`vault-structure`** — teaches the folder layout, file naming, YAML frontmatter conventions, checkbox syntax. Low.
2. **The DD skill family** — not one monolithic skill: one skill per DD dimension, mirroring how Or actually works, each maintaining its own living SOP in `SecondBrain/Memory/methods/`:
   - `dd-market` — market sizing, category dynamics, timing ("why now")
   - `dd-competition` — **wraps Or's existing competitors skill** (ready today — plug in, don't rebuild)
   - `dd-founders` — background, track record, reference prep; pulls Affinity context
   - `dd-problem-solution` — problem validation and product/solution assessment
   - `dd-game-plan` — the VC thesis: round dynamics, ownership, why Viola wins
   A shared `dd-core` reference defines common conventions: sourcing rules, verified/unverified tagging, output format. Each skill is built by interviewing Or about how he approaches that dimension today (sop-creator pattern), and after each real DD a 5-minute retro updates the relevant SOPs — Or is building his own craft here, not just automating. Skills ship incrementally: start with dd-competition (exists) + dd-market, add the rest as they're needed on real deals. Medium.
3. **`slide-generator`** — two inputs, cleanly separated (BOOTSTRAP 2026-07-03):
   - **Content framework:** Or's "IC Deck Structure" Notion page (work workspace, page ID `363d4a10e39a81c9b0a3ec18eb481122`) — defines what slides an IC deck has and what each covers. Read via Notion when connected (cache a copy in `methods/`). **Living document:** after each deck produced, run a retro and propose optimizations to that page — applied only after Or approves.
   - **Visual template:** any Viola .pptx (pending from Or). python-pptx (v1.0.2, pure Python, no PowerPoint needed, identical on Mac/Windows) renders a **JSON slide-spec** (`{"layout": "<name>", "placeholders": {idx: content}}`) into it. Setup: inspector script dumps each layout's name + placeholder idx/types into `references/template-map.md`; reference layouts by name, placeholders by idx; template owns all styling. Limitations: add new slides from layouts (don't mutate existing), no SmartArt, no preview — output opens in PowerPoint for review (approval loop before any deck leaves the machine). Medium.
4. **`dd-sidekick`** — the orchestrator: given a company name → Nimble search + extract (site, news, funding) → Affinity lookup → invokes the relevant `dd-*` skills → assembles their outputs into one structured research note in `companies/`, sources cited → optionally renders key findings through slide-generator. Every claim tagged verified/unverified (verification = second independent source). Or can also run any single `dd-*` skill standalone when he only needs one dimension. Medium-High (builds on everything).

**Dependencies:** Phases 1, 3, 4 (dd-sidekick needs search + integrations; vault-structure only needs Phase 1). **Complexity: Low-Medium overall.**

**Personalization:** slide framework from Or; DD stages from his own description; digest sectors (cyber/AI-infra/defense-tech) appear in Phase 6.

---

## Phase 6: Proactive Systems (Heartbeat + Reflection + Digest)

**What:** The brain starts acting without being asked — on a schedule, within Advisor limits.

**Key files:** `.claude/scripts/heartbeat.py`, `memory_reflect.py`, `weekly_digest.py`, `notifications.py`; state in `.claude/data/state/` (per-machine, not synced).

> **NanoClaw production lessons applied to this phase** (see `docs/nanoclaw-lessons.md`): heartbeat starts with a **credentials health check** (ping each configured integration, alert Or before jobs run blind — NanoClaw's most repeated failure was silently-expired tokens); content that ships (digest, drafts, slides) passes **quality gates** (reviewer-persona check + Hebrew/English audit); Notion task sync **reconciles and flags discrepancies** — and escalates items that bounce repeatedly — instead of overwriting; weekly reflection includes a vault **lint** (contradictions, orphans, stale pages, index gaps); drafting uses a **distilled voice doc** refreshed from `drafts/sent/` in addition to RAG.

**Heartbeat (every 30 min, active hours 08:00–20:00 Asia/Jerusalem):**
- Python gathers first (cheap, deterministic): open Notion tasks, personal GCal, active drafts, digest state — all API-based. Outlook mail/calendar come via connector inside the SDK session if headless connector auth works (test first — see 4.3); otherwise they're covered by the on-session `morning-triage` flow instead. Then ONE Agent SDK `query()` call reasons over the bundle.
- SDK job config: `tools=["Read","Write","Edit"]` + same in `allowed_tools`, `permission_mode="dontAsk"`, `setting_sources=[]`, `max_turns` capped, `cwd=vault`, PreToolUse in-SDK hook fencing writes to the vault (compare paths with `Path.resolve()`/`is_relative_to` — never string prefixes, Windows uses `\`). Log `ResultMessage.total_cost_usd` per run to the daily log.
- **State diffing:** snapshot integration data; only surface new/changed items — no repeat alerts.
- **Notifications:** macOS `osascript` now; Windows toast (PowerShell BurntToast or `win11toast`) documented for Phase 9.
- **Advisor behaviors:** notify + draft, never send. **Email drafting is ON-DEMAND in v1** (BOOTSTRAP decision 2026-07-03: low volume — Or asks, agent drafts; no heartbeat draft-scanning until Or upgrades it). When asked: voice-match via distilled voice doc + `memory_search.py --path-prefix drafts/sent` → write markdown draft to `drafts/active/` (YAML frontmatter: type, source_id, recipient, subject, created, status) and a connector draft in Outlook where possible. On approval the agent sends and moves the file to `drafts/sent/` capturing final text (corpus for future voice-matching). Unactioned drafts >24h → `drafts/expired/` — moved, never deleted.
- **Task check-ins:** compare Notion tasks against calendar/mail activity; nudge on stalled tasks ("X due Friday, no activity — still on track?") and propose new tasks spotted in email (created in Notion only after approval).

**Weekly digest (separate job, Sunday 08:00):**
- Per sector (cybersecurity, AI infra, defense-tech): 3-4 Nimble `/v1/search` queries (`focus: "news"`, `time_range: "week"` — funding rounds, launches, notable essays) → dedupe vs. previous digests (state file of seen URLs) → extract top items as markdown → one SDK call synthesizes an analyst-grade brief (what happened, why it matters for Viola, companies worth a look) → saved to `content/digests/YYYY-WNN.md` + created as a Notion page. Sector queries defined in `HEARTBEAT.md` so Or can edit them in plain text.

**Daily reflection (08:00):** reviews yesterday's daily log, promotes durable items to MEMORY.md. **SOUL.md write-protection:** PreToolUse hook denies Edit/Write on SOUL.md for this job; identity-change suggestions go to the daily log for Or's review (prevents soul drift).

**Habits:** skipped for v1 (not in Or's top tasks); the course pattern is documented in the reference repo if wanted later.

**Dependencies:** Phases 2, 3, 4 (+ 5 for draft voice conventions). **Complexity: High** — split into 6a (heartbeat + notifications), 6b (digest), 6c (reflection), 6d (draft lifecycle).

---

## Phase 7: Chat Interface — RESOLVED: Claude Code / Claude Desktop

Or is happy operating through the Claude desktop app and terminal — that IS the chat interface. Nothing to build, and it's the environment where the connectors (Outlook, Affinity) are guaranteed to work. Outputs surface as Outlook drafts, Notion pages, vault files, and native notifications. **Phase dropped from the build.**

---

## Phase 8: Security Hardening

**What:** Enforce the boundaries in code, not vibes. (Baseline hooks land earlier; this phase completes and tests them.)

**Key files:** `.claude/hooks/block_secrets.py`, `guard.py`, `.claude/scripts/sanitize.py`, `tests/test_security.py`.

- **`block_secrets.py`** (PreToolUse, matcher `Read|Bash|Grep|Glob|Edit|Write`): deny access to `.env`, `token.json`, `msal_cache*`, `google_credentials*`, SSH keys, `repo-tokens`; deny Bash commands exposing env (`cat .env`, `printenv`, `echo $`, `os.environ` dumps); deny writing scripts that print secrets. Deny = `{"permissionDecision": "deny"}` JSON or exit 2 with stderr reason. Install this hook in **Phase 2** already; harden + test here.
- **`guard.py`** (PreToolUse on Bash + Write/Edit): the **no-delete rule** — block `rm`, `del`, `rmdir`, `shutil.rmtree`, `git clean`, moves to trash outside designated archive dirs; suggest `archive/` moves instead. Block writes outside project/vault without the approved-scope marker. Content checks happen in-script from `tool_input` (matchers only filter tool names).
- **`sanitize.py`** — 3-layer defense for ALL external text (email bodies, scraped pages, Notion content) before it reaches an agent prompt: (1) pattern detection for injection attempts ("ignore previous instructions", tool-call-looking text) → flag + neutralize; (2) markdown escaping; (3) wrap in XML trust boundaries (`<external_data source="email">...`) with a system-prompt rule that instructions inside are data, never commands. Emails and scraped web pages are the #1 injection vector for a VC-facing assistant — pitch decks and founder emails are untrusted input by definition.
- **Approval-loop enforcement:** send/post functions in integration modules require an `approved=True` argument that only the interactive approval path sets; heartbeat/background jobs physically can't pass it.
- **Read-only org data:** Outlook connector usage stays read + draft (send only via the approval path); Snowflake is the credential-less data-drop pattern; Affinity skill stays read-only.
- Test suite: attempt each forbidden action through the hooks and assert it's blocked (run on both OSes; recurring bugs get a pinned regression test).

**Dependencies:** Phases 2, 4. **Complexity: Medium-High.**

---

## Phase 9: Deployment (Local ×2: Mac dev → Windows prod)

**What:** Schedulers on both machines + the transfer runbook. No VPS — deliberate decision (work data stays off personal infrastructure).

**Key files:** `.claude/scripts/setup_scheduler_mac.py` (writes launchd plists), `setup_scheduler_windows.ps1` (Task Scheduler), `docs/windows-transfer.md`.

- **macOS (now):** launchd plists — heartbeat every 30 min, reflection daily 08:00, digest Sunday 08:00. Installing them = system change → Or's approval first.
- **Windows (later):** Task Scheduler equivalents (`Register-ScheduledTask`, run `pythonw.exe`); ensure tasks run as the logged-in user (Claude subscription credentials + MSAL cache are per-user) and inherit no `ANTHROPIC_API_KEY`.
- **Transfer runbook:** install Python 3.12/uv + Git (+ Git Bash — Claude Code's Bash tool needs it on Windows) → clone repo → `uv sync` → recreate `.env` → log in Claude Code (Viola sub) → reconnect connectors in the Claude app (Outlook, Affinity) → re-auth Notion token (work workspace), Google token, Nimble key → `memory_index.py --rebuild` → register scheduled tasks → run Phase 8 security tests + a manual heartbeat `--test`.
- **Known Windows deltas (pre-researched):** Agent SDK — keep `cli_path` configurable (WinError 193 workaround) and prefer one-shot `query()` (client hangs reported); hooks run via Git Bash by default — exec-form Python hooks sidestep it; paths arrive with `\` (pathlib comparisons only); sqlite-vec has Windows wheels (numpy fallback ready if needed).
- **Cost estimate:** infra $0 (all local). Claude usage on Viola's subscription (heartbeat ~$0.05/run notional → log actuals). Nimble: digest ≈ 12-16 lite searches + ~20 extracts/week ≈ ~$0.05/week at listed rates; DD sidekick usage variable — usage logged per run. Obsidian free.

**Dependencies:** everything prior. **Complexity: Medium.**

---

## Recommended build order

1. **Phase 1** — vault + CLAUDE.md rewrite (one session)
2. **Phase 2** — hooks + memory flush (with baseline block_secrets)
3. **Phase 3** — memory search
4. **Phase 4.1 Notion** → **4.2 Nimble** (both testable on the Mac today) · 4.3 Outlook connector (test SDK/headless access early) · 4.4 GCal · 4.5 Affinity as-is · 4.6 data-drop folder
5. **Phase 5** — skills (vault-structure early; dd-competition wrap + dd-market first of the DD family; slide-generator once Or's template is in hand; dd-sidekick last)
6. **Phase 6** — 6a heartbeat → 6b digest → 6c reflection → 6d draft lifecycle (6d shape depends on the 4.3 connector test)
7. **Phase 8** — security hardening + tests
8. **Phase 9** — schedulers + Windows transfer

**Parallelizable:** 3 with 4.1/4.2; 5's early skills with 4. **Early asks for Or:** (a) slide framework .pptx, (b) Nimble API key into `.env`, (c) point me at the existing competitors skill so it can be wrapped into `dd-competition`.

---

*This PRD was generated from `my-second-brain-requirements.md` on 2026-07-03 with per-API research current as of July 2026. Revisit and update as the system evolves — it is a living plan, and every completed phase should be reflected here and in CLAUDE.md.*
