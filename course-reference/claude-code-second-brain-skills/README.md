# Claude Code Second Brain Skills

A collection of custom skills that transform Claude Code from a coding tool into a full content production system. These skills demonstrate progressive disclosure of context - there's no magic, just structured knowledge that makes Claude hyper-capable for specific tasks.

## What This Is

Most people think of Claude Code as a tool for writing and debugging code. These skills extend it into:

- **Content creation** - LinkedIn posts, X threads, presentation slides
- **Visual communication** - Excalidraw diagrams that argue visually
- **Documentation** - Runbooks, SOPs, and technical docs
- **Skill development** - Creating new skills to extend capabilities further

The system works through progressive disclosure: Claude only loads detailed instructions when needed, keeping context efficient while maintaining deep expertise for each domain.

---

## Brand & Voice Generator

Generate tone-of-voice and brand-system files that power the PPTX Generator and can guide customization of all the other skills. This skill walks you through creating your brand identity, defining your writing voice, and establishing your visual system.

**Core Philosophy**: Your brand and voice should be documented once and reused everywhere. The files this skill creates become the source of truth for all content generation.

<details>
<summary><big>📦 What It Creates</big></summary>

| File | Purpose | Used By |
|------|---------|---------|
| `brand.json` | Colors, fonts, assets | PPTX Generator, Excalidraw |
| `config.json` | Output settings | PPTX Generator |
| `brand-system.md` | Design philosophy & guidelines | All content skills |
| `tone-of-voice.md` | Writing voice & personality | LinkedIn, X, PPTX content |

</details>

<details>
<summary><big>🔄 Process Overview</big></summary>

1. **Gather Brand Basics** - Name, description, primary use case
2. **Define Colors** - 10 color values for the complete system
3. **Define Typography** - Heading, body, and code fonts
4. **Define Assets** - Logo and icon paths
5. **Discover Voice** - Personality, vocabulary, sentence patterns
6. **Create Design Philosophy** - Core principles and signature elements
7. **Generate Files** - Create all four files with gathered information

</details>

<details>
<summary><big>🎭 Voice Templates Included</big></summary>

The skill includes 5 example voice configurations to help you discover your own:

- **Technical Educator** - Enthusiastic expert who teaches by showing
- **Calm Authority** - Confident and measured, lets expertise speak through specifics
- **Builder's Perspective** - Developer-to-developer, unfiltered opinions backed by code
- **Approachable Expert** - Makes the complex accessible without dumbing it down
- **Contrarian Thinker** - Challenges conventional wisdom with evidence

</details>

**Triggers**: "help me create a brand system", "generate my tone of voice", "set up my brand for presentations", "create brand files"

---

## Skills Overview

### Excalidraw Diagram

Create `.excalidraw` JSON files that make visual arguments, not just display information.

**Core Philosophy**: Diagrams should ARGUE, not DISPLAY. The shape should BE the meaning. If you removed all text, the structure alone should communicate the concept.

<details>
<summary><big>✨ Key Features</big></summary>

- Visual pattern library (fan-out, convergence, tree, spiral/cycle, cloud, assembly line)
- Shape meanings mapped to concepts (ellipse for start/end, diamond for decision, rectangle for process)
- Color-coded semantic meanings (blue for primary, orange for start, green for success, red for warning)
- Detailed JSON structure templates for Excalidraw format

</details>

**Triggers**: Requests to visualize workflows, architectures, or concepts

---

### LinkedIn Post

Create authentic LinkedIn posts for AI/tech educational content.

**Core Philosophy**: Posts should sound like you, not like a template. Specificity, genuine voice, and earned insight beat formulas and prescribed phrases.

<details>
<summary><big>📝 Content Modes</big></summary>

- **Story** - Share what happened with real details
- **Observation** - Notice something others might miss
- **Take** - Explain why you believe something
- **Teach** - Share how to do something specific
- **React** - Respond to something happening in the world
- **Ask** - Genuinely learn from your audience

</details>

<details>
<summary><big>🚫 Anti-Patterns Avoided</big></summary>

- Template phrases ("Here's the thing...", "Game-changing")
- Engagement bait ("Agree or disagree?", "What would you add?")
- Performative vulnerability (struggle that exists to contrast with success)
- Abstract advice without real experience

</details>

**Triggers**: Requests to create LinkedIn posts, repurpose content into LinkedIn format, share AI/tech insights

---

