# tests/test_embedder.py
import math
import pytest
from unittest.mock import patch, MagicMock

import backend.ingestion.embedder  # pre-load so patch() can resolve the target
from backend.ingestion.embedder import Embedder


def _make_mock_model(dim=1024):
    """Returns a mock SentenceTransformer that produces normalized vectors."""
    import numpy as np
    model = MagicMock()

    def fake_encode(texts, batch_size=32, normalize_embeddings=True, **kwargs):
        n = len(texts) if isinstance(texts, list) else 1
        vecs = np.ones((n, dim)) / math.sqrt(dim)
        return vecs

    model.encode = MagicMock(side_effect=fake_encode)
    return model


def test_embed_chunks_adds_embedding_of_correct_dimension():
    """embed_chunks adds 'embedding' key with 1024-dimensional vector."""
    mock_model = _make_mock_model(1024)
    with patch("backend.ingestion.embedder.SentenceTransformer", return_value=mock_model):
        embedder = Embedder()
        chunks = [{"text": "Hello Tokyo", "chunk_index": 0}]
        result = embedder.embed_chunks(chunks)

    assert "embedding" in result[0]
    assert len(result[0]["embedding"]) == 1024


def test_embed_chunks_normalizes_embeddings():
    """Returned embeddings have magnitude ≈ 1.0."""
    mock_model = _make_mock_model(1024)
    with patch("backend.ingestion.embedder.SentenceTransformer", return_value=mock_model):
        embedder = Embedder()
        chunks = [{"text": "Kyoto temples", "chunk_index": 0}]
        result = embedder.embed_chunks(chunks)

    emb = result[0]["embedding"]
    magnitude = math.sqrt(sum(x**2 for x in emb))
    assert abs(magnitude - 1.0) < 1e-4


def test_passage_prefix_applied_to_chunks():
    """'passage: ' prefix is prepended to chunk text before embedding."""
    mock_model = _make_mock_model(1024)
    with patch("backend.ingestion.embedder.SentenceTransformer", return_value=mock_model):
        embedder = Embedder()
        chunks = [{"text": "great ramen", "chunk_index": 0}]
        embedder.embed_chunks(chunks)

    call_args = mock_model.encode.call_args
    texts_passed = call_args[0][0]
    assert texts_passed[0].startswith("passage: ")


def test_query_prefix_applied_to_queries():
    """'query: ' prefix is prepended to query text before embedding."""
    mock_model = _make_mock_model(1024)
    with patch("backend.ingestion.embedder.SentenceTransformer", return_value=mock_model):
        embedder = Embedder()
        embedder.embed_query("best sushi tokyo")

    call_args = mock_model.encode.call_args
    texts_passed = call_args[0][0]
    assert texts_passed.startswith("query: ")


def test_batch_processing_uses_batch_size_32():
    """embed_chunks calls encode with batch_size=32."""
    mock_model = _make_mock_model(1024)
    with patch("backend.ingestion.embedder.SentenceTransformer", return_value=mock_model):
        embedder = Embedder()
        chunks = [{"text": f"chunk {i}", "chunk_index": i} for i in range(10)]
        embedder.embed_chunks(chunks)

    call_kwargs = mock_model.encode.call_args[1]
    assert call_kwargs.get("batch_size") == 32


def test_embed_chunks_returns_same_list_with_embeddings():
    """embed_chunks modifies chunks in-place and returns the same list."""
    mock_model = _make_mock_model(1024)
    with patch("backend.ingestion.embedder.SentenceTransformer", return_value=mock_model):
        embedder = Embedder()
        chunks = [{"text": "test", "chunk_index": 0}, {"text": "test2", "chunk_index": 1}]
        result = embedder.embed_chunks(chunks)

    assert result is chunks
    assert all("embedding" in c for c in chunks)
