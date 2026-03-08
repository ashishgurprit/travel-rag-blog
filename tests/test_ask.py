"""Tests for /api/ask SSE endpoint and /health endpoint.

Python 3.14 compatibility: all production modules imported at top level
before any patch() calls.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Top-level imports of production modules BEFORE any patch() calls
import backend.api.ask
import backend.main
from backend.main import app
from starlette.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_sse(body: str) -> list[dict]:
    """Parse SSE body into a list of event dicts."""
    events = []
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("data:"):
            raw = line[len("data:"):].strip()
            events.append(json.loads(raw))
    return events


def _make_async_gen(items):
    """Return an async generator that yields each item in *items*."""
    async def _gen():
        for item in items:
            yield item
    return _gen()


# ---------------------------------------------------------------------------
# Shared mock events used across tests
# ---------------------------------------------------------------------------

_TEXT_EVENTS = [
    {"type": "text", "content": "Ramen in Tokyo is "},
    {"type": "text", "content": "amazing!"},
    {"type": "sources", "content": [{"title": "Reddit post", "url": "https://example.com", "source_type": "reddit", "timestamp_seconds": 0}]},
    {"type": "disclosure", "content": "This response may contain affiliate links."},
]

_AFFILIATE_DICT = {"program": "klook", "url": "https://www.klook.com/?aff=test", "cta": "Book on Klook"}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestAskEndpoint:
    """Tests for POST /api/ask."""

    def _make_client(self, generator_events, affiliate_return):
        """Build a TestClient with all dependencies mocked."""
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = [{"text": "great ramen", "title": "t", "url": "u", "source_type": "reddit", "timestamp_seconds": 0}]

        mock_reranker = MagicMock()
        mock_reranker.rerank.return_value = [{"text": "great ramen", "title": "t", "url": "u", "source_type": "reddit", "timestamp_seconds": 0}]

        mock_generator = MagicMock()
        mock_generator.generate.return_value = _make_async_gen(generator_events)

        with (
            patch.object(backend.api.ask, "retriever", mock_retriever),
            patch.object(backend.api.ask, "reranker", mock_reranker),
            patch.object(backend.api.ask, "generator", mock_generator),
            patch("backend.api.ask.route_affiliate", return_value=affiliate_return),
        ):
            client = TestClient(app, raise_server_exceptions=True)
            yield client, mock_retriever, mock_reranker, mock_generator

    def test_ask_returns_streaming_response(self):
        """POST /api/ask returns 200 with Content-Type: text/event-stream."""
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = [{"text": "great ramen", "title": "t", "url": "u", "source_type": "reddit", "timestamp_seconds": 0}]
        mock_reranker = MagicMock()
        mock_reranker.rerank.return_value = [{"text": "great ramen", "title": "t", "url": "u", "source_type": "reddit", "timestamp_seconds": 0}]
        mock_generator = MagicMock()
        mock_generator.generate.return_value = _make_async_gen(_TEXT_EVENTS)

        with (
            patch.object(backend.api.ask, "retriever", mock_retriever),
            patch.object(backend.api.ask, "reranker", mock_reranker),
            patch.object(backend.api.ask, "generator", mock_generator),
            patch("backend.api.ask.route_affiliate", return_value=None),
        ):
            client = TestClient(app, raise_server_exceptions=True)
            response = client.post("/api/ask", json={"query": "best ramen tokyo"})

        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

    def test_ask_streams_text_events(self):
        """SSE body contains data: lines with JSON {type: text, ...}."""
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = [{"text": "great ramen", "title": "t", "url": "u", "source_type": "reddit", "timestamp_seconds": 0}]
        mock_reranker = MagicMock()
        mock_reranker.rerank.return_value = [{"text": "great ramen", "title": "t", "url": "u", "source_type": "reddit", "timestamp_seconds": 0}]
        mock_generator = MagicMock()
        mock_generator.generate.return_value = _make_async_gen(_TEXT_EVENTS)

        with (
            patch.object(backend.api.ask, "retriever", mock_retriever),
            patch.object(backend.api.ask, "reranker", mock_reranker),
            patch.object(backend.api.ask, "generator", mock_generator),
            patch("backend.api.ask.route_affiliate", return_value=None),
        ):
            client = TestClient(app, raise_server_exceptions=True)
            response = client.post("/api/ask", json={"query": "best ramen tokyo"})

        events = _parse_sse(response.text)
        text_events = [e for e in events if e["type"] == "text"]
        assert len(text_events) == 2
        assert all("content" in e for e in text_events)

    def test_ask_streams_disclosure_event(self):
        """SSE body ends with {type: disclosure, ...} event."""
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = [{"text": "great ramen", "title": "t", "url": "u", "source_type": "reddit", "timestamp_seconds": 0}]
        mock_reranker = MagicMock()
        mock_reranker.rerank.return_value = [{"text": "great ramen", "title": "t", "url": "u", "source_type": "reddit", "timestamp_seconds": 0}]
        mock_generator = MagicMock()
        mock_generator.generate.return_value = _make_async_gen(_TEXT_EVENTS)

        with (
            patch.object(backend.api.ask, "retriever", mock_retriever),
            patch.object(backend.api.ask, "reranker", mock_reranker),
            patch.object(backend.api.ask, "generator", mock_generator),
            patch("backend.api.ask.route_affiliate", return_value=None),
        ):
            client = TestClient(app, raise_server_exceptions=True)
            response = client.post("/api/ask", json={"query": "best ramen tokyo"})

        events = _parse_sse(response.text)
        assert events, "Expected at least one SSE event"
        # Last event should be disclosure
        assert events[-1]["type"] == "disclosure"

    def test_ask_includes_affiliate_event_when_route_returns_match(self):
        """When route_affiliate returns a match, SSE includes affiliate event before disclosure."""
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = [{"text": "book hotel", "title": "t", "url": "u", "source_type": "reddit", "timestamp_seconds": 0}]
        mock_reranker = MagicMock()
        mock_reranker.rerank.return_value = [{"text": "book hotel", "title": "t", "url": "u", "source_type": "reddit", "timestamp_seconds": 0}]
        mock_generator = MagicMock()
        mock_generator.generate.return_value = _make_async_gen(_TEXT_EVENTS)

        with (
            patch.object(backend.api.ask, "retriever", mock_retriever),
            patch.object(backend.api.ask, "reranker", mock_reranker),
            patch.object(backend.api.ask, "generator", mock_generator),
            patch("backend.api.ask.route_affiliate", return_value=_AFFILIATE_DICT),
        ):
            client = TestClient(app, raise_server_exceptions=True)
            response = client.post("/api/ask", json={"query": "best ramen tokyo"})

        events = _parse_sse(response.text)
        event_types = [e["type"] for e in events]

        assert "affiliate" in event_types, f"Expected 'affiliate' event, got: {event_types}"
        affiliate_idx = event_types.index("affiliate")
        disclosure_idx = event_types.index("disclosure")
        assert affiliate_idx < disclosure_idx, "affiliate event must come before disclosure"

        affiliate_event = events[affiliate_idx]
        assert affiliate_event["content"] == _AFFILIATE_DICT

    def test_ask_no_affiliate_event_when_no_match(self):
        """When route_affiliate returns None, no affiliate event in SSE."""
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = [{"text": "great ramen", "title": "t", "url": "u", "source_type": "reddit", "timestamp_seconds": 0}]
        mock_reranker = MagicMock()
        mock_reranker.rerank.return_value = [{"text": "great ramen", "title": "t", "url": "u", "source_type": "reddit", "timestamp_seconds": 0}]
        mock_generator = MagicMock()
        mock_generator.generate.return_value = _make_async_gen(_TEXT_EVENTS)

        with (
            patch.object(backend.api.ask, "retriever", mock_retriever),
            patch.object(backend.api.ask, "reranker", mock_reranker),
            patch.object(backend.api.ask, "generator", mock_generator),
            patch("backend.api.ask.route_affiliate", return_value=None),
        ):
            client = TestClient(app, raise_server_exceptions=True)
            response = client.post("/api/ask", json={"query": "best ramen tokyo"})

        events = _parse_sse(response.text)
        event_types = [e["type"] for e in events]
        assert "affiliate" not in event_types, f"Did not expect affiliate event, got: {event_types}"


class TestHealthEndpoint:
    """Tests for GET /health."""

    def test_health_returns_ok(self):
        """GET /health returns 200 {status: ok}."""
        client = TestClient(app, raise_server_exceptions=True)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
