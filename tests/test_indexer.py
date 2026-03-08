# tests/test_indexer.py
import pytest
from unittest.mock import patch, MagicMock

import backend.ingestion.indexer
from backend.ingestion.indexer import Indexer


def _make_chunk(i=0, existing=False):
    return {
        "vector_id": f"youtube_vid{i}_{i}",
        "embedding": [0.1] * 1024,
        "text": f"chunk {i}",
        "destination": "japan",
        "source_type": "youtube",
        "url": f"https://youtube.com/watch?v=vid{i}&t=0s",
        "title": f"Video {i}",
        "timestamp_seconds": 0,
        "language": "en",
        "chunk_index": i,
        "total_chunks": 5,
    }


def _make_indexer_with_mock():
    mock_index = MagicMock()
    mock_pc = MagicMock()
    mock_pc.Index.return_value = mock_index
    with patch("backend.ingestion.indexer.Pinecone", return_value=mock_pc):
        indexer = Indexer()
    return indexer, mock_index


def test_upsert_chunks_calls_pinecone_upsert():
    """upsert_chunks upserts new chunks to Pinecone."""
    indexer, mock_index = _make_indexer_with_mock()
    mock_index.fetch.return_value = MagicMock(vectors={})  # no existing vectors

    chunks = [_make_chunk(i) for i in range(3)]
    result = indexer.upsert_chunks(chunks)

    assert mock_index.upsert.called
    assert result["upserted"] == 3
    assert result["skipped"] == 0


def test_upsert_chunks_batches_in_100():
    """upsert_chunks calls upsert in batches of 100."""
    indexer, mock_index = _make_indexer_with_mock()
    mock_index.fetch.return_value = MagicMock(vectors={})

    chunks = [_make_chunk(i) for i in range(250)]
    indexer.upsert_chunks(chunks)

    # 250 chunks → 3 upsert calls (100 + 100 + 50)
    assert mock_index.upsert.call_count == 3


def test_existing_vectors_are_skipped():
    """Chunks with vector_ids already in Pinecone are skipped."""
    indexer, mock_index = _make_indexer_with_mock()

    chunks = [_make_chunk(0), _make_chunk(1)]
    # Simulate chunk 0 already exists
    mock_index.fetch.return_value = MagicMock(vectors={"youtube_vid0_0": MagicMock()})

    result = indexer.upsert_chunks(chunks)

    assert result["skipped"] == 1
    assert result["upserted"] == 1


def test_upsert_payload_contains_metadata():
    """Upserted vectors include correct metadata fields."""
    indexer, mock_index = _make_indexer_with_mock()
    mock_index.fetch.return_value = MagicMock(vectors={})

    chunk = _make_chunk(0)
    indexer.upsert_chunks([chunk])

    call_args = mock_index.upsert.call_args[1]  # kwargs
    vectors = call_args["vectors"]
    assert len(vectors) == 1
    v = vectors[0]
    assert v["id"] == "youtube_vid0_0"
    assert len(v["values"]) == 1024
    assert v["metadata"]["destination"] == "japan"
    assert v["metadata"]["source_type"] == "youtube"
    assert v["metadata"]["text"] == "chunk 0"
    assert v["metadata"]["total_chunks"] == 5
