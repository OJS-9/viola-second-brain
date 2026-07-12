---
name: dealigence-classify
description: |
  Classify founders from the Dealigence monthly list by browsing their LinkedIn profiles
  and scoring them against Viola's investment thesis. Updates Affinity Status field.
  Use when Or says "classify dealigence", "process dealigence list", "rank new founders",
  "score founders from dealigence", "work through the dealigence list", "dealigence batch",
  "let's do the dealigence founders", or any request to review/rate/prioritize the monthly
  stealth founder list from Dealigence. Operates in training mode by default (5 founders at
  a time, Or confirms before Affinity is updated). Switch to autonomous mode only when
  Or explicitly says so.
---

# Dealigence Classify Workflow

Classifies stealth founders from the monthly Dealigence list by visiting their LinkedIn profiles
and scoring them against Viola's thesis. All Affinity updates require Or's explicit confirmation.

Scoring rubric: `.claude/skills/dealigence-classify/references/scoring-rubric.md`
State file: `.claude/data/state/dealigence/state/dealigence-config.json`

**Mechanics note (migration from the original Analyst_Agent project):** the original version of
this skill described a `query.py affinity <subcommand>` CLI and `agent-browser` LinkedIn automation.
Neither was ever built — this rewrite uses what's actually available in this session: the **Affinity
MCP connector** directly (tools like `get_saved_view_list_entries`, `get_person_info`,
`upsert_list_entry_field_values`) and the **`nimble` CLI's agent-run subcommand** (via the ported
`nimble_linkedin.py` script) for LinkedIn scraping. Don't reintroduce `query.py affinity` or
`agent-browser` — they don't exist in this project.

---

## Step 1: Load or Initialize State

Read the state file:
```bash
cat ".claude/data/state/dealigence/state/dealigence-config.json" 2>/dev/null || echo "{}"
```

State fields (real shape, as currently populated):
```json
{
  "list_id": 306606,
  "list_name": "Stealth Co-Founders (Dealigence)",
  "status_field_id": "field-5224221",
  "status_options": {
    "star": 22252497,
    "new": 20704071,
    "lead_high": 21182034,
    "lead_mid": 21195316,
    "lead_low": 21182033,
    "lead_for_portcomp": 20704073,
    "reached_out": 21238989,
    "not_relevant": 20704074,
    "miss": 21182035
  },
  "extra_fields": {
    "linkedin_url": "affinity-data-linkedin-url",
    "linkedin_url_viola": "field-4316045",
    "headline": "affinity-data-linkedin-profile-headline",
    "category": "field-5303459",
    "stealth_tag": "field-5224232",
    "geography": "field-5224226",
    "connections": "field-5224231",
    "started_stealth": "field-5224227",
    "dealigence_recommended": "field-5389046"
  },
  "fetch_method": "saved_view",
  "view_id": 2100923,
  "view_name": "Stealths New",
  "view_cursor": "<opaque cursor string>",
  "page_token": "DEPRECATED_use_view_cursor_instead",
  "last_batch_last_list_entry_id": 242394561,
  "mode": "autonomous-trial",
  "training_batches_completed": 23,
  "total_corrections": 39
}
```

**If `list_id` is null** -> go to Step 2 (first-run setup).
**If `list_id` is set** -> skip to Step 3.

`page_token` is a deprecated leftover from an earlier fetch method — ignore it. The live cursor is
`view_cursor`, used by `get_saved_view_list_entries`.

---

## Step 2: First-Run Setup (discover list ID, view ID, and field IDs)

### 2a. Find the Dealigence list and its saved view
```
get_lists()                     # look for "Stealth Co-Founders (Dealigence)"
get_list_info(list_id=<found>)  # confirm name + entity type ("person")
get_saved_views(list_id=<found>)  # look for "Stealths New" -> note view_id
```

### 2b. Discover the Status field and its option IDs
```
get_list_fields(list_id=<found>, filter='name="Status"')
get_list_field_dropdown_options(list_id=<found>, field_id="field-XXXXXXX")
```
The Status field is a ranked dropdown. Map its options to tier names (star / new / lead_high /
lead_mid / lead_low / lead_for_portcomp / reached_out / not_relevant / miss) exactly as shown in
the state shape above.

