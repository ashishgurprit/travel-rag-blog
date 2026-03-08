---
description: Auto-generate documentation from codebase analysis
allowed-tools: ["Read", "Write", "Bash", "Glob", "Grep", "Task"]
---

# Documentation Generator

Analyze the codebase and auto-generate comprehensive documentation.

## What This Does

```
┌─────────────────────────────────────────────────────────────┐
│                 CODEBASE ANALYSIS                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Source Code ──────────────────────────────────────────────▶│
│    │                                                        │
│    ├── Routes/Controllers ──▶ API Documentation             │
│    ├── Models/Schema ──────▶ Database Documentation         │
│    ├── Components ─────────▶ Component Library              │
│    ├── Services ───────────▶ Architecture Docs              │
│    ├── Config Files ───────▶ Environment Docs               │
│    ├── package.json ───────▶ Dependency Analysis            │
│    └── Folder Structure ───▶ Project Overview               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Ignored Paths

These are automatically excluded from analysis:

```
.claude/
.git/
node_modules/
__pycache__/
.venv/
venv/
env/
.env*
*.pyc
*.log
dist/
build/
coverage/
.next/
.nuxt/
```

## Instructions

### Phase 1: Detect Project Type

```bash
# Detect project type and frameworks
echo "=== Detecting Project Type ==="

if [ -f "package.json" ]; then
    echo "Node.js project detected"
    # Check for frameworks
    grep -q "next" package.json && echo "  Framework: Next.js"
    grep -q "express" package.json && echo "  Framework: Express"
    grep -q "fastify" package.json && echo "  Framework: Fastify"
    grep -q "react" package.json && echo "  Framework: React"
    grep -q "vue" package.json && echo "  Framework: Vue"
    grep -q "angular" package.json && echo "  Framework: Angular"
fi

if [ -f "pyproject.toml" ] || [ -f "requirements.txt" ]; then
    echo "Python project detected"
    grep -q "fastapi\|FastAPI" requirements.txt pyproject.toml 2>/dev/null && echo "  Framework: FastAPI"
    grep -q "django\|Django" requirements.txt pyproject.toml 2>/dev/null && echo "  Framework: Django"
    grep -q "flask\|Flask" requirements.txt pyproject.toml 2>/dev/null && echo "  Framework: Flask"
fi

if [ -f "go.mod" ]; then
    echo "Go project detected"
fi

if [ -f "Cargo.toml" ]; then
    echo "Rust project detected"
fi
```

### Phase 2: Analyze Folder Structure

Generate project structure documentation:

```markdown
# Project Structure

## docs/architecture/structure.md

## Directory Overview

\`\`\`
project-root/
├── src/                    # Source code
│   ├── api/                # API routes (12 files)
│   ├── components/         # React components (34 files)
│   ├── services/           # Business logic (8 files)
│   ├── models/             # Database models (6 files)
│   └── utils/              # Utilities (15 files)
├── tests/                  # Test files (45 files)
├── public/                 # Static assets
└── config/                 # Configuration
\`\`\`

## Key Entry Points

| File | Purpose |
|------|---------|
| src/index.ts | Application entry point |
| src/api/routes.ts | API route definitions |
| src/app.tsx | React app root |
```

### Phase 3: Generate API Documentation

#### 3.1 Find API Routes

For **Express/Node.js**:
```bash
# Find route definitions
grep -r "router\.\(get\|post\|put\|patch\|delete\)" src/ --include="*.ts" --include="*.js"
grep -r "app\.\(get\|post\|put\|patch\|delete\)" src/ --include="*.ts" --include="*.js"
```

For **FastAPI/Python**:
```bash
# Find route definitions
grep -r "@app\.\(get\|post\|put\|patch\|delete\)" --include="*.py"
grep -r "@router\.\(get\|post\|put\|patch\|delete\)" --include="*.py"
```

For **Next.js API Routes**:
```bash
# Find API route files
find pages/api -name "*.ts" -o -name "*.js" 2>/dev/null
find app/api -name "route.ts" -o -name "route.js" 2>/dev/null
```

#### 3.2 Generate OpenAPI Spec

Create `docs/api/reference/openapi.yaml`:

```yaml
openapi: 3.0.3
info:
  title: [Project Name] API
  version: 1.0.0
  description: Auto-generated API documentation

servers:
  - url: http://localhost:3000
    description: Development server

paths:
  /api/users:
    get:
      summary: List users
      tags: [Users]
      responses:
        '200':
          description: Successful response
    post:
      summary: Create user
      tags: [Users]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateUser'
      responses:
        '201':
          description: User created

components:
  schemas:
    User:
      type: object
      properties:
        id:
          type: string
        email:
          type: string
        name:
          type: string
```

