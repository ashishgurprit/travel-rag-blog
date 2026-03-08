---
description: Auto-fix all test failures (project)
allowed-tools: ["Read", "Write", "Bash", "Task", "Glob"]
---

# Test Fix Loop

Run tests and automatically fix failures until all pass, including documentation validation.

## Instructions

### Phase 1: Run Full Test Suite

```bash
# Detect test framework
if [ -f "pytest.ini" ] || [ -f "pyproject.toml" ]; then
    pytest -v --tb=short
elif [ -f "package.json" ]; then
    # Auto-detect package manager
    if [ -f "pnpm-lock.yaml" ]; then
        pnpm test
    elif [ -f "yarn.lock" ]; then
        yarn test
    else
        npm test
    fi
fi
```

### Phase 2: For Each Failure

1. **Parse the error**:
   - Which test failed?
   - What was the error message?
   - What was expected vs actual?

2. **Analyze the cause**:
   - Is it a code bug or test bug?
   - What file needs to change?

3. **Fix the issue**:
   - Make minimal change to fix
   - Don't change test unless test is wrong

4. **Re-run specific test**:
   ```bash
   pytest tests/test_file.py::test_function -v
   ```

5. **If still failing**: Iterate on fix

6. **If passing**: Move to next failure

### Phase 3: Documentation Validation Tests

After code tests pass, validate documentation:

**3.1 Code Examples in Docs**

Check that code examples in documentation are valid:

```bash
# Find code blocks in markdown
echo "=== Checking Documentation Code Examples ==="

# Python examples
for doc in $(find docs -name "*.md" 2>/dev/null); do
    # Extract Python code blocks and syntax check
    grep -Pzo '```python\n[\s\S]*?```' "$doc" 2>/dev/null | \
    python -m py_compile - 2>&1 | grep -v "^$" && \
    echo "⚠ Invalid Python in: $doc"
done

# JavaScript examples
for doc in $(find docs -name "*.md" 2>/dev/null); do
    grep -Pzo '```javascript\n[\s\S]*?```' "$doc" 2>/dev/null | \
    node --check - 2>&1 | grep -v "^$" && \
    echo "⚠ Invalid JavaScript in: $doc"
done
```

**3.2 API Documentation Sync**

Verify API docs match implementation:

```bash
echo "=== Checking API Documentation Sync ==="

# If OpenAPI spec exists
if [ -f "docs/api/reference/openapi.yaml" ] || [ -f "openapi.yaml" ]; then
    # Validate OpenAPI spec (auto-detect package manager)
    if [ -f "pnpm-lock.yaml" ]; then
        pnpm dlx @redocly/cli lint docs/api/reference/openapi.yaml 2>/dev/null || \
        echo "⚠ OpenAPI spec has validation errors"
    else
        npx @redocly/cli lint docs/api/reference/openapi.yaml 2>/dev/null || \
        echo "⚠ OpenAPI spec has validation errors"
    fi
fi

# Check for undocumented endpoints
if [ -d "src/api" ] || [ -d "src/routes" ]; then
    echo "Comparing endpoints..."
    # List defined routes vs documented routes
fi
```

**3.3 Link Validation**

Check for broken internal links:

```bash
echo "=== Checking Documentation Links ==="

# Find markdown links and verify files exist
for doc in $(find docs -name "*.md" 2>/dev/null); do
    # Extract relative links
    grep -oE '\[.*\]\((?!http)[^)]+\)' "$doc" | while read link; do
        target=$(echo "$link" | grep -oE '\([^)]+\)' | tr -d '()')
        dir=$(dirname "$doc")
        if [ ! -f "$dir/$target" ] && [ ! -f "$target" ]; then
            echo "⚠ Broken link in $doc: $target"
        fi
    done
done
```

**3.4 Documentation Freshness**

Check for stale documentation:

```bash
echo "=== Checking Documentation Freshness ==="

# Find docs older than related code
for doc in docs/api/*.md; do
    # Compare doc mtime with related source files
    doc_time=$(stat -f %m "$doc" 2>/dev/null || stat -c %Y "$doc" 2>/dev/null)
    # If source is newer, flag as potentially stale
done

# Check for TODO/FIXME in docs
grep -r "TODO\|FIXME\|TBD\|PLACEHOLDER" docs/ 2>/dev/null && \
echo "⚠ Found incomplete documentation markers"
```

### Phase 4: Fix Documentation Issues

If documentation issues found:

1. **Invalid code examples**: Fix syntax or mark as pseudo-code
2. **API doc mismatch**: Update OpenAPI spec or endpoint docs
3. **Broken links**: Update links or create missing files
4. **Stale docs**: Flag for review (don't auto-update content)

### Phase 5: Final Verification

After all failures addressed:

```bash
# Run full test suite again
# Python
pytest -v

# JavaScript (auto-detect package manager)
if [ -f "pnpm-lock.yaml" ]; then
    pnpm test
elif [ -f "yarn.lock" ]; then
    yarn test
else
    npm test
fi

# Run doc validation
echo "=== Final Documentation Check ==="
# Repeat Phase 3 checks
```

### Phase 6: Report

```
╔════════════════════════════════════════════════════════════╗
║                    TEST FIX COMPLETE                       ║
╠════════════════════════════════════════════════════════════╣
║ CODE TESTS                                                 ║
║   Initial:  12 tests, 3 failures                           ║
║   Fixed:    3 issues                                       ║
║   Final:    12 tests, 0 failures ✓                         ║
╠════════════════════════════════════════════════════════════╣
║ DOCUMENTATION TESTS                                        ║
║   Code examples:   8 checked, 0 invalid ✓                  ║
║   API sync:        12 endpoints, 12 documented ✓           ║
║   Internal links:  45 checked, 2 fixed ✓                   ║
║   Freshness:       3 docs flagged for review ⚠             ║
╠════════════════════════════════════════════════════════════╣
║ Changes made:                                              ║
║   • src/utils.py: Fixed null handling in parse_id()       ║
║   • src/api.py: Added missing error response              ║
║   • docs/api/users.md: Fixed broken link to auth.md       ║
║   • docs/api/reference/openapi.yaml: Added missing field  ║
╠════════════════════════════════════════════════════════════╣
║ Flagged for review:                                        ║
║   ⚠ docs/user/getting-started.md - older than src/        ║
║   ⚠ docs/api/webhooks.md - contains TODO                  ║
╚════════════════════════════════════════════════════════════╝
```

## Arguments

$ARGUMENTS

- No args: Fix all failures including docs
- Test name/pattern: Focus on specific tests
- `--no-commit`: Don't auto-commit fixes
- `--code-only`: Skip documentation validation
- `--docs-only`: Only run documentation validation
- `--strict`: Fail on any documentation issues
