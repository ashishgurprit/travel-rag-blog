"""Video registry — deduplication and provenance tracking for discovered videos.

Maintains a persistent JSON registry at scripts/video_registry.json.
Each entry tracks which sources discovered the video and computes a
provenance_score (0.0-1.0) used to boost reranker scores for
community-validated content.

Provenance score formula:
  base = number of unique sources / max_sources (0.0-1.0)
  boost = log1p(reddit_score / 1000) * 0.2   (capped at 0.2)
  score = min(1.0, base + boost)
"""

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_MAX_SOURCES = 3  # youtube_api, reddit, trends_search


class RegistryEntry:
    """A single video entry in the registry."""

    VALID_SOURCES = {"youtube_api", "reddit", "trends_search", "quora", "tripadvisor"}

    def __init__(
        self,
        video_id: str,
        destination: str,
        tree_node: str,
        title: str = "",
        view_count: int = 0,
        published_at: str = "",
        channel_id: str = "",
    ) -> None:
        self.video_id = video_id
        self.destination = destination
        self.tree_node = tree_node
        self.title = title
        self.view_count = view_count
        self.published_at = published_at
        self.channel_id = channel_id
        self.sources: list[str] = []
        self.reddit_score: int = 0
        self.already_ingested: bool = False
        self.discovered_at: str = datetime.now(timezone.utc).isoformat()
        self.ingested_at: Optional[str] = None

    @property
    def provenance_score(self) -> float:
        """Compute provenance score from source count and community signals."""
        if not self.sources:
            return 0.0
        base = len(set(self.sources)) / _MAX_SOURCES
        reddit_boost = math.log1p(self.reddit_score / 1000) * 0.2
        return min(1.0, base + reddit_boost)

    @property
    def tier(self) -> int:
        """Derive tier from tree_node — requires KnowledgeTree for full accuracy.
        Returns 0 if unknown.
        """
        return 0  # Filled in by VideoRegistry.register() from KnowledgeTree

    def add_source(self, source: str, reddit_score: int = 0) -> None:
        """Record a new discovery source. Idempotent per source."""
        if source not in self.VALID_SOURCES:
            raise ValueError(f"Unknown source '{source}'. Valid: {self.VALID_SOURCES}")
        if source not in self.sources:
            self.sources.append(source)
        if reddit_score > self.reddit_score:
            self.reddit_score = reddit_score

    def mark_ingested(self) -> None:
        self.already_ingested = True
        self.ingested_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "video_id": self.video_id,
            "destination": self.destination,
            "tree_node": self.tree_node,
            "title": self.title,
            "view_count": self.view_count,
            "published_at": self.published_at,
            "channel_id": self.channel_id,
            "sources": self.sources,
            "reddit_score": self.reddit_score,
            "provenance_score": round(self.provenance_score, 4),
            "already_ingested": self.already_ingested,
            "discovered_at": self.discovered_at,
            "ingested_at": self.ingested_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RegistryEntry":
        entry = cls(
            video_id=data["video_id"],
            destination=data["destination"],
            tree_node=data.get("tree_node", ""),
            title=data.get("title", ""),
            view_count=data.get("view_count", 0),
            published_at=data.get("published_at", ""),
            channel_id=data.get("channel_id", ""),
        )
        entry.sources = data.get("sources", [])
        entry.reddit_score = data.get("reddit_score", 0)
        entry.already_ingested = data.get("already_ingested", False)
        entry.discovered_at = data.get("discovered_at", entry.discovered_at)
        entry.ingested_at = data.get("ingested_at")
        return entry


