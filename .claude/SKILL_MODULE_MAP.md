# Skill-to-Module Dependency Map & Gap Analysis

> **Generated**: 2026-03-06
> **Scope**: 187 skills, 23 domains
> **Purpose**: Full skill registry, domain categorization, auto-discovery audit, and architectural gap analysis

---

## Table of Contents

1. [Auto-Discovery Audit](#1-auto-discovery-audit)
2. [Skill Registry by Domain](#2-skill-registry-by-domain)
3. [Foundational Skill Dependencies](#3-foundational-skill-dependencies)
4. [Gap Analysis](#4-gap-analysis)
5. [Summary Statistics](#5-summary-statistics)

---

## 1. Auto-Discovery Audit

Auto-discovery requires each skill to have `SKILL.md` with YAML frontmatter (`---` block containing `name` and `description`).

### Status as of 2026-03-06

| Status | Count | Skills |
|---|---|---|
| ✅ OK (has SKILL.md + frontmatter) | **187** | All skills below |
| ❌ NO SKILL.md | **0** | (Fixed: journaling-cbt-universal, website-seo-optimizer, wordpress-seo-optimizer) |
| ❌ NO FRONTMATTER | **0** | — |
| 🗑️ Removed noise files | **1** | README-NEW-SKILLS.md |

**Coverage: 100%** — All 187 skills are auto-discoverable.

---

## 2. Skill Registry by Domain

### AI & Agents (28 skills)

| Skill | Description Summary |
|---|---|
| ai-agent-patterns | Production patterns for building LLM-powered agents |
| agent-evals-harbor | Agent evaluation framework with Harbor/TerminalBench |
| agent-memory-patterns | Three-tier agent memory architecture |
| aws-bedrock-agents | AWS Bedrock Agents patterns |
| browser-use-agent | LLM-driven browser automation |
| claude-agent-sdk | Claude Agent SDK patterns |
| computer-use-agents | LLM-controlled desktop and browser automation |
| constrained-llm-output | Token-level constrained generation |
| crewai-agents | CrewAI role-based multi-agent orchestration |
| deepagents-framework | Batteries-included agent harness |
| dspy-prompt-optimization | Stanford DSPy framework for prompt programming |
| flowise-builder | Flowise open-source LLM orchestration |
| genai-agent-patterns | Comprehensive GenAI agent patterns |
| google-adk | Google Agent Development Kit |
| langgraph-computer-use | LangGraph Computer Use agent patterns |
| langgraph-js | LangGraph for TypeScript/JavaScript |
| langgraph-persistence | Cross-backend checkpointing for LangGraph |
| langgraph-state-machines | LangGraph state graph patterns |
| langsmith-observability | LangSmith observability and tracing |
| llm-agent-middleware | Composable middleware layer for LLM agents |
| llm-conversation-management | Managing long-running LLM conversations |
| llm-fine-tuning | Fine-tuning LLMs with Unsloth and LLaMA-Factory |
| mcp-protocol | Model Context Protocol patterns |
| multi-agent-framework-comparison | Decision guide for multi-agent frameworks |
| ralph-mode-agents | Autonomous looping agent pattern |
| self-healing-agents | Self-healing and self-improving agent patterns |
| semantic-kernel | Microsoft Semantic Kernel patterns |
| skyvern-vision-automation | Vision-based browser automation |

### RAG & Search (9 skills)

| Skill | Description Summary |
|---|---|
| flag-embedding | BAAI FlagEmbedding / BGE model family |
| graphrag-enhanced-rag | Graph-enhanced RAG patterns |
| lightrag | LightRAG graph-based RAG |
| rag-advanced-indexing | Advanced RAG indexing: multi-vector, ColBERT |
| rag-cloud-run-deployer | RAG Cloud Run Deployer (FastAPI + ChromaDB) |
| rag-fusion-reranking | Multi-retrieval fusion and cross-encoder reranking |
| rag-query-transformation | Query rewriting and transformation |
| rag-routing-query-construction | Intelligent query routing and structured queries |
| rag-self-corrective | Self-corrective RAG: CRAG, Self-RAG, Adaptive RAG |
| search-universal | Production search and discovery patterns |
| semantic-chunking | Intelligent text chunking for LLM/RAG |
| sql-database-agent | AI agents for database exploration and querying |
| structured-llm-outputs | Guaranteed schema-valid JSON from LLMs |
| vision-language-models | Production Vision Language Model patterns |

### Cloudflare (10 skills)

| Skill | Description Summary |
|---|---|
| cloudflare-agents | Cloudflare Agents SDK — persistent agents |
| cloudflare-ai-edge | Cloudflare AI at the Edge |
| cloudflare-d1-database | Cloudflare D1 Database |
| cloudflare-durable-objects | Stateful services with Durable Objects |
| cloudflare-kv-caching | Workers KV for caching and sessions |
| cloudflare-oauth-provider | OAuth 2.1 provider on Cloudflare |
| cloudflare-pages-deployment | Cloudflare Pages deployment patterns |
| cloudflare-queues-workflows | Cloudflare Queues and Workflows |
| cloudflare-r2-storage | Cloudflare R2 Storage |
| cloudflare-security-hardening | Cloudflare security hardening |
| cloudflare-workers | Production Cloudflare Workers patterns |
| hono-edge-framework | Hono web framework on Cloudflare |

### Mobile (15 skills)

| Skill | Description Summary |
|---|---|
| app-store-optimization | App Store Optimization (ASO) for iOS/Android |
| capacitor-mobile-app | Capacitor cross-platform mobile apps |
| expo-managed-workflow | Expo managed workflow for React Native |
| mobile-ar-camera | Mobile AR and Camera features |
| mobile-attribution-analytics | Mobile attribution and analytics |
| mobile-biometric-auth | FaceID/TouchID/fingerprint authentication |
| mobile-communication | Real-time communication for mobile |
| mobile-gamification | Mobile gamification patterns |
| mobile-health-fitness | Mobile health and fitness features |
| mobile-home-screen-widgets | Home screen widgets |
| mobile-in-app-messaging | In-app messaging for React Native |
| mobile-native-payments | Native payment integrations |
| mobile-on-device-ai | On-device AI/ML |
| mobile-resilience | Offline sync, network status, crash reporting |
| mobile-ux-patterns | Production UX patterns for React Native/Expo |
| mobile-voice-interface | Voice interface for mobile |
| revenuecat-monetization | RevenueCat in-app subscriptions |

### WordPress (8 skills)

| Skill | Description Summary |
|---|---|
| cms-headless-universal | Headless CMS patterns (WordPress, Ghost, Sanity) |
| woocommerce-development | WooCommerce extension development |
| wordpress-content-publishing | WordPress REST API batch content publishing |
| wordpress-gutenberg-blocks | Custom Gutenberg block development |
| wordpress-modern-stack | Modern WordPress development (Bedrock, ACF) |
| wordpress-patterns | Core WordPress development patterns |
| wordpress-plugin-scaffold | WordPress plugin scaffold |
| wordpress-seo-optimizer | WordPress SEO/AEO/GEO optimization via REST API |

### Frontend & Web (12 skills)

| Skill | Description Summary |
|---|---|
| accessibility-wcag | WCAG 2.2 AA accessibility compliance |
| design-system | Design system patterns |
| design-tokens-generator | CSS custom properties / design tokens |
| electron-desktop-app | Electron desktop app development |
| elite-frontend-developer | Elite frontend developer best practices |
| headless-cms | Headless CMS selection and integration |
| multi-step-wizard-ui | Multi-step wizard/form UI with Zustand |
| nextjs-app-patterns | Next.js App Router production patterns |
| openapi-schema-design | OpenAPI 3.1 spec-first API design |
| performance | Performance optimization patterns |
| wix-app-framework | Wix app framework and CLI patterns |
| wix-bi-analytics | Wix BI analytics and event tracking |
| wix-cli-patterns | Wix CLI extension architecture |

### Backend & API (12 skills)

| Skill | Description Summary |
|---|---|
| api-integration-middleware | Patterns for consuming third-party APIs |
| api-patterns | Core API design and implementation patterns |
| background-jobs-universal | Background job processing |
| batch-processing | Production batch processing framework |
| caching-universal | Production caching strategies |
| database-patterns | Database patterns and best practices |
| fastapi-security-middleware | FastAPI application security |
| file-upload-universal | File upload patterns |
| node-http-sdk-connection-management | Node.js HTTP SDK connection pool management |
| rate-limiting-universal | API rate limiting patterns |
| websocket-universal | WebSocket real-time communication |
| n8n-workflow-automation | n8n workflow automation |

### Auth & Payments (6 skills)

| Skill | Description Summary |
|---|---|
| auth-universal | Universal authentication system |
| firebase-auth-universal | Firebase authentication |
| payment-processing-universal | Payment processing patterns |
| stripe-subscription-billing | Stripe subscription billing |
| ecommerce-universal | Production e-commerce integration |
| ghost-cms | Ghost CMS production patterns |

### DevOps & Infrastructure (8 skills)

| Skill | Description Summary |
|---|---|
| cicd-templates | Ready-to-use CI/CD configurations |
| client-project-scaffolding | New project scaffolding |
| deployment-lifecycle | Expert production release management |
| deployment-patterns | Deployment strategy patterns |
| launchd-scheduler | macOS launchd config-driven job scheduler |
| migration-upgrade-patterns | Migration and upgrade patterns |
| pnpm-migration | npm/yarn to pnpm migration |
| railway-deployment | Railway.app deployment |

### SEO & Marketing (14 skills)

| Skill | Description Summary |
|---|---|
| affiliate-monetization | Affiliate link management and monetization |
| conversion-rate-optimization | CRO patterns and A/B testing |
| crm-marketing-automation | CRM and marketing automation integration |
| cross-linking-strategy | Multi-brand cross-linking with deterministic rules |
| customer-retention-loyalty | Customer retention and churn prediction |
| faq-schema-generator | FAQ generation and FAQPage schema markup |
| google-ads-campaigns | Google Ads PPC/SEM campaigns |
| google-analytics-search-console | GA4 Data API and Search Console |
| google-business-profile | Google Business Profile management |
| keyword-research-clustering | Keyword research and topical clustering |
| link-graph-analyzer | Link graph analysis |
| meta-ads-campaigns | Meta (Facebook & Instagram) advertising |
| seo-geo-aeo | SEO + GEO (AI search) + AEO (answer engines) |
| utm-attribution-tracking | UTM parameter strategy and campaign tagging |
| website-seo-optimizer | Universal multi-platform SEO analysis |
| youtube-advertising | YouTube advertising campaigns |

### Content & Publishing (10 skills)

| Skill | Description Summary |
|---|---|
| blog-content-writer | Expert blog content writer (Australian focus) |
| blog-orchestrator | Multi-site blog orchestration CLI |
| content-silo-governance | Content silo governance and violation detection |
| gts-sydney-sme-marketing | GTS Sydney SME marketing strategy |
| linkedin-viral-posts | Viral LinkedIn post generator |
| podcast-rss-publishing | Podcast RSS feed generation |
| potentialz-blog-writer | Healthcare blog writer |
| smart-content-scheduler | Intelligent content scheduling |
| social-media-manager | Social media management system |
| social-post-templates | Social media post templates |
| universal-content-pipeline | Document-to-content conversion pipeline |
| web-copywriter-fortune100 | Fortune 100 web copywriter |

### Media & Audio (4 skills)

| Skill | Description Summary |
|---|---|
| audio-media-pipeline | End-to-end audio/media processing |
| image-model-routing | Multi-model image generation with tiered fallback |
| media-processing-universal | Production media processing |
| pdf-processing | PDF processing pipeline |
| yt-dlp-media-downloader | yt-dlp media download patterns |

### Communication (5 skills)

| Skill | Description Summary |
|---|---|
| email-universal | Email system (transactional + marketing) |
| notification-universal | Multi-channel notification system |
| responsive-email-templates | Production email template development |
| sms-universal | SMS integration |
| translation-pipeline | Production multi-provider translation |

### Security (3 skills)

| Skill | Description Summary |
|---|---|
| penetration-testing | Penetration testing patterns |
| security-owasp | OWASP security patterns |
| website-security-hardening | Website security hardening |

### Google Cloud & LangChain (5 skills)

| Skill | Description Summary |
|---|---|
| langchain-gemini | Google Gemini via LangChain |
| langchain-google-cloud | Google Cloud data services via LangChain |
| langchain-google-workspace | Google Workspace via LangChain |
| langchain-vertex-ai | Vertex AI via LangChain |
| google-vertex-ai-imagen | Vertex AI image generation |

### Testing & Quality (3 skills)

| Skill | Description Summary |
|---|---|
| e2e-testing | End-to-end testing |
| stagehand-browser-automation | TypeScript AI browser automation |
| testing-strategies | Testing strategy patterns |

### Brand & Design (4 skills)

| Skill | Description Summary |
|---|---|
| brand-identity-system | Brand identity system patterns |
| competitive-intelligence | Competitive intelligence and market research |
| graphic-designer | Expert graphic design |
| visual-design-consultant | Visual design consulting |

### Platform Practices (5 skills)

| Skill | Description Summary |
|---|---|
| atlassian-practices | Atlassian engineering practices |
| canva-practices | Canva engineering practices |
| google-engineering | Google engineering practices |
| local-business-launch-automation | Local business launch pipeline |
| sales-funnel-builder | End-to-end sales funnel architecture |

### Strategy & Methodology (7 skills)

| Skill | Description Summary |
|---|---|
| admin-business-ops-universal | Admin and business operations |
| journaling-cbt-universal | CBT journaling module for mental health apps |
| module-first-development | Module-first development methodology |
| monthly-research-update | Monthly research and update cycle |
| phased-app-delivery | Phased app delivery methodology |
| skill-advisor | Knowledge navigator for the skill library |
| skill-maintenance-lifecycle | Skill staleness detection and lifecycle management |
| strategic-plan | Strategic planning with 3D Decision Matrix |

### Multi-Provider & Integration (4 skills)

| Skill | Description Summary |
|---|---|
| multi-provider-pattern | Multi-provider service architecture with fallback |
| api-integration-middleware | Third-party API consumption middleware |
| stagehand-browser-automation | TypeScript AI browser automation |
| brand-identity-system | Brand identity across channels |

---

## 3. Foundational Skill Dependencies

Skills most commonly consumed as dependencies by other skills (high = more foundational):

| Rank | Skill | Referenced By | Role |
|---|---|---|---|
| 1 | **batch-processing** | google-analytics, crm, affiliate, vertex-imagen, wordpress-patterns | Data processing backbone |
| 2 | **auth-universal** | wix, nextjs, ecommerce, stripe, firebase | Auth backbone |
| 3 | **security-owasp** | client-scaffolding, migration, wordpress-patterns, railway | Security backbone |
| 4 | **deployment-patterns** | wix, nextjs, client-scaffolding, migration | Deploy backbone |
| 5 | **seo-geo-aeo** | nextjs, cms-headless, ecommerce, cro | SEO backbone |
| 6 | **analytics-universal** | stripe, ecommerce, cro | Analytics backbone |
| 7 | **payment-processing-universal** | stripe, wix, ecommerce | Payments backbone |
| 8 | **testing-strategies** | accessibility, client-scaffolding, migration | QA backbone |
| 9 | **notification-universal** | crm, stripe, responsive-email | Notifications backbone |
| 10 | **deployment-lifecycle** | client-scaffolding, wordpress-patterns, railway | Lifecycle backbone |

### Key Module Dependencies (from skills with documented module refs)

| Module | Referenced By Skills | Status |
|---|---|---|
| `unified-api-client` | google-analytics, crm, affiliate, stripe, wix, vertex-imagen, ecommerce | In use |
| `database-orm-patterns` | google-analytics, crm, affiliate, smart-scheduler, stripe, migration | In use |
| `wordpress-publisher` | smart-scheduler, cms-headless, ecommerce, wordpress-seo-optimizer | In use |
| `content-pipeline-orchestrator` | affiliate, smart-scheduler | In use |
| `scheduling-framework` | google-analytics, smart-scheduler | In use |
| `supabase-database-setup` | nextjs, client-scaffolding | In use |
| `eas-deployment` | client-scaffolding, migration | In use |
| `image-optimizer` | cms-headless, vertex-imagen | In use |
| `mobile-remote-config` | migration, cro | In use |
| `astro-blog-seo` | nextjs, cms-headless | In use |

---

## 4. Gap Analysis

### Skills Proposed in v1 Map That Now Exist ✅

All 5 proposed skills from the Feb 2026 map were built:

| Proposed Skill | Status |
|---|---|
| `ai-agent-patterns` | ✅ Built |
| `mobile-ux-patterns` | ✅ Built |
| `audio-media-pipeline` | ✅ Built |
| `mobile-communication` | ✅ Built |
| `mobile-resilience` | ✅ Built |

### Missing Module Reference (from v1 map)

| Referenced Name | Referenced By | Status |
|---|---|---|
| `webhook-universal` | ecommerce-universal | Still missing — fold into `background-jobs-universal` or create module |

### Proposed Modules Still Unbuilt (Priority 1-2 from v1 map)

| Proposed Module | Would Serve | Priority |
|---|---|---|
| `feature-flags` | cro, migration, stripe, ecommerce, wix | P1 |
| `webhook-handler` | ecommerce, stripe, wix, crm, smart-scheduler | P1 |
| `csv-data-processor` | affiliate, vertex-imagen, crm, google-analytics | P2 |
| `google-auth-provider` | google-analytics, vertex-imagen, cms-headless | P2 |
| `queue-manager` | smart-scheduler, vertex-imagen, crm, affiliate | P2 |

### New Domains Since v1 Map (skills added ~Feb–Mar 2026)

| Domain | New Skills Added |
|---|---|
| Cloudflare (full stack) | cloudflare-agents, cloudflare-ai-edge, cloudflare-d1, cloudflare-durable-objects, cloudflare-kv, cloudflare-oauth, cloudflare-pages, cloudflare-queues, cloudflare-r2, cloudflare-security, cloudflare-workers, hono-edge-framework |
| Google LangChain | langchain-gemini, langchain-google-cloud, langchain-google-workspace, langchain-vertex-ai |
| Advanced RAG | rag-advanced-indexing, rag-cloud-run-deployer, rag-fusion-reranking, rag-query-transformation, rag-routing-query-construction, rag-self-corrective, graphrag-enhanced-rag, lightrag, flag-embedding |
| Mobile expanded | mobile-ar-camera, mobile-attribution-analytics, mobile-gamification, mobile-health-fitness, mobile-home-screen-widgets, mobile-in-app-messaging, mobile-native-payments, mobile-on-device-ai, mobile-voice-interface |
| Content/Brand | brand-identity-system, competitive-intelligence, content-silo-governance, cross-linking-strategy, customer-retention-loyalty, link-graph-analyzer, sales-funnel-builder |
| LLM Infra | constrained-llm-output, llm-agent-middleware, llm-conversation-management, llm-fine-tuning, structured-llm-outputs, vision-language-models |

---

## 5. Summary Statistics

| Metric | v1 (Feb 2026) | v2 (Mar 2026) | Change |
|---|---|---|---|
| Total skills | 67 | **187** | +120 (+179%) |
| Auto-discoverable | ~67 (39 missing FM at peak) | **187 (100%)** | +120 |
| Domains | 14 | **23** | +9 |
| Noise files in skills/ | 1 | **0** | -1 |
| Orphan modules (no skill ref) | 35 | **~10** (most consumed by new skills) | -25 est. |
| Proposed skills delivered | 0 | **5/5** | 100% |
| Missing module refs | 1 | **1** (`webhook-universal`) | same |

### Key Takeaway

The ecosystem has grown 3x since the v1 map. All auto-discovery gaps are resolved. The 5 previously proposed skills (ai-agent-patterns, mobile-ux-patterns, audio-media-pipeline, mobile-communication, mobile-resilience) are all built. The only outstanding architectural item is the `webhook-handler` / `webhook-universal` module gap, which affects 5+ skills (ecommerce, stripe, wix, crm, smart-scheduler).
