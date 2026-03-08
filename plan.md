# Implementation Plan: Travel RAG Search Engine MVP ("Perplexity for Travel")

## Overview

Build a depth-first travel RAG search engine covering 5 destinations (Japan, Thailand, Italy, Turkey, South Korea). Users ask natural-language travel questions and receive cited, streaming answers with one contextual affiliate link per response. Backend: FastAPI on Railway. Vector DB: Pinecone. Embedding: `intfloat/multilingual-e5-large`. LLM: Claude Sonnet 4.5 (streaming). Frontend: Next.js (web-first, mobile-responsive). Revenue: Affiliate-first (Klook, Booking.com, Wise).

---

## Success Criteria

- [ ] Pinecone index populated with ≥100K vectors across 5 destinations
- [ ] `/api/ask` endpoint returns streamed answers in <3s (p50), with source citations
- [ ] Cosine similarity confidence threshold: reject retrieval if similarity < 0.75
- [ ] Contextual affiliate link injected into every answer (1 per response max)
- [ ] Expandable source cards with YouTube timestamp deep-links render in UI
- [ ] FTC-compliant affiliate disclosure appears on every response
- [ ] Soft-launch to 100 beta users (Reddit r/JapanTravel)
- [ ] Monthly burn ≤ $800 at launch

---

## Technical Approach

```
Data Sources                 Indexing Pipeline              Serving Layer
─────────────               ─────────────────              ─────────────
YouTube Transcript API  ──► Chunker (semantic)  ──► Pinecone (125K vectors)
Reddit API (OAuth)      ──► Embedder (e5-large) ──►     │
Blog scraper (optional) ──► Metadata tagger     ──►     ▼
                                                  FastAPI /api/ask
                                                     │
                                               Query embedding
                                               Pinecone retrieval
                                               Cross-encoder reranker
                                               Confidence threshold (0.75)
                                               Claude Sonnet 4.5 streaming
                                               Affiliate router
                                                     │
                                                     ▼
                                              Next.js Chat UI
                                          (streamed response + source cards)
```

**Repo structure:**
```
travel-rag-blog/
├── backend/               # FastAPI app
│   ├── api/
│   │   └── ask.py         # /api/ask streaming endpoint
│   ├── ingestion/
│   │   ├── youtube.py     # YouTube Transcript API fetcher
│   │   ├── reddit.py      # Reddit OAuth fetcher
│   │   ├── chunker.py     # Semantic chunker
│   │   ├── embedder.py    # multilingual-e5-large embedder
│   │   └── indexer.py     # Pinecone upsert pipeline
│   ├── rag/
│   │   ├── retriever.py   # Pinecone query + threshold
│   │   ├── reranker.py    # Cross-encoder reranker
│   │   └── generator.py   # Claude streaming generator
│   ├── affiliate/
│   │   └── router.py      # Contextual affiliate link selection
│   ├── config.py
│   └── main.py
├── frontend/              # Next.js app
│   ├── app/
│   │   ├── page.tsx       # Chat interface
│   │   └── api/ask/route.ts  # Proxy to FastAPI (optional)
│   ├── components/
│   │   ├── ChatInput.tsx
│   │   ├── StreamedAnswer.tsx
│   │   ├── SourceCard.tsx
│   │   └── AffiliateLink.tsx
│   └── ...
├── scripts/
│   └── ingest_japan.py    # One-off indexing scripts per destination
├── tests/
│   ├── test_retriever.py
│   ├── test_reranker.py
│   └── test_generator.py
├── .env.example
├── railway.toml
└── plan.md
```

---

## Reusable Components

| Need | Component | Action | Justification |
|------|-----------|--------|---------------|
| RAG indexing pipeline | `rag-advanced-indexing` | USE | Covers Pinecone schema, chunking strategies, metadata fields |
| Cross-encoder reranking | `rag-fusion-reranking` | USE | BGE reranker patterns, latency tuning |
| Semantic chunking | `semantic-chunking` | USE | Sentence-boundary chunking, overlap, context windows |
| Query rewriting | `rag-query-transformation` | REFERENCE | HyDE + step-back prompting patterns |
| Confidence thresholding | `rag-self-corrective` | REFERENCE | CRAG-style fallback on low similarity scores |
| FastAPI backend | `fastapi-security-middleware` | REFERENCE | Rate limiting, CORS, request validation |
| Next.js frontend | `nextjs-app-patterns` | USE | App Router, streaming RSC, SSE client patterns |
| Affiliate monetization | `affiliate-monetization` | ADAPT | Contextual link injection (not banner-based) |
| Claude streaming | `claude-api` | USE | Anthropic SDK streaming patterns |
| Railway deployment | `railway-deployment` | USE | FastAPI + env var management |
| SEO optimization | `seo-geo-aeo` | REFERENCE | Metadata, OG tags, sitemap for Next.js |
| Flag embeddings | `flag-embedding` | REFERENCE | multilingual-e5-large specifics (normalize=True, query prefix) |

---

## Phases

### Phase 1: Infrastructure & Credentials (Week 1)

**Goal:** All external services connected, Japan indexing pipeline proven.

**Tasks:**
1. Create repo structure (monorepo: `backend/`, `frontend/`, `scripts/`)
2. Pinecone setup:
   - Create index: `travel-rag` with 1024 dims (e5-large), cosine metric
   - Define metadata schema: `{destination, source_type, url, title, timestamp_seconds, language, chunk_index}`
3. API credentials:
   - YouTube Data API v3 key (for video metadata) + `youtube-transcript-api` pip package
   - Reddit OAuth app (client_id, client_secret, user_agent) via `praw`
   - Pinecone API key + environment
   - Anthropic API key
4. Build `backend/ingestion/youtube.py`:
   - Fetch transcript for a list of Japan travel video IDs
   - Return chunks with `{text, video_id, title, timestamp_start, timestamp_end, url}`
5. Build `backend/ingestion/chunker.py`:
   - Semantic chunking: 400-token target, 50-token overlap, sentence boundaries
   - Tag each chunk with destination + source_type metadata
6. Build `backend/ingestion/embedder.py`:
   - Load `intfloat/multilingual-e5-large` via `sentence-transformers`
   - Apply query prefix: `"query: "` for queries, `"passage: "` for documents
   - Batch embed (batch_size=32), normalize embeddings
7. Build `backend/ingestion/indexer.py`:
   - Upsert to Pinecone in batches of 100
   - Idempotent: skip if vector ID already exists
8. `scripts/ingest_japan.py`: End-to-end Japan ingestion run
   - Target: ~25K vectors for Japan from 50-100 YouTube videos + top 20 Japan subreddit threads

**Files to create:**
- `backend/config.py`
- `backend/ingestion/youtube.py`
- `backend/ingestion/reddit.py`
- `backend/ingestion/chunker.py`
- `backend/ingestion/embedder.py`
- `backend/ingestion/indexer.py`
- `scripts/ingest_japan.py`
- `.env.example`
- `requirements.txt`

**Tests:**
- `tests/test_chunker.py`: chunk size bounds, overlap correctness
- `tests/test_embedder.py`: output dim=1024, normalize check

**Complexity:** Medium

---

### Phase 2: Core RAG Loop (Week 2–3)

**Goal:** End-to-end query → answer pipeline working, tuned on Japan.

**Tasks:**
1. Build `backend/rag/destination_detector.py`:
   - NLP classifier to extract destination from free-text query
   - Strategy: keyword matching + zero-shot classification via Claude (`"which destination does this query refer to?"`)
   - Returns one of: `japan | thailand | italy | turkey | south_korea | unknown`
   - `unknown` → no metadata filter (search all destinations)
2. Build `backend/rag/retriever.py`:
   - Embed query with `"query: "` prefix
   - Auto-detect destination, apply Pinecone metadata filter `{destination: detected}`
   - Apply confidence threshold: if `top_score < 0.75`, return sentinel `NO_COVERAGE`
   - Check Redis cache first: key = `sha256(query + destination)`, TTL = 24h
