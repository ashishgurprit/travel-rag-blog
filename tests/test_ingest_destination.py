"""Tests for scripts/ingest_destination.py — TDD for T14."""
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, call

# Import production modules at top level before any patch() calls (Python 3.14 compat)
import backend.ingestion.youtube
import backend.ingestion.reddit
import backend.ingestion.chunker
import backend.ingestion.embedder
import backend.ingestion.indexer

# Import the module under test — must be importable before implementation exists
# but will raise ImportError until implemented. Tests will fail (not error) once module exists.
import scripts.ingest_destination as ingest_mod


def _make_fake_doc(source_type="youtube", idx=0):
    return {
        "text": f"Some travel text {idx}",
        "video_id": f"vid{idx}",
        "title": f"Video {idx}",
        "destination": "japan",
        "source_type": source_type,
        "url": f"https://example.com/{idx}",
        "language": "en",
        "timestamp_start": 0,
    }


def _make_fake_chunk(idx=0):
    return {
        "text": f"chunk text {idx}",
        "chunk_index": 0,
        "total_chunks": 1,
        "destination": "japan",
        "source_type": "youtube",
        "url": f"https://example.com/{idx}",
        "title": f"Video {idx}",
        "timestamp_seconds": 0,
        "language": "en",
        "vector_id": f"youtube_vid{idx}_0",
        "embedding": [0.1] * 1024,
    }


class TestYoutubeSource:
    def test_youtube_source_fetches_and_upserts(self, tmp_path):
        """YouTube source: fetches transcripts and upserts chunks."""
        # Write a temp video_ids file for japan
        video_ids = ["vid1", "vid2"]
        video_ids_file = tmp_path / "japan_video_ids.json"
        video_ids_file.write_text(json.dumps(video_ids))

        fake_docs = [_make_fake_doc("youtube", i) for i in range(2)]
        fake_chunks = [_make_fake_chunk(i) for i in range(2)]

        mock_indexer_instance = MagicMock()
        mock_indexer_instance.upsert_chunks.return_value = {"upserted": 2, "skipped": 0}

        mock_embedder_instance = MagicMock()
        mock_embedder_instance.embed_chunks.return_value = fake_chunks

        with patch("scripts.ingest_destination.fetch_transcripts", return_value=fake_docs) as mock_fetch_yt, \
             patch("scripts.ingest_destination.chunk_document", return_value=fake_chunks[:1]) as mock_chunk, \
             patch("scripts.ingest_destination.Embedder", return_value=mock_embedder_instance), \
             patch("scripts.ingest_destination.Indexer", return_value=mock_indexer_instance), \
             patch("scripts.ingest_destination.SCRIPTS_DIR", tmp_path):

            result = ingest_mod.run_ingestion(
                destination="japan",
                sources=["youtube"],
                limit=100,
            )

        # fetch_transcripts was called with japan's video ids and destination
        mock_fetch_yt.assert_called_once_with(video_ids, destination="japan")
        # indexer.upsert_chunks was called
        mock_indexer_instance.upsert_chunks.assert_called_once()
        # result has expected keys
        assert "upserted" in result
        assert "skipped" in result


class TestRedditSource:
    def test_reddit_source_fetches_and_upserts(self, tmp_path):
        """Reddit source: fetches posts and upserts chunks."""
        # Write a temp subreddit_map.json
        subreddit_map = {
            "japan": ["JapanTravel", "japanlife"],
            "thailand": ["ThailandTourism"],
        }
        subreddit_map_file = tmp_path / "subreddit_map.json"
        subreddit_map_file.write_text(json.dumps(subreddit_map))

        fake_docs = [_make_fake_doc("reddit", i) for i in range(3)]
        fake_chunks = [_make_fake_chunk(i) for i in range(3)]

        mock_indexer_instance = MagicMock()
        mock_indexer_instance.upsert_chunks.return_value = {"upserted": 3, "skipped": 0}

        mock_embedder_instance = MagicMock()
        mock_embedder_instance.embed_chunks.return_value = fake_chunks

        with patch("scripts.ingest_destination.fetch_posts", return_value=fake_docs) as mock_fetch_reddit, \
             patch("scripts.ingest_destination.chunk_document", return_value=fake_chunks[:1]) as mock_chunk, \
             patch("scripts.ingest_destination.Embedder", return_value=mock_embedder_instance), \
             patch("scripts.ingest_destination.Indexer", return_value=mock_indexer_instance), \
             patch("scripts.ingest_destination.SCRIPTS_DIR", tmp_path):

            result = ingest_mod.run_ingestion(
                destination="japan",
                sources=["reddit"],
                limit=50,
            )

        # fetch_posts was called with japan's subreddits, destination, and limit
        mock_fetch_reddit.assert_called_once_with(
            subreddit_map["japan"],
            destination="japan",
            limit=50,
        )
        mock_indexer_instance.upsert_chunks.assert_called_once()
        assert "upserted" in result


