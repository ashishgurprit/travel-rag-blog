"""RAG retriever: destination detection, Redis cache, Pinecone vector search.

Pipeline:
  1. Detect destination from query text.
  2. Check Redis cache — return immediately on hit.
  3. Embed the query via multilingual-e5-large.
  4. Query Pinecone with optional destination metadata filter.
  5. Apply confidence threshold (0.75) — return None if top score is too low.
  6. Convert matches to dicts, store in Redis, return results.
"""

from pinecone import Pinecone

from backend.cache.redis_client import QueryCache
from backend.config import settings
from backend.ingestion.embedder import Embedder
from backend.rag.destination_detector import detect_destination


class Retriever:
    """Retrieve travel content from Pinecone with Redis caching."""

    def __init__(self) -> None:
        self._cache = QueryCache()
        self._embedder = Embedder()
        self._pc = Pinecone(api_key=settings.pinecone_api_key)
        self._index = self._pc.Index(settings.pinecone_index_name)

    def retrieve(self, query: str, top_k: int = 20) -> list[dict] | None:
        """Return top-k relevant documents for *query*, or None below confidence.

        Args:
            query:  Natural-language search query.
            top_k:  Maximum number of results to return (default 20).

        Returns:
            List of result dicts, or None when the top Pinecone score is below
            ``settings.confidence_threshold``.
        """
        # Step 1: detect destination
        destination = detect_destination(query)

        # Step 2: check Redis cache
        cached = self._cache.get(query, destination)
        if cached is not None:
            return cached

        # Step 3: embed query
        embedding = self._embedder.embed_query(query)

        # Step 4: query Pinecone (with or without destination filter)
        query_kwargs: dict = {
            "vector": embedding,
            "top_k": top_k,
            "include_metadata": True,
        }
        if destination != "unknown":
            query_kwargs["filter"] = {"destination": {"$eq": destination}}

        results = self._index.query(**query_kwargs)

        # Step 5: confidence threshold check
        if not results.matches or results.matches[0].score < settings.confidence_threshold:
            return None

        # Step 6: convert matches to dicts
        results_list = [
            {
                "text": match.metadata.get("text", ""),
                "score": match.score,
                "url": match.metadata.get("url", ""),
                "title": match.metadata.get("title", ""),
                "timestamp_seconds": match.metadata.get("timestamp_seconds", 0),
                "source_type": match.metadata.get("source_type", ""),
                "destination": match.metadata.get("destination", ""),
            }
            for match in results.matches
        ]

        # Step 7: cache results
        self._cache.set(query, destination, results_list)

        # Step 8: return
        return results_list
