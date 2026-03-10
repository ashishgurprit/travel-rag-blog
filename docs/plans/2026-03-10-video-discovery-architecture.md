# Video Discovery & Trip Planning Architecture

> **Status:** Design approved — ready for implementation planning
> **Date:** 2026-03-10

## Goal

Replace static `*_video_ids.json` files with a dynamic, self-improving knowledge system that:
- Discovers high-quality YouTube content through multiple sources
- Transcribes videos without captions locally at zero cost
- Organises content into a hierarchical destination tree
- Rebalances coverage based on real user behaviour
- Adds a conversational trip planning layer for logistics

---

## Architecture Overview

```
                    TRAVEL RAG KNOWLEDGE SYSTEM

[Sources]          [Discovery]        [Ingestion]        [Serve]

Tourism Stats  ─┐
TripAdvisor    ─┤→ Knowledge    →  Transcription  →  Pinecone
Quora          ─┤   Tree           Queue              Vector DB
Reddit         ─┤   (3-tier)       │                  │
YouTube API    ─┤                  ├─ YT Captions      ├─ RAG
Google Trends  ─┘                  ├─ Whisper local    │  (existing)
                                   └─ OpenAI API       │
                                                       ├─ Trip Planner
[Performance Review]                                   │  (Claude)
Weekly auto-triggers ──────────────────────────────────┤
Monthly human rebalancing                              └─ Voice
                                                          (Whisper)
```

---

## Section 1: The Knowledge Tree

A 3-level taxonomy: **Destination → City/Region → Category**

### Tier Allocation

| Tier | Examples | Video Budget |
|------|----------|-------------|
| Tier 1: Major Cities | Tokyo, Kyoto, Osaka | 40% |
| Tier 2: Regional | Hiroshima, Nara, Hakone | 35% |
| Tier 3: Emerging/Hidden Gems | Kanazawa, Yakushima | 25% |

### Budget Constraints
- **No node can exceed 20% of total budget** (prevents Tokyo monopoly)
- **Every node guaranteed minimum 3 videos** (ensures coverage of hidden gems)
- Demand scores are **log-scaled** before allocation (flattens long-tail skew)

### Category Taxonomy (per city node)
Seeded from multi-source signals:
- **TripAdvisor** top attraction types → cuisine, temples, museums, nightlife, nature
- **Quora** question clusters → day trips, budget tips, itineraries, safety
- **Reddit** trending threads → seasonal events, hidden gems, local experiences
- **Tourism stats** → visitor volume per region (floor/cap enforcement)

### Tree Node Schema
```json
{
  "japan/tokyo/cuisine": {
    "tier": 1,
    "min_videos": 5,
    "max_videos": 20,
    "current_videos": 12,
    "demand_score": 0.87,
    "allocated_budget": 15,
    "last_rebalanced": "2026-03-10"
  },
  "japan/kanazawa/traditional_culture": {
    "tier": 3,
    "min_videos": 3,
    "max_videos": 10,
    "current_videos": 3,
    "demand_score": 0.31,
    "allocated_budget": 6,
    "last_rebalanced": "2026-03-10"
  }
}
```

### Taxonomy Sources
- **Static base** — predefined cities and categories per destination (always covered)
- **Dynamic enrichment** — trending cities/topics discovered each run via Google Trends, Reddit, Quora
- **Monthly refresh** — tourism stats update tier allocations and budget caps

---

## Section 2: Multi-Source Discovery Per Node

For each tree node (e.g. `japan/tokyo/cuisine`), discovery runs as a parallel fan-out:

### Source A: YouTube Data API v3
- Search: `"Tokyo cuisine restaurants food 2025"`, `order=viewCount`, `publishedAfter=30 days ago`
- Filter: `viewCount > 50k`, `duration 5–30 min`
- Returns: `video_id`, `title`, `view_count`, `published_at`, `channel_id`
- Quota: 10,000 units/day free tier

### Source B: Reddit Mining
- Subreddits: `r/JapanTravel`, `r/Tokyo`, `r/travel`, `r/solotravel`, `r/food`
- Extract YouTube links from posts + top comments matching node keywords
- Score by upvotes + comment count (community validation signal)

