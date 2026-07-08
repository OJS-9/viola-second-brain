---
name: direct-integrations
description: Query Notion and Nimble (web research) directly via Python APIs. Use when the user asks to check Notion tasks, create/update Notion pages, search the web for news/research, or extract page content as markdown. Triggers on requests like "check my Notion tasks", "create a page in Notion", "search for news about X", "pull the content from this URL", or any platform query.
---

# Direct Platform Integrations

Query Notion and Nimble directly — no Zapier/MCP needed.

## Script Path

`.claude/skills/direct-integrations/scripts/query.py`

## Running Commands

```bash
# Notion
uv run --project .claude/scripts python .claude/skills/direct-integrations/scripts/query.py notion tasks --database-id <id> [--max-results 50]
uv run --project .claude/scripts python .claude/skills/direct-integrations/scripts/query.py notion whoami

# Nimble
uv run --project .claude/scripts python .claude/skills/direct-integrations/scripts/query.py nimble search "<query>" [--focus news] [--time-range week] [--max-results 10] [--search-depth lite]
uv run --project .claude/scripts python .claude/skills/direct-integrations/scripts/query.py nimble extract <url> [--render]
```

## Setup

Both integrations read their API key from `.claude/scripts/.env`:

- `NOTION_API_KEY` — Notion internal integration token (`ntn_...`)
- `NIMBLE_API_KEY` — from Nimble Account Settings -> API Keys

If a key is missing, the CLI prints which env var to set instead of a stack trace.

## Notes

- **Notion post-2025 API model:** databases are containers; rows + schema live in "data sources". `notion tasks` resolves the database ID to its data source ID automatically (via `databases.retrieve`) and caches it for the process lifetime — callers just pass the database ID or URL.
- **Notion writes follow the approval loop** (see root CLAUDE.md): page creation in the agent's own drafts/digest areas is pre-approved by convention; anything touching shared team pages needs per-item approval first.
- **Nimble credit usage** is logged to `.claude/data/state/nimble-usage.log` (one line per call: endpoint, query/url, timestamp) since the API key is on a shared Viola account.
- **Nimble extract** automatically retries once with `--render` behavior (headless-browser mode) if the returned markdown comes back suspiciously thin — no need to guess up front.
- The Notion Task DB ID isn't confirmed yet — see `SecondBrain/Memory/USER.md`'s platform access map. Once Or provides a real database ID, `notion tasks --database-id <id>` is ready to use immediately.
