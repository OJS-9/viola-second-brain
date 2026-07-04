# HEARTBEAT — What the proactive runs check

> Plain-text config: edit freely, the heartbeat reads this file. Sections marked *(inactive)* activate when their phase is built (Phase 6).

## Every run (every 30 min, 08:00–20:00 Asia/Jerusalem) *(inactive — Phase 6a)*

- [ ] **Credentials health check FIRST**: ping each configured integration; on failure notify Or and skip dependent checks (never run blind — NanoClaw lesson)
- [ ] Open Notion tasks: anything due in 48h with no recent activity? → nudge
- [ ] New action items spotted in email → propose as Notion tasks (create only after approval)
- [ ] Personal Google Calendar: next meeting soon? → prep prompt if it's an external meeting
- [ ] Outlook inbox triage *(pending connector test — may move to on-session morning-triage)*
- [ ] Drafts in `drafts/active/` older than 24h → move to `drafts/expired/`
- Only surface NEW or CHANGED items vs. the last run (state diffing). No repeat alerts.

## Morning (first run of the day) *(inactive — Phase 6a)*

- [ ] Today's agenda: work calendar + personal calendar merged
- [ ] Yesterday's daily log written? If reflection flagged items for review, surface them.

## Weekly digest (Sunday 08:00) *(inactive — Phase 6b)*

Format: **one-pager** — top 3-5 items per sector, each item 1-2 lines (what happened + why it matters for Viola). Save as a **vault file** in `content/digests/YYYY-WNN.md` (no Notion page — Or reads it in chat and asks to elaborate on interesting items, so each item ends with sources for follow-up). Sunday 08:00.

**Cybersecurity queries** (score hits against `research/thesis-cybersecurity.md` — flag profile matches):
- cybersecurity startup funding round announced
- cybersecurity startup Israel stealth emerged
- AI generated code security / cloud misconfiguration autonomous remediation startup   ← thesis #1 build-to-secure
- human risk management / social engineering prevention startup                        ← thesis #2 human factor
- autonomous risk remediation / exposure management startup                            ← thesis #3 risk remediation

**AI infrastructure queries:**
- AI infrastructure startup funding round
- LLM inference optimization startup launch
- GPU cloud / AI compute announcement

**Defense-tech queries:**
- defense tech startup funding round
- defense technology procurement startup
- dual-use technology startup Israel

(Nimble `/v1/search`, focus=news, time_range=week; dedupe against previously-seen URLs.)

## Daily reflection (08:00) *(inactive — Phase 6c)*

- Review yesterday's `daily/` log → promote durable decisions/lessons/facts to MEMORY.md
- Never edit SOUL.md (write-protected) — suggestions go to the daily log
