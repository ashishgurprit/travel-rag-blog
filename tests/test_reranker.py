# tests/test_reranker.py
import pytest
from unittest.mock import MagicMock

import backend.rag.reranker  # pre-load module (lazy FlagEmbedding import inside _load_model)
from backend.rag.reranker import Reranker


def _reranker_with_mock(scores: list[float]) -> tuple["Reranker", MagicMock]:
    """Create a Reranker with _model pre-injected to avoid loading FlagEmbedding."""
    mock_model = MagicMock()
    mock_model.compute_score.return_value = scores
    reranker = Reranker()
    reranker._model = mock_model  # inject before rerank() calls _load_model
    return reranker, mock_model


def test_rerank_returns_top_n_sorted_by_score():
    """rerank returns top_n chunks sorted by rerank_score descending."""
    chunks = [
        {"text": "Kyoto temples", "score": 0.8},
        {"text": "Tokyo ramen", "score": 0.9},
        {"text": "Osaka castle", "score": 0.7},
        {"text": "Nara deer", "score": 0.85},
        {"text": "Fuji views", "score": 0.75},
        {"text": "Hiroshima memorial", "score": 0.6},
    ]
    reranker, _ = _reranker_with_mock([0.3, 0.9, 0.1, 0.7, 0.5, 0.2])
    result = reranker.rerank("best places in Japan", chunks, top_n=3)

    assert len(result) == 3
    scores = [r["rerank_score"] for r in result]
    assert scores == sorted(scores, reverse=True)
    assert result[0]["text"] == "Tokyo ramen"  # score 0.9 = highest


def test_rerank_adds_rerank_score_to_chunks():
    """rerank adds 'rerank_score' key to returned chunks."""
    chunks = [{"text": "Ramen in Tokyo", "score": 0.8}]
    reranker, _ = _reranker_with_mock([0.75])
    result = reranker.rerank("ramen", chunks)

    assert "rerank_score" in result[0]
    assert result[0]["rerank_score"] == 0.75


def test_rerank_empty_chunks_returns_empty():
    """rerank returns [] when chunks is empty."""
    reranker = Reranker()
    result = reranker.rerank("test query", [])
    assert result == []


def test_rerank_none_chunks_returns_empty():
    """rerank returns [] when chunks is None."""
    reranker = Reranker()
    result = reranker.rerank("test query", None)
    assert result == []


def test_rerank_fewer_than_top_n_returns_all():
    """When input has fewer chunks than top_n, all are returned sorted."""
    chunks = [
        {"text": "Osaka food", "score": 0.8},
        {"text": "Kyoto shrine", "score": 0.7},
    ]
    reranker, _ = _reranker_with_mock([0.4, 0.9])
    result = reranker.rerank("Japan sights", chunks, top_n=10)

    assert len(result) == 2
    assert result[0]["text"] == "Kyoto shrine"  # 0.9 > 0.4


def test_query_chunk_pairs_passed_to_compute_score():
    """rerank passes [query, chunk_text] pairs to compute_score."""
    chunks = [{"text": "Ramen shop Tokyo", "score": 0.8}]
    reranker, mock_model = _reranker_with_mock([0.8])
    reranker.rerank("best ramen", chunks)

    call_args = mock_model.compute_score.call_args[0][0]
    assert call_args == [["best ramen", "Ramen shop Tokyo"]]
