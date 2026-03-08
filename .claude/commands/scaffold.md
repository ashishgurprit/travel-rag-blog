---
description: Generate boilerplate for new features/components
allowed-tools: ["Read", "Write", "Bash", "Glob"]
---

# Scaffold New Feature

Generate boilerplate files following project conventions.

## Instructions

### Phase 1: Detect Project Type

Analyze project structure to determine:
- Language (TypeScript, Python, Go, etc.)
- Framework (React, Next.js, FastAPI, etc.)
- Existing patterns (file naming, folder structure)

### Phase 1.5: Check Existing Components (MANDATORY)

**STOP. Before generating any boilerplate, check if it already exists.**

1. Read `.claude/COMPONENT_REGISTRY.md`
2. Search for the feature type being scaffolded
3. If a matching component exists:
   - Show the user what's available with a summary
   - Offer: "Use existing [component], adapt it, or scaffold fresh?"
   - If using existing: copy templates from the component's templates/ directory
4. Only scaffold fresh if NO matching component exists or user explicitly chooses fresh

### Phase 2: Parse Request

Feature to scaffold: $ARGUMENTS

Determine type:
- `component` - UI component
- `service` - Business logic service
- `api` - API endpoint/route
- `model` - Data model/schema
- `util` - Utility function
- `hook` - React hook
- `test` - Test file

### Phase 3: Generate Files

**For React Component:**
```
src/components/[FeatureName]/
├── index.ts              # Public exports
├── [FeatureName].tsx     # Main component
├── [FeatureName].test.tsx # Tests
├── [FeatureName].styles.ts # Styles (if CSS-in-JS)
└── types.ts              # Type definitions
```

**For API Endpoint:**
```
src/api/[feature]/
├── index.ts              # Route exports
├── [feature].routes.ts   # Route definitions
├── [feature].handlers.ts # Request handlers
├── [feature].schemas.ts  # Validation schemas
└── [feature].test.ts     # Tests
```

**For Service:**
```
src/services/[feature]/
├── index.ts              # Public exports
├── [feature].service.ts  # Main service
├── [feature].types.ts    # Type definitions
└── [feature].test.ts     # Tests
```

**For Python:**
```
src/[feature]/
├── __init__.py           # Public exports
├── [feature].py          # Main module
├── models.py             # Data models
└── test_[feature].py     # Tests
```

### Phase 4: Add Boilerplate Content

Include:
- Proper imports based on project
- Type definitions with TODOs
- Basic test structure
- JSDoc/docstrings

### Phase 5: Update Exports

Add new feature to relevant index files.

## Output Format

```
╔════════════════════════════════════════════════════════════╗
║              SCAFFOLD COMPLETE                             ║
╠════════════════════════════════════════════════════════════╣
║ Feature: [name]                                            ║
║ Type:    [component/service/api/etc]                       ║
╠════════════════════════════════════════════════════════════╣
║ Files Created                                              ║
║   ✓ src/components/UserProfile/index.ts                   ║
║   ✓ src/components/UserProfile/UserProfile.tsx            ║
║   ✓ src/components/UserProfile/UserProfile.test.tsx       ║
║   ✓ src/components/UserProfile/types.ts                   ║
╠════════════════════════════════════════════════════════════╣
║ TODOs Added                                                ║
║   • Implement main component logic                         ║
║   • Add prop types                                         ║
║   • Write test cases                                       ║
╠════════════════════════════════════════════════════════════╣
║ Next: /project:implement [feature] to build it             ║
╚════════════════════════════════════════════════════════════╝
```

## Arguments

$ARGUMENTS

Examples:
- `component UserProfile` - React component
- `service PaymentService` - Business service
- `api /users` - API endpoint
- `hook useAuth` - React hook
