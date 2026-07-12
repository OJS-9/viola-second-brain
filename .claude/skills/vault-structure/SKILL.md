---
name: vault-structure
description: |
  Reference for the SecondBrain/Memory/ vault's folder layout, file naming, YAML frontmatter,
  and checkbox conventions. Use whenever creating a new file under SecondBrain/Memory/, deciding
  where a piece of content should live, or unsure which folder/frontmatter/naming pattern applies.
  Triggers: "where should this go", "save this to the vault", "create a company/research/people
  note", "what frontmatter does this need", any file write under SecondBrain/Memory/.
---

# Vault Structure

Reference for `SecondBrain/Memory/` — Or's memory vault (open `SecondBrain/` in Obsidian; it's
plain markdown, works with any editor too). Read this before creating or filing any content
under `SecondBrain/Memory/`.

Source of truth for the layout itself: root `CLAUDE.md` → "Key paths" and "Vault conventions".
This skill exists to make those conventions load automatically when the assistant is about to
write into the vault — if the two ever disagree, `CLAUDE.md` wins; update this file to match.

---

## Folder layout — what goes where

| Folder | Purpose | Status as of 2026-07-08 |
|---|---|---|
| `SOUL.md` | Personality: tone, advisor-mode boundaries. **Write-protected** — don't edit without Or's explicit sign-off (prevents "soul drift"). | populated |
| `USER.md` | Or's profile: role, platforms, drafting criteria, account IDs. No secrets — those live in `.claude/scripts/.env`. | populated |
| `MEMORY.md` | Long-term facts/decisions/lessons. Loads into every session — keep it concise; details belong in daily logs or topic files. | populated |
| `HEARTBEAT.md` | Proactive-run config (what heartbeat monitors, digest seed queries). Plain-text editable by Or. | populated |
| `BOOTSTRAP.md` | First-run onboarding script. If present, run it. Archived once complete (see `archive/` row). | archived — none currently present (Phase 1 onboarding done 2026-07-03) |
| `daily/` | Append-only daily logs, one file per day. | has content (`2026-07-08.md`) |
| `companies/` | One file per startup in play — deal-flow context. | empty so far (`.gitkeep` only) |
| `people/` | One file per founder/partner/ecosystem contact (network memory). | empty so far |
| `research/` | DD research notes + sector research (cyber, AI-infra, defense-tech). | has content (`thesis-cybersecurity.md`) |
| `research/sources/` | Raw material — articles, exports, decks. **Read-only once saved**; notes cite it, never edit it in place. | empty so far |
| `methods/` | Or's DD-flow SOPs — living documents, updated via retros (see Phase 5 `dd-*` skills). | empty so far |
| `content/` | Slide outlines, event content, digest archive (e.g. `content/digests/YYYY-WNN.md`). | empty so far |
| `meetings/` | Meeting notes and decisions. | empty so far |
| `drafts/active/` | Email/message drafts awaiting Or's approval. | empty so far |
| `drafts/sent/` | Finalized drafts, captured after send — doubles as the voice-matching corpus. | empty so far |
| `drafts/expired/` | Drafts unactioned >24h, moved (not deleted). | empty so far |
| `archive/` | Obsolete files, moved here instead of deleted. Has one entry today: `BOOTSTRAP-completed-2026-07-03.md`. | has content |
| `index.md` | Catalog of every vault page. **Not yet created** — planned for Phase 5, part of the broader vault-lint/indexing work, not built by this skill. | does not exist yet |

**Decision rule:** ask "what kind of thing is this, and does it belong to one specific
company/person, or is it general?" — a specific startup's DD material goes in `companies/`, a
specific person's context goes in `people/`, sector-level or cross-company research goes in
`research/`, and raw un-editable source material (PDFs, saved articles, decks) goes in
`research/sources/`. If it's about *doing* DD (a process, not a finding) it belongs in `methods/`.

---

## File naming

**Established today:**
- Daily logs: `daily/YYYY-MM-DD.md` (e.g. `daily/2026-07-08.md`) — append-only, timestamped
  entries inside the file.
- Digests: `content/digests/YYYY-WNN.md` (ISO week number), per `CLAUDE.md`'s Phase 6 spec.
- Archived files keep a descriptive name plus a completion/archive date suffix, e.g.
  `archive/BOOTSTRAP-completed-2026-07-03.md`.

