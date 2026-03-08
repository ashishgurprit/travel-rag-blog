---
description: Generate project documentation structure with templates
allowed-tools: ["Read", "Write", "Bash", "Glob", "Task"]
---

# Documentation Generator

Generate comprehensive project documentation structure with templates for all required documentation types.

## When to Use

- **Project kickoff**: Initialize documentation structure
- **Before post-mortem**: Ensure documentation is current
- **Pre-deployment**: Verify all docs are complete
- **Compliance audits**: Generate required documentation

## Documentation Categories

```
┌─────────────────────────────────────────────────────────────┐
│                  DOCUMENTATION PYRAMID                       │
├─────────────────────────────────────────────────────────────┤
│                         /\                                   │
│                        /  \   User-Facing                    │
│                       /    \  (guides, tutorials)            │
│                      /──────\                                │
│                     /        \                               │
│                    /          \ Operations                   │
│                   /            \ (runbooks, playbooks)       │
│                  /──────────────\                            │
│                 /                \                           │
│                /                  \ Technical                │
│               /                    \ (API, architecture)     │
│              /──────────────────────\                        │
│             /                        \                       │
│            /                          \ Foundation           │
│           /                            \ (ADRs, security)    │
│          /──────────────────────────────\                    │
└─────────────────────────────────────────────────────────────┘
```

## Instructions

### Phase 1: Analyze Project

Detect project type and existing documentation:

```bash
# Check for existing docs
ls -la docs/ 2>/dev/null || echo "No docs folder"

# Detect project type
if [ -f "package.json" ]; then echo "Node.js project"; fi
if [ -f "pyproject.toml" ] || [ -f "requirements.txt" ]; then echo "Python project"; fi
if [ -f "go.mod" ]; then echo "Go project"; fi
if [ -f "Cargo.toml" ]; then echo "Rust project"; fi

# Check for existing OpenAPI
ls -la **/openapi*.yaml **/swagger*.yaml 2>/dev/null

# Check for existing ADRs
ls -la docs/architecture/decisions/ docs/adr/ 2>/dev/null
```

### Phase 2: Create Structure

Based on `$ARGUMENTS`, create appropriate structure:

**`init` or no args**: Create full structure
**`category`**: Create specific category only
**`audit`**: Check completeness without creating

#### Full Structure:

```
docs/
├── README.md                    # Documentation index
│
├── architecture/
│   ├── README.md                # Architecture overview
│   ├── decisions/               # ADRs
│   │   ├── template.md
│   │   └── 001-initial-architecture.md
│   ├── diagrams/
│   │   └── system-context.md
│   └── design-docs/
│       └── template.md
│
├── api/
│   ├── README.md                # API overview
│   ├── reference/
│   │   └── openapi.yaml
│   ├── guides/
│   │   └── authentication.md
│   └── changelog.md
│
├── operations/
│   ├── README.md                # Operations overview
│   ├── runbooks/
│   │   ├── template.md
│   │   ├── deployment.md
│   │   └── rollback.md
│   ├── playbooks/
│   │   ├── template.md
│   │   └── incident-response.md
│   └── on-call.md
│
├── security/
│   ├── README.md                # Security overview
│   ├── threat-model.md
│   ├── access-control.md
│   ├── incident-response.md
│   └── compliance/
│       ├── soc2-mapping.md
│       └── gdpr-mapping.md
│
├── sre/
│   ├── README.md                # SRE overview
│   ├── slo-definitions.md
│   ├── monitoring.md
│   ├── alerting.md
│   ├── capacity.md
│   └── post-incident/
│       └── template.md
│
├── development/
│   ├── README.md                # Dev overview
│   ├── contributing.md
│   ├── style-guide.md
│   ├── testing.md
│   ├── local-setup.md
│   └── ci-cd.md
│
├── product/
│   ├── README.md                # Product overview
│   ├── prds/
│   │   └── template.md
│   ├── releases/
│   │   └── template.md
│   ├── roadmap.md
│   └── feature-flags.md
│
├── user/
│   ├── README.md                # User docs overview
│   ├── getting-started.md
│   ├── guides/
│   ├── tutorials/
│   ├── faq.md
│   └── troubleshooting.md
│
├── infrastructure/
│   ├── README.md                # Infra overview
│   ├── network.md
│   ├── environments.md
│   ├── disaster-recovery.md
│   └── cost-analysis/
│
└── knowledge/
    ├── README.md                # Knowledge base
    ├── lessons-learned/         # Links to .claude/LESSONS*.md
    ├── decisions/               # Non-architectural decisions
    ├── glossary.md
    └── onboarding.md
```

