# tests/test_redis_cache.py
import json
import hashlib
import pytest
import redis
from unittest.mock import patch, MagicMock

import backend.cache.redis_client  # pre-load so patch() can resolve the target
from backend.cache.redis_client import QueryCache


def test_cache_key_is_sha256_of_normalized_query():
    """Cache key is sha256 of lowercased+stripped query:destination."""
    with patch("backend.cache.redis_client.redis.Redis") as mock_redis_cls:
        mock_redis_cls.from_url.return_value = MagicMock()
        cache = QueryCache()

    key = cache._make_key("  Best Ramen Tokyo  ", "japan")
    expected = hashlib.sha256("best ramen tokyo:japan".encode()).hexdigest()
    assert key == expected


def test_get_returns_deserialized_results_on_hit():
    """get() returns list[dict] when key exists in Redis."""
    stored = [{"text": "Ramen is great", "score": 0.9}]
    mock_client = MagicMock()
    mock_client.get.return_value = json.dumps(stored)

    with patch("backend.cache.redis_client.redis.Redis") as mock_redis_cls:
        mock_redis_cls.from_url.return_value = mock_client
        cache = QueryCache()

    result = cache.get("best ramen tokyo", "japan")
    assert result == stored


def test_get_returns_none_on_cache_miss():
    """get() returns None when key is not in Redis."""
    mock_client = MagicMock()
    mock_client.get.return_value = None

    with patch("backend.cache.redis_client.redis.Redis") as mock_redis_cls:
        mock_redis_cls.from_url.return_value = mock_client
        cache = QueryCache()

    result = cache.get("nonexistent query", "japan")
    assert result is None


def test_set_stores_json_with_correct_ttl():
    """set() stores JSON with the configured TTL."""
    mock_client = MagicMock()
    results = [{"text": "Tokyo ramen", "score": 0.85}]

    with patch("backend.cache.redis_client.redis.Redis") as mock_redis_cls, \
         patch("backend.cache.redis_client.settings") as mock_settings:
        mock_redis_cls.from_url.return_value = mock_client
        mock_settings.redis_cache_ttl = 86400
        mock_settings.redis_url = "redis://localhost:6379"
        cache = QueryCache()
        cache.set("ramen tokyo", "japan", results)

    mock_client.set.assert_called_once()
    call_kwargs = mock_client.set.call_args
    assert call_kwargs[1].get("ex") == 86400


def test_get_returns_none_on_redis_connection_error():
    """get() returns None (fail open) when Redis is unavailable."""
    mock_client = MagicMock()
    mock_client.get.side_effect = redis.exceptions.ConnectionError("Connection refused")

    with patch("backend.cache.redis_client.redis.Redis") as mock_redis_cls:
        mock_redis_cls.from_url.return_value = mock_client
        cache = QueryCache()

    result = cache.get("some query", "japan")
    assert result is None


def test_set_silently_continues_on_redis_connection_error():
    """set() does not raise when Redis is unavailable."""
    mock_client = MagicMock()
    mock_client.set.side_effect = redis.exceptions.ConnectionError("Connection refused")

    with patch("backend.cache.redis_client.redis.Redis") as mock_redis_cls:
        mock_redis_cls.from_url.return_value = mock_client
        cache = QueryCache()

    # Should not raise
    cache.set("some query", "japan", [{"text": "test"}])