#### 3.3 Generate API Endpoint List

Create `docs/api/endpoints.md`:

```markdown
# API Endpoints

## Authentication
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | /api/auth/login | User login | No |
| POST | /api/auth/register | User registration | No |
| POST | /api/auth/logout | User logout | Yes |
| GET | /api/auth/me | Get current user | Yes |

## Users
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | /api/users | List all users | Yes (Admin) |
| GET | /api/users/:id | Get user by ID | Yes |
| PUT | /api/users/:id | Update user | Yes |
| DELETE | /api/users/:id | Delete user | Yes (Admin) |
```

### Phase 4: Generate Database Documentation

#### 4.1 Find Models/Schema

For **Prisma**:
```bash
cat prisma/schema.prisma 2>/dev/null
```

For **SQLAlchemy/Python**:
```bash
grep -r "class.*Base\|Column\|relationship" --include="*.py" src/models/
```

For **TypeORM**:
```bash
grep -r "@Entity\|@Column\|@ManyToOne" --include="*.ts" src/
```

For **Mongoose**:
```bash
grep -r "new Schema\|mongoose.model" --include="*.ts" --include="*.js" src/
```

#### 4.2 Generate Schema Documentation

Create `docs/architecture/database-schema.md`:

```markdown
# Database Schema

## Entity Relationship Diagram

\`\`\`
┌──────────────┐       ┌──────────────┐
│    Users     │       │    Posts     │
├──────────────┤       ├──────────────┤
│ id (PK)      │──────<│ id (PK)      │
│ email        │       │ user_id (FK) │
│ name         │       │ title        │
│ password     │       │ content      │
│ created_at   │       │ created_at   │
└──────────────┘       └──────────────┘
        │
        │       ┌──────────────┐
        └──────<│   Comments   │
                ├──────────────┤
                │ id (PK)      │
                │ user_id (FK) │
                │ post_id (FK) │
                │ content      │
                └──────────────┘
\`\`\`

## Tables

### users
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| email | VARCHAR(255) | UNIQUE, NOT NULL | User email |
| name | VARCHAR(100) | NOT NULL | Display name |
| password | VARCHAR(255) | NOT NULL | Hashed password |
| created_at | TIMESTAMP | DEFAULT NOW() | Creation timestamp |

### posts
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| user_id | UUID | FOREIGN KEY → users.id | Author |
| title | VARCHAR(255) | NOT NULL | Post title |
| content | TEXT | | Post content |
| created_at | TIMESTAMP | DEFAULT NOW() | Creation timestamp |
```

### Phase 5: Generate Component Documentation

#### 5.1 Find Components

For **React**:
```bash
# Find React components
find src -name "*.tsx" -o -name "*.jsx" | xargs grep -l "export.*function\|export default"
```

For **Vue**:
```bash
find src -name "*.vue"
```

#### 5.2 Generate Component Library

Create `docs/architecture/components.md`:

```markdown
# Component Library

## Layout Components

### `<Header />`
**Location**: `src/components/layout/Header.tsx`

**Props**:
| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| title | string | No | "App" | Page title |
| showNav | boolean | No | true | Show navigation |

**Usage**:
\`\`\`tsx
<Header title="Dashboard" showNav={true} />
\`\`\`

---

### `<Sidebar />`
**Location**: `src/components/layout/Sidebar.tsx`

**Props**:
| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| collapsed | boolean | No | false | Collapse sidebar |
| items | NavItem[] | Yes | - | Navigation items |

---

## Form Components

### `<Button />`
**Location**: `src/components/ui/Button.tsx`

**Variants**: `primary` | `secondary` | `danger` | `ghost`

**Props**:
| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| variant | string | No | "primary" | Button style |
| size | "sm" \| "md" \| "lg" | No | "md" | Button size |
| disabled | boolean | No | false | Disable button |
| onClick | () => void | No | - | Click handler |
```

### Phase 6: Generate Dependency Analysis

Create `docs/architecture/dependencies.md`:

