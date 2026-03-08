---
description: Quick context refresh - what do I need to know?
allowed-tools: ["Read", "Bash", "Glob"]
---

# Project Recall

Quick context refresh when starting a session or resuming after a break.

## When to Use

- Starting a new Claude session
- Resuming after a significant time gap
- Before diving into a task
- When you need to remember what's been done

## Instructions

### Step 1: Load Project Memory

Read `.claude/PROJECT_MEMORY.md` and extract:
- Project name and initialized date
- Last post-mortem date
- Post-mortem count
- Recent activities (last 5 from Activity Log)

### Step 2: Load Project Lessons

Read `.claude/LESSONS-PROJECT.md` and extract:
- Count of lessons
- Most recent 3 lesson titles

### Step 3: Check Git Status

```bash
git status --short
git log --oneline -5
```

### Step 3.5: Toolkit Reminder

Display a brief reminder of the reusable component toolkit:

```
╠════════════════════════════════════════════════════════════╣
║ Toolkit: 108 reusable components available                 ║
║   Run: Read .claude/COMPONENT_REGISTRY.md before building  ║
║   Domains: auth, payments, email, SMS, deploy, RAG, etc.   ║
╚════════════════════════════════════════════════════════════╝
```

### Step 4: Display Context Summary

```
╔════════════════════════════════════════════════════════════╗
║                    PROJECT RECALL                          ║
╠════════════════════════════════════════════════════════════╣
║ Project:          [Name]                                   ║
║ Initialized:      YYYY-MM-DD                               ║
║ Last Post-Mortem: YYYY-MM-DD (N total) or "Never"          ║
╠════════════════════════════════════════════════════════════╣
║ Recorded Items:                                            ║
║   Scripts:        N items                                  ║
║   Env Vars:       N items (names only)                     ║
║   Infrastructure: N items                                  ║
╠════════════════════════════════════════════════════════════╣
║ Recent Activities:                                         ║
║   • [Activity 1]                                           ║
║   • [Activity 2]                                           ║
║   • [Activity 3]                                           ║
╠════════════════════════════════════════════════════════════╣
║ Project Lessons: N total                                   ║
║   Recent:                                                  ║
║   • [Lesson 1 title]                                       ║
║   • [Lesson 2 title]                                       ║
║   • [Lesson 3 title]                                       ║
╠════════════════════════════════════════════════════════════╣
║ Git Status:                                                ║
║   Branch: [current branch]                                 ║
║   Changes: [N modified, N untracked] or "Clean"            ║
║   Recent commits:                                          ║
║   • [commit 1]                                             ║
║   • [commit 2]                                             ║
║   • [commit 3]                                             ║
╠════════════════════════════════════════════════════════════╣
║ Toolkit: 108 reusable components available                 ║
║   Read .claude/COMPONENT_REGISTRY.md before building new   ║
║   Domains: auth, payments, email, SMS, deploy, RAG, etc.   ║
╚════════════════════════════════════════════════════════════╝
```

### Step 5: Offer Next Steps

Based on context, suggest:
- If uncommitted changes: "You have uncommitted work"
- If no recent post-mortem: "Consider running /project:post-mortem"
- If planning needed: "Use /project:plan to start"

## Output

Keep it concise - this is a quick refresh, not a deep dive.

## Graceful Fallback

If PROJECT_MEMORY.md doesn't exist:
- Note: "No project memory found"
- Offer: "Run /project:memory to create one"
- Still show git status and lessons if available
