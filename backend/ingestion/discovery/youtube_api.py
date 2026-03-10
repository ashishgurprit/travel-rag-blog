"""YouTube Data API v3 discovery source.

Searches YouTube by tree node keywords and returns video metadata
for registration in the VideoRegistry. Uses the free quota tier
(10,000 units/day). Each search call costs ~100 units.

Requires environment variable: YOUTUBE_API_KEY
"""

import os
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Search configuration
_DEFAULT_MAX_RESULTS = 25
_MIN_VIEW_COUNT = 50_000
_MIN_DURATION_SECONDS = 5 * 60    # 5 minutes
_MAX_DURATION_SECONDS = 30 * 60   # 30 minutes
_PUBLISHED_WITHIN_DAYS = 90       # Only fetch videos from last 90 days
_REQUEST_DELAY_SECONDS = 0.5      # Polite delay between API calls

# Category-to-query keyword mapping
# Enriches tree node searches with domain-specific terms
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "cuisine": ["food", "restaurant", "eat", "ramen", "street food", "best dishes"],
    "architecture": ["architecture", "buildings", "design", "historic", "structures"],
    "museums": ["museum", "gallery", "exhibition", "art", "culture", "history"],
    "nightlife": ["nightlife", "bars", "clubs", "evening", "entertainment", "night out"],
    "nature": ["nature", "hiking", "parks", "outdoors", "scenery", "landscape"],
    "temples": ["temples", "shrines", "sacred", "spiritual", "religious sites"],
    "shopping": ["shopping", "markets", "souvenirs", "malls", "street market"],
    "day_trips": ["day trip", "excursion", "nearby", "outside", "escape"],
    "budget_tips": ["budget", "cheap", "affordable", "save money", "cost"],
    "itinerary": ["itinerary", "travel guide", "days in", "trip plan", "schedule"],
    "traditional_culture": ["traditional", "culture", "customs", "local life", "heritage"],
    "beaches": ["beach", "coast", "sea", "snorkeling", "island"],
    "street_food": ["street food", "food stalls", "night market", "local food"],
    "hidden_gems": ["hidden", "secret", "underrated", "off the beaten path", "local tips"],
}


class YouTubeAPIDiscovery:
    """Discovers YouTube videos using the Data API v3 for a given tree node.

    Usage::

        discovery = YouTubeAPIDiscovery()
        results = discovery.search_node(
            destination="japan",
            city="tokyo",
            category="cuisine",
            max_results=25,
        )
        for video in results:
            print(video["video_id"], video["title"], video["view_count"])
    """

    def __init__(self, api_key: Optional[str] = None) -> None:
        key = api_key or os.environ.get("YOUTUBE_API_KEY")
        if not key:
            raise EnvironmentError(
                "YOUTUBE_API_KEY environment variable is required for YouTube API discovery."
            )
        self._service = build("youtube", "v3", developerKey=key, cache_discovery=False)

    def search_node(
        self,
        destination: str,
        city: str,
        category: str,
        max_results: int = _DEFAULT_MAX_RESULTS,
        published_within_days: int = _PUBLISHED_WITHIN_DAYS,
    ) -> list[dict]:
        """Search YouTube for videos matching a tree node.

        Args:
            destination: e.g. "japan"
            city:        e.g. "tokyo"
            category:    e.g. "cuisine"
            max_results: Max videos to return (max 50 per API call)
            published_within_days: Only include videos published within this window

        Returns:
            List of video metadata dicts with keys:
            video_id, title, view_count, published_at, channel_id,
            duration_seconds, description, destination, tree_node
        """
        query = self._build_query(destination, city, category)
        published_after = (
            datetime.now(timezone.utc) - timedelta(days=published_within_days)
        ).isoformat().replace("+00:00", "Z")

        try:
            search_response = self._service.search().list(
                q=query,
                part="id,snippet",
                type="video",
                maxResults=min(max_results, 50),
                order="viewCount",
                publishedAfter=published_after,
                relevanceLanguage="en",
                videoEmbeddable="true",
                videoDuration="medium",  # 4-20 min; we filter more precisely below
            ).execute()
        except HttpError as e:
            print(f"[youtube_api] Search failed for '{query}': {e}")
            return []

        time.sleep(_REQUEST_DELAY_SECONDS)

        video_ids = [
            item["id"]["videoId"]
            for item in search_response.get("items", [])
            if item["id"].get("videoId")
        ]

        if not video_ids:
            return []

        return self._fetch_video_details(
            video_ids=video_ids,
            destination=destination,
            tree_node=f"{destination}/{city}/{category}",
        )

    def search_multiple_nodes(
        self,
        nodes: list[tuple[str, str, str]],  # (destination, city, category)
        max_results_per_node: int = _DEFAULT_MAX_RESULTS,
    ) -> dict[str, list[dict]]:
        """Search multiple tree nodes. Returns {node_id: [video_metadata]}."""
        results: dict[str, list[dict]] = {}
        for destination, city, category in nodes:
            node_id = f"{destination}/{city}/{category}"
            print(f"[youtube_api] Searching node: {node_id}")
            results[node_id] = self.search_node(
                destination=destination,
                city=city,
                category=category,
                max_results=max_results_per_node,
            )
            time.sleep(_REQUEST_DELAY_SECONDS)
        return results

    # ── Internals ──────────────────────────────────────────────────────────────

    def _build_query(self, destination: str, city: str, category: str) -> str:
        """Build a rich search query from destination + city + category keywords."""
        city_display = city.replace("_", " ").title()
        dest_display = destination.replace("_", " ").title()

        # Pick 1-2 category enrichment keywords
        category_terms = CATEGORY_KEYWORDS.get(category, [category.replace("_", " ")])
        primary_term = category_terms[0] if category_terms else category

        year = datetime.now().year
        return f"{city_display} {primary_term} {dest_display} {year} travel guide"

    def _fetch_video_details(
        self,
        video_ids: list[str],
        destination: str,
        tree_node: str,
    ) -> list[dict]:
        """Fetch full video statistics and filter by view count + duration."""
        try:
            details_response = self._service.videos().list(
                id=",".join(video_ids),
                part="snippet,statistics,contentDetails",
            ).execute()
        except HttpError as e:
            print(f"[youtube_api] Details fetch failed: {e}")
            return []

        results = []
        for item in details_response.get("items", []):
            video_id = item["id"]
            stats = item.get("statistics", {})
            snippet = item.get("snippet", {})
            content = item.get("contentDetails", {})

            view_count = int(stats.get("viewCount", 0))
            duration_seconds = _parse_duration(content.get("duration", "PT0S"))

            # Apply filters
            if view_count < _MIN_VIEW_COUNT:
                continue
            if not (_MIN_DURATION_SECONDS <= duration_seconds <= _MAX_DURATION_SECONDS):
                continue

            results.append({
                "video_id": video_id,
                "title": snippet.get("title", ""),
                "description": snippet.get("description", "")[:500],
                "published_at": snippet.get("publishedAt", ""),
                "channel_id": snippet.get("channelId", ""),
                "channel_title": snippet.get("channelTitle", ""),
                "view_count": view_count,
                "like_count": int(stats.get("likeCount", 0)),
                "comment_count": int(stats.get("commentCount", 0)),
                "duration_seconds": duration_seconds,
                "destination": destination,
                "tree_node": tree_node,
                "source": "youtube_api",
            })

        return results


def _parse_duration(iso_duration: str) -> int:
    """Parse ISO 8601 duration (e.g. PT15M30S) to seconds."""
    import re
    pattern = re.compile(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?")
    match = pattern.match(iso_duration)
    if not match:
        return 0
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds
