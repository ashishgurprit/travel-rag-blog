---
description: Capture lessons learned after debugging
allowed-tools: ["Read", "Write", "Edit", "Bash", "Glob"]
---

# Post-Mortem: Capture Lessons

Analyze the debugging session, capture lessons for future reference, and create Post-Incident Review (PIR) documentation.

## When to Use

- After fixing a production issue
- After debugging a tricky problem
- When you discover a non-obvious gotcha
- After any "aha" moment

## Instructions

### Phase 0: Load Project Memory

**IMPORTANT**: Always start by loading project memory to scope the analysis.

1. **Read project memory**:
   ```bash
   cat .claude/PROJECT_MEMORY.md
   ```

2. **Extract last post-mortem timestamp** from YAML frontmatter:
   - Look for `last_post_mortem:` field
   - If `null` or missing, use project `initialized:` date
   - If no memory file exists, create one (see Phase 10)

3. **Scope git history since last post-mortem**:
   ```bash
   # If timestamp exists (e.g., 2026-01-01T12:00:00Z)
   git log --since="TIMESTAMP" --oneline --stat

   # If no timestamp, show recent history
   git log --oneline --stat -30
   ```

4. **Display scoped changes**:
   ```
   ╔════════════════════════════════════════════════════════════╗
   ║              CHANGES SINCE LAST POST-MORTEM                ║
   ╠════════════════════════════════════════════════════════════╣
   ║ Last Post-Mortem: YYYY-MM-DD (or "Never")                  ║
   ║ Commits Since:    N commits                                ║
   ║ Files Changed:    N files                                  ║
   ╚════════════════════════════════════════════════════════════╝
   ```

5. **Auto-detect new activities** (for recording later):
   ```bash
   # New scripts created
   git diff --name-only --diff-filter=A HEAD~20 | grep -E '\.(sh|py|js)$' || true

   # New env var references (names only, NOT values)
   git diff HEAD~20 -- '*.env.example' '.env.sample' 'README.md' 2>/dev/null | grep '^+' | grep -oE '[A-Z][A-Z0-9_]{2,}=' | sed 's/=$//' | sort -u || true

   # Infrastructure changes
   git diff --name-only HEAD~20 -- 'docker-compose*.yml' 'Dockerfile*' '*.tf' 'railway.json' 'fly.toml' 'vercel.json' 2>/dev/null || true
   ```

### Phase 1: Identify the Issue

Review the recent conversation/work:

1. **What was the symptom?** (Error message, unexpected behavior)
2. **What was the expected behavior?**
3. **How long did it take to debug?**
4. **What was the impact?** (Users affected, duration, severity)

### Phase 2: Find Root Cause

1. **Why did it happen?** (The real cause, not symptoms)
2. **Why wasn't it caught earlier?** (Missing test? Bad assumption?)
3. **Contributing factors?** (Time pressure, unclear requirements, etc.)

### Phase 3: Document Solution

1. **How was it fixed?**
2. **Is there a code pattern to follow?**
3. **Is there a code pattern to avoid?**

### Phase 4: Create Prevention Measures

1. **What test would catch this?**
2. **What validation would prevent this?**
3. **What checklist item would help?**
4. **What documentation was missing?**

### Phase 5: Categorize

Choose the most relevant category:
- Authentication & Identity
- Database & Data Types
- API Contracts
- Environment & Configuration
- Deployment & Infrastructure
- Payment Integration
- Testing Strategies
- Performance
- Security

### Phase 6: Write Lesson

Add to `.claude/LESSONS-PROJECT.md`:

```markdown
### LESSON: [Short Descriptive Title]
**Date**: [today's date]

**Symptom**: [What you observed]

**Root Cause**: [Why it happened]

**Solution**:
```[code if applicable]```

**Prevention**:
- [ ] [Test to add]
- [ ] [Validation to add]
- [ ] [Checklist item]
```

### Phase 7: Create Post-Incident Review (PIR)

For production incidents or significant issues, create a formal PIR document.

#### Check if docs/sre/post-incident/ exists:
```bash
mkdir -p docs/sre/post-incident
```

#### Create PIR document:

File: `docs/sre/post-incident/PIR-YYYY-MM-DD-[short-title].md`

