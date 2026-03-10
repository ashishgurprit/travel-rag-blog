"""Reddit miner — discovers YouTube links shared in travel subreddits.

Scans subreddits relevant to each tree node, extracts YouTube video IDs
from post bodies, titles, and top comments. Scores by upvotes + comment
count as a community-validation signal for provenance scoring.

Requires: REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET in environment.
"""

import re
import time
from typing import Optional

import praw

from backend.config import settings

# YouTube URL patterns to match
_YT_PATTERNS = [
    re.compile(r"youtube\.com/watch\?(?:[^&\s]*&)*v=([A-Za-z0-9_-]{11})"),
    re.compile(r"youtu\.be/([A-Za-z0-9_-]{11})"),
    re.compile(r"youtube\.com/shorts/([A-Za-z0-9_-]{11})"),
    re.compile(r"youtube\.com/embed/([A-Za-z0-9_-]{11})"),
]

# Subreddits to mine per destination
DESTINATION_SUBREDDITS: dict[str, list[str]] = {
    "japan": ["JapanTravel", "japan", "Tokyo", "JapanTravelTips", "travel"],
    "thailand": ["ThailandTourism", "thailand", "Bangkok", "ChiangMai", "travel"],
    "italy": ["ItalyTravel", "italy", "rome", "florence", "travel"],
    "turkey": ["turkey", "istanbul", "travel", "solotravel"],
    "south_korea": ["koreatravel", "korea", "Seoul", "travel"],
}

# Category keywords for post relevance filtering
_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "cuisine": ["food", "eat", "restaurant", "ramen", "dish", "cuisine", "menu", "chef"],
    "architecture": ["architecture", "building", "design", "structure", "historic"],
    "museums": ["museum", "gallery", "exhibition", "art", "history", "collection"],
    "nightlife": ["nightlife", "bar", "club", "party", "evening", "night out"],
    "nature": ["nature", "hike", "park", "mountain", "forest", "lake", "outdoor"],
    "temples": ["temple", "shrine", "sacred", "spiritual", "monk", "worship"],
    "shopping": ["shopping", "market", "mall", "souvenir", "buy", "store"],
    "day_trips": ["day trip", "nearby", "excursion", "outside", "escape"],
    "budget_tips": ["budget", "cheap", "save money", "affordable", "cost", "free"],
    "itinerary": ["itinerary", "days", "schedule", "plan", "guide", "trip"],
    "traditional_culture": ["traditional", "culture", "custom", "heritage", "local"],
    "beaches": ["beach", "sea", "coast", "island", "snorkel", "swim"],
    "street_food": ["street food", "stall", "night market", "vendor", "snack"],
    "hidden_gems": ["hidden", "secret", "underrated", "off beaten", "local tip"],
}

_REQUEST_DELAY = 1.0  # seconds between Reddit API calls
_TOP_COMMENTS_PER_POST = 10
_MIN_UPVOTES = 10  # Skip very low-engagement posts


def _extract_video_ids(text: str) -> list[str]:
    """Extract all YouTube video IDs from a block of text."""
    ids: list[str] = []
    for pattern in _YT_PATTERNS:
        for match in pattern.finditer(text):
            vid = match.group(1)
            if vid not in ids:
                ids.append(vid)
    return ids


def _post_matches_category(post_title: str, post_text: str, category: str) -> bool:
    """Check if a post is relevant to the given category."""
    keywords = _CATEGORY_KEYWORDS.get(category, [category.replace("_", " ")])
    combined = (post_title + " " + post_text).lower()
    return any(kw.lower() in combined for kw in keywords)