### Source C: Google Trends + yt-dlp Search
- `pytrends`: trending queries under destination/category last 7 days
- `yt-dlp`: `"ytsearch20:{trending_query}"` → extracts video IDs without downloading
- No IP rotation needed — yt-dlp search is lightweight

### Source D: TripAdvisor
- Top-reviewed attractions per city → extract category vocabulary
- Enriches search query generation for Sources A and C

### Source E: Quora
- Questions like "best food in Tokyo", "where to eat in Tokyo"
- Extract YouTube links from answers
- Extract intent vocabulary → enriches tree categories

### Source F: National Tourism Stats (monthly batch)
- Japan Tourism Agency, Tourism Authority of Thailand, etc.
- Visitor volume per region → adjusts tier allocations and budget caps

### Deduplication + Provenance Tracking

Video registry stored at `scripts/video_registry.json`:

```json
{
  "abc123xyz": {
    "video_id": "abc123xyz",
    "sources": ["youtube_api", "reddit"],
    "reddit_score": 847,
    "view_count": 1200000,
    "published_at": "2025-02-14",
    "destination": "japan",
    "tree_node": "japan/tokyo/cuisine",
    "provenance_score": 0.91,
    "already_ingested": false,
    "discovered_at": "2026-03-10"
  }
}
```

**Rules:**
- Already ingested → update provenance score only, skip transcription
- Discovered by multiple sources → higher provenance score → boosted in reranker
- New → add to transcription queue

---

## Section 3: Transcription Pipeline

### Transcription Priority (cost optimised)

```
For each video in queue:

Step 1: YouTube captions via youtube_transcript_api   [free, instant]
        → success? → proceed to chunking
        → fail?    → Step 2

Step 2: yt-dlp audio download (audio-only, ~5MB/video) [free]
        → download to temp file

Step 3: Local whisper-large-v3-turbo via transformers  [free, ~90s/video]
        → runs overnight batch on Mac M-series (Metal/MPS)
        → model size: 1.5GB disk, ~3-4GB RAM during inference
        → quality: equivalent to OpenAI Whisper API for English content
        → success? → proceed to chunking
        → fail?    → Step 4

Step 4: OpenAI Whisper API                             [~$0.20 AUD/min]
        → only for: high provenance score + no captions + Thai/Korean spoken
        → estimated cost: <$20 AUD/month at full scale
```

### Model Details
- **Model:** `openai/whisper-large-v3-turbo` via HuggingFace `transformers`
- **No HuggingFace token required** — fully public, MIT license
- **First run:** downloads 1.5GB model, cached permanently after
- **Speed:** ~8-10x real-time on Apple Silicon (15-min video ≈ 90 seconds)
- **Quality vs API:** identical for English vlogs; minor gap on Thai/Cantonese spoken content

### Chunk Metadata (provenance stored per chunk)
```json
{
  "text": "The best ramen in Tokyo is found in...",
  "video_id": "abc123xyz",
  "tree_node": "japan/tokyo/cuisine",
  "tier": 1,
  "sources": ["youtube_api", "reddit"],
  "provenance_score": 0.91,
  "reddit_score": 847,
  "destination": "japan",
  "source_type": "youtube",
  "timestamp_start": 142.5,
  "url": "https://www.youtube.com/watch?v=abc123xyz&t=142s"
}
```

---

## Section 4: Performance Review & Rebalancing

### Weekly (automated)

**RAG Retrieval Metrics:**
- Log every query → record which tree nodes were retrieved
- Flag nodes with retrieval confidence < 0.7 (thin content)
- Flag nodes with zero retrievals in 7 days (dead content)