2. Build `backend/rag/reranker.py`:
   - Load `BAAI/bge-reranker-base` via `FlagReranker`
   - Rerank top-20 → top-5
   - Adds ~200-400ms — acceptable with streaming masking latency
3. Build `backend/rag/generator.py`:
   - Construct context from top-5 chunks
   - System prompt: traveller-focused, cite sources, ONE affiliate suggestion, say so honestly if no info
   - Call Anthropic SDK with `stream=True`
   - Yield SSE events to client
4. Build `backend/api/ask.py` (FastAPI streaming endpoint):
   - `POST /api/ask` → `{query, destination, language?}`
   - Returns `text/event-stream`
   - Rate limit: 10 req/min per IP (via `slowapi`)
   - CORS: allow Next.js origin only
5. Build `backend/main.py`: FastAPI app, mount router, CORS middleware
6. Tune system prompt against 50 real Japan travel questions:
   - Test: "Best ramen in Tokyo under $15", "Japan Rail Pass worth it 2025", "Cherry blossom timing Kyoto"
   - Measure: answer quality, citation accuracy, affiliate fit

**Files to create:**
- `backend/rag/destination_detector.py`
- `backend/rag/retriever.py`
- `backend/rag/reranker.py`
- `backend/rag/generator.py`
- `backend/cache/redis_client.py`
- `backend/api/ask.py`
- `backend/main.py`

**Tests:**
- `tests/test_destination_detector.py`: "best ramen Tokyo" → japan, "Amalfi coast hotels" → italy
- `tests/test_retriever.py`: mock Pinecone, test threshold logic, test cache hit/miss
- `tests/test_reranker.py`: rerank order correctness
- `tests/test_generator.py`: mock Anthropic SDK, test SSE stream

**Complexity:** High

---

### Phase 3: Remaining Destinations (Week 3)

**Goal:** All 5 destinations indexed (~125K vectors total).

**Tasks:**
1. Run `scripts/ingest_japan.py` validation — confirm answer quality meets bar
2. Build `scripts/ingest_destination.py` (generalized ingestion script):
   - Parameterized: `--destination thailand --language en`
   - YouTube: curated video list per destination (50-100 videos each)
   - Reddit: `r/ThailandTourism`, `r/italytravel`, `r/Turkey`, `r/korea`
3. Index remaining 4 destinations: Thailand, Italy, Turkey, South Korea
   - ~25K vectors each → ~100K additional vectors → ~125K total
4. Validate retrieval quality per destination with 10 test queries each
5. Update retriever to support destination routing (no filter = all destinations)

**Files to create/modify:**
- `scripts/ingest_destination.py`
- `backend/ingestion/reddit.py` (destination-parameterized)
- `backend/rag/retriever.py` (destination filter update)

**Tests:**
- Integration test: query each destination, verify non-zero results

**Complexity:** Low-Medium (pipeline already proven in Phase 1)

---

### Phase 4: Affiliate Router (Week 4)

**Goal:** Contextual affiliate link injected into every answer, 1 per response.

**Tasks:**
1. Build `backend/affiliate/router.py`:
   - Rule-based routing table:
     ```
     accommodation mentions → Booking.com affiliate link
     tours/activities mentions → Klook affiliate link
     money/banking/forex mentions → Wise affiliate link
     flights mentions → Skyscanner/Kayak affiliate link (stretch)
     ```
   - Parse generator output for trigger keywords
   - Return single highest-confidence affiliate link + disclosure text
2. Affiliate account setup (manual):
   - Booking.com Partner Program
   - Klook Affiliate Program
   - Wise Affiliate Program
3. Integrate affiliate router into `generator.py`:
   - Inject affiliate suggestion as a structured `[affiliate]` SSE event type
   - Frontend renders it as a distinct UI component (not inline text)
4. FTC disclosure: append standard disclosure text to every response

**Files to create:**
- `backend/affiliate/router.py`
- `backend/affiliate/rules.py` (keyword → program mapping)

**Tests:**
- `tests/test_affiliate_router.py`: keyword matching, one-link-max enforcement

**Complexity:** Low-Medium

---

### Phase 5: Next.js Frontend (Week 4–5)

