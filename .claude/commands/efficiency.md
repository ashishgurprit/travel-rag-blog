---
description: Show the efficiency improvement dashboard and optionally record a new session data point
---

# /efficiency — Efficiency Dashboard

Show the efficiency improvement dashboard and optionally record a new data point.

## Usage

```
/efficiency           # Show dashboard
/efficiency record    # Record a data point after this session
/efficiency project   # Show dashboard filtered to current project
```

## What it shows

- **Efficiency trend** — session-by-session score over time
- **Gain attribution** — which source drove improvement (skills, lessons, version, modules, experience, tooling, planning)
- **Repeated mistakes** — mistakes that occurred despite being in LESSONS.md (tracks lesson effectiveness)
- **Lesson application rate** — how often past lessons were actually applied
- **Per-version score** — efficiency delta across Claude version upgrades
- **Per-project breakdown** — which projects improve fastest

## Instructions

Run the efficiency dashboard for the current context:

```bash
bash ~/documents/coding/streamlined-development/scripts/efficiency-dashboard.sh $ARGS
```

Where `$ARGS` is:
- empty → global dashboard
- `--record` → interactive prompt to record today's session data
- `--project "$(pwd)"` → filter to current project
- `--export csv` → export data as CSV

After showing the dashboard, summarize:
1. The top 3 efficiency drivers
2. Any repeated mistakes that need attention
3. One recommendation to improve next week

If the user says "record", run with `--record` flag for interactive data entry.
