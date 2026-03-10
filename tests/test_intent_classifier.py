"""Unit tests for IntentClassifier and _parse_result."""

import json
from unittest.mock import MagicMock, patch

import pytest

from backend.rag.intent_classifier import IntentClassifier, IntentResult, _parse_result


# ---------------------------------------------------------------------------
# _parse_result
# ---------------------------------------------------------------------------

class TestParseResult:
    """Tests for _parse_result — JSON → IntentResult."""

    def test_rag_intent_parsed(self):
        raw = json.dumps({"intent": "RAG", "destination": "japan", "cities": ["tokyo"]})
        result = _parse_result(raw)
        assert result.intent == "RAG"
        assert result.destination == "japan"
        assert result.cities == ["tokyo"]

    def test_logistics_intent_parsed(self):
        raw = json.dumps({
            "intent": "LOGISTICS",
            "destination": "japan",
            "cities": [],
            "passport": "AU",
            "travel_dates": "2026-04",
            "budget_tier": None,
        })
        result = _parse_result(raw)
        assert result.intent == "LOGISTICS"
        assert result.passport == "AU"
        assert result.travel_dates == "2026-04"

    def test_hybrid_intent_parsed(self):
        raw = json.dumps({"intent": "HYBRID", "destination": "thailand", "cities": ["bangkok"]})
        result = _parse_result(raw)
        assert result.intent == "HYBRID"

    def test_budget_tier_parsed(self):
        raw = json.dumps({"intent": "RAG", "destination": "italy", "budget_tier": "luxury"})
        result = _parse_result(raw)
        assert result.budget_tier == "luxury"

    def test_unknown_intent_falls_back_to_rag(self):
        raw = json.dumps({"intent": "UNKNOWN"})
        result = _parse_result(raw)
        assert result.intent == "RAG"

    def test_invalid_json_falls_back_to_rag(self):
        result = _parse_result("not json at all")
        assert result.intent == "RAG"

    def test_markdown_fences_stripped(self):
        raw = "```json\n" + json.dumps({"intent": "RAG", "destination": "turkey"}) + "\n```"
        result = _parse_result(raw)
        assert result.intent == "RAG"
        assert result.destination == "turkey"

    def test_missing_cities_defaults_to_empty_list(self):
        raw = json.dumps({"intent": "RAG"})
        result = _parse_result(raw)
        assert result.cities == []

    def test_null_cities_defaults_to_empty_list(self):
        raw = json.dumps({"intent": "RAG", "cities": None})
        result = _parse_result(raw)
        assert result.cities == []


# ---------------------------------------------------------------------------
# IntentResult properties
# ---------------------------------------------------------------------------

class TestIntentResultProperties:
    """Tests for needs_rag and needs_logistics properties."""

    def test_rag_needs_rag_true(self):
        r = IntentResult(intent="RAG")
        assert r.needs_rag is True
        assert r.needs_logistics is False

    def test_logistics_needs_logistics_true(self):
        r = IntentResult(intent="LOGISTICS")
        assert r.needs_rag is False
        assert r.needs_logistics is True

    def test_hybrid_needs_both(self):
        r = IntentResult(intent="HYBRID")
        assert r.needs_rag is True
        assert r.needs_logistics is True


# ---------------------------------------------------------------------------
# IntentClassifier
# ---------------------------------------------------------------------------

class TestIntentClassifier:
    """Tests for IntentClassifier.classify() — mocks Anthropic client."""

    def _make_classifier(self) -> IntentClassifier:
        with patch("backend.rag.intent_classifier.anthropic.Anthropic"):
            return IntentClassifier()

    def test_classify_calls_claude(self):
        """classify() calls self._client.messages.create with the correct model."""
        classifier = self._make_classifier()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps({"intent": "RAG", "destination": "japan", "cities": []}))]
        classifier._client.messages.create.return_value = mock_response

        result = classifier.classify("best ramen in tokyo")

        assert classifier._client.messages.create.called
        call_kwargs = classifier._client.messages.create.call_args[1]
        assert call_kwargs["model"] == "claude-haiku-4-5-20251001"
        assert result.intent == "RAG"
        assert result.destination == "japan"

    def test_classify_falls_back_on_api_error(self):
        """classify() returns RAG intent on any API exception."""
        classifier = self._make_classifier()
        classifier._client.messages.create.side_effect = Exception("API error")

        result = classifier.classify("best ramen in tokyo")

        assert result.intent == "RAG"

    def test_classify_extracts_passport(self):
        """Passport/nationality entity is extracted from classifier response."""
        classifier = self._make_classifier()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps({
            "intent": "LOGISTICS",
            "destination": "japan",
            "cities": [],
            "passport": "AU",
            "travel_dates": None,
            "budget_tier": None,
        }))]
        classifier._client.messages.create.return_value = mock_response

        result = classifier.classify("Japan visa requirements for Australian passport")

        assert result.passport == "AU"
        assert result.needs_logistics is True

    def test_classify_extracts_multiple_cities(self):
        """Multiple cities extracted from classifier response."""
        classifier = self._make_classifier()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps({
            "intent": "HYBRID",
            "destination": "japan",
            "cities": ["tokyo", "kyoto", "osaka"],
            "travel_dates": "2026-04",
            "passport": None,
            "budget_tier": "mid",
        }))]
        classifier._client.messages.create.return_value = mock_response

        result = classifier.classify("Plan my 7-day Japan trip through Tokyo Kyoto Osaka")

        assert set(result.cities) == {"tokyo", "kyoto", "osaka"}
        assert result.budget_tier == "mid"
        assert result.travel_dates == "2026-04"
