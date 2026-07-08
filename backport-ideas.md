# Backport Ideas → Personal Agent (NanoClaw)

Ideas from building the work Second Brain that could improve the personal agent.
Repo: https://github.com/OJS-9/nanoclaw (local path: ~/projects/nanoclaw, TBD)

Workflow: add candidates here as we build → periodically verify each against the
NanoClaw codebase (it may already have the feature) → open a GitHub issue for the
ones that hold up, then mark them with the issue link.

## Candidates (unverified — check NanoClaw before opening issues)

- [ ] **Daily reflection job** — reviews yesterday's logs and promotes important items to
  long-term memory; includes write-protection on the personality file to prevent "soul drift".
- [ ] **Heartbeat state diffing** — snapshot integration data between runs and only alert on
  new/changed items, so no repeat notifications.
- [ ] **Draft lifecycle with voice-matching** — drafts move through active/sent/expired;
  new drafts RAG-search past sent replies to match the user's tone.
- [ ] **block-secrets hook** — a PreToolUse hook that blocks the agent from reading .env,
  tokens, keys, and from running commands that print environment variables.
- [ ] **3-layer input sanitization** — pattern detection → markdown escaping → XML trust
  boundaries on all external text (emails, messages) before the agent reads it.

## Strong candidates (evidenced in NanoClaw's own logs, 2026-07-03 VPS review)

- [ ] **Credentials health-check cron** — NanoClaw's ops log shows the Nimble OAuth token expiring twice in June 2026, silently gutting the weekly LinkedIn review and fully blocking the competitor-intel cron. A daily "ping every configured integration, alert on failure" job would have caught both. It monitors everything except its own tokens.
- [ ] **Ops-log write locking/dedup** — duplicate consecutive entries visible in `groups/global/wiki/log.md` (e.g., the 2026-06-21 Typefully deletion logged twice). Verify whether concurrent writers are already serialized; if not, port the file-lock + dedup pattern from the second brain's `shared.py`.

## Opened Issues

- [ ] **Memory flush on session end** — https://github.com/OJS-9/nanoclaw/issues/TBD (verified missing, pre-check complete, ready to file)
- [ ] **Hybrid memory search** — https://github.com/OJS-9/nanoclaw/issues/TBD (verified missing, pre-check complete, ready to file)