### 2c. Save config to state file
Write `.claude/data/state/dealigence/state/dealigence-config.json` with the discovered IDs, using
the shape shown in Step 1 (`fetch_method: "saved_view"`, `view_id`, `view_cursor: null` on first run,
`mode: "training"`, `training_batches_completed: 0`, `total_corrections: 0`).

---

## Step 3: Fetch Next 5 Founders

```
get_saved_view_list_entries(list_id=306606, view_id=2100923, cursor=<view_cursor from state, or omit on first run>, limit=5)
```

This paginates the "Stealths New" saved view, which is already scoped to unclassified people —
no separate "Status = New" filter is needed. Each entry's list-specific fields (per the view's
configured columns) include the Dealigence metadata:
- geography / category / stealth tag fields (see `extra_fields` in state)
- LinkedIn connections count
- date the stealth signal was detected

Save the returned pagination cursor (`pagination.nextCursor`) to `view_cursor` in state after this
batch is processed.

---

## Step 4: Score Each Founder

For each founder:

### 4a. Read the Dealigence metadata
From the `get_saved_view_list_entries` result for that entry. Note:
- geography and stealth-tag fields tell you where they are and whether they're Israeli diaspora
- the "started stealth" field tells you roughly when they went stealth
- the category field is Dealigence's domain guess (useful but not authoritative)

**Interpreting the Stealth Tag + latest job end date:**

| Tag | Latest job end date | Signal | Action |
|-----|--------------------|---------|-|
| `Stealth` | any | Strong — Dealigence detected a stealth signal | Score per rubric |
| `Silent` | **has end date** | Moderate — left employer, may be building quietly | Score per rubric normally |
| `Silent` | no end date (still employed) | Weak — LinkedIn just went quiet | Score per rubric, note lower building confidence |

The latest job's end date comes from the scraped LinkedIn experience block (`end_date` on the most
recent position). A person with "Silent" tag but a clear end date on their last role has left their
employer — treat this the same as a founding signal for scoring purposes, even if their LinkedIn
headline hasn't updated yet.

**Do not use the absence of a "Stealth" tag to lower a tier** — the tag is a Dealigence
classification, not a quality signal. Scoring is always driven by track record and Israeli
connection, regardless of tag.

### 4b. Fetch the LinkedIn profile via Nimble

Get the person's LinkedIn URL — it's an enriched/global field, pulled per-person:
```
get_person_info(person_id=<id>, field_ids=["affinity-data-linkedin-url", "field-4316045"])
```

Write the resolved URLs for the batch to a text file (one per line), then scrape:
```bash
uv run --project .claude/scripts python .claude/scripts/dealigence/nimble_linkedin.py \
  --input <path-to-batch-profiles.txt> \
  --out <path-to-batch-output.jsonl>
```

`nimble_linkedin.py` calls `nimble agent run --agent linkedin_person_8d8884b2 --params "identifier: <slug>"`
per profile (the Nimble CLI is pre-authenticated on this machine — no token setup needed). Use
`--dry-run` first if you want to confirm slug resolution without spending a scrape.

**Fallback (legacy, costs money):** `apify_linkedin.py` in the same folder calls the Apify
`harvestapi/linkedin-profile-scraper` actor ($4/1k profiles). Needs `APIFY_TOKEN` in
`.claude/scripts/.env`. Only use this if the Nimble agent path fails.

**If no LinkedIn URL in Affinity:** Fall back to WebSearch (`site:linkedin.com "<Full Name>" <geo>`)
— but flag the result as medium-confidence.

Read the **Experience** section primarily. Also check **Education** as a tiebreaker:
- Top global university (Stanford, Harvard, MIT, Oxbridge, ETH, Weizmann Institute) -> bonus Star signal
- Technion / Hebrew University -> standard Israeli signal (expected, not bonus)

**If you can't identify the right LinkedIn profile from the name:** flag it and leave blank.
Do not guess — do not score based on the wrong person.

### 4c. Apply the scoring rubric
Reference: `.claude/skills/dealigence-classify/references/scoring-rubric.md`

Extract for each person:
- Israeli connection (IDF unit, location, company history in Israel)
- Most senior role + company name + tenure
- Domain fit (cyber / infra / adjacent / outside)
- Any prior founding experience
- Education (if top global university)

