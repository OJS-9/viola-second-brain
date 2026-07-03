---
name: x-post
description: Create X (Twitter) posts for AI/tech content. Use when the user wants to create a tweet, thread, or X content. Triggers on requests like "create a tweet about...", "write a thread on...", or any X/Twitter content request.
---

# X Post Creator

Create concise, engaging X posts for tech/AI content.

## Source Attribution (Required)

Every post file must start with source metadata:

**For digest items:**
```
**Source**: Digest #{number} - {title}
**Original**: {URL from topic file}
**Deep Dive**: {path to topic .md file}
```

**For daily notes:**
```
**Source**: Daily Notes - {IMPORTANT if marked}
**Original**: N/A
**Deep Dive**: {path to daily note file}
```

**For web research:**
```
**Source**: {Article/study title that informed the content}
**Original**: {specific URL(s) used}
**Deep Dive**: N/A
```

Get digest info from `DAILY_DIGEST.md` and topic files in `content-engine/output/topics/YYYY-MM-DD/`

## Definition of Done

Post is ready when:
- [ ] Hook stops the scroll (first line is compelling)
- [ ] One clear idea per post
- [ ] Specific numbers/examples (no vague claims)
- [ ] CTA included (if thread)
- [ ] Under character limit (280 for tweet, <250 per thread tweet)
- [ ] No links in main post (move to reply)

## Format Selection

| Content | Format |
|---------|--------|
| Quick insight, hot take | Single tweet (under 280 chars) |
| Tutorial, list, story | Thread (7-10 tweets) |
| Adding to discussion | Quote tweet |

## Single Tweet Templates

**Hot Take:**
```
[Unpopular opinion/Hot take]: [Bold statement]

[1-2 sentence reasoning]
```

**Listicle:**
```
[Number] [topic] that [benefit]:

1. [Item]
2. [Item]
3. [Item]

Which one are you trying first?
```

**Transformation:**
```
[Time] ago: [Struggle]
Today: [Success]

The turning point? [Key insight]
```

## Thread Structure

**Tweet 1 (Hook):**
```
I [did X] in [timeframe].

Here's exactly how:

🧵
```

**Middle Tweets (one point each):**
```
[Number]/ [Point]

[Explanation in 1-2 sentences]

[Example or evidence]
```

**Final Tweet:**
```
TL;DR:

1. [Key point]
2. [Key point]
3. [Key point]

Follow @[handle] for more [topic].
```

## Hook Formulas

| Type | Template |
|------|----------|
| Credibility | "I've [done X]. Here's what I learned:" |
| Contrarian | "[Popular belief] is wrong. Here's the truth:" |
| Curiosity | "The [topic] trick nobody talks about:" |
| Transformation | "From [bad] to [good] in [time]. Here's how:" |
| List promise | "[Number] [things] that will [outcome]:" |

## Writing Rules

- **Under 280 chars** for single tweets (shorter can work, but don't force it)
- **Under 250 chars** per tweet in threads
- **No hashtags** - they hurt reach on X
- **No links** in main post - put in reply
- **Line breaks** between ideas
- **Specific numbers** beat vague claims
- **Verify tools/products are current** - AI/tech moves fast; search "[tool] 2026 status" before citing specific frameworks or products

## Algorithm Tips

- Post 9 AM - 2 PM weekdays
- First hour engagement is critical
- Retweets worth 2x likes
- Rich media (images/video) = 40% better performance
- Stay in your niche for consistency

## What NOT to Do

- Links in main tweet (kills reach)
- Hashtags (hurt reach on X)
- Vague language ("as needed", "regularly")
- Corporate speak
- Describing commands instead of showing them