class TestGracefulSkips:
    def test_missing_video_ids_file_skips_youtube_gracefully(self, tmp_path, capsys):
        """When japan_video_ids.json doesn't exist, prints warning and skips (no exception)."""
        # tmp_path has no video_ids file — only subreddit_map
        subreddit_map = {"japan": ["JapanTravel"]}
        (tmp_path / "subreddit_map.json").write_text(json.dumps(subreddit_map))

        mock_indexer_instance = MagicMock()
        mock_indexer_instance.upsert_chunks.return_value = {"upserted": 0, "skipped": 0}
        mock_embedder_instance = MagicMock()
        mock_embedder_instance.embed_chunks.return_value = []

        with patch("scripts.ingest_destination.fetch_transcripts") as mock_fetch_yt, \
             patch("scripts.ingest_destination.fetch_posts", return_value=[]) as mock_fetch_reddit, \
             patch("scripts.ingest_destination.chunk_document", return_value=[]), \
             patch("scripts.ingest_destination.Embedder", return_value=mock_embedder_instance), \
             patch("scripts.ingest_destination.Indexer", return_value=mock_indexer_instance), \
             patch("scripts.ingest_destination.SCRIPTS_DIR", tmp_path):

            # Should NOT raise even though file is missing
            result = ingest_mod.run_ingestion(
                destination="japan",
                sources=["youtube"],
                limit=100,
            )

        # fetch_transcripts should NOT be called since file is missing
        mock_fetch_yt.assert_not_called()
        # A warning should have been printed
        captured = capsys.readouterr()
        assert "warning" in captured.out.lower() or "skip" in captured.out.lower()

    def test_missing_subreddit_key_skips_reddit_gracefully(self, tmp_path, capsys):
        """When destination not in subreddit_map, prints warning and skips (no exception)."""
        # subreddit_map.json exists but doesn't have 'turkey' key
        subreddit_map = {"japan": ["JapanTravel"]}
        (tmp_path / "subreddit_map.json").write_text(json.dumps(subreddit_map))

        mock_indexer_instance = MagicMock()
        mock_indexer_instance.upsert_chunks.return_value = {"upserted": 0, "skipped": 0}
        mock_embedder_instance = MagicMock()
        mock_embedder_instance.embed_chunks.return_value = []

        with patch("scripts.ingest_destination.fetch_posts") as mock_fetch_reddit, \
             patch("scripts.ingest_destination.fetch_transcripts", return_value=[]) as mock_fetch_yt, \
             patch("scripts.ingest_destination.chunk_document", return_value=[]), \
             patch("scripts.ingest_destination.Embedder", return_value=mock_embedder_instance), \
             patch("scripts.ingest_destination.Indexer", return_value=mock_indexer_instance), \
             patch("scripts.ingest_destination.SCRIPTS_DIR", tmp_path):

            # Need a video_ids file for turkey so youtube source doesn't interfere
            (tmp_path / "turkey_video_ids.json").write_text("[]")

            # Should NOT raise even though 'turkey' is not in subreddit_map
            result = ingest_mod.run_ingestion(
                destination="turkey",
                sources=["reddit"],
                limit=100,
            )

        # fetch_posts should NOT be called since key is missing
        mock_fetch_reddit.assert_not_called()
        # A warning should have been printed
        captured = capsys.readouterr()
        assert "warning" in captured.out.lower() or "skip" in captured.out.lower()
