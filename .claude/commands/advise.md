---
description: Knowledge navigator — recommends relevant skills, lessons, and commands for any task
allowed-tools: ["Read", "Glob", "Grep", "Bash"]
---

# Capability Advisor

Analyze a task description and recommend the most relevant skills, lessons, commands, and workflow from the Streamlined Development system.

## Usage

```
/project:advise <task description>
```

## Instructions

### Step 0: Handle Empty Arguments

If `$ARGUMENTS` is empty or missing, ask the user:

```
What are you working on? Describe the task and I'll recommend the right skills, lessons, and commands.

Examples:
  /project:advise Build a landing page with Google Ads for GTS
  /project:advise Deploy a Next.js app to Cloudflare with CI/CD
  /project:advise Create a content pipeline for 4 blogs
  /project:advise Build a RAG chatbot with LangGraph
  /project:advise Set up marketing for a new SaaS product
```

Then stop and wait for the user to provide a task description.

### Step 1: Load the Capability Index + Supporting Maps

Read all four reference files in parallel:

```
.claude/skills/skill-advisor/CAPABILITY_INDEX.md   — skill descriptions & categories
.claude/skills/skill-advisor/SKILL_GROUPS.md       — 23 domain groups covering all 183 skills
.claude/skills/skill-advisor/SKILL_MODULE_MAP.md   — skill → key npm/pip packages
.claude/skills/skill-advisor/MODULE_LESSON_MAP.md  — module → relevant lessons & gotchas
```

Also read:
- `.claude/LESSONS.md` — for full lesson text if needed

If CAPABILITY_INDEX.md does not exist, inform the user:
```
The capability index has not been built yet. Run:
  ./scripts/build-capability-index.sh
Then try again.
```

### Step 2: Analyze the Task

Parse the task description from `$ARGUMENTS`. Extract:

1. **Domain keywords**: Identify technologies, platforms, and concepts mentioned
   - Examples: "React", "Google Ads", "Cloudflare", "mobile", "blog", "SEO", "RAG"

2. **Development phase**: Determine the phase:
   - Planning (research, architecture, strategy)
   - Building (implementation, coding, integration)
   - Testing (QA, validation, benchmarks)
   - Deploying (CI/CD, hosting, monitoring)
   - Marketing (campaigns, content, growth)
   - Maintaining (debugging, optimization, updates)

3. **Project context** (if available): Check for:
   - `package.json` — tech stack detection
   - `CLAUDE.md` — project-specific context
   - `.claude/PROJECT_MEMORY.md` — recent activity

### Step 3: Match Group First, Then Individual Skills

**3a. Match to Skill Group(s) — always do this first**

Using SKILL_GROUPS.md, identify which 1-2 groups the task belongs to by matching domain keywords against each group's trigger keywords. State the group(s) upfront in your recommendation — this gives the developer the full domain context even before picking individual skills.

**3b. Score individual skills within the matched group(s)**

Using the capability index, score skills from the matched group(s):

**Scoring weights:**
- Direct keyword match in skill name or triggers: **+10 points**
- In-group match (skill is in the matched group): **+5 points**
- Partial keyword match in description: **+3 points**
- Cross-reference from a matched skill: **+2 points**
- Phase-appropriate skill: **+2 points**

**Tier assignment:**
- Score >= 10: PRIMARY (directly relevant)
- Score 5-9: SUPPORTING (tangentially useful)
- Score < 5: Skip

**3c. Auto-lookup modules for PRIMARY skills**

For each PRIMARY skill, look up its key packages in SKILL_MODULE_MAP.md.
Include these as the "Install" line in your recommendation.

**3d. Auto-lookup lessons for those modules**

For each module from step 3c, look up relevant lessons in MODULE_LESSON_MAP.md.
Surface the top 1-3 gotchas as the "Heads up" section — these are real footguns from production.

**Command matching:**
- Always include `/project:plan` for planning-phase tasks
- Always include `/project:implement` for building-phase tasks
- Always include `/project:pre-deploy` for deployment-phase tasks
- Always include `/project:post-mortem` for debugging/maintenance tasks
- Include `/project:explore` if the task involves understanding existing code
- Include `/project:scaffold` if the task involves creating new components
- Include `/project:test-fix` if the task involves fixing tests
- Include `/project:review` if the task involves code review

### Step 4: Generate the Recommendation

**Output format — piecemeal, sequential, one step at a time.**

The goal is actionable guidance, not a catalogue. Give the developer one thing to do right now, then reveal the next step when they're ready.

**Output this compact format:**

```
**Task**: <task description>
**Group**: `<stack-group-name>` — <one-line group description>

**Start here — Step 1 of N:**
  Skill: `<top-matching-skill>`
  Why: <one sentence explaining why this is the first thing to do>
  Install: `pip install X Y` / `npm install X Y`  ← from SKILL_MODULE_MAP
  Action: <concrete first action>

**What comes next (queue):**
  → Step 2: `<skill-2>` — <5-word reason>
  → Step 3: `<skill-3>` — <5-word reason>

**Heads up:** <1-2 sentences from MODULE_LESSON_MAP for the modules in Step 1 — real production gotchas only>

Say **"next"** when you're done with Step 1 and I'll give you the full details for Step 2.
```

