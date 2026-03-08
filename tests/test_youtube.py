# tests/test_youtube.py
import pytest
from unittest.mock import patch, MagicMock

import backend.ingestion.youtube  # pre-load so patch() can resolve the target
from backend.ingestion.youtube import fetch_transcripts


def _make_segment(text, start, duration):
    seg = MagicMock()
    seg.text = text
    seg.start = start
    seg.duration = duration
    return seg


def test_fetch_transcripts_returns_correct_schema():
    """Each returned dict has all required keys with correct values."""
    mock_fetched = [
        _make_segment("Welcome to Tokyo", 0.0, 3.5),
        _make_segment("Let's explore Shibuya", 3.5, 4.0),
    ]
    with patch("backend.ingestion.youtube._api.fetch", return_value=mock_fetched), \
         patch("backend.ingestion.youtube.time.sleep"):
        results = fetch_transcripts(["abc123"], destination="japan")

    assert len(results) == 2
    first = results[0]
    assert first["text"] == "Welcome to Tokyo"
    assert first["video_id"] == "abc123"
    assert first["destination"] == "japan"
    assert first["source_type"] == "youtube"
    assert first["timestamp_start"] == 0.0
    assert first["timestamp_end"] == 3.5
    assert first["url"] == "https://www.youtube.com/watch?v=abc123&t=0s"
    assert "title" in first
    assert "language" in first


def test_missing_transcript_is_skipped_gracefully():
    """Videos with no transcript are skipped, others still processed."""
    good_seg = _make_segment("Hello Japan", 0.0, 2.0)

    def raise_for_first(video_id, **kwargs):
        if video_id == "bad_id":
            raise Exception("No transcript available")
        return [good_seg]

    with patch("backend.ingestion.youtube._api.fetch", side_effect=raise_for_first), \
         patch("backend.ingestion.youtube.time.sleep"):
        results = fetch_transcripts(["bad_id", "good_id"], destination="japan")

    assert len(results) == 1
    assert results[0]["video_id"] == "good_id"


def test_url_format_includes_timestamp():
    """URL contains video_id and timestamp in seconds."""
    mock_fetched = [_make_segment("Kyoto temples", 65.5, 3.0)]
    with patch("backend.ingestion.youtube._api.fetch", return_value=mock_fetched), \
         patch("backend.ingestion.youtube.time.sleep"):
        results = fetch_transcripts(["vid999"], destination="japan")

    assert results[0]["url"] == "https://www.youtube.com/watch?v=vid999&t=65s"


def test_rate_limit_sleep_called_between_videos():
    """time.sleep(1) is called between video fetches."""
    mock_fetched = [_make_segment("test", 0.0, 1.0)]
    with patch("backend.ingestion.youtube._api.fetch", return_value=mock_fetched), \
         patch("backend.ingestion.youtube.time.sleep") as mock_sleep:
        fetch_transcripts(["vid1", "vid2"], destination="japan")

    assert mock_sleep.call_count == 2