```markdown
# Dependency Analysis

## Production Dependencies

### Core
| Package | Version | Purpose |
|---------|---------|---------|
| react | ^18.2.0 | UI framework |
| next | ^14.0.0 | React framework |
| typescript | ^5.0.0 | Type safety |

### API & Data
| Package | Version | Purpose |
|---------|---------|---------|
| axios | ^1.6.0 | HTTP client |
| @prisma/client | ^5.0.0 | Database ORM |
| zod | ^3.22.0 | Schema validation |

### Authentication
| Package | Version | Purpose |
|---------|---------|---------|
| next-auth | ^4.24.0 | Authentication |
| bcrypt | ^5.1.0 | Password hashing |

### UI
| Package | Version | Purpose |
|---------|---------|---------|
| tailwindcss | ^3.4.0 | CSS framework |
| @radix-ui/react-* | various | UI primitives |

## Dev Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| jest | ^29.0.0 | Testing |
| eslint | ^8.0.0 | Linting |
| prettier | ^3.0.0 | Formatting |

## Dependency Graph

\`\`\`
Application
├── next (framework)
│   ├── react
│   └── react-dom
├── @prisma/client (database)
│   └── prisma (dev)
├── next-auth (auth)
│   ├── @auth/prisma-adapter
│   └── bcrypt
└── tailwindcss (styling)
    └── postcss
\`\`\`

## Security Audit

Run `pnpm audit`, `npm audit`, or `pip audit` to check for vulnerabilities.

Last audit: [DATE]
Vulnerabilities: 0 critical, 0 high, 2 moderate
```

### Phase 7: Generate Environment Documentation

Create `docs/development/environment.md`:

```markdown
# Environment Configuration

## Required Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| DATABASE_URL | Yes | PostgreSQL connection string | postgresql://user:pass@localhost:5432/db |
| NEXTAUTH_SECRET | Yes | Auth encryption secret | random-32-char-string |
| NEXTAUTH_URL | Yes | Application URL | http://localhost:3000 |

## Optional Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| LOG_LEVEL | info | Logging verbosity |
| REDIS_URL | - | Redis connection (for caching) |
| SENTRY_DSN | - | Error tracking |

## Environment Files

| File | Purpose | Git Ignored |
|------|---------|-------------|
| .env | Local development | Yes |
| .env.example | Template for developers | No |
| .env.test | Test environment | Yes |
| .env.production | Production (on server) | Yes |

## Setup

\`\`\`bash
# Copy example env file
cp .env.example .env

# Edit with your values
nano .env

# Verify configuration
if [ -f "pnpm-lock.yaml" ]; then
    pnpm run validate-env
else
    npm run validate-env
fi
\`\`\`
```

### Phase 8: Generate README

Create/update `README.md` if minimal or missing:

```markdown
# [Project Name]

> [Auto-generated description based on package.json or pyproject.toml]

## Quick Start

\`\`\`bash
# Install dependencies
if [ -f "pnpm-lock.yaml" ]; then
    pnpm install
elif [ -f "yarn.lock" ]; then
    yarn install
else
    npm install  # or pip install -r requirements.txt
fi

# Setup environment
cp .env.example .env

# Run database migrations
if [ -f "pnpm-lock.yaml" ]; then
    pnpm run db:migrate
elif [ -f "yarn.lock" ]; then
    yarn run db:migrate
else
    npm run db:migrate
fi

# Start development server
if [ -f "pnpm-lock.yaml" ]; then
    pnpm run dev
elif [ -f "yarn.lock" ]; then
    yarn run dev
else
    npm run dev
fi
\`\`\`

## Tech Stack

- **Framework**: Next.js 14
- **Language**: TypeScript
- **Database**: PostgreSQL + Prisma
- **Auth**: NextAuth.js
- **Styling**: Tailwind CSS

## Project Structure

\`\`\`
src/
├── app/           # Next.js app router
├── components/    # React components
├── lib/           # Utilities and helpers
├── server/        # Server-side code
└── types/         # TypeScript types
\`\`\`

## Documentation

- [API Reference](docs/api/endpoints.md)
- [Database Schema](docs/architecture/database-schema.md)
- [Component Library](docs/architecture/components.md)
- [Environment Setup](docs/development/environment.md)

## Scripts

| Command | Description |
|---------|-------------|
| `pnpm run dev` (or `npm run dev`) | Start development server |
| `pnpm run build` (or `npm run build`) | Build for production |
| `pnpm run test` (or `npm run test`) | Run tests |
| `pnpm run lint` (or `npm run lint`) | Run linter |

## License

[LICENSE]
```

### Phase 9: Generate Architecture Overview

Create `docs/architecture/README.md`:

