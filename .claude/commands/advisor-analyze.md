---
description: Analyze accumulated debriefs to detect patterns and recommend new skills/modules
allowed-tools: ["Read", "Write", "Edit", "Bash", "Glob", "Grep"]
---

# Advisor Analysis: Pattern Detection & Skill Recommendations

Analyze all accumulated debrief data from `.claude/debriefs/` to detect patterns, identify recurring gaps, and generate actionable recommendations for new skills, skill updates, and module extractions.

## When to Use

- After accumulating 3+ debriefs (minimum for meaningful pattern detection)
- Weekly, as part of a regular review cadence
- After completing a major project milestone
- When planning what skills to build next
- After running `/project:debrief` and wanting to see the bigger picture

## Instructions

### Phase 1: Load All Debrief Data

1. **Read all debrief records**:
   ```bash
   ls .claude/debriefs/*.md 2>/dev/null | grep -v FEEDBACK_LOG
   ```

2. **Read the feedback log**:
   ```bash
   cat .claude/debriefs/FEEDBACK_LOG.md 2>/dev/null
   ```

3. **Count and validate**:
   - Total debrief files found
   - Date range of debriefs (earliest to latest)
   - Projects represented
   - If fewer than 3 debriefs exist, warn that recommendations may be premature

4. **Read each debrief file** to extract structured data:
   - Skills used (with frequency count)
   - Gaps reported (with exact descriptions)
   - Patterns created (with file paths and descriptions)
   - Skill issues found (with skill names and issue descriptions)
   - Technologies without skills (with descriptions)
   - Recommendations made (CREATE/UPDATE/EXTEND/EXTRACT)

### Phase 2: Load Existing Skills Inventory + Skill Groups

1. **List all current skills**:
   ```bash
   ls .claude/skills/ 2>/dev/null
   ```

2. **Load the skill group map**:
   Read `.claude/skills/skill-advisor/SKILL_GROUPS.md` to understand the 23 domain groups. Use this to cluster skills by group for group-level pattern detection.

3. **Build a skills index** for cross-referencing:
   - Skill name
   - Skill group (from SKILL_GROUPS.md)
   - Brief description (from SKILL.md first line or frontmatter)
   - Last updated date

4. **Also check the master repository skills** if this is a child project:
   ```bash
   cat .claude/.master-path 2>/dev/null
   ```
   If a master path exists, also scan the master's skills directory for the full inventory.

### Phase 3: Pattern Detection

Run each detection algorithm against the collected data.

#### 3a. Frequency Patterns — Technologies Mentioned Without Skills

Scan all `Technologies Used Without Skills` sections across all debriefs.

**Rule**: If a technology appears in 2+ debriefs, it is a STRONG signal for a new skill.
**Rule**: If a technology appears in 3+ debriefs, it is a CRITICAL signal.
**Rule**: If a technology appears in only 1 debrief, it is a WATCH signal (track but do not yet recommend).

Group by technology name. Count occurrences. List the projects where each appeared.

#### 3b. Gap Patterns — Missing Skills Reported

Scan all `Skills That Would Have Helped` sections across all debriefs.

**Rule**: If the same gap (by semantic similarity, not exact match) appears in 2+ debriefs, recommend a new skill.
**Rule**: If a gap mentions an existing skill by name (e.g., "stripe skill doesn't cover Connect"), treat as an UPDATE recommendation instead.

Cluster related gaps together. For example:
- "No skill for Redis caching" + "Need Redis session management guidance" = one cluster: "redis-patterns"
- "Webhook retry logic needed" + "No webhook error handling skill" = one cluster: "webhook-patterns"

#### 3c. Skill Issue Patterns — Outdated or Incorrect Skills

Scan all `Skill Issues Found` sections across all debriefs.

**Rule**: Any skill issue reported 1+ times should be queued for update.
**Rule**: If the same skill has issues reported in 2+ debriefs, mark as URGENT update.
**Rule**: API version mismatches are always HIGH priority.

Group by skill name. Aggregate all issues per skill.

#### 3d. Reusable Pattern Patterns — Code Worth Extracting

