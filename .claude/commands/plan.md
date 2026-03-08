---
description: Create implementation plan (research first, no code)
allowed-tools: ["Read", "Bash", "Grep", "Task"]
---

# Research-First Planning

Create a comprehensive implementation plan BEFORE writing any code.

## Critical Rule

**DO NOT WRITE CODE** during this phase. Research and plan only.

## Instructions

### Phase 0: Review Project Context

**IMPORTANT**: Before planning, review existing project knowledge.

1. **Read project memory** (`.claude/PROJECT_MEMORY.md`):
   - Check recent activities and changes
   - Note existing scripts and infrastructure
   - Review what env vars are already configured
   - Check when last post-mortem was done

2. **Read project lessons** (`.claude/LESSONS-PROJECT.md`):
   - Check for relevant past issues
   - Note prevention patterns that apply
   - Look for similar work done before

3. **Consider**:
   - Does this plan conflict with existing work?
   - Can we reuse existing scripts or patterns?
   - Are there lessons that apply to this feature?

### Phase 1: Understand the Request

Parse the feature/task: $ARGUMENTS

1. What is the user trying to accomplish?
2. What are the success criteria?
3. What are the constraints?

### Phase 2: Research Existing Code

Use subagents to explore without polluting main context:

1. **Architecture scan**: How does the codebase structure this type of feature?
2. **Pattern discovery**: What patterns are already established?
3. **Dependency analysis**: What will this feature touch?

```
Task: Explore the codebase for [relevant area]
      Return: file structure, key patterns, integration points
```

### Phase 2.5: Check Component Toolkit (MANDATORY)

**STOP. Before designing anything new, consult the team.**

1. Read `.claude/COMPONENT_REGISTRY.md`
2. For EACH aspect of the feature, search the registry keywords
3. For each match, read the SKILL.md or README.md to assess fit
4. Classify each match:
   - **USE**: Component covers this need. Copy/adapt its templates.
   - **ADAPT**: Component covers 60%+ of need. Start from its code.
   - **REFERENCE**: Component has patterns/lessons relevant to our approach.
   - **BUILD**: Nothing exists. Must build from scratch.

**The plan MUST include a "Reusable Components" section:**

| Need | Component | Action | Justification |
|------|-----------|--------|---------------|
| User auth | firebase-auth-universal | USE | Has iOS + Android + React templates |
| Payment processing | payment-processing-universal | ADAPT | Need custom subscription logic |
| Custom dashboard | — | BUILD | No matching component |

**If building from scratch**: Note it as a candidate for extraction into a new reusable component after implementation.

### Phase 3: Check Lessons Learned

Read `.claude/LESSONS.md` for relevant lessons:
- Has a similar feature caused issues before?
- Are there specific patterns to follow or avoid?
- Any known gotchas for this type of work?

### Phase 4: Create Plan

Generate `plan.md` with:

```markdown
# Implementation Plan: [Feature Name]

## Overview
[What we're building]

## Success Criteria
- [ ] [Criterion 1]
- [ ] [Criterion 2]

## Technical Approach
[High-level approach]

## Phases

### Phase 1: [Name]
- Files to modify: [list]
- Tests to write: [list]
- Estimated complexity: [low/medium/high]

### Phase 2: [Name]
...

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| [Risk 1] | [How to handle] |

## Reusable Components
| Need | Component | Action | Justification |
|------|-----------|--------|---------------|
| [Need 1] | [component-name] | USE/ADAPT/REFERENCE/BUILD | [Why] |

## Lessons Applied
- [Relevant lesson from LESSONS.md]

## Open Questions
- [Questions needing answers before starting]
```

### Phase 5: Review

Present plan summary and ask:
1. Does this align with your expectations?
2. Any constraints I should know about?
3. Ready to proceed to implementation?

## Output

After creating plan.md:

```
╔════════════════════════════════════════════════════════════╗
║                    PLAN CREATED                            ║
╠════════════════════════════════════════════════════════════╣
║ Feature: [name]                                            ║
║ Phases:  [count]                                           ║
║ Files:   [count] to modify                                 ║
║ Tests:   [count] to write                                  ║
║ Risk:    [low/medium/high]                                 ║
╠════════════════════════════════════════════════════════════╣
║ Lessons Applied:                                           ║
║   • [Relevant lesson 1]                                    ║
║   • [Relevant lesson 2]                                    ║
╠════════════════════════════════════════════════════════════╣
║ Next: Review plan.md then run /project:implement           ║
╚════════════════════════════════════════════════════════════╝
```
