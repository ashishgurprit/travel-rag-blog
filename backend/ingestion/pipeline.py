"""Discovery pipeline orchestrator.

Fans out across all 3 discovery sources per tree node, registers
results into VideoRegistry with provenance tracking, and queues
new videos for transcription via a Redis list.

Single-writer guarantee: Only this module pushes to the transcription
queue. Manual ingest_destination.py runs bypass this pipeline entirely
(they use the static video_ids JSONs). Never run both simultaneously.

Usage::

    pipeline = DiscoveryPipeline()
    summary = pipeline.run_destination("japan")
    print(summary)
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import redis as redis_lib

from backend.config import settings
from backend.ingestion.knowledge_tree import KnowledgeTree
from backend.ingestion.video_registry import VideoRegistry

_TRANSCRIPTION_QUEUE_KEY = "transcription_queue"
_DISCOVERY_LOCK_KEY = "discovery_lock"
_DISCOVERY_LOCK_TTL = 3600  # 1 hour

VALID_DESTINATIONS = {"japan", "thailand", "italy", "turkey", "south_korea"}


class DiscoveryPipeline:
    """Orchestrates multi-source discovery for all tree nodes in a destination.

    Sources run in order: YouTube API → Reddit → Trends/yt-dlp.
    All results are deduplicated via VideoRegistry before queuing.
    """

    def __init__(
        self,
        registry_path: Optional[Path] = None,
        youtube_api_key: Optional[str] = None,
    ) -> None:
        self._registry = VideoRegistry.load(registry_path)
        self._redis = self._connect_redis()
        self._youtube_api_key = youtube_api_key or settings.youtube_api_key

    def _connect_redis(self):
        """Connect to Redis, fails open if unavailable."""
        try:
            client = redis_lib.Redis.from_url(settings.redis_url, decode_responses=True)
            client.ping()
            return client
        except Exception as e:
            print(f"[pipeline] Warning: Redis unavailable ({e}). Queue disabled.")
            return None

    # ── Public API ─────────────────────────────────────────────────────────────

    def run_destination(
        self,
        destination: str,
        sources: Optional[list[str]] = None,
        max_nodes: Optional[int] = None,
    ) -> dict:
        """Run discovery for all tree nodes in a destination.

        Args:
            destination: e.g. "japan"
            sources:     Subset of ["youtube_api", "reddit", "trends_search"]
                         Default: all three
            max_nodes:   Limit nodes processed (useful for testing)

        Returns:
            Summary dict with discovered, new, queued, skipped counts.
        """
        if destination not in VALID_DESTINATIONS:
            raise ValueError(f"Unknown destination: {destination}")

        sources = sources or ["youtube_api", "reddit", "trends_search"]
        tree = KnowledgeTree.load(destination)
        nodes_needing = tree.get_nodes_needing_content()

        if max_nodes:
            nodes_needing = nodes_needing[:max_nodes]

        print(
            f"[pipeline] {destination}: {len(nodes_needing)} nodes need content "
            f"(sources: {sources})"
        )

        total_discovered = 0
        total_new = 0
        total_queued = 0

        for node in nodes_needing:
            discovered, new, queued = self._run_node(node, sources)
            total_discovered += discovered
            total_new += new
            total_queued += queued

        self._registry.save()

        summary = {
            "destination": destination,
            "nodes_processed": len(nodes_needing),
            "discovered": total_discovered,
            "new": total_new,
            "queued": total_queued,
            "skipped_duplicates": total_discovered - total_new,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        print(f"[pipeline] {destination} summary: {summary}")
        return summary

    def run_all_destinations(self, sources: Optional[list[str]] = None) -> list[dict]:
        """Run discovery for all 5 destinations sequentially."""
        summaries = []
        for dest in sorted(VALID_DESTINATIONS):
            print(f"\n[pipeline] === Starting {dest} ===")
            summary = self.run_destination(dest, sources=sources)
            summaries.append(summary)
            time.sleep(2)  # Brief pause between destinations
        return summaries

    # ── Node-level discovery ───────────────────────────────────────────────────

    def _run_node(
        self,
        node,  # TreeNode
        sources: list[str],
    ) -> tuple[int, int, int]:
        """Run all sources for a single tree node. Returns (discovered, new, queued)."""
        discovered = 0
        new = 0
        queued = 0

        for source in sources:
            try:
                videos = self._fetch_from_source(source, node)
            except Exception as e:
                print(f"[pipeline] {node.node_id} — {source} error: {e}")
                continue

            for video in videos:
                discovered += 1
                entry, is_new = self._registry.register(
                    video_id=video["video_id"],
                    destination=node.destination,
                    tree_node=node.node_id,
                    source=source,
                    title=video.get("title", ""),
                    view_count=video.get("view_count", 0),
                    published_at=video.get("published_at", ""),
                    channel_id=video.get("channel_id", ""),
                    reddit_score=video.get("reddit_score", 0),
                )
                if is_new:
                    new += 1
                    if self._queue_for_transcription(entry):
                        queued += 1

        return discovered, new, queued

    def _fetch_from_source(self, source: str, node) -> list[dict]:
        """Dispatch to the right discovery source."""
        if source == "youtube_api":
            if not self._youtube_api_key:
                print(f"[pipeline] Skipping youtube_api — YOUTUBE_API_KEY not set")
                return []
            from backend.ingestion.discovery.youtube_api import YouTubeAPIDiscovery
            d = YouTubeAPIDiscovery(api_key=self._youtube_api_key)
            return d.search_node(
                destination=node.destination,
                city=node.city,
                category=node.category,
            )

        elif source == "reddit":
            from backend.ingestion.discovery.reddit_miner import RedditMiner
            miner = RedditMiner()
            return miner.mine_node(
                destination=node.destination,
                city=node.city,
                category=node.category,
            )

        elif source == "trends_search":
            from backend.ingestion.discovery.trends_search import TrendsSearchDiscovery
            d = TrendsSearchDiscovery()
            return d.search_node(
                destination=node.destination,
                city=node.city,
                category=node.category,
            )

        return []

    # ── Queue ──────────────────────────────────────────────────────────────────

    def _queue_for_transcription(self, entry) -> bool:
        """Push a video entry onto the Redis transcription queue.

        Returns True if queued, False if Redis unavailable.
        """
        if self._redis is None:
            return False
        try:
            payload = json.dumps({
                "video_id": entry.video_id,
                "destination": entry.destination,
                "tree_node": entry.tree_node,
                "provenance_score": round(entry.provenance_score, 4),
                "sources": entry.sources,
            })
            self._redis.lpush(_TRANSCRIPTION_QUEUE_KEY, payload)
            return True
        except Exception as e:
            print(f"[pipeline] Queue error for {entry.video_id}: {e}")
            return False

    def queue_depth(self) -> int:
        """Return number of items pending in the transcription queue."""
        if self._redis is None:
            return 0
        try:
            return self._redis.llen(_TRANSCRIPTION_QUEUE_KEY) or 0
        except Exception:
            return 0

    # ── Distributed lock ───────────────────────────────────────────────────────

    def acquire_lock(self) -> bool:
        """Acquire distributed lock to prevent overlapping runs.

        Uses Redis SET NX EX pattern. Returns True if lock acquired.
        """
        if self._redis is None:
            return True  # No Redis — allow single-process runs
        try:
            result = self._redis.set(
                _DISCOVERY_LOCK_KEY, "1",
                nx=True,
                ex=_DISCOVERY_LOCK_TTL,
            )
            return result is True
        except Exception:
            return True

    def release_lock(self) -> None:
        if self._redis is None:
            return
        try:
            self._redis.delete(_DISCOVERY_LOCK_KEY)
        except Exception:
            pass
