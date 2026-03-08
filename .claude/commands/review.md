---
description: Review code changes for quality, security, and best practices
allowed-tools: ["Read", "Bash", "Grep", "Glob"]
---

# Code Review

Comprehensive review of code changes before commit/PR, including documentation verification.

## Instructions

### Phase 1: Get Changes

```bash
# Unstaged changes
git diff

# Staged changes
git diff --cached

# All changes
git status
```

### Phase 2: Review Each File

For each modified file, check:

**Correctness**
- [ ] Logic is correct
- [ ] Edge cases handled
- [ ] No obvious bugs
- [ ] Error handling present

**Code Quality**
- [ ] Follows project conventions
- [ ] No code duplication
- [ ] Functions are focused (single responsibility)
- [ ] Naming is clear and consistent
- [ ] No dead code or TODOs left behind

**Security (OWASP Top 10)**
- [ ] No hardcoded secrets
- [ ] Input validation present
- [ ] No SQL injection risks
- [ ] No XSS vulnerabilities
- [ ] Auth/authz properly checked
- [ ] Sensitive data not logged

**Performance**
- [ ] No N+1 queries
- [ ] No unnecessary loops
- [ ] No memory leaks
- [ ] Appropriate caching

**Testing**
- [ ] Changes have tests
- [ ] Tests are meaningful
- [ ] Edge cases tested

### Phase 3: Documentation Review

**CRITICAL**: Code changes must have corresponding documentation updates.

**Inline Documentation**
- [ ] Complex logic has comments explaining WHY (not what)
- [ ] Public APIs have docstrings/JSDoc
- [ ] Magic numbers have named constants with comments

**Architecture Documentation** (if applicable)
- [ ] New patterns documented in docs/architecture/
- [ ] Significant decisions have ADRs
- [ ] Diagrams updated if structure changed

**API Documentation** (if API changed)
- [ ] OpenAPI/Swagger spec updated
- [ ] API changelog updated
- [ ] Breaking changes documented
- [ ] New endpoints documented in docs/api/

**Operations Documentation** (if deployment affected)
- [ ] Runbooks updated for new procedures
- [ ] Environment variables documented
- [ ] New dependencies documented

**User Documentation** (if user-facing)
- [ ] User guides updated
- [ ] FAQ updated if addressing common issue
- [ ] Release notes drafted

**Check documentation freshness**:
```bash
# Files changed in this commit
CHANGED_FILES=$(git diff --cached --name-only)

# Check if docs need updating
echo "=== Documentation Check ==="

# API changes without doc updates
if echo "$CHANGED_FILES" | grep -q "api/\|routes/\|endpoints/"; then
    if ! echo "$CHANGED_FILES" | grep -q "docs/api\|openapi\|swagger"; then
        echo "⚠ API files changed - verify docs/api/ is updated"
    fi
fi

# Schema changes without doc updates
if echo "$CHANGED_FILES" | grep -q "models/\|schema/\|migrations/"; then
    if ! echo "$CHANGED_FILES" | grep -q "docs/"; then
        echo "⚠ Schema changed - verify docs/architecture/ is updated"
    fi
fi

# Config changes without doc updates
if echo "$CHANGED_FILES" | grep -q "config\|\.env"; then
    if ! echo "$CHANGED_FILES" | grep -q "docs/\|README"; then
        echo "⚠ Config changed - verify environment docs are updated"
    fi
fi
```

### Phase 4: Check Against Lessons

Review `.claude/LESSONS.md` for relevant patterns:
- Any lessons apply to these changes?
- Following prevention checklists?

### Phase 5: Generate Report

## Output Format

```
╔════════════════════════════════════════════════════════════╗
║                    CODE REVIEW                             ║
╠════════════════════════════════════════════════════════════╣
║ Files Reviewed: 5                                          ║
║ Lines Changed: +127 / -34                                  ║
╠════════════════════════════════════════════════════════════╣
║ CRITICAL (Must Fix)                                        ║
║   ✗ src/api/auth.ts:45 - SQL injection risk               ║
║   ✗ src/config.ts:12 - Hardcoded API key                  ║
╠════════════════════════════════════════════════════════════╣
║ WARNINGS (Should Fix)                                      ║
║   ⚠ src/utils/parse.ts:23 - Missing null check            ║
║   ⚠ src/components/Form.tsx - No error handling           ║
╠════════════════════════════════════════════════════════════╣
║ DOCUMENTATION GAPS                                         ║
║   📝 API endpoint added - update docs/api/reference/       ║
║   📝 New env var REDIS_URL - add to docs/development/      ║
║   📝 Breaking change - add to docs/api/changelog.md        ║
╠════════════════════════════════════════════════════════════╣
║ SUGGESTIONS (Nice to Have)                                 ║
║   → src/services/user.ts - Consider caching               ║
║   → src/api/routes.ts - Could extract middleware          ║
╠════════════════════════════════════════════════════════════╣
║ POSITIVE                                                   ║
║   ✓ Good test coverage                                     ║
║   ✓ Clear naming conventions                               ║
║   ✓ Proper error messages                                  ║
║   ✓ ADR added for new caching strategy                     ║
╠════════════════════════════════════════════════════════════╣
║ LESSONS APPLICABLE                                         ║
║   • Firebase UID ≠ UUID - Check ID handling               ║
║   • Contract tests - Verify FE/BE IDs match               ║
╠════════════════════════════════════════════════════════════╣
║ VERDICT: CHANGES REQUESTED                                 ║
║   2 critical issues, 2 doc gaps                            ║
╚════════════════════════════════════════════════════════════╝
```

### Phase 6: Documentation Completeness Matrix

For significant changes, show documentation coverage:

```
┌─────────────────────────────────────────────────────────────┐
│              DOCUMENTATION COVERAGE                          │
├─────────────────────────────────────────────────────────────┤
│ Change Type         │ Required Docs      │ Status           │
├─────────────────────┼────────────────────┼──────────────────┤
│ New API endpoint    │ OpenAPI spec       │ ✓ Updated        │
│                     │ API guide          │ ⚠ Missing        │
│                     │ Changelog          │ ✓ Updated        │
├─────────────────────┼────────────────────┼──────────────────┤
│ Database migration  │ Schema diagram     │ ⚠ Outdated       │
│                     │ Migration runbook  │ ✓ Present        │
├─────────────────────┼────────────────────┼──────────────────┤
│ New feature         │ User guide         │ ✗ Missing        │
│                     │ Feature flag doc   │ ✓ Present        │
└─────────────────────────────────────────────────────────────┘
```

### Phase 7: Offer Fixes

If issues found:
```
Would you like me to:
1. Fix critical and warning code issues?
2. Generate missing documentation stubs?
3. Both?
```

## Arguments

$ARGUMENTS

- No args: Review all uncommitted changes
- `--staged`: Only staged changes
- `--file path/to/file`: Specific file
- `--pr 123`: Review PR (requires gh CLI)
- `--docs-only`: Only check documentation
- `--skip-docs`: Skip documentation checks
