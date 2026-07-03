# Backport Ideas → Personal Agent (NanoClaw)

Ideas from building the work Second Brain that could improve the personal agent.
Repo: https://github.com/OJS-9/nanoclaw_multi_agent (local: ~/projects/nanoclaw_multi_agent)

Workflow: add candidates here as we build → periodically verify each against the
NanoClaw codebase (it may already have the feature) → open a GitHub issue for the
ones that hold up, then mark them with the issue link.

## Candidates (unverified — check NanoClaw before opening issues)

- [ ] **Memory flush on session end** — course pattern: when a session ends, a background
  Claude call (no tools) summarizes what mattered into a daily log, instead of losing it.
- [ ] **Daily reflection job** — reviews yesterday's logs and promotes important items to
  long-term memory; includes write-protection on the personality file to prevent "soul drift".
- [ ] **Hybrid memory search** — local embeddings (FastEmbed) + keyword search over memory
  files, SQLite + sqlite-vec, 0.7 vector / 0.3 keyword weighting. Fully local, no API cost.
- [ ] **Heartbeat state diffing** — snapshot integration data between runs and only alert on
  new/changed items, so no repeat notifications.
- [ ] **Draft lifecycle with voice-matching** — drafts move through active/sent/expired;
  new drafts RAG-search past sent replies to match the user's tone.
- [ ] **block-secrets hook** — a PreToolUse hook that blocks the agent from reading .env,
  tokens, keys, and from running commands that print environment variables.
- [ ] **3-layer input sanitization** — pattern detection → markdown escaping → XML trust
  boundaries on all external text (emails, messages) before the agent reads it.

## Opened Issues

- (none yet)
