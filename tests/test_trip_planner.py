"""Unit tests for TripPlanner — session management and event streaming."""

import json
from unittest.mock import MagicMock, patch

import pytest

from backend.rag.intent_classifier import IntentResult
from backend.rag.trip_planner import (
    TripPlanner,
    _empty_session,
    _enrich_query,
    _format_session_context,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_planner() -> TripPlanner:
    """Build a TripPlanner with all external deps mocked."""
    with (
        patch("backend.rag.trip_planner.anthropic.Anthropic"),
        patch("backend.rag.trip_planner.redis.Redis.from_url") as mock_redis_cls,
    ):
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis_cls.return_value = mock_redis
        planner = TripPlanner()
        planner._redis = mock_redis
        return planner


# ---------------------------------------------------------------------------
# _empty_session
# ---------------------------------------------------------------------------

class TestEmptySession:
    def test_empty_session_structure(self):
        s = _empty_session()
        assert s["destination"] is None
        assert s["travel_dates"] is None
        assert s["passport"] is None
        assert s["budget_tier"] is None
        assert s["confirmed_cities"] == []
        assert s["history"] == []


# ---------------------------------------------------------------------------
# _enrich_query
# ---------------------------------------------------------------------------

class TestEnrichQuery:
    def test_enrich_adds_destination(self):
        q = _enrich_query("visa requirements", {"destination": "japan"})
        assert "japan" in q

    def test_enrich_adds_passport(self):
        q = _enrich_query("visa", {"destination": "japan", "passport": "Australian"})
        assert "Australian" in q

    def test_enrich_base_query_preserved(self):
        q = _enrich_query("how to get there", {})
        assert "how to get there" in q


# ---------------------------------------------------------------------------
# _format_session_context
# ---------------------------------------------------------------------------

class TestFormatSessionContext:
    def test_empty_session_returns_no_context_message(self):
        ctx = _format_session_context(_empty_session())
        assert "No session context" in ctx

    def test_full_session_includes_all_fields(self):
        session = {
            "destination": "japan",
            "travel_dates": "2026-04",
            "passport": "AU",
            "budget_tier": "mid",
            "confirmed_cities": ["tokyo", "kyoto"],
            "history": [],
        }
        ctx = _format_session_context(session)
        assert "japan" in ctx
        assert "2026-04" in ctx
        assert "AU" in ctx
        assert "mid" in ctx
        assert "tokyo" in ctx


# ---------------------------------------------------------------------------
# Session management
# ---------------------------------------------------------------------------

class TestSessionManagement:
    def test_load_session_returns_empty_on_miss(self):
        planner = _make_planner()
        planner._redis.get.return_value = None
        session = planner.load_session("unknown-session")
        assert session == _empty_session()

    def test_load_session_deserializes_stored_data(self):
        planner = _make_planner()
        stored = {"destination": "thailand", "history": [], "travel_dates": None,
                  "passport": None, "budget_tier": None, "confirmed_cities": []}
        planner._redis.get.return_value = json.dumps(stored)
        session = planner.load_session("sess-1")
        assert session["destination"] == "thailand"

    def test_save_session_sets_redis_key_with_ttl(self):
        planner = _make_planner()
        session = _empty_session()
        session["destination"] = "italy"
        planner.save_session("sess-1", session)
        assert planner._redis.set.called
        call_args = planner._redis.set.call_args
        assert "sess-1" in call_args[0][0]   # key contains session id
        assert call_args[1]["ex"] == 86400   # 24h TTL

    def test_save_session_trims_long_history(self):
        planner = _make_planner()
        session = _empty_session()
        # Add 25 turns (50 messages) — over the 10-turn (20 message) limit
        session["history"] = [{"role": "user", "content": f"msg {i}"} for i in range(50)]
        planner.save_session("sess-1", session)
        saved_json = planner._redis.set.call_args[0][1]
        saved = json.loads(saved_json)
        assert len(saved["history"]) == 20  # trimmed to last 10 turns * 2

    def test_save_session_handles_redis_failure_gracefully(self):
        planner = _make_planner()
        import redis
        planner._redis.set.side_effect = redis.exceptions.RedisError("connection lost")
        # Should not raise
        planner.save_session("sess-1", _empty_session())

    def test_load_session_handles_redis_failure_gracefully(self):
        planner = _make_planner()
        import redis
        planner._redis.get.side_effect = redis.exceptions.RedisError("connection lost")
        # Should return empty session, not raise
        session = planner.load_session("sess-1")
        assert session == _empty_session()


# ---------------------------------------------------------------------------
# update_session_from_intent
# ---------------------------------------------------------------------------

class TestUpdateSessionFromIntent:
    def test_seeds_destination_from_intent(self):
        planner = _make_planner()
        session = _empty_session()
        intent = IntentResult(intent="LOGISTICS", destination="turkey")
        planner.update_session_from_intent(session, intent)
        assert session["destination"] == "turkey"

    def test_does_not_overwrite_existing_destination(self):
        planner = _make_planner()
        session = _empty_session()
        session["destination"] = "japan"
        intent = IntentResult(intent="LOGISTICS", destination="italy")
        planner.update_session_from_intent(session, intent)
        assert session["destination"] == "japan"  # unchanged

    def test_merges_new_cities(self):
        planner = _make_planner()
        session = _empty_session()
        session["confirmed_cities"] = ["tokyo"]
        intent = IntentResult(intent="HYBRID", destination="japan", cities=["kyoto", "osaka"])
        planner.update_session_from_intent(session, intent)
        assert set(session["confirmed_cities"]) == {"tokyo", "kyoto", "osaka"}

    def test_seeds_passport_from_intent(self):
        planner = _make_planner()
        session = _empty_session()
        intent = IntentResult(intent="LOGISTICS", passport="AU")
        planner.update_session_from_intent(session, intent)
        assert session["passport"] == "AU"


# ---------------------------------------------------------------------------
# plan() — streaming
# ---------------------------------------------------------------------------

class TestPlan:
    def test_plan_streams_text_and_disclosure(self):
        """plan() yields text + disclosure events from Claude."""
        planner = _make_planner()
        planner._redis.get.return_value = None  # empty session

        # Mock Claude streaming
        mock_stream = MagicMock()
        mock_stream.__enter__ = MagicMock(return_value=mock_stream)
        mock_stream.__exit__ = MagicMock(return_value=False)
        mock_stream.text_stream = iter(["You need a ", "visa on arrival."])
        planner._client.messages.stream.return_value = mock_stream

        with patch("backend.rag.trip_planner.search_web", return_value=[]):
            import asyncio

            async def _collect():
                events = []
                async for event in planner.plan("visa for Japan", session_id="s1"):
                    events.append(event)
                return events

            events = asyncio.run(_collect())

        text_events = [e for e in events if e["type"] == "text"]
        assert len(text_events) == 2
        full_text = "".join(e["content"] for e in text_events)
        assert "visa on arrival" in full_text

        disclosure_events = [e for e in events if e["type"] == "disclosure"]
        assert len(disclosure_events) == 1

    def test_plan_saves_conversation_to_session(self):
        """plan() saves user query + assistant response to Redis session."""
        planner = _make_planner()
        planner._redis.get.return_value = None

        mock_stream = MagicMock()
        mock_stream.__enter__ = MagicMock(return_value=mock_stream)
        mock_stream.__exit__ = MagicMock(return_value=False)
        mock_stream.text_stream = iter(["Transport answer."])
        planner._client.messages.stream.return_value = mock_stream

        with patch("backend.rag.trip_planner.search_web", return_value=[]):
            import asyncio

            async def _run():
                async for _ in planner.plan("how to get from tokyo to kyoto", session_id="s1"):
                    pass

            asyncio.run(_run())

        assert planner._redis.set.called
        saved = json.loads(planner._redis.set.call_args[0][1])
        history = saved["history"]
        assert history[0]["role"] == "user"
        assert "tokyo" in history[0]["content"]
        assert history[1]["role"] == "assistant"

    def test_plan_handles_claude_error_gracefully(self):
        """plan() yields error text event instead of raising on Claude failure."""
        planner = _make_planner()
        planner._redis.get.return_value = None
        planner._client.messages.stream.side_effect = Exception("Claude API down")

        with patch("backend.rag.trip_planner.search_web", return_value=[]):
            import asyncio

            async def _collect():
                events = []
                async for e in planner.plan("visa", session_id="s1"):
                    events.append(e)
                return events

            events = asyncio.run(_collect())

        text_events = [e for e in events if e["type"] == "text"]
        assert any("error" in e["content"].lower() for e in text_events)
