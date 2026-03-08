---
description: Show Claude Code usage analytics — session trends, skills used vs. missed, intent breakdown, and IDE/device context
---

# /analytics — Usage Analytics Dashboard

Show Claude Code usage analytics: session trends, skills used vs. missed, intent breakdown, and IDE/device context.

## Usage

```
/analytics            # Full dashboard
/analytics --skills   # Skills focus: used, missed opportunities, adoption
/analytics --trends   # Volume trends only (messages, sessions, projects)
/analytics --export csv  # Export telemetry to CSV
```

## What it shows

- **Activity trends** — weekly message volume, sessions, tool calls (from Claude Code native stats)
- **Top projects** — most active projects by prompt count
- **Skills dashboard** — which skills used how often + missed opportunity detection
- **Intent breakdown** — build / debug / review / plan / deploy / learn distribution
- **Environment** — IDE type (terminal, VSCode, Cursor) + device
- **Skill adoption over time** — unique skills per month trend

## Skill missed opportunities

When you write a prompt containing keywords that match an available skill (e.g., "blog" → blog-content-writer), but the skill isn't invoked, it's flagged as a missed opportunity. This helps identify skills you have but aren't using.

## Instructions

Run the analytics dashboard:

```bash
bash ~/documents/coding/streamlined-development/scripts/usage-analytics.sh $ARGS
```

Where `$ARGS` maps from the user's command suffix:
- no args → full dashboard
- `--skills` → skills focus only
- `--trends` → trends only
- `--export csv` → output CSV

After showing the dashboard, summarize:
1. The 3 most used skills and what they tell us about workflow
2. Top 3 missed skill opportunities with specific usage examples
3. Activity trend — are we getting more or less productive over time?
4. One recommendation based on the data

If the dashboard is empty (no telemetry yet), explain that telemetry is captured on every prompt going forward and show what data IS available from Claude Code's native stats.
