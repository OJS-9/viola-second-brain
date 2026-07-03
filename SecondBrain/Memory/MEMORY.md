# MEMORY — Long-term facts, decisions, lessons

> Keep concise — this loads into every session. Details belong in daily logs or topic files; this file holds only what must always be known.

## Decisions

- **2026-07-03 — Local-only, no VPS.** Work email/Dropbox data and credentials never live on personal cloud infrastructure. The vault holds confidential Viola deal data.
- **2026-07-03 — Connector-first for work tools.** Outlook and Affinity go through Claude connectors; no Microsoft Graph app registration; avoid IT tickets wherever possible.
- **2026-07-03 — Snowflake = data-drop pattern.** Direct access won't be approved. Or exports CSV/XLSX into `data-drops/`; agent parses read-only.
- **2026-07-03 — DD is a skill family.** One skill per dimension (market, competition, founders, problem-solution, game-plan); Or's existing competitors skill becomes `dd-competition`.
- **2026-07-03 — Chat interface = Claude Desktop/terminal.** No bot to build.

## Standing goals

- Build the second brain phase-by-phase from `.agent/plans/second-brain-prd.md`; Or approves between phases.
- Capture patterns worth backporting to NanoClaw (personal agent) in `backport-ideas.md` at the project root.

## Lessons

- **2026-07-03 — From NanoClaw's 2 months in production** (full notes: `docs/nanoclaw-lessons.md`): keep a vault `index.md` + run periodic lint; separate raw `sources/` from generated notes; ingest one source at a time (batching → shallow notes); people pages carry network memory; distill a voice doc instead of only RAG-ing examples; gate outgoing content (persona review + Hebrew/English audit); check integration credentials proactively — expired tokens silently killed NanoClaw jobs twice.
