---
description: Pre-deployment checklist with lessons applied
allowed-tools: ["Read", "Bash", "Task", "Glob"]
---

# Pre-Deployment Checks

Comprehensive checks before deploying, incorporating lessons learned and documentation verification.

## Instructions

### Phase 1: Load Lessons

Read lessons from:
1. `.claude/LESSONS.md` (master lessons)
2. `.claude/LESSONS-PROJECT.md` (project-specific)

Extract all prevention checklist items.

### Phase 2: Environment Validation

Check configuration:

```bash
# Required environment variables
echo "=== Environment Check ==="

# List based on project type
REQUIRED_VARS="DATABASE_URL"

# Add based on detected features
if grep -q "stripe" package.json pyproject.toml 2>/dev/null; then
    REQUIRED_VARS="$REQUIRED_VARS STRIPE_SECRET_KEY STRIPE_WEBHOOK_SECRET"
fi

if grep -q "firebase" package.json pyproject.toml 2>/dev/null; then
    REQUIRED_VARS="$REQUIRED_VARS FIREBASE_CREDENTIALS"
fi

for var in $REQUIRED_VARS; do
    if [ -z "${!var}" ]; then
        echo "❌ Missing: $var"
    else
        echo "✓ Set: $var"
    fi
done
```

### Phase 3: Run Contract Tests

If `tests/test_contracts.py` or similar exists:

```bash
echo "=== Contract Tests ==="
pytest tests/test_contracts.py -v --tb=short 2>/dev/null || \
[ -f "pnpm-lock.yaml" ] && pnpm test -- --testPathPattern=contract 2>/dev/null || npm test -- --testPathPattern=contract 2>/dev/null || \
echo "No contract tests found"
```

### Phase 4: Run Integration Tests

```bash
echo "=== Integration Tests ==="
pytest tests/test_integration.py -v --tb=short 2>/dev/null || \
[ -f "pnpm-lock.yaml" ] && pnpm test -- --testPathPattern=integration 2>/dev/null || npm test -- --testPathPattern=integration 2>/dev/null || \
echo "No integration tests found"
```

### Phase 5: Startup Validation

If project has startup validation:

```bash
echo "=== Startup Validation ==="
# Python
python -c "from src.startup_validation import validate_startup_environment; validate_startup_environment()" 2>/dev/null || \

# Node
node -e "require('./src/startup-validation').validate()" 2>/dev/null || \

echo "No startup validation found (consider adding)"
```

### Phase 6: Security Checks

**CRITICAL**: Security vulnerabilities must be addressed before deployment.

#### 6.1 Dependency Vulnerabilities

```bash
echo "=== Dependency Security ==="

# Node.js projects
if [ -f "package.json" ]; then
    npm audit --production 2>/dev/null | grep -E "High|Critical" && \
    echo "❌ BLOCKING: High/Critical npm vulnerabilities found" || \
    echo "✓ npm audit: No high/critical vulnerabilities"
fi

# Python projects
if [ -f "requirements.txt" ] || [ -f "pyproject.toml" ]; then
    pip-audit 2>/dev/null | grep -E "HIGH|CRITICAL" && \
    echo "❌ BLOCKING: High/Critical Python vulnerabilities found" || \
    echo "✓ pip-audit: No high/critical vulnerabilities"
fi

# Ruby projects
if [ -f "Gemfile" ]; then
    bundle audit check 2>/dev/null | grep -E "Severity: High|Severity: Critical" && \
    echo "❌ BLOCKING: High/Critical gem vulnerabilities found" || \
    echo "✓ bundle audit: No high/critical vulnerabilities"
fi
```

#### 6.2 Hardcoded Secrets Detection