**Not yet established — proposed here, flag as a proposal, not a rule:** `companies/`,
`people/`, and `research/` (beyond the one existing thesis file) have zero real files yet, so
there's no precedent to follow for one-note-per-entity naming. Proposed convention, to confirm
with Or the first time it's actually used:
- `companies/<kebab-case-company-name>.md` (e.g. `companies/acme-security.md`)
- `people/<kebab-case-full-name>.md` (e.g. `people/jane-doe.md`)
- `research/<kebab-case-topic>.md` for standalone topic notes (the existing
  `research/thesis-cybersecurity.md` already follows this pattern, which is the one piece of
  real precedent supporting the proposal).

If Or has a different preference (e.g. including a date prefix, or grouping by sector
subfolder), update this section and don't treat kebab-case as locked in.

---

## YAML frontmatter

Company/research notes carry frontmatter with `type`, `created`, `status`, `sources` (per
`CLAUDE.md`'s Vault conventions). Real example, from `research/thesis-cybersecurity.md`:

```yaml
---
type: thesis
sector: cybersecurity
created: 2026-07-03
status: active
sources: [Or, BOOTSTRAP interview]
---
```

Notes:
- `type` describes the note's category (`thesis`, `company`, `person`, `research`, etc. — pick
  what's accurate, this isn't a closed enum yet).
- `status` reflects lifecycle (`active`, `archived`, etc.).
- `sources` is a list — cite where the content came from (a person, an interview, a URL, a doc).
- Extra fields beyond the core four are fine when useful (`thesis-cybersecurity.md` adds
  `sector`) — the four listed in `CLAUDE.md` are the floor, not a strict schema.
- Daily logs, `SOUL.md`, `USER.md`, `MEMORY.md`, and `HEARTBEAT.md` are structural/system files
  and don't follow this frontmatter pattern — it applies to company/research/people-style content
  notes.

---

## Verified / unverified tagging

Tag factual claims **[verified]** (backed by 2 independent sources) or **[unverified]**
(single source or inference). Example usage:

> The company raised a $12M Series A in March 2026 **[verified]** (per TechCrunch and the
> company's own funding announcement). Their reported ARR is ~$4M **[unverified]** (founder claim
> only, no independent confirmation).

Apply this inside company/research notes wherever a claim could matter for a decision — not
required in daily logs or system files.

---

## Checkbox / task-tracking syntax

Real precedent from this project (`backport-ideas.md`, `archive/BOOTSTRAP-completed-2026-07-03.md`):

- `- [ ] **Item name** — description` for an open item.
- `- [x] **Item name** — description (YYYY-MM-DD)` for a completed item — append the completion
  date inline rather than deleting context, so the history of when things were resolved stays
  readable.
- Grouping checkboxes under a `##`/`###` heading by theme or batch (BOOTSTRAP.md groups by
  onboarding topic: "A. Communication style", "B. Drafting criteria"; `backport-ideas.md` groups
  by "Candidates" vs. "Strong candidates" vs. "Opened Issues").
- When an item resolves into something trackable elsewhere (e.g. a GitHub issue), keep the
  checkbox but append the link rather than removing the line — see `backport-ideas.md`'s
  "Opened Issues" section.

---

## Archive, never delete

- Obsolete files move to `archive/`; obsolete/unactioned drafts move to `drafts/expired/`.
- Never delete — this is a hard rule (see `CLAUDE.md` → Approval Required).
- When archiving, keep the original filename and append context (what happened, when) either in
  the filename itself (`BOOTSTRAP-completed-2026-07-03.md`) or in a closing note inside the file
  (see the "ONBOARDING COMPLETE 2026-07-03" line at the end of that file).
- Archiving a file doesn't mean scrubbing it — leave the content intact; the point is signaling
  it's no longer active, not hiding it.

---

## When to trigger this skill

- Before creating any new file under `SecondBrain/Memory/`.
- When uncertain which folder a piece of content belongs in.
- When writing frontmatter for a company/research/people note and unsure which fields to include.
- When tagging a factual claim and unsure whether it qualifies as verified.
- When archiving or expiring a file and unsure of the naming/placement convention.