Scan all `New Patterns Created` sections across all debriefs.

**Rule**: If similar patterns (by description similarity) are created in 2+ projects, recommend extraction into a shared module.
**Rule**: If a pattern is created in 3+ projects, mark as STRONG extraction candidate.

Cluster similar patterns together. Note the file paths for reference.

#### 3e. Usage Patterns — Skill Popularity

Scan all `Skills Used` sections across all debriefs.

Calculate:
- **Most used skills** (top 5 by session count)
- **Least used skills** (skills that exist but have never appeared in a debrief)
- **Rising skills** (skills that were recently created and are already being used)
- **Declining skills** (skills that were popular early but unused in recent debriefs)

#### 3f. Evolution Patterns — Skills Becoming Outdated

Cross-reference skill issue reports with the skill-health-check data.

**Rule**: If a skill has issues reported AND is classified as STALE by health-check, mark as CRITICAL update.
**Rule**: If a skill's issues mention newer API versions, calculate the version delta.

#### 3g. Group-Level Patterns — Domain Hotspots

Using the `GROUPS:` and `GAP_GROUP:` fields from the FEEDBACK_LOG, aggregate activity at the skill-group level.

Calculate for each group:
- **Sessions touching this group** (from `GROUPS:` field)
- **Gaps in this group** (from `GAP_GROUP:` field)
- **Coverage ratio**: skills in group used / skills in group that exist

**Rule**: If a group has 2+ gap reports but all existing skills were used, the group may need more skills — recommend adding skills to that group.
**Rule**: If a group has high sessions-touching but low individual-skill diversity (same 1 skill always), the other skills in that group are under-promoted — flag for `/advise` keyword expansion.
**Rule**: If a group has 0 sessions-touching across 3+ debriefs, its skills may be too hard to discover — flag for SKILL_GROUPS.md trigger keyword review.

### Phase 4: Generate Prioritized Recommendations

Compile all detected patterns into a prioritized recommendation list.

**Priority scoring**:
- CRITICAL: 3+ mentions across projects, or STALE skill with reported issues
- Priority 1: 2+ mentions, no existing skill covering the topic
- Priority 2: 2+ mentions, existing skill is close but needs extension
- Priority 3: 1 mention, but in a high-value project or a growing technology area
- WATCH: 1 mention only, monitor for future signals

### Phase 5: Display the Analysis Report