### Phase 3: Generate Templates

Create templates for each document type. Key templates:

#### ADR Template (docs/architecture/decisions/template.md):
```markdown
# ADR-XXX: [Title]

## Status
[Proposed | Accepted | Deprecated | Superseded]

## Context
[What is the issue that we're seeing that is motivating this decision?]

## Decision
[What is the change that we're proposing/doing?]

## Consequences
### Positive
- [Good thing 1]

### Negative
- [Trade-off 1]

### Neutral
- [Side effect 1]

## Alternatives Considered
| Alternative | Pros | Cons | Why Not |
|-------------|------|------|---------|
| [Option 1]  |      |      |         |

## References
- [Link to design doc]
- [Link to relevant code]
```

#### Runbook Template (docs/operations/runbooks/template.md):
```markdown
# Runbook: [Task Name]

## Overview
**Purpose**: [What this runbook does]
**Owner**: [Team/Person]
**Last Updated**: [Date]
**Estimated Time**: [Duration]

## Prerequisites
- [ ] [Access requirement]
- [ ] [Tool requirement]

## Steps

### Step 1: [Name]
```bash
# Command(s)
```
**Expected output**: [What you should see]
**If this fails**: [What to do]

### Step 2: [Name]
...

## Verification
- [ ] [Check 1]
- [ ] [Check 2]

## Rollback
If something goes wrong:
1. [Rollback step 1]
2. [Rollback step 2]

## Escalation
| Level | Contact | When |
|-------|---------|------|
| L1    | [Name]  | [Condition] |
| L2    | [Name]  | [Condition] |
```

#### Threat Model Template (docs/security/threat-model.md):
```markdown
# Threat Model: [System Name]

## System Overview
[Brief description and diagram]

## Assets
| Asset | Sensitivity | Location |
|-------|-------------|----------|
| User PII | High | PostgreSQL |
| API Keys | Critical | Vault |

## Threat Actors
| Actor | Motivation | Capability |
|-------|------------|------------|
| External Attacker | Financial | Medium |
| Insider | Various | High |

## STRIDE Analysis

### Spoofing
| Threat | Mitigation | Status |
|--------|------------|--------|
| [Threat] | [Control] | [Done/Pending] |

### Tampering
...

### Repudiation
...

### Information Disclosure
...

### Denial of Service
...

### Elevation of Privilege
...

## Attack Surfaces
| Surface | Exposure | Controls |
|---------|----------|----------|
| Public API | Internet | WAF, Rate Limiting |
| Admin Panel | VPN Only | MFA, IP Whitelist |

## Open Issues
- [ ] [Issue needing resolution]
```

#### SLO Template (docs/sre/slo-definitions.md):
```markdown
# Service Level Objectives

## Service: [Name]

### Availability SLO
- **Target**: 99.9% uptime
- **Measurement**: HTTP 2xx responses / total requests
- **Window**: 30-day rolling
- **Error Budget**: 43.2 minutes/month

### Latency SLO
- **Target**: p99 < 500ms
- **Measurement**: Server-side response time
- **Window**: 30-day rolling

### Quality SLO
- **Target**: <0.1% error rate
- **Measurement**: 5xx responses / total requests
- **Window**: 7-day rolling

## Error Budget Policy

| Remaining Budget | Action |
|------------------|--------|
| >50% | Normal development |
| 25-50% | Reduce risky deployments |
| 10-25% | Focus on reliability |
| <10% | Freeze features, fix reliability |

## SLIs (Indicators)

| SLI | Good Event | Total Events | Data Source |
|-----|------------|--------------|-------------|
| Availability | status < 500 | all requests | Access logs |
| Latency | duration < 500ms | all requests | APM |
```

### Phase 4: Check Project-Specific Needs

Based on detected integrations, add relevant docs:

| Detection | Add Documentation |
|-----------|------------------|
| Firebase/Auth0 | docs/security/authentication.md |
| Stripe/Payments | docs/operations/runbooks/payment-reconciliation.md |
| PostgreSQL | docs/infrastructure/database.md |
| Kubernetes | docs/infrastructure/kubernetes.md |
| GraphQL | docs/api/schema.md |

