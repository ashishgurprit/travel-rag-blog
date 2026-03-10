# Debrief: Video Discovery + RAG Pipeline + E2E Tests
Date: 2026-03-10
Project: travel-rag-blog
Session Duration: ~8 hours
Commits: 6

## Skills Used
- rag-advanced-indexing (group: stack-rag) (sections: metadata filtering, multi-vector indexing — designed Pinecone chunk schema with tree_node/tier/provenance_score/sources[])
- audio-media-pipeline (group: stack-media) (sections: transcription fallback chain, Whisper singleton, yt-dlp temp file pattern)
- yt-dlp-media-downloader (group: stack-media) (sections: audio-only download, subprocess pattern)
- batch-processing (group: stack-backend) (sections: Redis queue consumer, fan-out pattern)
- background-jobs-universal (group: stack-backend) (sections: APScheduler BlockingScheduler, distributed lock)
- ai-agent-patterns (group: stack-ai) (sections: intent routing, multi-turn session memory, Tavily augmentation, affiliate injection)
- e2e-testing (group: stack-testing) (sections: Playwright route interception, SSE mocking)
- testing-orchestrator-fullstack (group: stack-testing) (sections: web surface + API contract layer structure)

## Skill Groups Active This Session
- stack-rag: Pinecone schema with provenance metadata, reranker provenance boost, logistics namespace separation
- stack-media: Whisper transcription fallback chain (captions → local Whisper → OpenAI API), yt-dlp audio download
- stack-backend: Multi-source discovery fan-out (YouTube/Reddit/Trends), Redis queue, APScheduler + launchd scheduler
- stack-ai: Intent classifier (RAG/LOGISTICS/HYBRID), trip planner chatbot, multi-turn session memory
- stack-testing: 35 new backend tests, 26 Playwright E2E tests, SSE contract tests

## Skills That Would Have Helped
- No skill covers SSE streaming API patterns — FastAPI generator composition, mid-stream event injection, double-yield bug prevention (likely group: stack-backend or stack-rag)
- No skill covers pytrends / Google Trends integration — quota handling, trending query extraction, combining with yt-dlp search (likely group: stack-media)
- No skill covers hierarchical taxonomy trees with tiered budget allocation — log-scale demand scoring, floor/cap rebalancing, monthly human-approval gate (likely group: stack-rag or stack-backend)
- launchd-scheduler skill exists but missing two-layer pattern: launchd fires → APScheduler owns cron logic internally (likely group: stack-backend)

## New Patterns Created
- backend/ingestion/knowledge_tree.py: 3-tier hierarchical budget tree with log-scale demand scoring + floor/cap enforcement. Reusable for any tiered content taxonomy.
- backend/ingestion/video_registry.py: Multi-source deduplication registry with provenance scoring. Reusable for any multi-source ingestion pipeline needing dedup + quality scoring.
- backend/ingestion/transcriber.py: 4-step transcription fallback chain with MPS Whisper singleton, yt-dlp subprocess audio, try/finally temp cleanup. Directly reusable.
- backend/rag/trip_planner.py: Multi-turn Redis session chatbot with intent entity seeding, Tavily live data, logistics affiliate routing. Reusable for any domain-specific multi-turn assistant.
- backend/rag/intent_classifier.py: Single-call intent + entity extraction with JSON parsing, fence stripping, graceful fallback. Reusable for any query routing system.
- frontend/e2e/api-contract.spec.ts: SSE schema contract testing via Playwright route.fulfill() interception. Reusable for any streaming API frontend.
- scripts/apply_rebalance.py: Human-approval gate pattern (dry-run preview → --approve → archive). Reusable for any automated system requiring human-in-the-loop before applying changes.

## Skill Issues Found
- ai-agent-patterns: no warning about str.format() + literal {} in prompt templates — caused silent production bug where intent_classifier always fell back to RAG (KeyError on JSON example block). Fix: escape with {{ / }}. Add as "Heads up" in prompt templating section.
- batch-processing: Redis BRPOP consumer pattern shows item but should document that item[1] contains payload (item[0] is the queue key). Minor but causes AttributeError on first use.
- testing-orchestrator-fullstack: invocation failed because testing-orchestrator-web sub-skill didn't exist at project path. Skill needs graceful degradation when sub-orchestrators are missing.
- audio-media-pipeline: recommends torch.float16 for Apple Silicon MPS but Whisper on MPS requires float32 — float16 throws runtime errors. Should be a documented gotcha.

## Technologies Used Without Skills
- pytrends: Google Trends Python client — TrendReq, interest_over_time(), graceful quota fallback, combining trending queries with yt-dlp search
- PRAW (Python Reddit API Wrapper): subreddit scanning, YouTube URL regex extraction from posts/comments, upvote-based relevance scoring
- APScheduler: BlockingScheduler + CronTrigger, coalesce/misfire_grace_time, SIGTERM graceful shutdown handler
- launchd (macOS): StartCalendarInterval plist for wake-safe scheduling, two-layer architecture with APScheduler inside process
- whisper-large-v3-turbo via HuggingFace transformers: pipeline() ASR singleton on MPS, segment timestamp mapping to chunk schema, float32 requirement
- Playwright SSE interception: route.fulfill() with text/event-stream content-type for deterministic streaming API mocking in E2E

## Recommendations
- CREATE: sse-streaming-fastapi — patterns for FastAPI generator composition, buffered event injection, mid-stream affiliate/metadata events, preventing double-yield in composed generators
- CREATE: knowledge-taxonomy-budget-tree — hierarchical content taxonomy with tiered budget allocation, log-scale demand scoring, floor/cap enforcement, monthly human-approval rebalancing
- CREATE: pytrends-yt-dlp-discovery — Google Trends + yt-dlp search integration, quota handling, trending query extraction, no-download search mode
- CREATE: praw-reddit-discovery — PRAW subreddit scanning for YouTube links, URL regex patterns, upvote scoring, relevance filtering
- UPDATE: audio-media-pipeline — add gotcha: torch.float16 fails on MPS; use float32 for Whisper on Apple Silicon
- UPDATE: ai-agent-patterns — add warning: escape {{ }} in prompt templates when using str.format(); or prefer f-strings with concatenated query at end
- UPDATE: batch-processing — clarify: redis.brpop() returns (key, value) tuple; use item[1] for payload
- EXTEND: launchd-scheduler — add two-layer scheduling pattern: launchd for wake-safe firing + APScheduler for cron logic inside process
- EXTRACT: backend/ingestion/transcriber.py — Whisper singleton + fallback chain is a standalone reusable module
- EXTRACT: scripts/apply_rebalance.py — human-approval gate pattern is reusable for any automated change system