```bash
echo "=== Secrets Scanning ==="

# Check for common secret patterns
SECRETS_FOUND=0

# API keys
if grep -r "API_KEY\s*=\s*['\"]" . --exclude-dir={node_modules,.git,dist,build,venv} 2>/dev/null; then
    echo "❌ BLOCKING: Hardcoded API_KEY found"
    SECRETS_FOUND=1
fi

# Passwords
if grep -r "PASSWORD\s*=\s*['\"][^{]" . --exclude-dir={node_modules,.git,dist,build,venv} 2>/dev/null; then
    echo "❌ BLOCKING: Hardcoded PASSWORD found"
    SECRETS_FOUND=1
fi

# Tokens
if grep -r "TOKEN\s*=\s*['\"][a-zA-Z0-9]{20,}" . --exclude-dir={node_modules,.git,dist,build,venv} 2>/dev/null; then
    echo "❌ BLOCKING: Hardcoded TOKEN found"
    SECRETS_FOUND=1
fi

# AWS keys
if grep -r "AKIA[0-9A-Z]{16}" . --exclude-dir={node_modules,.git,dist,build,venv} 2>/dev/null; then
    echo "❌ BLOCKING: AWS access key found"
    SECRETS_FOUND=1
fi

if [ $SECRETS_FOUND -eq 0 ]; then
    echo "✓ No hardcoded secrets detected"
fi
```

#### 6.3 Injection Vulnerability Patterns

