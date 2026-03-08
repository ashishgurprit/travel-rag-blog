---
description: Capture what happened in a coding session — skills used, gaps found, patterns created
allowed-tools: ["Read", "Write", "Edit", "Bash", "Glob", "Grep"]
---

# Post-Session Debrief: Close the Learning Loop

Capture structured data about what happened during a coding session so the advisor system can detect patterns, recommend new skills, and keep existing skills up to date.

## When to Use

- After completing a significant coding session
- After finishing a feature, bug fix, or integration
- When you discovered that a skill was missing or outdated
- When you built something reusable that other projects could benefit from
- At the end of a work day before switching contexts

## Instructions

### Phase 0: Gather Session Context Automatically

Before asking any questions, silently gather context about what happened.

1. **Read recent git history** to understand what was built:
   ```bash
   git log --since="8 hours ago" --oneline --stat 2>/dev/null || git log --oneline -10 --stat
   ```

2. **Identify modified and created files**:
   ```bash
   git diff --name-status HEAD~10 2>/dev/null | head -40
   ```

3. **Check which skills exist in this project**:
   ```bash
   ls .claude/skills/ 2>/dev/null || echo "No skills directory"
   ```

4. **Read the project identity** (for recording):
   ```bash
   cat .claude/PROJECT_MEMORY.md 2>/dev/null | head -10
   ```
   If no PROJECT_MEMORY.md, extract project name from the directory name or CLAUDE.md.

5. **Check for existing debriefs** to avoid duplication:
   ```bash
   ls .claude/debriefs/*.md 2>/dev/null | tail -5
   ```

6. **Display the session overview**:
   ```
   ╔══════════════════════════════════════════════════════════════╗
   ║                    SESSION DEBRIEF                           ║
   ╠══════════════════════════════════════════════════════════════╣
   ║ Project:  [project name]                                    ║
   ║ Date:     YYYY-MM-DD                                        ║
   ║ Commits:  N commits in last 8 hours                         ║
   ║ Files:    N files modified/created                           ║
   ╠══════════════════════════════════════════════════════════════╣
   ║ I'll walk you through a quick debrief to capture what       ║
   ║ happened. This takes about 2-3 minutes.                     ║
   ╚══════════════════════════════════════════════════════════════╝
   ```

### Phase 1: Skills Used (Ask the Agent/User)

Ask ONE question at a time. Start with:

