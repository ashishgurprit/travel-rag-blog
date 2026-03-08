# tests/test_retriever.py
from unittest.mock import patch, MagicMock

import backend.rag.retriever
from backend.rag.retriever import Retriever


def _make_pinecone_match(score, metadata=None):
    match = MagicMock()
    match.score = score
    match.metadata = metadata or {"text": "Ramen in Tokyo", "url": "http://yt.com",
                                   "title": "Japan Guide", "timestamp_seconds": 0,
                                   "source_type": "youtube", "destination": "japan"}
    return match


def _make_mock_pinecone_results(scores):
    results = MagicMock()
    results.matches = [_make_pinecone_match(s) for s in scores]
    return results


def test_returns_none_when_top_score_below_threshold():
    """Returns None when top match score < 0.75 (confidence threshold)."""
    pinecone_results = _make_mock_pinecone_results([0.60, 0.55])

    with patch("backend.rag.retriever.Pinecone") as mock_pc_cls, \
         patch("backend.rag.retriever.Embedder") as mock_emb_cls, \
         patch("backend.rag.retriever.QueryCache") as mock_cache_cls, \
         patch("backend.rag.retriever.detect_destination", return_value="japan"):
        mock_pc_cls.return_value.Index.return_value.query.return_value = pinecone_results
        mock_emb_cls.return_value.embed_query.return_value = [0.1] * 1024
        mock_cache_cls.return_value.get.return_value = None

        retriever = Retriever()
        result = retriever.retrieve("random query")

    assert result is None


def test_returns_cached_result_without_calling_pinecone():
    """Returns cached result; Pinecone is NOT called on cache hit."""
    cached = [{"text": "cached result", "score": 0.9}]

    with patch("backend.rag.retriever.Pinecone") as mock_pc_cls, \
         patch("backend.rag.retriever.Embedder") as mock_emb_cls, \
         patch("backend.rag.retriever.QueryCache") as mock_cache_cls, \
         patch("backend.rag.retriever.detect_destination", return_value="japan"):
        mock_cache_cls.return_value.get.return_value = cached
        mock_index = mock_pc_cls.return_value.Index.return_value

        retriever = Retriever()
        result = retriever.retrieve("best ramen tokyo")

    assert result == cached
    mock_index.query.assert_not_called()


def test_pinecone_called_with_destination_filter():
    """When destination detected, Pinecone query uses metadata filter."""
    pinecone_results = _make_mock_pinecone_results([0.85, 0.80])

    with patch("backend.rag.retriever.Pinecone") as mock_pc_cls, \
         patch("backend.rag.retriever.Embedder") as mock_emb_cls, \
         patch("backend.rag.retriever.QueryCache") as mock_cache_cls, \
         patch("backend.rag.retriever.detect_destination", return_value="japan"):
        mock_index = mock_pc_cls.return_value.Index.return_value
        mock_index.query.return_value = pinecone_results
        mock_emb_cls.return_value.embed_query.return_value = [0.1] * 1024
        mock_cache_cls.return_value.get.return_value = None

        retriever = Retriever()
        retriever.retrieve("best ramen tokyo")

    call_kwargs = mock_index.query.call_args[1]
    assert call_kwargs.get("filter") == {"destination": {"$eq": "japan"}}


def test_pinecone_called_without_filter_for_unknown_destination():
    """When destination='unknown', Pinecone query has no metadata filter."""
    pinecone_results = _make_mock_pinecone_results([0.85])

    with patch("backend.rag.retriever.Pinecone") as mock_pc_cls, \
         patch("backend.rag.retriever.Embedder") as mock_emb_cls, \
         patch("backend.rag.retriever.QueryCache") as mock_cache_cls, \
         patch("backend.rag.retriever.detect_destination", return_value="unknown"):
        mock_index = mock_pc_cls.return_value.Index.return_value
        mock_index.query.return_value = pinecone_results
        mock_emb_cls.return_value.embed_query.return_value = [0.1] * 1024
        mock_cache_cls.return_value.get.return_value = None

        retriever = Retriever()
        retriever.retrieve("best beaches anywhere")

    call_kwargs = mock_index.query.call_args[1]
    assert "filter" not in call_kwargs


def test_results_stored_in_cache_after_pinecone_query():
    """After Pinecone query, results are stored in Redis cache."""
    pinecone_results = _make_mock_pinecone_results([0.90, 0.85])

    with patch("backend.rag.retriever.Pinecone") as mock_pc_cls, \
         patch("backend.rag.retriever.Embedder") as mock_emb_cls, \
         patch("backend.rag.retriever.QueryCache") as mock_cache_cls, \
         patch("backend.rag.retriever.detect_destination", return_value="japan"):
        mock_index = mock_pc_cls.return_value.Index.return_value
        mock_index.query.return_value = pinecone_results
        mock_emb_cls.return_value.embed_query.return_value = [0.1] * 1024
        mock_cache = mock_cache_cls.return_value
        mock_cache.get.return_value = None

        retriever = Retriever()
        result = retriever.retrieve("ramen tokyo")

    assert mock_cache.set.called
    assert result is not None
    assert len(result) == 2
