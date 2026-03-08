"""Redis query cache client.

Caches RAG retrieval results to avoid redundant Pinecone + Claude calls.
Fails open — if Redis is unavailable, queries proceed normally.
"""

import hashlib
import json
import redis

from backend.config import settings


class QueryCache:
    """SHA256-keyed Redis cache for RAG query results."""

    def __init__(self) -> None:
        self._client = redis.Redis.from_url(settings.redis_url, decode_responses=True)

    def _make_key(self, query: str, destination: str) -> str:
        normalized = f"{query.lower().strip()}:{destination}"
        return hashlib.sha256(normalized.encode()).hexdigest()

    def get(self, query: str, destination: str) -> list[dict] | None:
        """Return cached results or None on miss / connection failure."""
        try:
            value = self._client.get(self._make_key(query, destination))
            if value is None:
                return None
            return json.loads(value)
        except redis.exceptions.ConnectionError as e:
            print(f"Warning: Redis unavailable: {e}")
            return None

    def set(self, query: str, destination: str, results: list[dict]) -> None:
        """Store results in Redis with configured TTL. Fails open on error."""
        try:
            self._client.set(
                self._make_key(query, destination),
                json.dumps(results),
                ex=settings.redis_cache_ttl,
            )
        except redis.exceptions.ConnectionError as e:
            print(f"Warning: Redis unavailable, skipping cache write: {e}")
