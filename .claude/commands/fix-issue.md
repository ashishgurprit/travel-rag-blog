---
description: Analyze and fix GitHub issue
allowed-tools: ["Bash", "Read", "Write", "Task"]
---

# Fix GitHub Issue

Analyze and fix a GitHub issue end-to-end.

## Instructions

### Phase 1: Get Issue Details

```bash
gh issue view $ARGUMENTS --json title,body,labels,comments
```

### Phase 2: Understand the Problem

1. Parse issue description
2. Identify: bug, feature, or improvement
3. Note any reproduction steps
4. Check for related issues/PRs

### Phase 3: Search Codebase

Find relevant files:
- Where might this issue originate?
- What tests cover this area?
- Any related code comments?

### Phase 4: Check Lessons

Does LESSONS.md have relevant guidance for this type of issue?

### Phase 5: Plan Fix

- What files need changes?
- What tests need updates?
- Any risks?

### Phase 6: Implement

1. Write/update tests first (TDD)
2. Implement fix
3. Run tests

### Phase 7: Verify

```bash
# Run related tests
pytest tests/ -v -k "relevant_keyword"

# Run full suite
pytest
```

### Phase 8: Commit

```bash
git add .
git commit -m "fix: [description]

Fixes #$ARGUMENTS"
```

## Arguments

$ARGUMENTS

GitHub issue number (e.g., `123` or `#123`)

## Output

```
╔════════════════════════════════════════════════════════════╗
║                    ISSUE FIXED                             ║
╠════════════════════════════════════════════════════════════╣
║ Issue:  #123 - [title]                                     ║
║ Type:   Bug fix                                            ║
║ Files:  3 modified                                         ║
║ Tests:  2 added, 1 updated                                 ║
╠════════════════════════════════════════════════════════════╣
║ Ready to create PR? Run:                                   ║
║   gh pr create --fill                                      ║
╚════════════════════════════════════════════════════════════╝
```
