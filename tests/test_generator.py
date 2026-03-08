# tests/test_generator.py
import asyncio
import pytest
from unittest.mock import patch, MagicMock

import backend.rag.generator  # pre-load so patch() can resolve the target
from backend.rag.generator import Generator


def _collect(async_gen):
    """Collect all events from an async generator into a list."""
    async def _inner():
        events = []
        async for event in async_gen:
            events.append(event)
        return events
    return asyncio.run(_inner())


def _make_mock_stream(tokens=None):
    """Returns a mock that behaves like anthropic streaming context manager."""
    tokens = tokens or ["Hello", " Tokyo", "!"]
    mock_stream = MagicMock()
    mock_stream.__enter__ = MagicMock(return_value=mock_stream)
    mock_stream.__exit__ = MagicMock(return_value=False)
    mock_stream.text_stream = iter(tokens)
    return mock_stream


def test_no_coverage_yields_informative_message():
    """When chunks=None, yields a text event saying no info available."""
    with patch("backend.rag.generator.anthropic.Anthropic"):
        gen = Generator()
        events = _collect(gen.generate("best ramen in mars", None))

    text_events = [e for e in events if e["type"] == "text"]
    assert len(text_events) == 1
    assert "reliable" in text_events[0]["content"].lower()


def test_no_coverage_always_yields_disclosure():
    """Disclosure event is always the last event, even for NO_COVERAGE."""
    with patch("backend.rag.generator.anthropic.Anthropic"):
        gen = Generator()
        events = _collect(gen.generate("query", None))

    assert events[-1]["type"] == "disclosure"


def test_text_events_yielded_during_streaming():
    """One text event per token is yielded when chunks provided."""
    mock_stream = _make_mock_stream(["Great", " sushi", " in", " Tokyo"])
    chunks = [{"text": "Sushi in Tokyo", "title": "Guide", "url": "http://example.com",
               "source_type": "youtube", "timestamp_seconds": 0}]

    with patch("backend.rag.generator.anthropic.Anthropic") as mock_anthropic_cls:
        mock_client = MagicMock()
        mock_client.messages.stream.return_value = mock_stream
        mock_anthropic_cls.return_value = mock_client
        gen = Generator()
        events = _collect(gen.generate("best sushi tokyo", chunks))

    text_events = [e for e in events if e["type"] == "text"]
    assert len(text_events) == 4
    assert text_events[0]["content"] == "Great"


def test_sources_event_yielded_after_text():
    """Sources event comes after all text events, before disclosure."""
    mock_stream = _make_mock_stream(["Answer"])
    chunks = [{"text": "Ramen info", "title": "Ramen Guide", "url": "https://yt.com/v/abc",
               "source_type": "youtube", "timestamp_seconds": 10}]

    with patch("backend.rag.generator.anthropic.Anthropic") as mock_anthropic_cls:
        mock_client = MagicMock()
        mock_client.messages.stream.return_value = mock_stream
        mock_anthropic_cls.return_value = mock_client
        gen = Generator()
        events = _collect(gen.generate("ramen", chunks))

    types = [e["type"] for e in events]
    assert "sources" in types
    assert types.index("sources") < types.index("disclosure")

    sources_event = next(e for e in events if e["type"] == "sources")
    assert isinstance(sources_event["content"], list)
    assert sources_event["content"][0]["url"] == "https://yt.com/v/abc"


def test_disclosure_always_last():
    """Disclosure event is always the very last event."""
    mock_stream = _make_mock_stream(["token"])
    chunks = [{"text": "x", "title": "", "url": "", "source_type": "reddit", "timestamp_seconds": 0}]

    with patch("backend.rag.generator.anthropic.Anthropic") as mock_anthropic_cls:
        mock_client = MagicMock()
        mock_client.messages.stream.return_value = mock_stream
        mock_anthropic_cls.return_value = mock_client
        gen = Generator()
        events = _collect(gen.generate("query", chunks))

    assert events[-1]["type"] == "disclosure"
    assert "affiliate" in events[-1]["content"].lower()


def test_system_prompt_contains_required_phrases():
    """System prompt mentions the 5 destinations and citation instructions."""
    mock_stream = _make_mock_stream([])
    chunks = [{"text": "x", "title": "", "url": "", "source_type": "reddit", "timestamp_seconds": 0}]

    captured_kwargs = {}

    def capture_stream(**kwargs):
        captured_kwargs.update(kwargs)
        return mock_stream

    with patch("backend.rag.generator.anthropic.Anthropic") as mock_anthropic_cls:
        mock_client = MagicMock()
        mock_client.messages.stream.side_effect = capture_stream
        mock_anthropic_cls.return_value = mock_client
        gen = Generator()
        _collect(gen.generate("test", chunks))

    system = captured_kwargs.get("system", "")
    assert "Japan" in system
    assert "Thailand" in system
    assert "Source" in system
