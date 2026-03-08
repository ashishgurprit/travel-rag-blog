"""FastAPI router for the /api/ask SSE endpoint."""

import json
from typing import AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.affiliate.router import route_affiliate
from backend.rag.generator import Generator
from backend.rag.reranker import Reranker
from backend.rag.retriever import Retriever

router = APIRouter()

# Module-level singletons — initialized lazily on first request.
# Tests replace these via patch.object(backend.api.ask, "retriever", mock).
retriever: Retriever | None = None
reranker: Reranker | None = None
generator: Generator | None = None


class AskRequest(BaseModel):
    query: str


async def _stream_response(query: str) -> AsyncGenerator[str, None]:
    """Run the RAG pipeline and yield SSE-formatted strings.

    Pipeline:
    1. retriever.retrieve(query) -> chunks (None = no coverage)
    2. reranker.rerank(query, chunks, top_n=5) -> reranked
    3. generator.generate(query, reranked) -> stream events
    4. Collect full text from text events
    5. route_affiliate(full_text) -> affiliate dict or None
    6. If affiliate found, yield affiliate event before disclosure
    """
    global retriever, reranker, generator
    if retriever is None:
        retriever = Retriever()
    if reranker is None:
        reranker = Reranker()
    if generator is None:
        generator = Generator()

    chunks = retriever.retrieve(query)

    # Only rerank if retrieval returned results; otherwise pass None to generator
    if chunks is not None:
        gen_input = reranker.rerank(query, chunks, top_n=5)
    else:
        gen_input = None

    full_text_parts: list[str] = []
    pending_events: list[dict] = []  # sources + disclosure held until affiliate resolved

    async for event in generator.generate(query, gen_input):
        if event["type"] == "text":
            full_text_parts.append(event["content"])
            yield f"data: {json.dumps(event)}\n\n"
        else:
            # Buffer non-text events (sources, disclosure) so we can inject affiliate
            pending_events.append(event)

    # Resolve affiliate from accumulated text
    full_text = "".join(full_text_parts)
    affiliate = route_affiliate(full_text)

    # Emit buffered events, injecting affiliate before disclosure
    for event in pending_events:
        if event["type"] == "disclosure" and affiliate is not None:
            # Emit affiliate first, then disclosure
            yield f"data: {json.dumps({'type': 'affiliate', 'content': affiliate})}\n\n"
            affiliate = None  # ensure we only emit once
        yield f"data: {json.dumps(event)}\n\n"


@router.post("/api/ask")
async def ask(request: AskRequest) -> StreamingResponse:
    """Stream a RAG-powered travel answer as Server-Sent Events."""
    return StreamingResponse(
        _stream_response(request.query),
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no"},
    )