Assign: **Star / Lead-High / Lead-Mid / Lead-Low**
Set confidence: **High** (clear signals) / **Medium** (some ambiguity) / **Flag** (ask Or)

---

## Step 5: Present Review Table (Training Mode)

Show the table inline:

```
## Dealigence Batch — [Date] (Batch #N, Training Mode)

| # | Name | LinkedIn Highlights | Suggested Tier | Confidence | Reasoning |
|---|------|---------------------|----------------|------------|-----------|
| 1 | [Name](https://www.linkedin.com/in/slug) | [2-3 line summary: IDF unit, key company + role + tenure, domain] | Star | High | [1 sentence] |
| 2 | [Name](https://www.linkedin.com/in/slug) | [summary] | Lead-High | Medium | [1 sentence] |
...
```

**Below the table — flag any uncertain cases:**
```
### Flags (need your call)
- **[Name]**: [Why I'm uncertain — e.g. "8200 background but spent last 6 years in fintech, not cyber. Star pedigree, weak domain fit."]
```

**Do NOT update Affinity yet.** Wait for Or to confirm or correct.

---

## Step 6: Wait for Or's Confirmation

Or will either:
- **Approve the table**: "looks good", "confirmed", "go ahead"
- **Correct specific entries**: "make #2 a Star", "that one's a Low", etc.
- **Resolve flags**: "that's a High", "Low on that one"

Apply all corrections before proceeding.

---

## Step 7: Update Affinity

For each confirmed/corrected founder, update their Status field on the list entry:

```
upsert_list_entry_field_values(
    list_id=306606,
    list_entry_id=<list_entry_id>,
    upserts=[
        {"id": "field-5224221", "value": {"type": "ranked-dropdown", "data": {"dropdownOptionId": <option_id_for_tier>}}}
    ]
)
```

Run one call per person. Report success/failure inline.

---

## Step 8: Update State and Report Calibration

Update `.claude/data/state/dealigence/state/dealigence-config.json`:
- Set `view_cursor` to the `pagination.nextCursor` from Step 3
- Increment `training_batches_completed`
- Add correction count for this batch to `total_corrections`

**Calibration check** (training mode only):
After each batch, if the last 3 batches averaged < 2 corrections each:
> "Calibration is looking solid — 3 batches, N total corrections. Want to switch to autonomous mode for the next run?"

Do NOT switch automatically. Or must explicitly confirm.

---

## Autonomous Mode

