---
description: TDD implementation (tests first, then code)
allowed-tools: ["Read", "Write", "Bash", "Task", "Glob"]
---

# Test-Driven Implementation

Implement features using TDD: write tests first, then make them pass, then update documentation.

## The TDD + Docs Loop

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│  WRITE   │──▶│   RUN    │──▶│ CONFIRM  │──▶│  COMMIT  │
│  TESTS   │   │  TESTS   │   │   FAIL   │   │  TESTS   │
└──────────┘   └──────────┘   └──────────┘   └──────────┘
                                    │
                                    ▼
┌──────────┐   ┌──────────┐   ┌──────────┐
│  COMMIT  │◀──│   RUN    │◀──│IMPLEMENT │
│   CODE   │   │  TESTS   │   │   CODE   │
└────┬─────┘   └──────────┘   └──────────┘
     │              ▲              │
     │              └──────────────┘
     │              (iterate until pass)
     ▼
┌──────────┐   ┌──────────┐   ┌──────────┐
│  UPDATE  │──▶│  VERIFY  │──▶│  COMMIT  │
│   DOCS   │   │   DOCS   │   │   DOCS   │
└──────────┘   └──────────┘   └──────────┘
```

## Instructions

### Phase 1: Load Plan

If `plan.md` exists, read it for:
- What to implement
- Which phase we're on
- Files to modify
- Tests to write

If no plan: Ask what to implement or suggest running `/project:plan` first.

### Phase 2: Write Tests First

**CRITICAL**: We are doing TDD. Write tests BEFORE implementation.

1. Create test file(s) for the feature
2. Write tests based on expected behavior
3. Use REAL input/output examples
4. **DO NOT** create mock implementations

```
# Example test structure
def test_feature_success_case():
    # Arrange
    input_data = {...}
    expected_output = {...}

    # Act
    result = feature_function(input_data)

    # Assert
    assert result == expected_output

def test_feature_error_handling():
    # Test error cases too
```

### Phase 3: Confirm Tests Fail

Run the test suite:

```bash
# Python
pytest tests/test_new_feature.py -v

# JavaScript (auto-detects package manager)
if [ -f "pnpm-lock.yaml" ]; then
    pnpm test -- --testPathPattern=new-feature
elif [ -f "yarn.lock" ]; then
    yarn test --testPathPattern=new-feature
else
    npm test -- --testPathPattern=new-feature
fi
```

**Verify tests fail for the right reason** (not implemented, not syntax error).

### Phase 4: Commit Tests

```bash
git add tests/
git commit -m "test: add tests for [feature]"
```

### Phase 5: Implement

Now write the implementation code:
1. Focus on making tests pass
2. Don't over-engineer
3. Follow existing patterns (from /project:plan research)

### Phase 6: Run Tests Until Pass

```bash
# Run tests
pytest tests/test_new_feature.py -v

# If fail: fix and repeat
# If pass: continue
```

### Phase 7: Commit Implementation

```bash
git add src/
git commit -m "feat: implement [feature]"
```

### Phase 8: Full Test Suite

Run ALL tests to ensure no regressions:

```bash
# Python
pytest

# JavaScript (auto-detects package manager)
if [ -f "pnpm-lock.yaml" ]; then
    pnpm test
elif [ -f "yarn.lock" ]; then
    yarn test
else
    npm test
fi
```

If failures: fix before proceeding.

### Phase 9: Update Documentation

**CRITICAL**: Documentation is part of the definition of done.

Determine which documentation needs updating based on changes:

#### 9.1 Documentation Decision Matrix

| Change Type | Required Documentation |
|-------------|----------------------|
| New API endpoint | docs/api/reference/, docs/api/changelog.md |
| New feature | docs/user/guides/, docs/product/releases/ |
| New component | docs/architecture/, inline JSDoc/docstrings |
| Database change | docs/architecture/diagrams/, migration runbook |
| Config change | docs/development/local-setup.md, README |
| Breaking change | docs/api/changelog.md, migration guide |
| Security-sensitive | docs/security/, threat model update |
| New integration | docs/api/guides/, docs/operations/runbooks/ |

#### 9.2 Update Required Docs

For each applicable doc type:

**API Documentation** (if API changed):
```bash
# Update OpenAPI spec
docs/api/reference/openapi.yaml

