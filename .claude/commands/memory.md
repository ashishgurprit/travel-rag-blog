---
description: View and update project memory
allowed-tools: ["Read", "Write", "Edit", "Bash"]
---

# Project Memory Management

View, update, and maintain project activity memory.

## When to Use

- To record a new script you created
- To record environment variables you added (names only!)
- To log significant project activities
- To view what's been recorded in project memory
- To check when the last post-mortem was done

## Usage

```
/project:memory              # Show memory summary
/project:memory add-script   # Record a new script
/project:memory add-env      # Record env var (name only)
/project:memory add-infra    # Record infrastructure change
/project:memory log          # Add activity log entry
/project:memory reset        # Reset post-mortem timestamp
```

## Instructions

### Default: Show Summary

If no arguments or unrecognized arguments, display current project memory state:

1. Read `.claude/PROJECT_MEMORY.md`
2. Display summary:

```
╔════════════════════════════════════════════════════════════╗
║                    PROJECT MEMORY                          ║
╠════════════════════════════════════════════════════════════╣
║ Project:          [Name from frontmatter]                  ║
║ Initialized:      YYYY-MM-DD                               ║
║ Last Post-Mortem: YYYY-MM-DD (N total) or "Never"          ║
╠════════════════════════════════════════════════════════════╣
║ Recorded Items:                                            ║
║   Scripts:        N items                                  ║
║   Env Vars:       N items (names only)                     ║
║   Infrastructure: N items                                  ║
║   Activity Log:   N entries                                ║
╠════════════════════════════════════════════════════════════╣
║ Recent Activities:                                         ║
║   • [Most recent 3 activity log entries]                   ║
╚════════════════════════════════════════════════════════════╝
```

### add-script

Record a new script that was created in the project.

1. Ask: "What is the script path? (e.g., scripts/deploy.sh)"
2. Ask: "What is its purpose? (brief description)"
3. Add row to **Scripts Created** table:
   ```markdown
   | [path] | [today's date] | [purpose] |
   ```
4. Confirm: "Recorded script: [path]"

### add-env

Record a new environment variable (name only, NEVER the value).

**Security Warning**: Display this before asking:
```
⚠️  SECURITY: Only the variable NAME will be stored.
    NEVER enter the actual value or secret.
```

1. Ask: "What is the variable name? (e.g., STRIPE_SECRET_KEY)"
2. Ask: "What is its purpose? (e.g., Payment processing)"
3. Ask: "Which environment? (dev/prod/both)"
4. Add row to appropriate **Environment Variables** section:
   ```markdown
   | [NAME] | [today's date] | [purpose] |
   ```
5. Confirm: "Recorded env var: [NAME] (name only, value NOT stored)"

### add-infra

Record infrastructure or deployment resource.

1. Ask: "What is the resource? (e.g., railway.app/my-project)"
2. Ask: "What type? (e.g., Hosting, Database, CDN, Storage)"
3. Ask: "Any notes? (optional)"
4. Add row to **Infrastructure & Deployments** table:
   ```markdown
   | [resource] | [type] | [today's date] | [notes] |
   ```
5. Confirm: "Recorded infrastructure: [resource]"

### log

Add a general activity log entry.

1. Ask: "What activity? (brief description)"
2. Ask: "How many files affected? (approximate)"
3. Add row to **Activity Log** table:
   ```markdown
   | [today's date] | [activity] | [files] |
   ```
4. Confirm: "Logged activity: [activity]"

### reset

Reset the post-mortem timestamp (use when starting a new development phase).

1. Confirm: "This will reset last_post_mortem to null. Continue? (y/n)"
2. If yes, update YAML frontmatter:
   - Set `last_post_mortem: null`
3. Confirm: "Post-mortem timestamp reset. Next post-mortem will analyze all recent history."

## Arguments

$ARGUMENTS

Parse for subcommand: `add-script`, `add-env`, `add-infra`, `log`, `reset`

If no subcommand or unrecognized, show the summary.

## Security Reminders

**CRITICAL - Do NOT record**:
- Actual secret values (API keys, passwords, tokens)
- Connection strings with credentials
- Private keys or certificates
- Any sensitive data

**ONLY record**:
- Variable NAMES (e.g., `STRIPE_SECRET_KEY`, not the key itself)
- File PATHS (e.g., `scripts/deploy.sh`)
- Purpose DESCRIPTIONS (e.g., "Payment processing")
- Resource identifiers (e.g., `railway.app/project-name`)

## Graceful Fallback

If `.claude/PROJECT_MEMORY.md` doesn't exist:

1. Display: "No project memory file found."
2. Offer: "Create one now? (y/n)"
3. If yes, create using the standard template with project name from CLAUDE.md