Activated when Or says: "go autonomous", "switch to autonomous mode", "run it autonomously", "make it rain", "batch of N".
Update `mode` in state file to `"autonomous"` (or leave as `"autonomous-trial"` if that's the
current value — see the live state file for what's actually set).

In autonomous mode:
1. Process the requested founders in internal batches of 5.
2. Apply the scoring rubric without pausing for each batch.
3. Collect all results into a single summary table.
4. **Present the full table to Or — do NOT write anything to Affinity yet.**
5. Wait for Or's explicit confirmation (or corrections) before writing any tier to Affinity.

**Autonomous mode output format:**
```
## Dealigence Autonomous Run — [Date]

Processed: N founders

### Full results (NOT yet written to Affinity — confirm to write)
| # | Name | Tier | Conf | Rationale |
| 1 | [Name](https://www.linkedin.com/in/slug) | Lead-High | High | ... |
...

### Flags (need your call before writing)
| Name | LinkedIn Highlights | My lean | Why I flagged |
...
```

**After Or confirms or corrects:** apply all edits, then write every founder to Affinity in one pass.

---

## Calibration Replay Mode

A backtest loop that hardens the rubric against past **human-labeled** decisions, instead of grading
new founders blind. Activated when Or says: "calibration", "replay", "calibrate the rubric",
"study past gradings". Goal: make the rubric trustworthy enough to run autonomously.

State and output live under `.claude/data/state/dealigence/`:
- `state/calibration-queue.json` — ordered queue (`ordered`, `cursor`, `processed`, `tier_counts`)
- `state/calibration-index.json` — partial label index built from cached pages
- `state/calib-batch-N.json` / `state/calib-batch-N-profiles.txt` — per-batch roster + URL list
- `output/calibration/batch-N.jsonl` / `output/calibration/batch-N.md` — scraped profiles + batch study
- `output/calibration/divergence-ledger.md` — running log of disagreements across all batches

### Step 0 — Build the study queue (one-time, already done for the existing queue)
Page list `306606` via `get_saved_view_list_entries` (or `search_list_entries` if not scoped to a
view), requesting only the Status field so payloads stay small. Exclude `New`. Bucket by tier and
order **Star -> Not Relevant -> Lead-High -> Lead-Mid -> Lead-Low -> Reached Out -> Lead for
Portcomp -> Miss** (highest-cost errors first). Persist to
`.claude/data/state/dealigence/state/calibration-queue.json`.

### Step 1 — Per batch (5)
1. Take the next 5 from the queue (`cursor`).
2. Fetch each person's LinkedIn URL via `get_person_info(person_id, field_ids=["affinity-data-linkedin-url", "field-4316045"])`.
   Write roster `.claude/data/state/dealigence/state/calib-batch-N.json` + URL list
   `.claude/data/state/dealigence/state/calib-batch-N-profiles.txt`.
3. Scrape:
   ```bash
   uv run --project .claude/scripts python .claude/scripts/dealigence/nimble_linkedin.py \
     --input .claude/data/state/dealigence/state/calib-batch-N-profiles.txt \
     --out .claude/data/state/dealigence/output/calibration/batch-N.jsonl
   ```
4. Apply the rubric **blind** -> predicted tier + confidence + reasoning. **Never write to Affinity in replay.**
5. Compare predicted vs stored: `agree` / `adjacent-miss` (+/-1 tier) / `cross-gate-miss` (NR<->pursue or Star<->non-Star).

### Step 2 — Focused session with Or
Present the divergence table (`# | Name | signals | predicted | stored | verdict | likely root cause`).
For each disagreement decide together: **(a)** rubric gap -> edit rubric · **(b)** off-LinkedIn info ->
unlearnable, no change · **(c)** identity/wrong-person -> data note · **(g)** grader error -> no change.

### Step 3 — Fold learnings back
Append confirmed (a)-patterns to `scoring-rubric.md` as a new **"From replay batch N"** calibration note.
Log the batch to `.claude/data/state/dealigence/output/calibration/batch-N.md` and append rows to
`.claude/data/state/dealigence/output/calibration/divergence-ledger.md`. Advance
`calibration-queue.json` cursor + `processed`.

### Step 4 — Autonomy-readiness signal (qualitative, never automatic)
Track divergence rate in the ledger. Candidate for autonomous = several consecutive batches with **no new
cross-gate misses and no new systematic (a)-patterns**. Surface it to Or; do not flip `mode` automatically.

---

## Fallback Behavior

- **No LinkedIn URL in Affinity**: Fall back to WebSearch. Assign Lead-Low by default, flag as medium-confidence.
- **Very sparse LinkedIn profile** (< 3 roles, no dates): Flag — can't assess reliably.
- **Nimble agent run fails** (non-zero exit, JSON parse error, or `status != "success"`): `nimble_linkedin.py`
  logs a warning to stderr and skips that profile — check stderr output and retry that one slug, or fall
  back to WebSearch.
- **Affinity API error on upsert**: Report the error, do NOT retry silently. Show the failed call for Or to re-run manually.
- **list_id, view_id, or field IDs missing from state**: Re-run Step 2 setup.

---

## Notes

- Never update Affinity in training mode without Or's explicit confirmation.
- Never use "Israeli connection unclear" as a reason to downgrade — flag it instead.
- The scoring rubric in `references/scoring-rubric.md` is the source of truth.
  If Or's correction contradicts it, update the rubric to reflect the new calibration.
- `view_cursor` persists between sessions — always resume from where you left off.
- Do not re-process founders whose Status is already set (not "New") — the saved view already
  filters these out.
- This skill's data (`.claude/data/state/dealigence/`) contains real dealflow PII (founder names,
  LinkedIn URLs, investment-tier scores). Never print full batches of it into chat unnecessarily —
  work with counts/structure where possible, cite specific names only when presenting the review
  table for Or's confirmation.
