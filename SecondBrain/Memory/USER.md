# USER — Who Or is

- **Name:** Or Salinas
- **Role:** Investment Analyst, Viola Ventures (https://www.viola-group.com/fund/violaventures/)
- **Timezone:** Asia/Jerusalem · **Languages:** Hebrew + English
- **Programming:** beginner — Python, SQL, Flask only. Explain simply.
- **Personal email:** optimusor@gmail.com (personal Google Calendar lives here)
- **Work email:** <!-- fill on work PC -->

## What Or does

1. **Startup due diligence** — founders, market, problem, solution, VC game plan.
2. **Portfolio GTM projects** — hands-on code projects for portfolio companies (e.g., `ib-agent`, `bh-the-list` on his personal GitHub).
3. **Category / new-market research** — coverage sectors: **cybersecurity, AI infrastructure, defense-tech**.
4. **Webinars & events** — organizing and preparing content.

## Platform access map

| Platform | Route | Notes |
|---|---|---|
| Notion (docs + tasks — center of gravity) | API token (`.env`) | Task DB ID: <!-- fill in Phase 4.1 --> |
| Web research | Nimbleway API (`.env`) | digest + DD fetching |
| Outlook mail + calendar | Claude connector | no Graph app — avoid IT |
| Personal Google Calendar | API, read-only | publish OAuth app to Production (7-day token trap) |
| Affinity | existing Claude skill | read-only, founder classification |
| Snowflake | data-drop only | Or exports CSV/XLSX → `SecondBrain/data-drops/` |
| WhatsApp / Teams | none in v1 | Teams barely used |
| PitchBook | manual/browser | no API access |

## Drafting criteria

**Email voice:** always English. Sign-off: just "**Or**", usually preceded by one short context-fitting line ("Thanks," / "Here for anything," / etc. — pick what matches the email). Overall tone: adaptive to the email's context rather than one fixed register.

**When to draft: ON-DEMAND ONLY (v1).** Email volume is low — draft a reply only when Or explicitly asks. No proactive draft scanning by the heartbeat for now; revisit making it automatic once volume or trust grows.

## Notifications

**Every heartbeat finding pings** (native notification), not just urgent ones. Active hours 08:00–20:00 Asia/Jerusalem (heartbeat schedule) — no extra quiet hours defined. State diffing still applies: only NEW/changed findings ping, never repeats.

## Inbox urgent-flag list (heartbeat notifies immediately)

- Emails from **Alon Cinamon** (Principal — direct manager), the partners, **Alex Shmulovich** (Partner), **Asaf Schriber** (Associate)
- Emails from portfolio founders
- Anything with a term sheet / deal doc attached

## Assets & pending deliveries

- **IC Deck Structure (slide framework):** Notion page in the WORK workspace — https://app.notion.com/p/IC-Deck-Structure-363d4a10e39a81c9b0a3ec18eb481122 (page ID `363d4a10e39a81c9b0a3ec18eb481122`). This is the CONTENT framework for decks. **Living document:** after each deck we produce, run a retro and propose updates/optimizations to this page — updates applied only after Or approves (it's a work page). Accessible once work Notion is connected; until then, Or can paste its content for caching in `methods/`.
- **PENDING — visual .pptx template:** any Viola deck to render into (python-pptx needs the theme/layouts). Needed by Phase 5 slide-generator.
- **PENDING — competitors skill location:** path/repo of the existing skill, to wrap as `dd-competition`. Needed by Phase 5.
- **PENDING — Nimble API key:** Or creates `.claude/scripts/.env` with `NIMBLE_API_KEY=...` (never pasted in chat). Needed by Phase 4.2.

## Team context

- **Alon Cinamon** — Principal, Or's direct manager (Cyber / AI Infra)
- **Alex Shmulovich** — Partner (Deep Tech / AI)
- **Asaf Schriber** — Associate
<!-- ongoing: expand with partners, coverage areas, preferences -->