```bash
echo "=== Injection Vulnerabilities ==="

# SQL injection patterns (Python)
if grep -r "execute.*f\"" . --include="*.py" --exclude-dir={node_modules,.git,venv} 2>/dev/null; then
    echo "⚠️  SQL injection risk: f-string in execute() (Python)"
fi

if grep -r "query.*+.*input\|query.*+.*request\|query.*+.*params" . --include="*.py" --exclude-dir={node_modules,.git,venv} 2>/dev/null; then
    echo "⚠️  SQL injection risk: String concatenation in query (Python)"
fi

# SQL injection patterns (JavaScript/TypeScript)
if grep -r 'query.*+.*req\.\|query.*`.*\${' . --include="*.js" --include="*.ts" --exclude-dir={node_modules,.git,dist,build} 2>/dev/null; then
    echo "⚠️  SQL injection risk: String concatenation in query (JS/TS)"
fi

# Command injection patterns
if grep -r "exec\|system\|eval" . --include="*.py" --include="*.js" --include="*.ts" --exclude-dir={node_modules,.git,dist,build,venv} 2>/dev/null | grep -v "subprocess.run\|spawn"; then
    echo "⚠️  Command injection risk: exec/system/eval usage"
fi

# Check for subprocess with shell=True (Python)
if grep -r "subprocess.*shell=True\|os\.system" . --include="*.py" --exclude-dir={node_modules,.git,venv} 2>/dev/null; then
    echo "⚠️  Command injection risk: shell=True or os.system()"
fi
```

#### 6.4 XSS Vulnerability Patterns

```bash
echo "=== XSS Vulnerabilities ==="

# innerHTML usage
if grep -r "innerHTML\s*=" . --include="*.js" --include="*.jsx" --include="*.ts" --include="*.tsx" --exclude-dir={node_modules,.git,dist,build} 2>/dev/null; then
    echo "⚠️  XSS risk: innerHTML usage detected"
    echo "   Consider using textContent or DOMPurify"
fi

# dangerouslySetInnerHTML in React
if grep -r "dangerouslySetInnerHTML" . --include="*.jsx" --include="*.tsx" --exclude-dir={node_modules,.git,dist,build} 2>/dev/null; then
    echo "⚠️  XSS risk: dangerouslySetInnerHTML usage"
    echo "   Ensure content is sanitized with DOMPurify"
fi
```

#### 6.5 Security Headers Verification

```bash
echo "=== Security Headers ==="

# Check for security headers configuration
HEADERS_FOUND=0

# Cloudflare Pages
if [ -f "public/_headers" ]; then
    echo "✓ Found _headers file (Cloudflare)"

    grep -q "Content-Security-Policy" public/_headers && echo "  ✓ CSP" || echo "  ❌ Missing CSP"
    grep -q "X-Frame-Options" public/_headers && echo "  ✓ X-Frame-Options" || echo "  ❌ Missing X-Frame-Options"
    grep -q "X-Content-Type-Options" public/_headers && echo "  ✓ X-Content-Type-Options" || echo "  ❌ Missing X-Content-Type-Options"
    grep -q "Strict-Transport-Security" public/_headers && echo "  ✓ HSTS" || echo "  ❌ Missing HSTS"
    HEADERS_FOUND=1
fi

# Express/Node middleware
if grep -r "helmet\|setHeader.*X-Frame-Options" . --include="*.js" --include="*.ts" --exclude-dir={node_modules,.git,dist,build} 2>/dev/null; then
    echo "✓ Security headers middleware found (Express)"
    HEADERS_FOUND=1
fi

# FastAPI/Python middleware
if grep -r "add_security_headers\|CORSMiddleware" . --include="*.py" --exclude-dir={venv,.git} 2>/dev/null; then
    echo "✓ Security headers middleware found (FastAPI)"
    HEADERS_FOUND=1
fi

if [ $HEADERS_FOUND -eq 0 ]; then
    echo "⚠️  No security headers configuration found"
fi
```

#### 6.6 Rate Limiting Check

```bash
echo "=== Rate Limiting ==="

# Check for rate limiting implementation
RATE_LIMIT_FOUND=0

# Cloudflare Functions
if grep -r "RATE_LIMIT\|rate_limit" functions/ 2>/dev/null; then
    echo "✓ Rate limiting found in Cloudflare Functions"
    RATE_LIMIT_FOUND=1
fi

# Express rate limiting
if grep -r "express-rate-limit\|slowapi\|limiter" . --include="*.js" --include="*.ts" --include="*.py" --exclude-dir={node_modules,.git,venv} 2>/dev/null; then
    echo "✓ Rate limiting middleware found"
    RATE_LIMIT_FOUND=1
fi

if [ $RATE_LIMIT_FOUND -eq 0 ]; then
    echo "⚠️  No rate limiting detected"
    echo "   Consider adding rate limiting to auth/API endpoints"
fi
```

#### 6.7 CORS Configuration

```bash
echo "=== CORS Configuration ==="

# Check for wildcard CORS (insecure)
if grep -r "Access-Control-Allow-Origin.*\*\|cors.*origin.*\*" . --include="*.js" --include="*.ts" --include="*.py" --exclude-dir={node_modules,.git,venv} 2>/dev/null; then
    echo "⚠️  Wildcard CORS detected (allows any origin)"
    echo "   Production should use specific domains"
fi

# Check for proper CORS configuration
if grep -r "ALLOWED_ORIGINS\|allowedOrigins" . --include="*.js" --include="*.ts" --include="*.py" --exclude-dir={node_modules,.git,venv} 2>/dev/null; then
    echo "✓ CORS whitelist configuration found"
fi
```

#### 6.8 Authentication Security

```bash
echo "=== Authentication Security ==="

# Check for bcrypt/argon2 usage
if grep -r "bcrypt\|argon2" . --include="*.js" --include="*.ts" --include="*.py" --exclude-dir={node_modules,.git,venv} 2>/dev/null; then
    echo "✓ Password hashing library found (bcrypt/argon2)"
else
    echo "⚠️  No password hashing library detected"
fi

# Check for insecure password storage
if grep -r "password.*=.*plain\|md5.*password\|sha1.*password" . --include="*.py" --include="*.js" --include="*.ts" --exclude-dir={node_modules,.git,venv} 2>/dev/null; then
    echo "❌ BLOCKING: Insecure password storage detected"
fi

# Check for auth header forwarding (if using proxy)
if [ -f "nginx.conf" ] || [ -f "nginx/nginx.conf" ]; then
    if grep -q "proxy_set_header Authorization" nginx.conf nginx/nginx.conf 2>/dev/null; then
        echo "✓ Nginx forwards Authorization header"
    else
        echo "⚠️  Nginx may not forward Authorization header"
    fi
fi
```

#### 6.9 Security Checklist from Lessons

Based on real-world incidents across 30+ projects:

```bash
echo "=== Security Checklist ==="

# From LESSONS.md - Authentication
echo "Authentication & Identity:"
echo "  [ ] Database ID columns: varchar(128) minimum (not varchar(36))"
echo "  [ ] Tests use realistic auth provider IDs (Firebase, Auth0, OAuth)"
echo "  [ ] Auth headers pass through proxy/CDN"
echo "  [ ] Password fields excluded from security pattern matching"
echo ""

# From LESSONS.md - Injection Prevention
echo "Injection Prevention:"
echo "  [ ] SQL queries use parameterized queries (NEVER string concatenation)"
echo "  [ ] Shell commands use spawn() with arrays (NEVER exec() with strings)"
echo "  [ ] User input to shell uses temp files (NOT escaping)"
echo "  [ ] XSS protection: textContent OR escapeHtml() OR DOMPurify"
echo ""

# From LESSONS.md - Configuration
echo "Configuration:"
echo "  [ ] Startup environment validation implemented (fail-fast)"
echo "  [ ] No hardcoded secrets in code/git"
echo "  [ ] Debug mode OFF in production"
echo "  [ ] CORS restricted to production domains"
echo ""

# From LESSONS.md - Multi-Site Standards
echo "Multi-Site Standards:"
echo "  [ ] Security template applied from master"
echo "  [ ] Rate limiting: 5 requests/hour per IP for contact forms"
echo "  [ ] Rate limiting: 5 requests/minute per IP for auth endpoints"
echo "  [ ] CAPTCHA on all public forms"
echo "  [ ] HTTP security headers configured (CSP, X-Frame-Options, HSTS)"
echo ""
```

### Phase 7: Documentation Verification

**CRITICAL**: Production deployments require complete documentation.

#### 7.1 Required Documentation Check

```bash
echo "=== Documentation Completeness ==="

# Check for required docs folders
REQUIRED_DOCS=(
    "docs/operations/runbooks"
    "docs/operations/playbooks"
    "docs/security"
    "docs/sre"
)

for doc_path in "${REQUIRED_DOCS[@]}"; do
    if [ -d "$doc_path" ] && [ "$(ls -A $doc_path 2>/dev/null)" ]; then
        echo "✓ $doc_path exists and has content"
    else
        echo "❌ $doc_path missing or empty"
    fi
done
```

#### 7.2 Critical Documentation Files

| Document | Required For | Status Check |
|----------|--------------|--------------|
| Deployment runbook | Any deploy | `docs/operations/runbooks/deployment.md` |
| Rollback runbook | Any deploy | `docs/operations/runbooks/rollback.md` |
| Incident playbook | Production | `docs/operations/playbooks/incident-response.md` |
| On-call guide | Production | `docs/operations/on-call.md` |
| SLO definitions | Production | `docs/sre/slo-definitions.md` |
| Monitoring docs | Production | `docs/sre/monitoring.md` |
| Threat model | Production | `docs/security/threat-model.md` |

```bash
echo "=== Critical Documentation ==="

# For ANY deployment
REQUIRED_FOR_DEPLOY=(
    "docs/operations/runbooks/deployment.md:Deployment runbook"
    "docs/operations/runbooks/rollback.md:Rollback runbook"
)

# For PRODUCTION deployment
REQUIRED_FOR_PROD=(
    "docs/operations/playbooks/incident-response.md:Incident playbook"
    "docs/operations/on-call.md:On-call guide"
    "docs/sre/slo-definitions.md:SLO definitions"
    "docs/sre/monitoring.md:Monitoring documentation"
    "docs/security/threat-model.md:Threat model"
)

for item in "${REQUIRED_FOR_DEPLOY[@]}"; do
    path="${item%%:*}"
    name="${item##*:}"
    if [ -f "$path" ]; then
        echo "✓ $name"
    else
        echo "❌ BLOCKING: $name missing ($path)"
    fi
done

# If deploying to production, check additional docs
if [ "$DEPLOY_ENV" = "production" ] || [ "$1" = "--production" ]; then
    echo ""
    echo "=== Production-Required Documentation ==="
    for item in "${REQUIRED_FOR_PROD[@]}"; do
        path="${item%%:*}"
        name="${item##*:}"
        if [ -f "$path" ]; then
            echo "✓ $name"
        else
            echo "❌ BLOCKING: $name missing ($path)"
        fi
    done
fi
```

#### 7.3 Documentation Freshness

```bash
echo "=== Documentation Freshness ==="

# Check if docs are older than 90 days
STALE_THRESHOLD=$((90 * 24 * 60 * 60))  # 90 days in seconds
NOW=$(date +%s)

for doc in docs/operations/runbooks/*.md docs/sre/*.md; do
    if [ -f "$doc" ]; then
        DOC_TIME=$(stat -f %m "$doc" 2>/dev/null || stat -c %Y "$doc" 2>/dev/null)
        AGE=$((NOW - DOC_TIME))
        if [ $AGE -gt $STALE_THRESHOLD ]; then
            echo "⚠ STALE: $doc ($(($AGE / 86400)) days old)"
        fi
    fi
done

# Check for TODOs in critical docs
if grep -r "TODO\|FIXME\|TBD" docs/operations/ docs/sre/ docs/security/ 2>/dev/null; then
    echo "⚠ Incomplete markers found in critical documentation"
fi
```

#### 7.4 API Documentation Sync

```bash
echo "=== API Documentation ==="

# Check OpenAPI spec is valid
if [ -f "docs/api/reference/openapi.yaml" ]; then
    npx @redocly/cli lint docs/api/reference/openapi.yaml 2>/dev/null && \
    echo "✓ OpenAPI spec is valid" || \
    echo "❌ OpenAPI spec has errors"
fi

# Check API changelog has recent entries
if [ -f "docs/api/changelog.md" ]; then
    LAST_ENTRY=$(grep -m1 "^## \[" docs/api/changelog.md | head -1)
    echo "✓ API Changelog last entry: $LAST_ENTRY"
fi
```

#### 7.5 Compliance Documentation

For regulated deployments:

```bash
echo "=== Compliance Documentation ==="

COMPLIANCE_DOCS=(
    "docs/security/compliance/soc2-mapping.md:SOC 2 mapping"
    "docs/security/compliance/gdpr-mapping.md:GDPR mapping"
    "docs/security/access-control.md:Access control matrix"
)

for item in "${COMPLIANCE_DOCS[@]}"; do
    path="${item%%:*}"
    name="${item##*:}"
    if [ -f "$path" ]; then
        echo "✓ $name"
    else
        echo "○ $name not found (may not be required)"
    fi
done
```

### Phase 8: Lessons Checklist

Review each prevention item from lessons. Output checklist:

**Authentication & Identity** (from lessons)
- [ ] Tested with REAL auth provider IDs (not mock UUIDs)
- [ ] Credential format matches deployment platform
- [ ] Auth headers pass through proxy/CDN

**Database** (from lessons)
- [ ] ID column types match auth provider format
- [ ] Migrations run separately from app startup
- [ ] Connection string verified

**API Contracts** (from lessons)
- [ ] Frontend/backend IDs match (contract test)
- [ ] Error responses are structured and displayed
- [ ] CORS configured for production domain

**Payments** (if applicable, from lessons)
- [ ] Webhook URL registered in dashboard
- [ ] Webhook handler is transactional
- [ ] Test vs live mode keys verified

### Phase 9: Generate Report

**All Checks Pass:**
```
╔════════════════════════════════════════════════════════════╗
║                 DEPLOYMENT READY ✓                         ║
╠════════════════════════════════════════════════════════════╣
║ TESTS                                                      ║
║   Contract Tests: ✓ 5/5 passed                             ║
║   Integration:    ✓ 8/8 passed                             ║
║   Startup:        ✓ Validation passed                      ║
╠════════════════════════════════════════════════════════════╣
║ ENVIRONMENT                                                ║
║   Variables:      ✓ All required vars set                  ║
║   Credentials:    ✓ Format validated                       ║
╠════════════════════════════════════════════════════════════╣
║ DOCUMENTATION                                              ║
║   Operations:     ✓ Runbooks present and current           ║
║   Security:       ✓ Threat model up to date                ║
║   SRE:            ✓ SLOs defined, monitoring documented    ║
║   API:            ✓ OpenAPI valid, changelog current       ║
╠════════════════════════════════════════════════════════════╣
║ LESSONS                                                    ║
║   Checklist:      ✓ 12/12 items verified                   ║
╠════════════════════════════════════════════════════════════╣
║ Ready to deploy!                                           ║
║                                                            ║
║ After deploy, run smoke tests:                             ║
║   ./scripts/smoke-test.sh production                       ║
╚════════════════════════════════════════════════════════════╝
```

**Issues Found:**
```
╔════════════════════════════════════════════════════════════╗
║                 DEPLOYMENT BLOCKED ✗                       ║
╠════════════════════════════════════════════════════════════╣
║ BLOCKING ISSUES                                            ║
║                                                            ║
║ ❌ Documentation: Rollback runbook missing                 ║
║    Create: docs/operations/runbooks/rollback.md            ║
║    Run: /project:docs operations                           ║
║                                                            ║
║ ❌ Contract Tests: 1 failure                               ║
║    - test_plan_ids_match: 'pack_10' not in backend         ║
╠════════════════════════════════════════════════════════════╣
║ WARNINGS (should fix, not blocking)                        ║
║                                                            ║
║ ⚠️  docs/sre/monitoring.md is 95 days old                  ║
║ ⚠️  No integration tests for Firebase UIDs                 ║
║    (See LESSON: Firebase UID ≠ UUID)                       ║
║ ⚠️  TODO found in docs/operations/runbooks/deployment.md   ║
╠════════════════════════════════════════════════════════════╣
║ Fix blocking issues before deploying                       ║
╚════════════════════════════════════════════════════════════╝
```

### Phase 10: Documentation Gate

If documentation is incomplete:

```
╔════════════════════════════════════════════════════════════╗
║              DOCUMENTATION GATE FAILED                     ║
╠════════════════════════════════════════════════════════════╣
║ Missing critical documentation for production deploy:      ║
║                                                            ║
║ Operations (required):                                     ║
║   ❌ docs/operations/runbooks/deployment.md                ║
║   ❌ docs/operations/runbooks/rollback.md                  ║
║   ❌ docs/operations/playbooks/incident-response.md        ║
║                                                            ║
║ SRE (required for production):                             ║
║   ❌ docs/sre/slo-definitions.md                           ║
║   ❌ docs/sre/monitoring.md                                ║
║                                                            ║
║ Quick fix:                                                 ║
║   /project:docs operations   - Generate operations docs    ║
║   /project:docs sre          - Generate SRE docs           ║
╚════════════════════════════════════════════════════════════╝
```

## Arguments

$ARGUMENTS

- `--skip-tests`: Only check environment and docs, skip tests
- `--skip-docs`: Skip documentation checks (NOT RECOMMENDED)
- `--production`: Apply stricter production requirements
- `--staging`: Apply staging-level checks
- `--verbose`: Show all checks, not just failures
- `--fix`: Attempt to fix common issues
- `--docs-only`: Only run documentation verification