```
╔══════════════════════════════════════════════════════════════╗
║              ADVISOR ANALYSIS — YYYY-MM-DD                   ║
║              Debriefs analyzed: N | Period: [date range]     ║
║              Projects: N unique | Skills tracked: N          ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  NEW SKILLS RECOMMENDED:                                     ║
║                                                              ║
║  [CRITICAL] (mentioned Nx across N projects):                ║
║    * "[skill-name]" — [reason]                               ║
║      Evidence: [project1], [project2], [project3]            ║
║      Suggested scope: [brief description]                    ║
║                                                              ║
║  [Priority 1] (mentioned Nx, no existing skill):             ║
║    * "[skill-name]" — [reason]                               ║
║      Evidence: [project1], [project2]                        ║
║                                                              ║
║  [Priority 2] (mentioned Nx, gap in existing skill):         ║
║    * "[skill-name]" — extend [existing-skill] with [topic]   ║
║      Evidence: [project1], [project2]                        ║
║                                                              ║
║  [WATCH] (1 mention, tracking):                              ║
║    * "[technology]" — seen in [project]                      ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  SKILLS TO UPDATE:                                           ║
║                                                              ║
║  [URGENT] (issues in 2+ debriefs):                           ║
║    * [skill-name] — [aggregated issues]                      ║
║      Reported in: [debrief1], [debrief2]                     ║
║                                                              ║
║  [Normal] (issue in 1 debrief):                              ║
║    * [skill-name] — [issue description]                      ║
║      Reported in: [debrief]                                  ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  REUSABLE MODULES TO EXTRACT:                                ║
║                                                              ║
║  [STRONG] (similar pattern in N projects):                   ║
║    * "[module-name]" — [description]                         ║
║      Found in: [project1/path], [project2/path]              ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  SKILL USAGE STATISTICS:                                     ║
║                                                              ║
║  Most used (top 5):                                          ║
║    1. [skill-name] — used in N sessions                      ║
║    2. [skill-name] — used in N sessions                      ║
║    3. [skill-name] — used in N sessions                      ║
║    4. [skill-name] — used in N sessions                      ║
║    5. [skill-name] — used in N sessions                      ║
║                                                              ║
║  Never used (exist but 0 debrief mentions):                  ║
║    * [skill-name], [skill-name], [skill-name]...             ║
║                                                              ║
║  Gap hotspots (most gap reports by group):                   ║
║    1. [stack-group-name] — N gaps, N sessions                ║
║    2. [stack-group-name] — N gaps, N sessions                ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  ACTIONS AVAILABLE:                                          ║
║                                                              ║
║  Create new skill:                                           ║
║    /project:advise "create [skill-name]"                     ║
║                                                              ║
║  Update existing skill:                                      ║
║    /project:skill-health update [skill-name]                 ║
║                                                              ║
║  Extract reusable module:                                    ║
║    ./scripts/extract-module.sh [source-path] [module-name]   ║
║                                                              ║
║  Run full skill health check:                                ║
║    ./scripts/skill-health-check.sh                           ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

### Phase 6: Write Analysis Report to File

Save the analysis to `.claude/debriefs/ANALYSIS-YYYY-MM-DD.md`:

```markdown
# Advisor Analysis Report
Date: YYYY-MM-DD
Debriefs Analyzed: N
Period: YYYY-MM-DD to YYYY-MM-DD
Projects: [list]

## New Skills Recommended

### CRITICAL
| Skill Name | Mentions | Projects | Reason |
|------------|----------|----------|--------|
| [name]     | N        | [list]   | [reason] |

### Priority 1
| Skill Name | Mentions | Projects | Reason |
|------------|----------|----------|--------|
| [name]     | N        | [list]   | [reason] |

### Priority 2
| Skill Name | Mentions | Projects | Reason |
|------------|----------|----------|--------|
| [name]     | N        | [list]   | [reason] |

### Watch List
| Technology | Mentions | Project | Notes |
|------------|----------|---------|-------|
| [name]     | 1        | [project] | [notes] |

## Skills To Update

### Urgent
| Skill | Issues | Debriefs | Details |
|-------|--------|----------|---------|
| [name] | N     | [list]   | [aggregated issues] |

### Normal
| Skill | Issue | Debrief | Details |
|-------|-------|---------|---------|
| [name] | [issue] | [debrief] | [details] |

## Reusable Modules to Extract

| Module Name | Similar Patterns | Projects | Files |
|-------------|-----------------|----------|-------|
| [name]      | N               | [list]   | [file paths] |

## Skill Usage Statistics

### Most Used
| Rank | Skill | Sessions |
|------|-------|----------|
| 1    | [name] | N      |
| 2    | [name] | N      |
| 3    | [name] | N      |
| 4    | [name] | N      |
| 5    | [name] | N      |

### Never Used
[comma-separated list of skills with 0 debrief mentions]

### Gap Hotspots
| Domain | Gap Reports | Key Gaps |
|--------|-------------|----------|
| [domain] | N         | [brief list] |

## Raw Data Summary

