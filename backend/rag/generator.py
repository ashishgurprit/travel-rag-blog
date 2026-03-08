"""Claude Sonnet streaming generator for RAG answers."""

from typing import AsyncGenerator
import anthropic

from backend.config import settings

_SYSTEM_PROMPT = (
    "You are a knowledgeable travel assistant specialising in Japan, Thailand, "
    "Italy, Turkey, and South Korea.\n"
    "Answer the user's question using ONLY the provided source excerpts.\n"
    "Always cite sources inline as [Source N].\n"
    "Suggest ONE relevant booking action at the end (hotel, tour, or money transfer).\n"
    "If the sources don't contain enough information, say so honestly."
)

_DISCLOSURE = (
    "This response may contain affiliate links. "
    "We may earn a commission at no cost to you."
)

_NO_COVERAGE_MSG = (
    "I don't have reliable information on this destination yet. "
    "Try asking about Japan, Thailand, Italy, Turkey, or South Korea."
)


class Generator:
    """Streams Claude Sonnet answers from retrieved RAG context."""

    def __init__(self) -> None:
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    async def generate(
        self,
        query: str,
        chunks: list[dict] | None,
    ) -> AsyncGenerator[dict, None]:
        """Yield SSE-style event dicts: {type, content}.

        Event types: 'text' | 'sources' | 'disclosure'
        """
        if chunks is None:
            yield {"type": "text", "content": _NO_COVERAGE_MSG}
            yield {"type": "disclosure", "content": _DISCLOSURE}
            return

        # Build context string
        context_parts = []
        for i, chunk in enumerate(chunks):
            title = chunk.get("title", "")
            url = chunk.get("url", "")
            context_parts.append(f"[Source {i + 1}: {title} ({url})]\n{chunk['text']}")
        context = "\n\n".join(context_parts)

        # Stream answer
        with self._client.messages.stream(
            model="claude-sonnet-4-5",
            max_tokens=1024,
            system=_SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\nQuestion: {query}",
                }
            ],
        ) as stream:
            for token in stream.text_stream:
                yield {"type": "text", "content": token}

        # Sources after all text
        sources = [
            {
                "title": c.get("title", ""),
                "url": c.get("url", ""),
                "source_type": c.get("source_type", ""),
                "timestamp_seconds": c.get("timestamp_seconds", 0),
            }
            for c in chunks
        ]
        yield {"type": "sources", "content": sources}
        yield {"type": "disclosure", "content": _DISCLOSURE}
