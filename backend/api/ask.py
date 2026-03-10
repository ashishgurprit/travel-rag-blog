"""FastAPI router for /api/ask (SSE) and /api/ask/voice endpoints.

Intent routing:
  RAG       → Pinecone retrieval + reranker + generator
  LOGISTICS → TripPlanner (Claude + Tavily + Redis session)
  HYBRID    → both paths merged

Session IDs are passed via the X-Session-ID header (optional).
If absent, a random UUID is generated per request (stateless).
"""

import json
import uuid
from typing import AsyncGenerator

from fastapi import APIRouter, File, Header, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.affiliate.router import route_affiliate
from backend.rag.generator import Generator
from backend.rag.intent_classifier import IntentClassifier
from backend.rag.reranker import Reranker
from backend.rag.retriever import Retriever
from backend.rag.trip_planner import TripPlanner
from backend.rag.web_search import search_web

router = APIRouter()

# Module-level singletons — initialized lazily on first request.
retriever: Retriever | None = None
reranker: Reranker | None = None
generator: Generator | None = None
classifier: IntentClassifier | None = None
trip_planner: TripPlanner | None = None


class AskRequest(BaseModel):
    query: str


def _get_singletons():
    global retriever, reranker, generator, classifier, trip_planner
    if retriever is None:
        retriever = Retriever()
    if reranker is None:
        reranker = Reranker()
    if generator is None:
        generator = Generator()
    if classifier is None:
        classifier = IntentClassifier()
    if trip_planner is None:
        trip_planner = TripPlanner()


# ── RAG path ─────────────────────────────────────────────────────────────────

async def _rag_stream(query: str) -> AsyncGenerator[dict, None]:
    """Pinecone retrieval → reranker → generator. Yields raw events; no affiliate injection."""
    chunks = retriever.retrieve(query)
    web_chunks = search_web(query, max_results=3)

    if chunks is not None:
        all_chunks = chunks + web_chunks
    elif web_chunks:
        all_chunks = web_chunks
    else:
        all_chunks = None

    gen_input = reranker.rerank(query, all_chunks, top_n=5) if all_chunks else None

    async for event in generator.generate(query, gen_input):
        yield event


async def _logistics_stream(
    query: str,
    session_id: str,
    intent_result,
) -> AsyncGenerator[dict, None]:
    """TripPlanner — Claude + Tavily + Redis session memory."""
    async for event in trip_planner.plan(query, session_id, intent_result):
        yield event


async def _stream_response(
    query: str,
    session_id: str,
) -> AsyncGenerator[str, None]:
    """Route query by intent and stream SSE events."""
    _get_singletons()

    intent = classifier.classify(query)

    if intent.needs_rag and intent.needs_logistics:
        # HYBRID: run both paths, interleave text, merge sources/affiliate
        rag_events: list[dict] = []
        logistics_events: list[dict] = []

        async for event in _rag_stream(query):
            rag_events.append(event)

        async for event in _logistics_stream(query, session_id, intent):
            logistics_events.append(event)

        # Yield a separator header before RAG section
        yield f"data: {json.dumps({'type': 'text', 'content': '**Experiences & Highlights**\\n'})}\n\n"
        for event in rag_events:
            if event["type"] not in ("disclosure",):
                yield f"data: {json.dumps(event)}\n\n"

        yield f"data: {json.dumps({'type': 'text', 'content': '\\n**Planning & Logistics**\\n'})}\n\n"
        for event in logistics_events:
            yield f"data: {json.dumps(event)}\n\n"

    elif intent.needs_logistics:
        async for event in _logistics_stream(query, session_id, intent):
            yield f"data: {json.dumps(event)}\n\n"

    else:
        # Pure RAG
        full_text_parts: list[str] = []
        pending_events: list[dict] = []

        async for event in _rag_stream(query):
            if event["type"] == "text":
                full_text_parts.append(event["content"])
                yield f"data: {json.dumps(event)}\n\n"
            else:
                pending_events.append(event)

        full_text = "".join(full_text_parts)
        affiliate = route_affiliate(full_text)

        for event in pending_events:
            if event["type"] == "disclosure" and affiliate is not None:
                yield f"data: {json.dumps({'type': 'affiliate', 'content': affiliate})}\n\n"
                affiliate = None
            yield f"data: {json.dumps(event)}\n\n"


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/api/ask")
async def ask(
    request: AskRequest,
    x_session_id: str | None = Header(default=None, alias="X-Session-ID"),
) -> StreamingResponse:
    """Stream a travel answer as Server-Sent Events.

    Pass X-Session-ID header for multi-turn trip planning context.
    """
    session_id = x_session_id or str(uuid.uuid4())
    return StreamingResponse(
        _stream_response(request.query, session_id),
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no"},
    )


@router.post("/api/ask/voice")
async def ask_voice(
    audio: UploadFile = File(...),
    x_session_id: str | None = Header(default=None, alias="X-Session-ID"),
) -> StreamingResponse:
    """Transcribe audio upload and stream a travel answer.

    Accepts audio/wav, audio/mp4, audio/webm, audio/ogg uploads.
    Uses local Whisper transcription (same pipeline as video ingestion).
    """
    session_id = x_session_id or str(uuid.uuid4())

    audio_bytes = await audio.read()
    query = _transcribe_audio(audio_bytes)

    return StreamingResponse(
        _stream_response(query, session_id),
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no"},
    )


def _transcribe_audio(audio_bytes: bytes) -> str:
    """Transcribe raw audio bytes using the local Whisper pipeline.

    Falls back to a placeholder if Whisper is unavailable.
    """
    import tempfile
    import os

    try:
        from backend.ingestion.transcriber import _get_whisper_pipe

        pipe = _get_whisper_pipe()
        if pipe is None:
            return ""

        suffix = ".wav"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            result = pipe(tmp_path, return_timestamps=False)
            return result.get("text", "").strip()
        finally:
            os.unlink(tmp_path)

    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("Voice transcription failed: %s", e)
        return ""
