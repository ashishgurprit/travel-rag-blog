"""Tests for /api/ask SSE endpoint and /health endpoint.

Python 3.14 compatibility: all production modules imported at top level
before any patch() calls.
"""

import json
from contextlib import ExitStack
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Top-level imports of production modules BEFORE any patch() calls
import backend.api.ask
import backend.main
from backend.main import app
from backend.rag.intent_classifier import IntentResult
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


def _rag_intent():
    return IntentResult(intent="RAG", destination="japan", cities=["tokyo"])


def _make_client(generator_events, affiliate_return=None, intent=None) -> TestClient:
    """Build a TestClient with all external dependencies mocked.

    Returns the client; caller must manage context via ExitStack.
    """
    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = [
        {"text": "great ramen", "title": "t", "url": "u", "source_type": "reddit",
         "timestamp_seconds": 0, "provenance_score": 0.5}
    ]
    mock_reranker = MagicMock()
    mock_reranker.rerank.return_value = [
        {"text": "great ramen", "title": "t", "url": "u", "source_type": "reddit",
         "timestamp_seconds": 0, "provenance_score": 0.5}
    ]
    mock_generator = MagicMock()
    mock_generator.generate.return_value = _make_async_gen(generator_events)

    mock_classifier = MagicMock()
    mock_classifier.classify.return_value = intent or _rag_intent()

    mock_trip_planner = MagicMock()

    stack = ExitStack()
    stack.enter_context(patch.object(backend.api.ask, "retriever", mock_retriever))
    stack.enter_context(patch.object(backend.api.ask, "reranker", mock_reranker))
    stack.enter_context(patch.object(backend.api.ask, "generator", mock_generator))
    stack.enter_context(patch.object(backend.api.ask, "classifier", mock_classifier))
    stack.enter_context(patch.object(backend.api.ask, "trip_planner", mock_trip_planner))
    stack.enter_context(patch("backend.api.ask.route_affiliate", return_value=affiliate_return))
    stack.enter_context(patch("backend.api.ask.search_web", return_value=[]))

    client = TestClient(app, raise_server_exceptions=True)
    return stack, client, mock_generator, mock_trip_planner, mock_classifier


# ---------------------------------------------------------------------------
# Shared mock events used across tests
# ---------------------------------------------------------------------------

_TEXT_EVENTS = [
    {"type": "text", "content": "Ramen in Tokyo is "},
    {"type": "text", "content": "amazing!"},
    {"type": "sources", "content": [{"title": "Reddit post", "url": "https://example.com",
                                     "source_type": "reddit", "timestamp_seconds": 0}]},
    {"type": "disclosure", "content": "This response may contain affiliate links."},
]

_AFFILIATE_DICT = {"program": "klook", "url": "https://www.klook.com/?aff=test", "cta": "Book on Klook"}


# ---------------------------------------------------------------------------
# Tests: RAG path
# ---------------------------------------------------------------------------

class TestAskEndpoint:
    """Tests for POST /api/ask — RAG intent path."""

    def test_ask_returns_streaming_response(self):
        """POST /api/ask returns 200 with Content-Type: text/event-stream."""
        stack, client, *_ = _make_client(_TEXT_EVENTS)
        with stack:
            response = client.post("/api/ask", json={"query": "best ramen tokyo"})
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

    def test_ask_streams_text_events(self):
        """SSE body contains data: lines with JSON {type: text, ...}."""
        stack, client, *_ = _make_client(_TEXT_EVENTS)
        with stack:
            response = client.post("/api/ask", json={"query": "best ramen tokyo"})
        events = _parse_sse(response.text)
        text_events = [e for e in events if e["type"] == "text"]
        assert len(text_events) == 2
        assert all("content" in e for e in text_events)

    def test_ask_streams_disclosure_event(self):
        """SSE body ends with {type: disclosure, ...} event."""
        stack, client, *_ = _make_client(_TEXT_EVENTS)
        with stack:
            response = client.post("/api/ask", json={"query": "best ramen tokyo"})
        events = _parse_sse(response.text)
        assert events, "Expected at least one SSE event"
        assert events[-1]["type"] == "disclosure"

    def test_ask_includes_affiliate_event_when_route_returns_match(self):
        """When route_affiliate returns a match, SSE includes affiliate event before disclosure."""
        stack, client, *_ = _make_client(_TEXT_EVENTS, affiliate_return=_AFFILIATE_DICT)
        with stack:
            response = client.post("/api/ask", json={"query": "best ramen tokyo"})
        events = _parse_sse(response.text)
        event_types = [e["type"] for e in events]

        assert "affiliate" in event_types, f"Expected 'affiliate' event, got: {event_types}"
        affiliate_idx = event_types.index("affiliate")
        disclosure_idx = event_types.index("disclosure")
        assert affiliate_idx < disclosure_idx, "affiliate event must come before disclosure"
        assert events[affiliate_idx]["content"] == _AFFILIATE_DICT

    def test_ask_no_affiliate_event_when_no_match(self):
        """When route_affiliate returns None, no affiliate event in SSE."""
        stack, client, *_ = _make_client(_TEXT_EVENTS, affiliate_return=None)
        with stack:
            response = client.post("/api/ask", json={"query": "best ramen tokyo"})
        events = _parse_sse(response.text)
        assert "affiliate" not in [e["type"] for e in events]

    def test_ask_no_duplicate_sources_or_disclosure(self):
        """Ensure sources and disclosure each appear exactly once (no double-yield bug)."""
        stack, client, *_ = _make_client(_TEXT_EVENTS, affiliate_return=None)
        with stack:
            response = client.post("/api/ask", json={"query": "best ramen tokyo"})
        events = _parse_sse(response.text)
        assert sum(1 for e in events if e["type"] == "sources") == 1
        assert sum(1 for e in events if e["type"] == "disclosure") == 1


