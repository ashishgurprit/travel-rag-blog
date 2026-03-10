"""Google Trends + yt-dlp search discovery.

Uses pytrends to find what travel topics are trending for each
destination, then feeds those queries into yt-dlp's built-in YouTube
search to extract video IDs — without downloading any audio.

No IP rotation needed: yt-dlp search is lightweight and doesn't
trigger YouTube's rate limiting at the volumes we use.

Requires: pip install pytrends yt-dlp
"""

import json
import subprocess
import time
from typing import Optional

# yt-dlp search configuration
_SEARCH_COUNT = 15          # Videos per search query
_REQUEST_DELAY = 2.0        # Seconds between yt-dlp calls
_TRENDS_TIMEFRAME = "now 7-d"  # Google Trends lookback window

# Fallback queries if Trends returns nothing (always-relevant travel topics)
_FALLBACK_QUERY_TEMPLATES = [
    "{city} travel guide {year}",
    "{city} things to do {year}",
    "{city} {category} guide",
    "best {category} in {city}",
    "{city} travel tips {year}",
]


class TrendsSearchDiscovery:
    """Discovers trending YouTube videos by combining Google Trends + yt-dlp search.

    Strategy:
    1. Query Google Trends for trending travel topics in the destination country
    2. Filter trends relevant to the tree node's city/category
    3. Use yt-dlp search to find YouTube video IDs for each trending query
    4. Return video metadata for VideoRegistry registration

    Usage::

        discovery = TrendsSearchDiscovery()
        results = discovery.search_node(
            destination="japan",
            city="tokyo",
            category="cuisine",
        )
        for video in results:
            print(video["video_id"], video["query"])
    """

    # Maps destination to Google Trends geo code
    _GEO_CODES = {
        "japan": "JP",
        "thailand": "TH",
        "italy": "IT",
        "turkey": "TR",
        "south_korea": "KR",
    }

    def search_node(
        self,
        destination: str,
        city: str,
        category: str,
        max_results: int = _SEARCH_COUNT,
    ) -> list[dict]:
        """Find trending videos for a tree node.

        Args:
            destination: e.g. "japan"
            city:        e.g. "tokyo"
            category:    e.g. "cuisine"
            max_results: Max videos to return

        Returns:
            List of dicts with video_id, query, destination, tree_node, source
        """
        city_display = city.replace("_", " ").title()
        category_display = category.replace("_", " ")
        tree_node = f"{destination}/{city}/{category}"

        queries = self._build_queries(destination, city_display, category_display)
        results: dict[str, dict] = {}  # video_id → metadata

        for query in queries:
            if len(results) >= max_results:
                break
            videos = self._yt_dlp_search(query, destination, tree_node, count=5)
            for v in videos:
                if v["video_id"] not in results:
                    results[v["video_id"]] = v
            time.sleep(_REQUEST_DELAY)

        return list(results.values())[:max_results]

    def search_multiple_nodes(
        self,
        nodes: list[tuple[str, str, str]],
        max_results_per_node: int = _SEARCH_COUNT,
    ) -> dict[str, list[dict]]:
        """Search multiple tree nodes. Returns {node_id: [video_metadata]}."""
        results: dict[str, list[dict]] = {}
        for destination, city, category in nodes:
            node_id = f"{destination}/{city}/{category}"
            print(f"[trends_search] Searching node: {node_id}")
            results[node_id] = self.search_node(
                destination=destination,
                city=city,
                category=category,
                max_results=max_results_per_node,
            )
        return results

    # ── Query building ─────────────────────────────────────────────────────────

    def _build_queries(
        self,
        destination: str,
        city_display: str,
        category_display: str,
    ) -> list[str]:
        """Build search queries: trending topics first, fallback templates second."""
        from datetime import datetime
        year = datetime.now().year
        queries: list[str] = []

        # Try Google Trends first
        trending = self._get_trending_queries(destination, city_display, category_display)
        queries.extend(trending)

        # Always append fallback templates to ensure coverage
        for template in _FALLBACK_QUERY_TEMPLATES:
            q = template.format(
                city=city_display,
                category=category_display,
                year=year,
            )
            if q not in queries:
                queries.append(q)

        return queries

    def _get_trending_queries(
        self,
        destination: str,
        city_display: str,
        category_display: str,
    ) -> list[str]:
        """Fetch trending travel queries from Google Trends."""
        try:
            from pytrends.request import TrendReq
        except ImportError:
            print("[trends_search] pytrends not installed — skipping Trends, using fallback queries.")
            return []

        geo = self._GEO_CODES.get(destination, "")
        seed_keyword = f"{city_display} {category_display} travel"

        try:
            pt = TrendReq(hl="en-US", tz=0, timeout=(5, 15))
            pt.build_payload(
                kw_list=[seed_keyword],
                timeframe=_TRENDS_TIMEFRAME,
                geo=geo,
            )
            related = pt.related_queries()
            top_df = related.get(seed_keyword, {}).get("top")

            if top_df is None or top_df.empty:
                return []

            # Filter to queries mentioning city or category
            city_lower = city_display.lower()
            cat_lower = category_display.lower()
            queries = []
            for q in top_df["query"].tolist()[:10]:
                q_lower = q.lower()
                if city_lower in q_lower or cat_lower in q_lower:
                    queries.append(q)

            return queries[:5]

        except Exception as e:
            print(f"[trends_search] Google Trends error for '{seed_keyword}': {e}")
            return []

    # ── yt-dlp search ──────────────────────────────────────────────────────────

    def _yt_dlp_search(
        self,
        query: str,
        destination: str,
        tree_node: str,
        count: int = 5,
    ) -> list[dict]:
        """Use yt-dlp to search YouTube and extract video IDs without downloading.

        Runs yt-dlp as a subprocess with --dump-json --no-download so it only
        fetches metadata, not audio. Much lighter than the YouTube Data API
        and doesn't consume quota.
        """
        search_term = f"ytsearch{count}:{query}"
        cmd = [
            "yt-dlp",
            "--dump-json",
            "--no-download",
            "--no-playlist",
            "--match-filter", "duration > 300 & duration < 1800",  # 5-30 min
            search_term,
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
            )
        except subprocess.TimeoutExpired:
            print(f"[trends_search] yt-dlp timeout for query: {query}")
            return []
        except FileNotFoundError:
            print("[trends_search] yt-dlp not installed. Run: pip install yt-dlp")
            return []

        if result.returncode != 0:
            return []

        videos = []
        for line in result.stdout.strip().splitlines():
            if not line.strip():
                continue
            try:
                meta = json.loads(line)
                video_id = meta.get("id") or meta.get("webpage_url_basename")
                if not video_id:
                    continue
                videos.append({
                    "video_id": video_id,
                    "title": meta.get("title", ""),
                    "view_count": meta.get("view_count", 0),
                    "published_at": meta.get("upload_date", ""),
                    "channel_id": meta.get("channel_id", ""),
                    "channel_title": meta.get("channel", ""),
                    "duration_seconds": meta.get("duration", 0),
                    "description": (meta.get("description") or "")[:500],
                    "destination": destination,
                    "tree_node": tree_node,
                    "query": query,
                    "source": "trends_search",
                })
            except json.JSONDecodeError:
                continue

        return videos
