---
description: Run the skill health check system to identify stale skills that need updating
---

# Skill Health Check

Run the skill health check system to identify skills that need updating.

## Instructions

1. Run the health check script:
   ```bash
   ./scripts/skill-health-check.sh
   ```

2. Review the output and identify:
   - 🔴 STALE skills that reference outdated API versions or deprecated patterns
   - ⚠️ REVIEW DUE skills approaching their review window

3. For each stale skill:
   - Web search for the latest version/docs of the referenced technology
   - Identify what changed since the skill's last update (breaking changes, new features, deprecations)
   - Update outdated code examples, API versions, and best practices
   - Preserve working patterns that haven't changed
   - Bump the skill's version number and Last Updated date
   - Add a note in the skill about what was updated

4. For batch updates:
   ```bash
   ./scripts/skill-health-check.sh --all-stale
   ```

## Arguments

- No args: Full health report
- `--stale`: Show only skills needing attention
- `--tier high`: Show only high-churn (API-dependent) skills
- `update <name>`: Focus on updating a specific skill

## Review Cadence Tiers

| Tier | Cycle | Trigger Keywords |
|------|-------|-----------------|
| HIGH | 90 days | API integrations, cloud platforms, frameworks |
| MEDIUM | 180 days | SEO, email, CRM, deployment, databases |
| LOW | 365 days | Methodology, branding, copywriting, design |

## Update Process

When updating a skill:
1. Research current state of the technology
2. Check for breaking changes, deprecations, new features
3. Update code examples to current API versions
4. Update best practices and recommendations
5. Bump version: `1.0.0` → `1.1.0` for content updates, `2.0.0` for major rewrites
6. Update `Last Updated` date
7. Commit with message: `chore: update <skill-name> to reflect <technology> v<X>`