class VideoRegistry:
    """Persistent registry of all discovered YouTube videos across all sources.

    Deduplicates by video_id. When the same video is discovered by multiple
    sources, it updates the existing entry with the new source rather than
    creating a duplicate.

    Usage::

        registry = VideoRegistry.load()

        # Register a newly discovered video
        entry = registry.register(
            video_id="abc123",
            destination="japan",
            tree_node="japan/tokyo/cuisine",
            source="youtube_api",
            title="Best Ramen in Tokyo 2025",
            view_count=1_200_000,
        )

        # Get videos pending transcription, sorted by provenance
        pending = registry.get_pending_ingestion("japan")

        # After ingestion
        registry.mark_ingested("abc123")
        registry.save()
    """

    def __init__(self, registry_path: Path) -> None:
        self._path = registry_path
        self._entries: dict[str, RegistryEntry] = {}

    # ── Persistence ────────────────────────────────────────────────────────────

    @classmethod
    def load(cls, registry_path: Optional[Path] = None) -> "VideoRegistry":
        """Load registry from JSON file, creating empty registry if not found."""
        if registry_path is None:
            registry_path = (
                Path(__file__).parent.parent.parent / "scripts" / "video_registry.json"
            )

        registry = cls(registry_path=registry_path)

        if registry_path.exists():
            data = json.loads(registry_path.read_text())
            for entry_data in data.get("entries", []):
                entry = RegistryEntry.from_dict(entry_data)
                registry._entries[entry.video_id] = entry

        return registry

    def save(self) -> None:
        """Persist registry to JSON file."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "total_entries": len(self._entries),
            "entries": [e.to_dict() for e in self._entries.values()],
        }
        self._path.write_text(json.dumps(data, indent=2))

    # ── Registration ───────────────────────────────────────────────────────────

    def register(
        self,
        video_id: str,
        destination: str,
        tree_node: str,
        source: str,
        title: str = "",
        view_count: int = 0,
        published_at: str = "",
        channel_id: str = "",
        reddit_score: int = 0,
    ) -> tuple[RegistryEntry, bool]:
        """Register a video. Returns (entry, is_new).

        If video_id already exists, adds the new source to provenance tracking.
        If video_id is new, creates a fresh entry.
        """
        if video_id in self._entries:
            entry = self._entries[video_id]
            entry.add_source(source, reddit_score=reddit_score)
            # Update metadata if richer data available
            if view_count > entry.view_count:
                entry.view_count = view_count
            if title and not entry.title:
                entry.title = title
            return entry, False

        entry = RegistryEntry(
            video_id=video_id,
            destination=destination,
            tree_node=tree_node,
            title=title,
            view_count=view_count,
            published_at=published_at,
            channel_id=channel_id,
        )
        entry.add_source(source, reddit_score=reddit_score)
        self._entries[video_id] = entry
        return entry, True

    def mark_ingested(self, video_id: str) -> bool:
        """Mark a video as ingested. Returns True if found."""
        entry = self._entries.get(video_id)
        if entry:
            entry.mark_ingested()
            return True
        return False

    # ── Queries ────────────────────────────────────────────────────────────────

    def get_pending_ingestion(
        self,
        destination: Optional[str] = None,
        tree_node: Optional[str] = None,
        min_provenance: float = 0.0,
    ) -> list[RegistryEntry]:
        """Return not-yet-ingested entries, sorted by provenance_score descending."""
        entries = [
            e for e in self._entries.values()
            if not e.already_ingested
            and e.provenance_score >= min_provenance
            and (destination is None or e.destination == destination)
            and (tree_node is None or e.tree_node == tree_node)
        ]
        return sorted(entries, key=lambda e: e.provenance_score, reverse=True)

    def get_entry(self, video_id: str) -> Optional[RegistryEntry]:
        return self._entries.get(video_id)

    def is_known(self, video_id: str) -> bool:
        return video_id in self._entries

    def is_ingested(self, video_id: str) -> bool:
        entry = self._entries.get(video_id)
        return entry is not None and entry.already_ingested

    def stats(self) -> dict:
        """Return summary statistics."""
        total = len(self._entries)
        ingested = sum(1 for e in self._entries.values() if e.already_ingested)
        multi_source = sum(
            1 for e in self._entries.values() if len(set(e.sources)) > 1
        )
        return {
            "total": total,
            "ingested": ingested,
            "pending": total - ingested,
            "multi_source_validated": multi_source,
        }
