# Lessons from NanoClaw (2 months in production on the VPS)

Reviewed 2026-07-03: `/root/nanoclaw` — wiki skill, `groups/global/wiki/` (82 pages), and the append-only ops log. Patterns only; no personal data copied here.

## Adopt into the Second Brain

1. **Wiki discipline: index + log + lint** *(→ Phase 5 vault-structure, Phase 6c reflection)*
   NanoClaw's knowledge base stays navigable because of three habits: `index.md` (catalog of every page, updated on every ingest), `log.md` (append-only record of every operation), and a periodic **lint** pass (find contradictions, orphan pages, stale content, missing cross-links — flag gaps to the user). Our vault gets all three: `SecondBrain/Memory/index.md`, ops entries in daily logs, and lint folded into the weekly reflection.

2. **Sources vs. generated pages** *(→ Phase 1 amendment, dd-sidekick)*
   Raw material (articles, exports, decks) lives in `sources/`, never modified; generated analysis lives in wiki pages that cite it. Added `research/sources/` to the vault. DD research notes must link back to their raw sources.

3. **One source at a time** *(→ dd-sidekick, digest)*
   NanoClaw's skill is explicit: batch-processing sources produces shallow pages. Ingest → understand → write pages → THEN next source. Our DD pipeline follows this.

4. **People pages are load-bearing** *(→ Phase 1 amendment)*
   People files (who they are, relationship, last touch, next step) carry NanoClaw's network memory. For a VC analyst this is core: added `people/` to the vault (founders, partners, ecosystem).

5. **Distilled voice doc beats raw RAG** *(→ Phase 6d drafting)*
   NanoClaw has `self_voice.md` — tone/vocabulary/rhythm distilled from 25 real posts — plus structure and hook libraries. Cheaper and more consistent than RAG-ing raw examples every time. We'll do both: distill a voice profile from sent drafts periodically; RAG only for context-specific matching.

6. **Quality gates before anything ships** *(→ Phase 6 drafting, slides, digest)*
   Every NanoClaw post passes: persona-panel review (3 named reader avatars must "green" it), an AI-tone check, and a **Hebrew-language audit** (its log shows real fixes each round). We'll adapt: reviewer-persona pass for slides/digests (e.g., "skeptical partner"), plus a Hebrew/English audit step on drafts.

7. **Credentials health check** *(→ Phase 6a heartbeat — added)*
   The single most repeated failure in 2 months of logs: **expired OAuth tokens silently killing scheduled jobs** (Nimble token expired → weekly review ran without data; competitor-intel cron fully blocked). Heartbeat gets a first-step auth check: ping each configured integration, notify Or on failure *before* a job runs blind. Prefer API keys over OAuth where possible (our Nimble integration already is).

8. **Two-way sync must reconcile, not overwrite** *(→ Notion task sync)*
   NanoClaw's weekly GitHub↔Notion sync flags discrepancies ("marked Done in Notion but still open on GitHub") and — critically — notices when the *same* items bounce repeatedly and escalates to the user. Our Notion sync adopts both behaviors.

9. **Catalyst calendar** *(→ digest / companies pages)*
   A rolling "what's coming in the next 2 weeks that matters" page, refreshed on schedule. For Or: funding-round rumors, conferences, product launches, portfolio events per coverage sector. Add as a digest section once the digest is stable.

10. **Concurrency is real, not theoretical**
    Duplicate entries appear in NanoClaw's own ops log (same line logged twice). Validates the PRD's file-locking + dedup requirements (Phase 2 `shared.py`) — keep them, test them.

## Backport candidates (Second Brain → NanoClaw) — added to backport-ideas.md

- **Credentials health-check cron** — NanoClaw suffered this twice in its own logs; it monitors everything except its own tokens. [strong candidate — evidenced]
- **File locking / log dedup** — duplicate ops-log entries observed. [verify: may be fixed already]
