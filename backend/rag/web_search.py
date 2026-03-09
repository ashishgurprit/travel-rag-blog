"""Tavily web search for live travel info (prices, advisories, visa requirements)."""

from __future__ import annotations

import logging

from backend.config import settings

logger = logging.getLogger(__name__)


def search_web(query: str, max_results: int = 3) -> list[dict]:
    """Search Tavily for live web results to augment Pinecone retrieval.

    Returns a list of chunk-compatible dicts with keys:
        text, title, url, source_type, timestamp_seconds

    Returns [] if TAVILY_API_KEY is not configured or the request fails.
    """
    if not settings.tavily_api_key:
        return []

    try:
        from tavily import TavilyClient  # noqa: PLC0415

        client = TavilyClient(api_key=settings.tavily_api_key)
        response = client.search(
            query=query,
            search_depth="basic",
            max_results=max_results,
            include_answer=False,
        )
        results = []
        for r in response.get("results", []):
            content = r.get("content", "").strip()
            if not content:
                continue
            results.append(
                {
                    "text": content,
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "source_type": "web",
                    "timestamp_seconds": 0,
                    "score": r.get("score", 0.0),
                }
            )
        return results
    except Exception as exc:  # noqa: BLE001
        logger.warning("Tavily search failed: %s", exc)
        return []