**Rules for this format:**
- N = total number of steps in the queue (2-4 max)
- Step 1 always has the full detail block (Skill + Why + Action)
- Steps 2-N show only skill name + 5-word reason (reveal details when user asks)
- NEVER show all steps in full detail at once
- NEVER show SUPPORTING SKILLS, LESSONS, COMMANDS as separate sections — fold them into the step details if relevant
- "Heads up" is optional — only include if there's a real gotcha (e.g., a known footgun from LESSONS.md)
- If the task is single-skill (N=1), skip the queue and just give Step 1 + say "That's all you need"

**Example output for "add rate limiting to my FastAPI app":**

```
**Task**: add rate limiting to my FastAPI app
**Group**: `stack-backend` — Backend & API (FastAPI, rate limiting, middleware)

**Start here — Step 1 of 2:**
  Skill: `fastapi-security-middleware`
  Why: Covers slowapi setup, proxy-aware IP extraction, and CORS+rate-limit interaction in one place — the complete stack for FastAPI.
  Install: `pip install fastapi slowapi pydantic starlette`
  Action: Invoke the skill and follow the "Complete main.py Template" section.

**What comes next (queue):**
  → Step 2: `rate-limiting-universal` — Redis token bucket, tier limits

**Heads up:** slowapi requires `request: Request` as a param on every rate-limited route, or you'll get a runtime error.

Say **"next"** when you're done with Step 1 and I'll give you the full details for Step 2.
```

### Step 5: When User Says "next"

When the user responds with "next" (or "continue", "next step", "step 2", etc.):

Give the full detail block for the next step:

```
**Step N of M — `<skill-name>`:**
  Why: <one sentence>
  Action: <concrete action>
  Key patterns: <2-3 bullet points of the most important things from this skill>

[Queue remaining:]
  → Step N+1: `<skill>` — <5-word reason>  [if any remain]

Say **"next"** to continue, or **"done"** if you're finished.
```

## Matching Rules

### Technology-to-Skill Mapping (Quick Reference)

These are high-confidence direct mappings:

| Keyword | Primary Skill |
|---------|---------------|
| React, Next.js, frontend | elite-frontend-developer, nextjs-app-patterns |
| Capacitor, mobile app, iOS, Android | capacitor-mobile-app, mobile-ux-patterns |
| Cloudflare, Workers, Pages | cloudflare-workers, cloudflare-pages-deployment |
| Google Ads, PPC, SEM | conversion-rate-optimization |
| SEO, search optimization | seo-geo-aeo, website-seo-optimizer |
| RAG, retrieval, embeddings | rag-advanced-indexing, rag-fusion-reranking |
| LangGraph, agents, LLM | ai-agent-patterns, langgraph-state-machines |
| Blog, content pipeline | blog-orchestrator, universal-content-pipeline |
| WordPress | wordpress-patterns, wordpress-content-publishing |
| Email, newsletter | responsive-email-templates, email-universal |
| Authentication, OAuth | auth-universal, firebase-auth-universal |
| Deployment, CI/CD | deployment-patterns, cicd-templates |
| Testing, E2E | testing-strategies, e2e-testing |
| Database, SQL | database-patterns, sql-database-agent |
| Payment, Stripe | payment-processing-universal, stripe-subscription-billing |
| GTS, Cloud Geeks, Cosmos | gts-sydney-sme-marketing |
| Branding, design system | design-system, design-tokens-generator |
| LinkedIn, social media | linkedin-viral-posts, social-post-templates |
| YouTube, video ads | youtube-advertising |
| Copy, landing page | web-copywriter-fortune100 |
| UTM, attribution, tracking | utm-attribution-tracking |
| GA4, analytics | google-analytics-search-console, analytics-universal |
| CRM, marketing automation | crm-marketing-automation |
| Security, OWASP | security-owasp, website-security-hardening |
| Docker, deploy | deployment-lifecycle, deployment-patterns |
| Wix | wix-app-framework, wix-cli-patterns |
| Podcast, RSS | podcast-rss-publishing |
| PDF, document | pdf-processing |
| Accessibility, WCAG | accessibility-wcag |
| Translation, i18n | translation-pipeline |
| MCP, tool protocol | mcp-protocol |
| App Store, ASO | app-store-optimization |
| Ecommerce, Shopify | ecommerce-universal |
| Affiliate, monetization | affiliate-monetization |
| RevenueCat, in-app purchase | revenuecat-monetization |
| Claude SDK, agent SDK | claude-agent-sdk |
| Electron, desktop | electron-desktop-app |

### Cross-Reference Boosting

If a primary skill references other skills (via `consumes_modules` or mentions in its description), those referenced skills get a +2 boost. Common cross-references:

- `ai-agent-patterns` references: `rag-advanced-indexing`, `semantic-chunking`, `llm-conversation-management`
- `blog-orchestrator` references: `blog-content-writer`, `seo-geo-aeo`, `wordpress-content-publishing`
- `capacitor-mobile-app` references: `mobile-ux-patterns`, `mobile-resilience`, `app-store-optimization`
- `gts-sydney-sme-marketing` references: `conversion-rate-optimization`, `utm-attribution-tracking`, `google-analytics-search-console`
- `elite-frontend-developer` references: `nextjs-app-patterns`, `design-system`, `performance`, `accessibility-wcag`

## Important Notes

- Limit PRIMARY skills to 3-6 (too many dilutes the recommendation)
- Limit SUPPORTING skills to 3-8
- Limit LESSONS to 3-5 most relevant
- Always provide a RECOMMENDED APPROACH with concrete steps
- The approach should reference specific skills by name
- If the task spans multiple domains, organize the approach by phase
- If no skills match at all, say so honestly and suggest creating a new skill