```markdown
# Post-Incident Review: [Incident Title]

## Incident Summary

| Field | Value |
|-------|-------|
| **Date** | YYYY-MM-DD |
| **Duration** | X hours Y minutes |
| **Severity** | P1/P2/P3/P4 |
| **Affected Services** | [List] |
| **Users Impacted** | [Number/Percentage] |
| **Incident Commander** | [Name] |

## Timeline

| Time (UTC) | Event |
|------------|-------|
| HH:MM | [First detection/alert] |
| HH:MM | [Investigation started] |
| HH:MM | [Root cause identified] |
| HH:MM | [Fix deployed] |
| HH:MM | [Service restored] |
| HH:MM | [Incident closed] |

## Impact

### User Impact
- [Describe how users were affected]

### Business Impact
- [Revenue loss, SLA breach, reputation, etc.]

### Technical Impact
- [Data loss, degraded performance, etc.]

## Root Cause Analysis

### What Happened
[Detailed description of the failure]

### Why It Happened
1. **Immediate cause**: [Direct trigger]
2. **Contributing factors**:
   - [Factor 1]
   - [Factor 2]

### 5 Whys Analysis
1. Why did [symptom] occur? → [Answer]
2. Why did [answer 1] occur? → [Answer]
3. Why did [answer 2] occur? → [Answer]
4. Why did [answer 3] occur? → [Answer]
5. Why did [answer 4] occur? → [Root cause]

## What Went Well
- [Positive aspect 1]
- [Positive aspect 2]

## What Went Poorly
- [Issue 1]
- [Issue 2]

## Action Items

| Priority | Action | Owner | Due Date | Status |
|----------|--------|-------|----------|--------|
| P1 | [Prevent recurrence] | [Name] | [Date] | Open |
| P2 | [Improve detection] | [Name] | [Date] | Open |
| P2 | [Update runbook] | [Name] | [Date] | Open |
| P3 | [Improve documentation] | [Name] | [Date] | Open |

## Lessons Learned

### Technical Lessons
- [Lesson 1]
- [Lesson 2]

### Process Lessons
- [Lesson 1]
- [Lesson 2]

## Related Documentation

- [Link to relevant runbook]
- [Link to relevant architecture doc]
- [Link to monitoring dashboard]

## Appendix

### Relevant Logs
```
[Key log entries]
```

### Relevant Metrics
[Screenshots or links to graphs]
```

### Phase 8: Update Runbooks

If the incident revealed gaps in operational documentation:

1. **Check existing runbook**: Does it cover this scenario?
2. **Update or create runbook**: Add steps that would have helped
3. **Add to monitoring**: Document new alerts that should be added

### Phase 9: Offer to Contribute

If this lesson applies beyond this project:

```
This lesson might help other projects too.
Contribute to master? (y/n)

If yes, run: ~/streamlined-development/scripts/contribute-lesson.sh
```

### Phase 10: Update Project Memory

**CRITICAL**: Always update project memory after completing the post-mortem.

1. **Update YAML frontmatter** in `.claude/PROJECT_MEMORY.md`:
   - Set `last_post_mortem:` to current UTC timestamp (format: `YYYY-MM-DDTHH:MM:SSZ`)
   - Increment `post_mortem_count:`

2. **Add to Post-Mortem History table**:
   ```markdown
   | YYYY-MM-DD | [Brief lesson summary] | 1 |
   ```

3. **Record detected activities** from Phase 0:
   - Add new scripts to **Scripts Created** table
   - Add new env var NAMES to **Environment Variables** table (NEVER values!)
   - Add infrastructure changes to **Infrastructure** table

4. **Append to Activity Log**:
   ```markdown
   | YYYY-MM-DD | Post-mortem: [Issue summary] | N files |
   ```

5. **If PROJECT_MEMORY.md doesn't exist**, create it using this template:
   ```markdown
   ---
   project: [Project Name from CLAUDE.md]
   initialized: [Today's date]
   last_post_mortem: [Current UTC timestamp]
   post_mortem_count: 1
   ---

   # Project Memory: [Project Name]

   > Persistent memory for Claude across sessions.
   > **Security**: Only variable NAMES stored, never values.

   [... standard sections ...]
   ```

**Security Reminder**:
- ONLY store variable NAMES (e.g., `STRIPE_SECRET_KEY`)
- NEVER store actual values, secrets, or credentials
- File paths and purposes are safe to store

## Arguments

$ARGUMENTS

If provided, use as context for what issue to analyze.
If empty, analyze the most recent debugging in this conversation.

## Output

```
╔════════════════════════════════════════════════════════════╗
║                  POST-MORTEM COMPLETE                      ║
╠════════════════════════════════════════════════════════════╣
║ Lesson Captured                                            ║
║   Title:    [lesson title]                                 ║
║   Category: [category]                                     ║
║   Saved to: .claude/LESSONS-PROJECT.md                     ║
╠════════════════════════════════════════════════════════════╣
║ Project Memory Updated                                     ║
║   Previous Post-Mortem: YYYY-MM-DD (or "Never")            ║
║   Current Post-Mortem:  YYYY-MM-DD                         ║
║   Total Post-Mortems:   N                                  ║
╠════════════════════════════════════════════════════════════╣
║ Activities Recorded:                                       ║
║   • N new scripts                                          ║
║   • N new env vars (names only)                            ║
║   • N infrastructure changes                               ║
╠════════════════════════════════════════════════════════════╣
║ PIR Created (if applicable)                                ║
║   File:     docs/sre/post-incident/PIR-2024-12-27-xxx.md  ║
║   Severity: P2                                             ║
║   Actions:  3 items assigned                               ║
╠════════════════════════════════════════════════════════════╣
║ Prevention measures:                                       ║
║   • [Test to add]                                          ║
║   • [Validation to add]                                    ║
║   • [Runbook to update]                                    ║
╠════════════════════════════════════════════════════════════╣
║ Contribute to master for all projects?                     ║
║ Run: ~/streamlined-development/scripts/contribute-lesson.sh║
╚════════════════════════════════════════════════════════════╝
```

## Severity Guidelines

| Severity | Criteria |
|----------|----------|
| **P1** | Complete service outage, data loss, security breach |
| **P2** | Major feature broken, significant user impact |
| **P3** | Minor feature broken, limited user impact |
| **P4** | Cosmetic issue, no user impact |
