# Feedback Log

> Running summary of all session debriefs. Used by `/project:advisor-analyze` for pattern detection.
> Each entry is one debrief session. Newest entries at the bottom.

---

## 2026-03-10 | project: travel-rag-blog | topic: video-discovery-rag-pipeline
- USED: rag-advanced-indexing, audio-media-pipeline, yt-dlp-media-downloader, batch-processing, background-jobs-universal, ai-agent-patterns, e2e-testing, testing-orchestrator-fullstack
- GROUPS: stack-rag, stack-media, stack-backend, stack-ai, stack-testing
- GAP: no SSE streaming API skill (FastAPI generator composition, mid-stream injection); no pytrends/Google Trends skill; no hierarchical budget taxonomy skill; launchd-scheduler missing two-layer APScheduler pattern
- GAP_GROUP: stack-backend, stack-media, stack-rag, stack-backend
- CREATED: backend/ingestion/knowledge_tree.py, backend/ingestion/video_registry.py, backend/ingestion/transcriber.py, backend/rag/trip_planner.py, backend/rag/intent_classifier.py, frontend/e2e/api-contract.spec.ts, scripts/apply_rebalance.py
- ISSUE: ai-agent-patterns: str.format() + literal {} in prompt causes silent KeyError; audio-media-pipeline: float16 fails on MPS use float32; batch-processing: brpop() returns tuple use item[1]; testing-orchestrator-fullstack: fails when sub-skills missing
- TECH_NO_SKILL: pytrends, PRAW, APScheduler, launchd, whisper-large-v3-turbo via transformers, Playwright SSE route interception
- RECOMMEND: CREATE sse-streaming-fastapi; CREATE knowledge-taxonomy-budget-tree; CREATE pytrends-yt-dlp-discovery; CREATE praw-reddit-discovery; UPDATE audio-media-pipeline (MPS float32); UPDATE ai-agent-patterns (prompt template escaping); UPDATE batch-processing (brpop tuple); EXTEND launchd-scheduler (two-layer pattern); EXTRACT transcriber.py; EXTRACT apply_rebalance.py
