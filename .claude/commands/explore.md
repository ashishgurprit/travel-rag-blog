---
description: Explore and understand codebase without writing code
allowed-tools: ["Read", "Glob", "Grep", "Bash", "Task"]
---

# Explore Codebase

Deep dive into a codebase area to understand architecture, patterns, and constraints.

## Critical Rule

**DO NOT WRITE CODE** - This is research only.

## When to Use

- Starting work on an unfamiliar codebase
- Before planning a new feature
- Understanding how existing features work
- Finding integration points

## Instructions

### Phase 1: Identify Scope

Parse the exploration target: $ARGUMENTS

- What area/feature to explore?
- What questions need answering?

### Phase 2: Structural Analysis

```bash
# Get directory structure
find . -type f -name "*.ts" | head -50

# Find entry points
grep -r "main\|index\|app" --include="*.ts" -l

# Find configuration
ls -la *.json *.yaml *.toml 2>/dev/null
```

### Phase 3: Deep Dive

1. **Entry Points**: Where does execution start?
2. **Data Flow**: How does data move through the system?
3. **Dependencies**: What external services/libraries?
4. **Patterns**: What conventions are used?

### Phase 4: Document Findings

## Output Format

```
╔════════════════════════════════════════════════════════════╗
║              EXPLORATION: [Topic]                          ║
╠════════════════════════════════════════════════════════════╣
║ Overview                                                   ║
║   [High-level summary]                                     ║
╠════════════════════════════════════════════════════════════╣
║ Key Files                                                  ║
║   • src/main.ts - Entry point                              ║
║   • src/api/ - API routes                                  ║
║   • src/services/ - Business logic                         ║
╠════════════════════════════════════════════════════════════╣
║ Architecture                                               ║
║   [How components connect]                                 ║
╠════════════════════════════════════════════════════════════╣
║ Patterns Used                                              ║
║   • Repository pattern for data access                     ║
║   • Dependency injection                                   ║
╠════════════════════════════════════════════════════════════╣
║ Integration Points                                         ║
║   • Database: PostgreSQL via Prisma                        ║
║   • Auth: Firebase                                         ║
║   • Payments: Stripe                                       ║
╠════════════════════════════════════════════════════════════╣
║ Questions/Unclear                                          ║
║   • [Things needing clarification]                         ║
╠════════════════════════════════════════════════════════════╣
║ Next: /project:plan [feature] to plan implementation       ║
╚════════════════════════════════════════════════════════════╝
```

## Arguments

$ARGUMENTS

- Area to explore (e.g., "authentication", "payments", "api")
- If empty, explore overall architecture