Total debriefs: N
Total skills used: N (unique)
Total gaps reported: N
Total patterns created: N
Total skill issues: N
Total techs without skills: N
Total recommendations generated: N
```

### Phase 7: Offer Auto-Actions

Based on the analysis, offer concrete next steps.

#### For CRITICAL and Priority 1 New Skills:

> I found **N** strong signals for new skills. Would you like me to:
>
> 1. **Create skill proposals** — Generate a detailed structure for each recommended skill
> 2. **Launch skill creation** — Use `./scripts/create-skill-from-pattern.sh` to scaffold them
> 3. **Just save the report** — Keep the analysis for later action
>
> For a specific skill: `/project:advise "create [skill-name]"`

#### For Skills Needing Updates:

> There are **N** skills with reported issues. Would you like me to:
>
> 1. **Run health check** — `./scripts/skill-health-check.sh --stale`
> 2. **Update specific skill** — I'll research and update the affected sections
> 3. **Queue for batch update** — Add to the next skill maintenance cycle

#### For Reusable Modules:

> There are **N** patterns that could be extracted as shared modules. Would you like me to:
>
> 1. **Review the patterns** — Show me the code from each project for comparison
> 2. **Extract a module** — Create a shared module from the best implementation
> 3. **Skip for now** — They can be extracted later

### Phase 8: Update the Feedback Log

Append an analysis record to `.claude/debriefs/FEEDBACK_LOG.md`:

```markdown
## ANALYSIS: YYYY-MM-DD | debriefs: N | period: [range]
- NEW_SKILLS: [count] recommended ([skill names])
- UPDATES: [count] skills need updating ([skill names])
- EXTRACTIONS: [count] modules to extract ([module names])
- TOP_USED: [top 3 skill names]
- TOP_GAPS: [top 3 gap domains]
```

## Arguments

$ARGUMENTS

If provided, use to filter the analysis:
- `--since YYYY-MM-DD` — Only analyze debriefs since this date
- `--project [name]` — Only analyze debriefs from this project
- `--focus gaps` — Focus report on gap analysis
- `--focus usage` — Focus report on usage statistics
- `--focus updates` — Focus report on skill update needs
- `--quick` — Summary report only, skip detailed tables

If no arguments, perform full analysis of all available debriefs.

## Handling Edge Cases

### Fewer than 3 debriefs
Display a warning:
```
NOTE: Only N debrief(s) found. Pattern detection works best with 3+ debriefs.
Showing preliminary analysis — recommendations may change as more data accumulates.
Tip: Run /project:debrief after each coding session to build the dataset.
```
Still generate the report, but mark all recommendations as "PRELIMINARY".

### No debriefs found
```
No debriefs found in .claude/debriefs/.

To start building your feedback dataset:
1. Complete a coding session
2. Run /project:debrief to capture what happened
3. Repeat for 3+ sessions
4. Run /project:advisor-analyze again

The advisor gets smarter with each debrief you record.
```

### Debriefs from only one project
Note that cross-project pattern detection is limited. Encourage debriefing in other projects too.

### Master repository context
If running from the master repository (streamlined-development), look for debriefs contributed from child projects:
```bash
ls .claude/debriefs/*.md 2>/dev/null
```
These may have been synced from child projects via `daily-sync.sh`.

## Cross-Project Intelligence

When analyzing debriefs from multiple projects:

1. **Highlight cross-project patterns** — Same gap in different projects is a stronger signal than multiple mentions in one project.
2. **Track project diversity** — A gap in 3 different projects beats a gap mentioned 3 times in one project.
3. **Consider project types** — A pattern in a frontend project AND a backend project suggests broader applicability.
4. **Weight recent debriefs higher** — A gap reported last week is more relevant than one from 3 months ago.

## Pattern Detection Quality

The analysis is only as good as the debrief data. To improve quality:

1. **Be specific in debriefs** — "Need Redis skill" is less useful than "Need Redis caching patterns for session management and rate limiting"
2. **Name skills consistently** — Use the exact skill directory name when referencing skills
3. **Include file paths** — When reporting patterns created, include the exact file path
4. **Report API versions** — When flagging outdated skills, specify both the old and new version numbers

## Integration Points

This command reads from:
- `.claude/debriefs/*.md` — Individual debrief records
- `.claude/debriefs/FEEDBACK_LOG.md` — Running summary
- `.claude/skills/` — Existing skills inventory
- `./scripts/skill-health-check.sh --json` — Current skill health data

This command feeds into:
- `./scripts/create-skill-from-pattern.sh` — Creates new skills
- `/project:skill-health update [name]` — Triggers skill updates
- `./scripts/extract-module.sh` — Extracts reusable modules
- `./scripts/bump-version.sh` — Version bumps after skill changes