# ---------------------------------------------------------------------------
# Tests: Intent routing
# ---------------------------------------------------------------------------

class TestIntentRouting:
    """Tests for the intent classifier routing in /api/ask."""

    def test_rag_intent_uses_generator(self):
        """RAG intent routes to the RAG pipeline (generator is called)."""
        stack, client, mock_generator, *_ = _make_client(
            _TEXT_EVENTS, intent=IntentResult(intent="RAG")
        )
        with stack:
            response = client.post("/api/ask", json={"query": "best ramen in tokyo"})
        assert response.status_code == 200
        assert mock_generator.generate.called

    def test_logistics_intent_uses_trip_planner(self):
        """LOGISTICS intent routes to trip planner (generator is NOT called)."""
        async def _fake_plan(*args, **kwargs):
            yield {"type": "text", "content": "Visa info here."}
            yield {"type": "disclosure", "content": "disclosure text"}

        mock_trip_planner = MagicMock()
        mock_trip_planner.plan.return_value = _fake_plan()

        mock_generator = MagicMock()
        mock_classifier = MagicMock()
        mock_classifier.classify.return_value = IntentResult(intent="LOGISTICS", destination="japan")

        stack = ExitStack()
        stack.enter_context(patch.object(backend.api.ask, "retriever", MagicMock(retrieve=MagicMock(return_value=[]))))
        stack.enter_context(patch.object(backend.api.ask, "reranker", MagicMock(rerank=MagicMock(return_value=[]))))
        stack.enter_context(patch.object(backend.api.ask, "generator", mock_generator))
        stack.enter_context(patch.object(backend.api.ask, "classifier", mock_classifier))
        stack.enter_context(patch.object(backend.api.ask, "trip_planner", mock_trip_planner))
        stack.enter_context(patch("backend.api.ask.route_affiliate", return_value=None))
        stack.enter_context(patch("backend.api.ask.search_web", return_value=[]))
        client = TestClient(app, raise_server_exceptions=True)

        with stack:
            response = client.post("/api/ask", json={"query": "how do I get a Japan visa"})

        assert response.status_code == 200
        assert mock_trip_planner.plan.called
        assert not mock_generator.generate.called

        events = _parse_sse(response.text)
        text_events = [e for e in events if e["type"] == "text"]
        assert any("Visa" in e["content"] for e in text_events)

    def test_session_id_header_passed_to_trip_planner(self):
        """X-Session-ID header is forwarded to trip_planner.plan() as session_id."""
        captured = []

        async def _fake_plan(query, session_id, intent_result=None):
            captured.append(session_id)
            yield {"type": "text", "content": "answer"}
            yield {"type": "disclosure", "content": "d"}

        mock_trip_planner = MagicMock()
        mock_trip_planner.plan.side_effect = _fake_plan
        mock_classifier = MagicMock()
        mock_classifier.classify.return_value = IntentResult(intent="LOGISTICS")

        stack = ExitStack()
        stack.enter_context(patch.object(backend.api.ask, "retriever", MagicMock()))
        stack.enter_context(patch.object(backend.api.ask, "reranker", MagicMock()))
        stack.enter_context(patch.object(backend.api.ask, "generator", MagicMock()))
        stack.enter_context(patch.object(backend.api.ask, "classifier", mock_classifier))
        stack.enter_context(patch.object(backend.api.ask, "trip_planner", mock_trip_planner))
        stack.enter_context(patch("backend.api.ask.route_affiliate", return_value=None))
        stack.enter_context(patch("backend.api.ask.search_web", return_value=[]))
        client = TestClient(app, raise_server_exceptions=True)

        with stack:
            client.post(
                "/api/ask",
                json={"query": "what visa do I need"},
                headers={"X-Session-ID": "session-abc-123"},
            )

        assert captured == ["session-abc-123"]


# ---------------------------------------------------------------------------
# Tests: Health endpoint
# ---------------------------------------------------------------------------

class TestHealthEndpoint:
    """Tests for GET /health."""

    def test_health_returns_ok(self):
        """GET /health returns 200 {status: ok}."""
        client = TestClient(app, raise_server_exceptions=True)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