### X Post

Create concise, engaging X (Twitter) posts for tech/AI content.

<details>
<summary><big>📋 Format Types</big></summary>

- Single tweets (under 280 characters)
- Threads (7-10 tweets for tutorials, lists, stories)
- Quote tweets

</details>

<details>
<summary><big>✨ Key Features</big></summary>

- Hook formulas (credibility, contrarian, curiosity, transformation, list promise)
- Source attribution requirements
- Thread structure templates
- Algorithm-aware posting guidelines

</details>

<details>
<summary><big>📏 Writing Rules</big></summary>

- No hashtags (they hurt reach on X)
- No links in main post (move to reply)
- Specific numbers over vague claims
- Line breaks between ideas
- Under 280 chars for single tweets, under 250 per thread tweet

</details>

**Triggers**: Requests to create tweets, threads, or X content

---

### PPTX Generator

Generate professional, on-brand presentation slides and LinkedIn carousels using python-pptx.

> **Credit**: This skill was originally created by Rasmus and is [maintained here](https://github.com/Wirasm/presentation-slides-skill). The version here has been adapted with brand-specific configurations.

<details>
<summary><big>🎛️ Three Operating Modes</big></summary>

1. **Slide Generation** - Create 16:9 presentations with brand styling
2. **Carousel Generation** - Create square 1:1 LinkedIn carousels (exports to PDF)
3. **Layout Management** - Create, edit, and improve cookbook layouts

</details>

<details>
<summary><big>✨ Key Features</big></summary>

- 16 slide layout templates in the cookbook (title, content, stats, two-column, multi-card, floating-cards, circular-hero, quote, chart, code, and more)
- 5 carousel-specific layouts (hook, single-point, numbered-point, quote, CTA)
- Brand system with colors, fonts, and assets
- Batch generation (max 5 slides at a time) for reliability
- Variety enforcement rules to prevent repetitive layouts

</details>

<details>
<summary><big>💡 Critical Concept</big></summary>

**Visual-first layout selection** - content-slide is the LAST RESORT, not the default.

The skill includes a decision tree to transform bullets into visual layouts:
- 3-5 equal items → multi-card-slide
- 2-4 big numbers → stats-slide
- Comparing two things → two-column-slide
- Central concept with surrounding items → circular-hero-slide
- Powerful quote → quote-slide

Only use content-slide when none of the visual layouts fit.

</details>

**Triggers**: Requests for slides, presentations, carousels, PPTX, or layouts with a brand name

---

### SOP Creator

Create runbooks, playbooks, and technical documentation that people actually follow.

**Core Philosophy**: Nobody reads 50-page docs. Make it scannable, actionable, and impossible to misunderstand.

<details>
<summary><big>📂 Document Types</big></summary>

- **Tech/Engineering**: Runbook, Deployment Playbook, Troubleshooting Guide, How-To, ADR
- **Operations/Business**: Process SOP, Checklist, Decision Tree, Handoff Doc
- **Content/Creative**: Production Workflow, Review Process, Publishing Checklist
- **General**: Standard SOP, Quick Reference, Onboarding Guide

</details>

<details>
<summary><big>🏗️ Universal Structure</big></summary>

1. Definition of Done (checklist - most important, put near the top)
2. When to Use This
3. Prerequisites
4. The Process (numbered steps)
5. Verify Completion
6. When Things Go Wrong
7. Questions?

</details>

<details>
<summary><big>📏 Writing Rules</big></summary>

- Be specific (numbers, names, thresholds - not "as needed" or "regularly")
- Action-first steps (verbs, not descriptions)
- Warnings come first (before the dangerous step, not after)
- Clear decision points (if X, then Y - not "handle based on priority")

</details>

**Triggers**: Requests to document a process, create a runbook, build operational docs, formalize technical procedures

---

### Skill Creator

Guide for creating effective skills that extend Claude's capabilities.

**Core Philosophy**: Skills are modular, self-contained packages that transform Claude from a general-purpose agent into a specialized agent. Only add context Claude doesn't already have.

<details>
<summary><big>🎁 What Skills Provide</big></summary>

1. Specialized workflows - Multi-step procedures for specific domains
2. Tool integrations - Instructions for working with specific file formats or APIs
3. Domain expertise - Company-specific knowledge, schemas, business logic
4. Bundled resources - Scripts, references, and assets for complex tasks

</details>

<details>
<summary><big>🧭 Core Principles</big></summary>

- **Concise is Key** - Only add context Claude doesn't already have
- **Set Appropriate Degrees of Freedom** - Match specificity to task fragility
- **Progressive Disclosure** - Metadata always in context, body when triggered, resources as needed

</details>

<details>
<summary><big>🗂️ Skill Anatomy</big></summary>

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter (name, description)
│   └── Markdown instructions
└── Bundled Resources (optional)
    ├── scripts/     - Executable code
    ├── references/  - Documentation loaded as needed
    └── assets/      - Files used in output
```

</details>

<details>
<summary><big>🔄 Creation Process</big></summary>

1. Understand with concrete examples
2. Plan reusable contents
3. Initialize (run init_skill.py)
4. Edit and implement
5. Package (run package_skill.py)
6. Iterate based on real usage

</details>

**Triggers**: Requests to create or update skills that extend Claude's capabilities

---

## Customization Guide

These skills work out of the box, but some contain brand-specific configurations you'll want to customize for your own use.

### What Needs Customization

| Skill | Customization Required | Effort |
|-------|------------------------|--------|
| **LinkedIn Post** | Optional tone adjustments | Low |
| **X Post** | Optional tone adjustments | Low |
| **SOP Creator** | Works as-is | None |
| **Skill Creator** | Works as-is | None |
| **Excalidraw Diagram** | Color palette customization | Medium |
| **PPTX Generator** | Brand system setup required | High |

<details>
<summary><big>🟢 Low Effort: LinkedIn Post & X Post</big></summary>

These skills focus on writing principles that apply universally. The guidance around authentic voice, specificity, and anti-patterns works for anyone.

**Optional customizations**:
- `linkedin-post/references/style-guide.md` - Add your specific voice patterns
- `x-post/references/templates.md` - Adjust hook formulas to your style

You can use these skills immediately without any changes.

</details>

<details>
<summary><big>🟡 Medium Effort: Excalidraw Diagram</big></summary>

The color palette in `excalidraw-diagram/references/color-palette.md` uses a default blue scheme with semantic colors.

**To customize**:
1. Edit `references/color-palette.md` with your brand colors
2. Update the color table in `skill.md` (Color as Meaning section)
3. Keep the semantic mappings (start=orange tones, success=green tones, etc.) or create your own system

The current palette:
- Primary: Blues (#3b82f6, #60a5fa)
- Start/Trigger: Orange (#fed7aa)
- End/Success: Green (#a7f3d0)
- Warning: Red (#fee2e2)
- Decision: Yellow (#fef3c7)
- AI/LLM: Purple (#ddd6fe)

</details>

<details>
<summary><big>🔴 High Effort: PPTX Generator</big></summary>

This skill requires a complete brand setup before generating slides. Use the **Brand & Voice Generator** skill to create these files interactively, or manually copy from the template folder.

**Required files** (in `brands/your-brand-name/`):

1. **`brand.json`** - Colors (10 values), fonts (3), and asset paths
2. **`config.json`** - Output directory, batch size, file naming
3. **`brand-system.md`** - Design philosophy, color rationale, typography rules, signature elements
4. **`tone-of-voice.md`** - Voice character, vocabulary patterns, do's and don'ts, example phrases

**Setup steps**:
1. Run the Brand & Voice Generator skill, OR
2. Copy `brands/template/` to `brands/your-brand-name/`
3. Replace all `REPLACE` placeholders in each file
4. Add your logo to `brands/your-brand-name/assets/`
5. Test by generating a simple presentation

See `brands/dynamous/` for a complete example of a configured brand.

</details>

---

## Quick Start

1. **For LinkedIn/X posts**: Just use the skills immediately - they work out of the box
2. **For SOPs and documentation**: Use the SOP Creator directly
3. **For diagrams**: Review the color palette, customize if desired, then create diagrams
4. **For presentations**:
   - Run the brand-voice-generator skill to set up your brand
   - Or manually copy and configure the template folder
   - Then generate slides with the pptx-generator skill
5. **For new skills**: Use the Skill Creator to build your own extensions

---

## Skills Not Included

This workshop focuses on the skills in this folder. Other skills mentioned in the workshop (Content Engine, Video Processor) are not included here as they involve additional infrastructure and integrations.

---

*These skills demonstrate that extending Claude Code is straightforward - it's just well-organized context that makes the agent an expert in your specific workflows.*