```markdown
# Architecture Overview

## System Context

\`\`\`
┌─────────────────────────────────────────────────────────────┐
│                        USERS                                 │
│                          │                                   │
│                          ▼                                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                   FRONTEND                           │    │
│  │              (Next.js / React)                       │    │
│  │                                                      │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │    │
│  │  │  Pages   │  │Components│  │  Hooks   │          │    │
│  │  └──────────┘  └──────────┘  └──────────┘          │    │
│  └─────────────────────┬───────────────────────────────┘    │
│                        │ API Calls                           │
│                        ▼                                     │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                   BACKEND                            │    │
│  │               (API Routes)                           │    │
│  │                                                      │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │    │
│  │  │  Auth    │  │ Business │  │  Data    │          │    │
│  │  │  Layer   │  │  Logic   │  │  Access  │          │    │
│  │  └──────────┘  └──────────┘  └──────────┘          │    │
│  └─────────────────────┬───────────────────────────────┘    │
│                        │                                     │
│           ┌────────────┼────────────┐                       │
│           ▼            ▼            ▼                       │
│     ┌──────────┐ ┌──────────┐ ┌──────────┐                 │
│     │ Database │ │  Redis   │ │ Storage  │                 │
│     │(Postgres)│ │ (Cache)  │ │  (S3)    │                 │
│     └──────────┘ └──────────┘ └──────────┘                 │
└─────────────────────────────────────────────────────────────┘
\`\`\`

## Request Flow

1. User makes request to frontend
2. Frontend calls API route
3. API validates authentication
4. Business logic processes request
5. Data layer interacts with database
6. Response flows back to user

## Key Patterns

- **Repository Pattern**: Data access abstraction
- **Service Layer**: Business logic encapsulation
- **Middleware**: Auth, logging, error handling
- **DTOs**: Type-safe data transfer

## External Integrations

| Service | Purpose | Docs |
|---------|---------|------|
| Stripe | Payments | [Link] |
| SendGrid | Email | [Link] |
| S3 | File storage | [Link] |
```

## Arguments

$ARGUMENTS

- **No args / `all`**: Generate all documentation
- **`api`**: Generate API documentation only
- **`database`**: Generate database schema docs only
- **`components`**: Generate component library only
- **`dependencies`**: Generate dependency analysis only
- **`architecture`**: Generate architecture overview only
- **`readme`**: Generate/update README only
- **`--force`**: Overwrite existing documentation
- **`--dry-run`**: Show what would be generated without writing

## Output

```
╔════════════════════════════════════════════════════════════╗
║              DOCUMENTATION GENERATED                        ║
╠════════════════════════════════════════════════════════════╣
║ Project: my-app                                            ║
║ Type: Next.js + TypeScript + Prisma                        ║
╠════════════════════════════════════════════════════════════╣
║ Generated:                                                 ║
║   ✓ docs/api/endpoints.md (24 endpoints)                   ║
║   ✓ docs/api/reference/openapi.yaml                        ║
║   ✓ docs/architecture/README.md                            ║
║   ✓ docs/architecture/structure.md                         ║
║   ✓ docs/architecture/database-schema.md (8 tables)        ║
║   ✓ docs/architecture/components.md (34 components)        ║
║   ✓ docs/architecture/dependencies.md                      ║
║   ✓ docs/development/environment.md (12 env vars)          ║
║   ✓ README.md (updated)                                    ║
╠════════════════════════════════════════════════════════════╣
║ Skipped (already exists):                                  ║
║   ○ docs/architecture/decisions/ (has content)             ║
║   ○ docs/operations/runbooks/ (has content)                ║
╠════════════════════════════════════════════════════════════╣
║ Manual review recommended:                                 ║
║   ⚠ 3 API endpoints have no descriptions                  ║
║   ⚠ 5 components missing prop documentation               ║
║   ⚠ DATABASE_URL format not validated                     ║
╠════════════════════════════════════════════════════════════╣
║ Next: Review generated docs, then /project:docs audit      ║
╚════════════════════════════════════════════════════════════╝
```

## What Gets Analyzed

| Source | Generates |
|--------|-----------|
| Route files (routes.ts, api/*.ts) | API endpoint docs |
| Prisma schema / SQLAlchemy models | Database schema |
| Component files (*.tsx, *.vue) | Component library |
| package.json / requirements.txt | Dependency analysis |
| .env.example | Environment docs |
| Folder structure | Architecture overview |
| Existing README | Enhanced README |

## What Gets Preserved

- Existing ADRs in `docs/architecture/decisions/`
- Existing runbooks in `docs/operations/`
- Manual documentation with content
- Custom additions to generated files (marked sections)