class RedditMiner:
    """Mines travel subreddits for YouTube video links per tree node.

    Usage::

        miner = RedditMiner()
        results = miner.mine_node(
            destination="japan",
            city="tokyo",
            category="cuisine",
            limit=100,
        )
        for video in results:
            print(video["video_id"], video["reddit_score"])
    """

    def __init__(self) -> None:
        if not settings.reddit_client_id or not settings.reddit_client_secret:
            raise EnvironmentError(
                "REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET are required for Reddit mining."
            )
        self._reddit = praw.Reddit(
            client_id=settings.reddit_client_id,
            client_secret=settings.reddit_client_secret,
            user_agent=settings.reddit_user_agent,
        )
        # Cache seen video IDs within a single run to avoid duplicates
        self._seen: set[str] = set()

    def mine_node(
        self,
        destination: str,
        city: str,
        category: str,
        limit: int = 100,
        time_filter: str = "month",
    ) -> list[dict]:
        """Mine subreddits for YouTube links relevant to a tree node.

        Args:
            destination:  e.g. "japan"
            city:         e.g. "tokyo"
            category:     e.g. "cuisine"
            limit:        Max posts to scan per subreddit
            time_filter:  Reddit time filter: hour/day/week/month/year/all

        Returns:
            List of dicts with video_id, reddit_score, sources, tree_node, etc.
        """
        subreddits = DESTINATION_SUBREDDITS.get(destination, ["travel"])
        tree_node = f"{destination}/{city}/{category}"
        city_display = city.replace("_", " ").lower()
        results: dict[str, dict] = {}  # video_id → metadata

        for subreddit_name in subreddits:
            try:
                found = self._mine_subreddit(
                    subreddit_name=subreddit_name,
                    city=city_display,
                    category=category,
                    destination=destination,
                    tree_node=tree_node,
                    limit=limit,
                    time_filter=time_filter,
                )
                # Merge — boost score if found in multiple subreddits
                for video in found:
                    vid = video["video_id"]
                    if vid in results:
                        results[vid]["reddit_score"] = max(
                            results[vid]["reddit_score"], video["reddit_score"]
                        )
                    else:
                        results[vid] = video
            except Exception as e:
                print(f"[reddit_miner] Error mining r/{subreddit_name}: {e}")

            time.sleep(_REQUEST_DELAY)

        return list(results.values())

    def _mine_subreddit(
        self,
        subreddit_name: str,
        city: str,
        category: str,
        destination: str,
        tree_node: str,
        limit: int,
        time_filter: str,
    ) -> list[dict]:
        """Mine a single subreddit for YouTube links."""
        sub = self._reddit.subreddit(subreddit_name)
        found: list[dict] = []

        for post in sub.top(limit=limit, time_filter=time_filter):
            if post.score < _MIN_UPVOTES:
                continue

            # Filter by relevance to city and category
            combined_text = f"{post.title} {post.selftext}"
            if city not in combined_text.lower():
                continue
            if not _post_matches_category(post.title, post.selftext, category):
                continue

            # Extract from post body + title
            post_text = f"{post.title}\n{post.selftext}\n{post.url}"
            video_ids = _extract_video_ids(post_text)

            # Extract from top comments
            try:
                post.comments.replace_more(limit=0)
                for comment in post.comments.list()[:_TOP_COMMENTS_PER_POST]:
                    if hasattr(comment, "body"):
                        video_ids.extend(_extract_video_ids(comment.body))
            except Exception:
                pass

            # Deduplicate and build result entries
            seen_in_post: set[str] = set()
            for vid in video_ids:
                if vid in seen_in_post or vid in self._seen:
                    continue
                seen_in_post.add(vid)
                self._seen.add(vid)
                found.append({
                    "video_id": vid,
                    "destination": destination,
                    "tree_node": tree_node,
                    "title": "",  # Will be enriched by YouTube API if needed
                    "view_count": 0,
                    "published_at": "",
                    "channel_id": "",
                    "reddit_score": post.score,
                    "reddit_post_url": f"https://www.reddit.com{post.permalink}",
                    "source": "reddit",
                })

        return found

    def reset_seen_cache(self) -> None:
        """Reset the within-run deduplication cache."""
        self._seen.clear()