### Phase 5: Generate Index

Create `docs/README.md` with links to all docs and status.

### Phase 6: Audit Mode

If `$ARGUMENTS` contains `audit`:

```
╔════════════════════════════════════════════════════════════╗
║                 DOCUMENTATION AUDIT                         ║
╠════════════════════════════════════════════════════════════╣
║ Category        │ Status     │ Files │ Last Updated        ║
╠═════════════════╪════════════╪═══════╪═════════════════════╣
║ Architecture    │ ✓ Complete │ 5     │ 2024-12-20         ║
║ API             │ ⚠ Partial  │ 2/4   │ 2024-12-15         ║
║ Operations      │ ✗ Missing  │ 0     │ -                   ║
║ Security        │ ✓ Complete │ 4     │ 2024-12-18         ║
║ SRE             │ ⚠ Partial  │ 1/5   │ 2024-12-10         ║
║ Development     │ ✓ Complete │ 5     │ 2024-12-22         ║
║ Product         │ ⚠ Partial  │ 2/4   │ 2024-12-01         ║
║ User            │ ✗ Missing  │ 0     │ -                   ║
║ Infrastructure  │ ⚠ Partial  │ 1/4   │ 2024-11-30         ║
║ Knowledge       │ ✓ Complete │ 3     │ 2024-12-22         ║
╠════════════════════════════════════════════════════════════╣
║ Overall: 6/10 categories complete (60%)                    ║
║                                                            ║
║ Priority gaps:                                             ║
║   1. Operations - No runbooks (CRITICAL for production)    ║
║   2. User docs - No user documentation                     ║
║   3. SRE - Missing SLO definitions                         ║
╠════════════════════════════════════════════════════════════╣
║ Run: /project:docs operations  to create operations docs   ║
╚════════════════════════════════════════════════════════════╝
```

## Arguments

$ARGUMENTS

### Structure Commands (create empty templates)
- **No args / `init`**: Create full documentation structure
- **`audit`**: Check documentation completeness
- **`architecture`**: Create architecture docs only
- **`api`**: Create API docs only
- **`operations`**: Create operations docs only
- **`security`**: Create security docs only
- **`sre`**: Create SRE docs only
- **`development`**: Create development docs only
- **`product`**: Create product docs only
- **`user`**: Create user docs only
- **`infrastructure`**: Create infrastructure docs only
- **`knowledge`**: Create knowledge base only
- **`--force`**: Overwrite existing templates

### Generate Commands (auto-generate from codebase)
- **`generate`**: Auto-generate ALL documentation from codebase analysis
- **`generate api`**: Generate API docs from routes/endpoints
- **`generate database`**: Generate schema docs from models
- **`generate components`**: Generate component library from React/Vue files
- **`generate dependencies`**: Generate dependency analysis
- **`generate architecture`**: Generate architecture overview
- **`generate readme`**: Generate/update README

**See `/project:docs-generate` for full codebase analysis documentation.**

## Output

```
╔════════════════════════════════════════════════════════════╗
║                 DOCUMENTATION CREATED                       ║
╠════════════════════════════════════════════════════════════╣
║ Structure: docs/ (10 categories)                           ║
║ Templates: 15 files created                                ║
║ Preserved: 3 existing files                                ║
╠════════════════════════════════════════════════════════════╣
║ Next Steps:                                                ║
║   1. Review docs/README.md for overview                    ║
║   2. Start with docs/architecture/decisions/               ║
║   3. Add runbooks before production                        ║
║   4. Run /project:docs audit before deployment             ║
╠════════════════════════════════════════════════════════════╣
║ Workflow Integration:                                      ║
║   • /project:review   - Now checks doc updates            ║
║   • /project:pre-deploy - Verifies doc completeness       ║
║   • /project:post-mortem - Creates PIR in docs/sre/       ║
╚════════════════════════════════════════════════════════════╝
```

## Cloud Provider Alignment

This structure aligns with:

| Framework | Covered By |
|-----------|------------|
| AWS Well-Architected | architecture/, security/, sre/, operations/ |
| GCP Architecture Framework | architecture/, sre/, security/ |
| Azure Well-Architected | All categories |
| SOC 2 Type II | security/, operations/, sre/ |
| ISO 27001 | security/, operations/, infrastructure/ |
| GDPR | security/compliance/, knowledge/ |