**User Engagement Signals:**
- Affiliate link clicks per tree node (commercial intent signal)
- Session length per destination/category
- Query reformulations (user rephrasing = answer wasn't satisfactory)

**Auto-triggers:**
- Node retrieval confidence < 0.7 → queue 5 more videos for that node
- Node zero retrievals in 7 days → flag for monthly review
- Trending query not matching any node → create new node candidate

### Monthly (human-in-loop)

**Deep Coverage Audit:**
- Heatmap: query volume vs content volume per node
- Identify 80/20 skew — cap over-served nodes, boost under-served

**Tree Rebalancing:**
- Promote Tier 3 nodes gaining traction → Tier 2
- Demote Tier 1 nodes with declining engagement
- Add new nodes from Quora/Reddit emerging topics
- Retire nodes with 0 queries in 30 days

**Budget Reallocation:**
- Log-scale demand scores → recalculate % allocations
- Enforce: no node > 20% of budget
- Enforce: every node ≥ 3 videos minimum
- Generate rebalancing report → **human approves before applying**

---

## Section 5: Trip Planning Chatbot

A conversational logistics layer alongside RAG, powered by Claude.

### Intent Routing

```
User Input (voice or text)
│
├── Voice → whisper-large-v3-turbo (local) → text
└── Text → direct

↓

Claude Intent Classifier
│
├── "What to do / see / eat / experience"
│   → RAG pipeline (existing)
│
└── "How to get there / costs / logistics"
    → Trip Planner
```

### Trip Planner Capabilities

**Entry & Exit Points:**
- Visa requirements by passport nationality
- Main airports + border crossings per destination
- Recommended open-jaw routing (fly into Tokyo, out of Osaka)

**Transport Modes:**
- Within destination: trains, buses, domestic flights, ferries
- Between cities: pass options vs point-to-point cost comparison
- Airport transfers: cost + time + all options

**Budget Planning:**
- Daily cost ranges: budget / mid / luxury tiers
- Seasonal price variance (cherry blossom season = ~40% premium)
- Currency context + tipping norms
- Affiliate links via existing router: Booking.com, Klook, Wise

### Data Sources for Logistics
- **Static structured data** per destination (visa rules, transport networks) — ingested into Pinecone
- **Tavily web search** (already built) — live prices + current visa rules
- **Redis conversation memory** (already built) — multi-turn trip planning sessions

---

## Implementation Phases

### Phase 1: Foundation
- Build `KnowledgeTree` class — taxonomy definition, tier/budget management
- Build `VideoRegistry` — deduplication + provenance tracking
- Integrate `youtube-data-api` discovery source

### Phase 2: Multi-Source Discovery
- Reddit miner for YouTube link extraction
- Google Trends + yt-dlp search integration
- TripAdvisor + Quora vocabulary enrichment

### Phase 3: Local Transcription
- Integrate `whisper-large-v3-turbo` via `transformers`
- yt-dlp audio download pipeline
- Fallback chain: captions → local Whisper → OpenAI API

### Phase 4: Performance Layer
- Query logging + retrieval metrics
- Weekly auto-trigger system
- Monthly rebalancing report generator

### Phase 5: Trip Planning Chatbot
- Claude intent classifier
- Logistics knowledge ingestion (visa, transport, budget data)
- Voice input via local Whisper
- Multi-turn session management

---

## New Dependencies

```
# Discovery
google-api-python-client   # YouTube Data API v3
pytrends                   # Google Trends
yt-dlp                     # YouTube audio download + search

# Transcription
transformers               # whisper-large-v3-turbo
torch                      # Metal/MPS support on Apple Silicon

# Sources
praw                       # Reddit API (already used)
beautifulsoup4             # TripAdvisor / Quora scraping
```

---

## Files To Create

```
backend/ingestion/
├── discovery/
│   ├── __init__.py
│   ├── youtube_api.py        # YouTube Data API v3 search
│   ├── reddit_miner.py       # Extract YouTube links from Reddit
│   ├── trends_search.py      # Google Trends + yt-dlp search
│   ├── tripadvisor.py        # Category vocabulary enrichment
│   └── quora.py              # Intent vocabulary + YouTube links
├── knowledge_tree.py         # Tree taxonomy + budget management
├── video_registry.py         # Deduplication + provenance tracking
├── transcriber.py            # Fallback transcription chain
└── scheduler.py              # Weekly/monthly pipeline orchestration

backend/rag/
└── trip_planner.py           # Claude logistics chatbot

scripts/
├── tree_config/
│   ├── japan.json            # Static base taxonomy for Japan
│   ├── thailand.json
│   ├── italy.json
│   ├── turkey.json
│   └── south_korea.json
└── video_registry.json       # Provenance registry (gitignored if large)
```
