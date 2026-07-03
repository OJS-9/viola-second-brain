# My Second Brain - Requirements Template

> Fill this out during the workshop (Section 1.4). Your answers feed directly into the `/create-second-brain-prd <path to this file>` command, which generates your personalized build plan.

---

## 1. About You

- **Name:** Or
- **Role/Title:** Investment Analyst at Viola Ventures (https://www.viola-group.com/fund/violaventures/)
- **What I do daily** (1-2 sentences): Startup due diligence (founders, market, problem, solution, VC game plan); hands-on GTM work for portfolio companies and founders (often as code projects, e.g. the ib-agent and bh-the-list GitHub repos); researching categories and new markets; organizing webinars/events and preparing their content.
- **Timezone:** Asia/Jerusalem (GMT+3)
- **Memory vault folder name:** SecondBrain (e.g., "SecondBrain", "MyVault", "Memory" — this is the root folder for all your memory files)
- **Using Obsidian?** [x] Yes [ ] No (Obsidian is optional — the vault is just a folder of markdown files. Obsidian provides a nice UI for browsing/editing them, but everything works without it.)

---

## 2. Your Platforms

Check every platform you actively use and fill in the specific tool:

- [x] Email (e.g., Gmail, Outlook): Outlook (work)
- [x] Calendar (e.g., Google Calendar, Outlook Calendar): Outlook Calendar (work) + awareness of personal Google Calendar
- [x] Task Management (e.g., Asana, Linear, Todoist, Jira): Notion (current home for tasks; open to suggestions)
- [x] Chat/Messaging (e.g., Slack, Discord, Teams): Teams (infrequent); day-to-day communication is mostly WhatsApp + email
- [x] Notes/Documents (e.g., Notion, Obsidian, Google Docs): Notion — all work lives in Notion
- [x] Cloud Storage (e.g., Google Drive, Dropbox, OneDrive): Dropbox + local PC files
- [x] Code Hosting (e.g., GitHub, GitLab): GitHub (personal account; sole author of his repos)
- [ ] Community (e.g., Circle, Discord server, Mighty Networks): —
- [x] CRM (e.g., HubSpot, Salesforce, Pipedrive): Affinity (already has a Claude skill that classifies founders straight from Affinity — reuse it)
- [x] Other: PitchBook (research), Zoom (meetings/webinars), Snowflake (internal org data), Nimbleway web scraping/search API (has API key — https://docs.nimbleway.com/home)

---

## 3. Top Tasks for AI

List 3-5 tasks you'd want your second brain to handle proactively:

**My list:**

1. **Due-diligence sidekick** — help fetch, understand, and verify information about a company, then render the findings as slides based on my existing slide framework.
2. **Slide ideation + design** — ideate and create slide decks for due diligence and for events, and design them well.
3. **Research flow builder** — I'm new in the role; help me structure and codify my own repeatable method ("flow") for DD-ing a company.
4. **Task sync + proactive check-ins** — keep tasks in sync (Notion) and proactively ask me about progress and new tasks.
5. **Email replies + routing** — help me draft replies, and route email action items into tasks.
6. **Weekly sector digest** — cybersecurity, AI infra, and defense-tech: new startups, ideas, and articles, so I'm the smartest in the room.


---

## 4. Proactivity Level

How bold should your agent be? Pick one:

- [ ] **Observer** - Notify only, never take action
- [x] **Advisor** - Draft things for my review, but never send or post
- [ ] **Assistant** - Act on low-risk items (log notes, organize files), ask for high-risk
- [ ] **Partner** - Act autonomously on most things, ask only for irreversible actions

> **Advisor + execute-on-approval loop:** the agent works (drafts/prepares) → I approve → the agent handles the operation itself (sending, posting, creating). It never executes an external action without my explicit approval of that specific item, but once approved, IT does the execution — not me manually.

---

## 5. Security Boundaries

What should your agent NEVER do without explicit permission?

- [x] Send emails or messages on my behalf — allowed ONLY per-item after my explicit approval (the approve-then-execute loop)
- [x] Post to social media — never without approval
- [x] Modify files outside the memory vault — only after I agree on the scope and the exact change
- [x] Access financial data or make purchases — NEVER make purchases or modify financial data; data access in general is READ-ONLY (writes only via the approval loop)
- [x] Delete anything — NEVER deletes, no exceptions
- [x] Other: runs on the organization's Claude subscription — treat all org data access as read-only by default

---

## 6. Memory Categories

What types of knowledge matter most to you? Check all that apply and add your own:

- [x] Meeting notes and decisions
- [x] Project status and progress
- [x] Client/customer information — founders, startups, deal flow context
- [x] Research and learning notes — DD research, sector research (cyber / AI infra / defense-tech)
- [ ] Personal goals and habits
- [x] Content ideas and drafts — slides, event content, email drafts
- [x] Team context (who does what, preferences, timezones)
- [x] Other: my DD methodology/flow documents — living SOPs that improve with each deal

---

## 7. Infrastructure

- **Operating System:** [x] Windows [x] macOS [ ] Linux (building on a private MacBook, will run on the Windows work PC — must be cross-platform)
- **Deployment:** [x] Local only [ ] Local + cloud server (VPS) — deliberate decision: work email/Dropbox data and credentials must not live on personal infrastructure
- **Existing tools I already have set up:** Claude Code (building on the Mac now; the agent will ultimately run on the Viola organization Claude subscription on the work PC). An existing Claude skill that classifies founders from Affinity. Prior experience running a personal agent (NanoClaw) locally and on a VPS. Comfortable with Python, SQL, Flask.

---

## 8. Integration Priority

Rank your top 3 integrations to build first (from your answers in Section 2):

1. **Notion** — docs + tasks hub; where digests, check-ins, and DD outputs land. Testable immediately.
2. **Web research via Nimbleway API** (search + scraping, API key in hand) — powers the weekly sector digest and the DD sidekick's fetching. No work accounts needed; fully buildable on the Mac now.
3. **Outlook email + calendar (Microsoft Graph)** — highest daily value, but gated on Viola IT consent; built last, wired up on the work PC. Personal Google Calendar added alongside.

(Affinity is already covered by an existing skill — reuse, not rebuild.)

---

> After filling this out, run: `/create-second-brain-prd <path to this file>`