**Goal:** Chat UI with streamed responses, source cards, YouTube timestamp links.

**Tasks:**
1. Scaffold Next.js app (App Router, TypeScript, Tailwind):
   ```
   npx create-next-app@latest frontend --typescript --tailwind --app
   ```
2. Build `components/ChatInput.tsx`:
   - Plain text input — no destination dropdown (NLP auto-detects from query)
   - Placeholder: "Ask anything about Japan, Thailand, Italy, Turkey, or South Korea..."
   - Keyboard: Enter to submit
3. Build `components/StreamedAnswer.tsx`:
   - Connect to `/api/ask` SSE stream
   - Render markdown tokens as they arrive
   - Handle `[affiliate]` SSE event type → render `<AffiliateLink />`
   - Handle `[sources]` SSE event type → render `<SourceCard />` list
4. Build `components/SourceCard.tsx`:
   - Expandable card per source chunk
   - YouTube: thumbnail + title + timestamp deep-link (`?t=NNs`)
   - Reddit: thread title + subreddit + link
5. Build `components/AffiliateLink.tsx`:
   - CTA button (e.g., "Book on Booking.com →")
   - FTC disclosure tooltip
6. SEO:
   - `app/layout.tsx`: OpenGraph meta, JSON-LD for SoftwareApplication schema
   - `app/sitemap.ts`: static sitemap with destination pages
   - `app/robots.ts`

**Files to create:**
- `frontend/app/page.tsx`
- `frontend/app/layout.tsx`
- `frontend/components/ChatInput.tsx`
- `frontend/components/StreamedAnswer.tsx`
- `frontend/components/SourceCard.tsx`
- `frontend/components/AffiliateLink.tsx`
- `frontend/app/sitemap.ts`
- `frontend/app/robots.ts`

**Tests:**
- Component smoke tests (React Testing Library)
- SSE stream connection test (mock EventSource)

**Complexity:** Medium

---

### Phase 6: Deployment + Legal + Beta (Week 5–6)

**Goal:** Live product, legally compliant, soft-launched to 100 users.

**Tasks:**
1. **Railway deployment** (backend):
   - `railway.toml` with `startCommand = "uvicorn backend.main:app --host 0.0.0.0 --port $PORT"`
   - Set env vars via Railway dashboard: `PINECONE_API_KEY`, `ANTHROPIC_API_KEY`, etc.
   - Health check endpoint: `GET /health`
2. **Vercel deployment** (frontend):
   - `NEXT_PUBLIC_API_URL` pointing to Railway backend
   - Deploy via `vercel --prod`
3. **Legal/compliance:**
   - Add `robots.txt` with crawl rate limits for indexer bots
   - FTC disclosure: `"This response may contain affiliate links. We may earn a commission at no cost to you."`
   - Review YouTube ToS section 5C — document decision in `LEGAL_REVIEW.md`
   - Review Reddit API Data Terms — confirm batch weekly indexing is compliant
4. **Rate limiting on indexer:**
   - YouTube: 1 request/second (well under quota)
   - Reddit: 60 requests/minute (per OAuth app limit)
5. **Beta launch:**
   - Post to `r/JapanTravel`: soft launch, ask for feedback
   - Monitor: Pinecone query latency, Railway logs, error rate
   - Target: 100 users, collect qualitative feedback on answer quality

**Files to create:**
- `railway.toml`
- `LEGAL_REVIEW.md`
- `backend/api/health.py`

**Complexity:** Medium

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| YouTube ToS: commercial RAG use of transcripts is contested | Document usage as "transformative search" not training data; rate-limit fetching; obtain YouTube API v3 key (not scraping); review ToS 5C before launch |
| Reddit API: commercial RAG usage requires Data API compliance | Use OAuth app (not scraping); weekly batch indexing stays under 100 req/min; review Reddit's Data API terms |
| Claude API cost spike at 10K DAU ($2,160/mo) | Launch at soft scale; add query caching (Redis) for repeated questions before scaling beyond 1K DAU |
| Reranker adds 200-400ms latency | Stream answer text immediately after retrieval; reranker runs before generation, not inline |
| Pinecone 100K free tier exhausted | MVP at 125K vectors requires starter plan ($70/mo) — budgeted |
| Hallucination / low-quality retrieval | Confidence threshold: reject if top cosine similarity < 0.75; respond "I don't have reliable info on this yet" |
| FTC non-compliance | Disclosure on every response, not just on click; implement from day one |
| Embedding model: multilingual-e5-large requires query/passage prefixes | `"query: "` prefix on all queries, `"passage: "` on all document chunks — failing to do this degrades retrieval significantly |