> Looking at the commits and files changed, I can see you worked on [summary of changes].
>
> **Which skills from `.claude/skills/` did you reference or rely on during this session?**
>
> For example: `elite-frontend-developer`, `stripe-subscription-billing`, `nextjs-app-patterns`
>
> (If none, just say "none" and we'll move on.)

Wait for response. Record the answer.

If the user provides skill names, **map each skill to its group** (from `.claude/skills/skill-advisor/SKILL_GROUPS.md`) and record the group alongside the skill. This enables group-level pattern detection.

Then ask:

> Were there specific **sections** within those skills that were most useful?
> (e.g., "section 3 on error handling" or "the API versioning guide")

### Phase 2: Missing Skills

Ask:

> **Were there any skills that would have helped but don't exist yet?**
>
> Think about:
> - Technologies you used that have no skill coverage
> - Patterns you had to figure out from scratch
> - Integrations where a skill would have saved you time
>
> Describe each gap briefly. For example: "No skill covers Stripe Connect for marketplace payments"

Wait for response. Record the answer.

### Phase 3: New Patterns Created

Based on the git diff and user input, ask:

> **Did you create any reusable patterns, utilities, or components during this session?**
>
> I can see these new files were created:
> [list newly created files from git diff that look reusable — utils, helpers, hooks, services, middleware, etc.]
>
> Which of these (or others) would be useful across other projects?

Wait for response. Record the answer including file paths and descriptions.

### Phase 4: Skill Issues Found

Ask:

> **Did you find any issues with existing skills?**
>
> Common issues:
> - Outdated API version referenced (e.g., API v17 but current is v19)
> - Missing coverage of a subtopic (e.g., skill covers Stripe but not Stripe Connect)
> - Incorrect code examples or deprecated patterns
> - Conflicting advice between skills
>
> If you noticed anything off, describe it now.

Wait for response. Record the answer.

### Phase 5: Technologies Without Skills

Ask:

> **What technologies, APIs, or frameworks did you use that don't have a skill yet?**
>
> Based on the code changes, I can see references to:
> [scan imports, package.json changes, config files for technology names]
>
> Are any of these significant enough to warrant their own skill?

Wait for response. Record the answer.

### Phase 6: Generate the Debrief Record

Now compile all the data into a structured debrief document.

1. **Determine the topic** from the session summary (e.g., "payment-integration", "auth-refactor", "blog-pipeline").

2. **Create the debrief directory** if it does not exist:
   ```bash
   mkdir -p .claude/debriefs
   ```

3. **Write the debrief file** to `.claude/debriefs/YYYY-MM-DD-<topic>.md`:

```markdown
# Debrief: [Topic Title]
Date: YYYY-MM-DD
Project: [project name]
Session Duration: ~[estimated hours based on commit timestamps]
Commits: [count]

## Skills Used
- [skill-name] (group: stack-[group-name]) (sections: [specific sections if mentioned])
- [skill-name] (group: stack-[group-name]) (sections: [specific sections if mentioned])

## Skill Groups Active This Session
- [stack-group-name]: [one-line what was done in this domain]
- [stack-group-name]: [one-line what was done in this domain]

## Skills That Would Have Helped
- [description of gap] — no skill covers [X] (likely group: stack-[group-name])
- [description of gap] — existing skill [Y] is close but missing [Z]

## New Patterns Created
- [file path]: [description of reusable pattern]
- [file path]: [description of reusable pattern]

## Skill Issues Found
- [skill-name]: [section X] has outdated API version ([old] -> [new])
- [skill-name]: missing coverage of [topic]
- [skill-name]: code example in section [X] uses deprecated pattern

## Technologies Used Without Skills
- [technology]: [brief description of what was done with it]
- [technology]: [brief description of what was done with it]

## Recommendations
- CREATE: [proposed skill name] — [why it's needed, evidence from this session]
- UPDATE: [existing skill] — [what needs changing and why]
- EXTEND: [existing skill] — [what section to add and why]
- EXTRACT: [module name] from [file path] — [why it's reusable]
```

4. **If any section has no data**, write `- (none this session)` rather than omitting the section. Every section must be present for machine parsing.

### Phase 7: Update the Feedback Log

Append a summary entry to `.claude/debriefs/FEEDBACK_LOG.md`.

If the file does not exist, create it with this header first:

```markdown
# Feedback Log

> Running summary of all session debriefs. Used by `/project:advisor-analyze` for pattern detection.
> Each entry is one debrief session. Newest entries at the bottom.

---
```

Then append the new entry:

```markdown
## YYYY-MM-DD | project: [name] | topic: [topic]
- USED: [comma-separated skill names, or "none"]
- GROUPS: [comma-separated stack-group names active this session, or "none"]
- GAP: [one-line description of each gap, or "none"]
- GAP_GROUP: [stack-group-name where gap belongs, or "none"]
- CREATED: [file paths of reusable patterns, or "none"]
- ISSUE: [skill-name: brief issue description, or "none"]
- TECH_NO_SKILL: [technology names without skills, or "none"]
- RECOMMEND: [CREATE/UPDATE/EXTEND: brief, or "none"]
```

### Phase 8: Display Summary

Show the completion summary:

```
╔══════════════════════════════════════════════════════════════╗
║                    DEBRIEF COMPLETE                          ║
╠══════════════════════════════════════════════════════════════╣
║ Debrief saved to:                                           ║
║   .claude/debriefs/YYYY-MM-DD-topic.md                      ║
║                                                              ║
║ Summary:                                                     ║
║   Skills used:           N                                   ║
║   Gaps identified:       N                                   ║
║   Patterns created:      N                                   ║
║   Skill issues found:    N                                   ║
║   Techs without skills:  N                                   ║
║   Recommendations:       N                                   ║
╠══════════════════════════════════════════════════════════════╣
║ Feedback log updated:                                        ║
║   .claude/debriefs/FEEDBACK_LOG.md                           ║
║   Total debriefs on record: N                                ║
╠══════════════════════════════════════════════════════════════╣
║ Next steps:                                                  ║
║   • Run /project:advisor-analyze to detect patterns          ║
║   • Run contribute-lesson.sh to share findings with master   ║
║   • Sync debriefs to master with sync-from-master.sh         ║
╚══════════════════════════════════════════════════════════════╝
```

### Phase 9: Offer Follow-up Actions

Based on the debrief findings:

- **If CREATE recommendations exist**: "I found N gaps that suggest new skills. Run `/project:advisor-analyze` to see if these patterns appear across other projects too."
- **If UPDATE/ISSUE items exist**: "There are skill issues to address. Run `/project:skill-health update [skill-name]` to update the affected skills."
- **If reusable patterns were created**: "Consider extracting these to shared modules. Run `./scripts/extract-module.sh` for assistance."
- **If this is the first debrief**: "This is your first debrief! The advisor system gets smarter with each debrief. Aim for a quick debrief after each significant session."

## Arguments

$ARGUMENTS

If provided, use as the topic/context for the debrief (e.g., "payment integration work" or "auth refactor").
If empty, infer the topic from the git log and changed files.

## Debrief File Naming Convention

Format: `YYYY-MM-DD-<topic-slug>.md`

Examples:
- `2026-03-03-payment-integration.md`
- `2026-03-03-auth-refactor.md`
- `2026-03-03-blog-pipeline-setup.md`

If multiple debriefs on the same day for the same topic, append a number:
- `2026-03-03-payment-integration-2.md`

## Handling Edge Cases

### No git history available
If `git log --since="8 hours ago"` returns nothing:
- Fall back to `git log --oneline -10`
- Ask the user to describe what they worked on manually

### No skills directory
If `.claude/skills/` does not exist:
- Skip the "Skills Used" question
- Focus on "Technologies Used Without Skills" and "New Patterns Created"
- Note in the debrief that the project has no skills configured

### Agent self-debrief
If the coding agent is debriefing itself (no human in the loop):
- Use the git diff and file analysis to auto-fill as much as possible
- Mark auto-filled sections with `(auto-detected)`
- Still write the full structured debrief

### Interrupted session
If the user wants to do a quick debrief:
- Offer a "quick mode": just capture skills used and gaps found
- Write a minimal debrief with the available data
- Mark it as `## Quick Debrief` in the file

## Integration Points

This command feeds data to:
- `/project:advisor-analyze` — reads debriefs for pattern detection
- `contribute-lesson.sh` — debrief findings can become shared lessons
- `skill-health-check.sh` — skill issues feed update recommendations
- `daily-sync.sh` — debriefs sync across projects to master
- `build-capability-index.sh` — new skill recommendations trigger index rebuilds