# Add to changelog
docs/api/changelog.md

# Update integration guide if needed
docs/api/guides/
```

**Architecture Documentation** (if significant change):
```markdown
# Create ADR if architectural decision made
docs/architecture/decisions/XXX-decision-name.md

# Update diagrams if structure changed
docs/architecture/diagrams/
```

**User Documentation** (if user-facing):
```markdown
# Update relevant user guide
docs/user/guides/

# Add to FAQ if addressing common question
docs/user/faq.md

# Draft release notes
docs/product/releases/
```

**Operations Documentation** (if deployment affected):
```markdown
# Update or create runbook
docs/operations/runbooks/

# Document new environment variables
docs/development/local-setup.md
```

#### 9.3 Inline Documentation

```python
# Add docstrings to new public functions
def new_feature(param: str) -> Result:
    """
    Brief description of what it does.

    Args:
        param: Description of parameter

    Returns:
        Description of return value

    Raises:
        ValueError: When param is invalid

    Example:
        >>> new_feature("test")
        Result(success=True)
    """
```

```typescript
/**
 * Brief description of what it does.
 *
 * @param param - Description of parameter
 * @returns Description of return value
 * @throws {Error} When param is invalid
 *
 * @example
 * ```typescript
 * newFeature("test"); // Returns { success: true }
 * ```
 */
```

### Phase 10: Verify Documentation

```bash
# Check for broken links
find docs -name "*.md" -exec grep -l "\[.*\](.*)" {} \;

# Validate OpenAPI spec (using appropriate package manager)
if [ -f "pnpm-lock.yaml" ]; then
    pnpm dlx @redocly/cli lint docs/api/reference/openapi.yaml
else
    npx @redocly/cli lint docs/api/reference/openapi.yaml
fi

# Check code examples compile
# (ideally run as part of test suite)
```

### Phase 11: Commit Documentation

```bash
git add docs/
git commit -m "docs: add documentation for [feature]"
```

### Phase 12: Final Verification

```bash
# Run all tests including doc tests
pytest --doctest-modules

# or for JS (auto-detects package manager)
if [ -f "pnpm-lock.yaml" ]; then
    pnpm test:docs
elif [ -f "yarn.lock" ]; then
    yarn test:docs
else
    npm run test:docs
fi
```

## Arguments

$ARGUMENTS

- Feature name or description
- If matches a phase in plan.md, implement that phase

## Output

```
╔════════════════════════════════════════════════════════════╗
║                 IMPLEMENTATION COMPLETE                    ║
╠════════════════════════════════════════════════════════════╣
║ Feature: [name]                                            ║
║ Tests:   [X] written, [X] passing                          ║
║ Files:   [list of modified files]                          ║
║ Commits: 3 (tests + implementation + docs)                 ║
╠════════════════════════════════════════════════════════════╣
║ Documentation Updated:                                     ║
║   ✓ docs/api/reference/openapi.yaml                        ║
║   ✓ docs/api/changelog.md                                  ║
║   ✓ docs/user/guides/new-feature.md                        ║
║   ✓ Inline docstrings added                                ║
╠════════════════════════════════════════════════════════════╣
║ Documentation Skipped (not applicable):                    ║
║   ○ Security (no security changes)                         ║
║   ○ Operations (no deployment changes)                     ║
╠════════════════════════════════════════════════════════════╣
║ Next: /project:review then /project:pre-deploy             ║
╚════════════════════════════════════════════════════════════╝
```

## Documentation Checklist

Before marking implementation complete:

- [ ] All new public APIs have docstrings/JSDoc
- [ ] API changes reflected in OpenAPI spec
- [ ] Breaking changes documented in changelog
- [ ] User-facing changes have user docs
- [ ] New config/env vars documented
- [ ] ADR created for significant decisions
- [ ] Code examples in docs are valid and tested