---

## Lessons Applied

- **No project memory exists yet** — this is greenfield. Start clean.
- **Embed prefixes are critical for e5-large**: `"query: "` / `"passage: "` prefixes are mandatory, not optional. Omitting them causes ~15-20% retrieval quality degradation.
- **Streaming masks reranker latency**: Don't skip reranker for speed — stream the answer while reranker runs in the pipeline.
- **One affiliate link max**: Multiple affiliate links erode trust. Hard-enforce in router.
- **Ship Japan first**: Validate full pipeline on one destination before expanding to 4 more. Don't index all 5 simultaneously.

---

## Resolved Decisions

| Question | Decision |
|----------|----------|
| YouTube video curation | Manual curated list for MVP (Phase 1), then switch to YouTube Data API search auto-discovery in Phase 3+ |
| Destination routing | NLP auto-detect destination from query text — no dropdown required |
| Query caching | Redis from day 1 — cache repeated queries before they hit Pinecone + Claude |

## Open Questions

1. **Reranker model size**: `bge-reranker-base` (270M params, ~250ms) vs `bge-reranker-large` (560M, ~500ms) — which latency budget is acceptable?
2. **FTC disclosure review**: Has a legal review been done, or is the standard disclosure text sufficient for soft launch?
3. **Blog scraping**: Strategic plan mentions blog scraper as optional. Include in MVP or Phase 2?
4. **Auth**: Beta is open access. When does user auth (to enforce rate limits per user) become necessary?

---

## Phase Trigger Gates

| Gate | Trigger | Action |
|------|---------|--------|
| Phase 2 → Phase 3 | Japan retrieval quality: 8/10 test queries return relevant answers | Expand to remaining 4 destinations |
| Phase 3 → Phase 4 | All 5 destinations return relevant answers on 10 test queries each | Build affiliate router |
| Phase 5 → Phase 6 | End-to-end demo working locally (answer + sources + affiliate) | Deploy to Railway + Vercel |
| Post-launch Phase 2 | 1,000 DAU | Add 5 more destinations + Hindi interface |
| Post-launch Mobile | First affiliate revenue | Start React Native app |

---

## Environment Variables Required

```bash
# Pinecone
PINECONE_API_KEY=
PINECONE_ENVIRONMENT=
PINECONE_INDEX_NAME=travel-rag

# Anthropic
ANTHROPIC_API_KEY=

# Reddit OAuth
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
REDDIT_USER_AGENT=travel-rag-indexer/1.0

# YouTube
YOUTUBE_API_KEY=

# Affiliate
BOOKING_AFFILIATE_ID=
KLOOK_AFFILIATE_ID=
WISE_AFFILIATE_ID=

# Redis
REDIS_URL=redis://localhost:6379
REDIS_CACHE_TTL=86400

# App
CORS_ORIGIN=https://your-frontend.vercel.app
CONFIDENCE_THRESHOLD=0.75
```

---

## Week-by-Week Summary

| Week | Focus | Done When |
|------|-------|-----------|
| 1 | Infra + Japan ingestion | 25K Japan vectors in Pinecone |
| 2 | RAG loop (retrieval + reranker + streaming) | `/api/ask` returns streamed Japan answers |
| 3 | Remaining 4 destinations | 125K vectors, all destinations returning results |
| 4 | Affiliate router + Next.js frontend | End-to-end demo: chat → answer → affiliate link |
| 5 | Frontend polish + deployment | Live on Railway + Vercel |
| 6 | Beta launch + legal | 100 beta users, FTC compliant |
