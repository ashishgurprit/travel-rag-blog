"""APScheduler-based pipeline scheduler.

Runs two jobs:
  - Weekly  (Monday 2am): full discovery + transcription queue drain
  - Monthly (1st, 6am):   rebalancing report generation

Also runs a Redis queue consumer that drains the transcription queue
continuously during the weekly run window.

Usage (run directly)::

    python -m backend.ingestion.scheduler

Or imported by the launchd-managed process:

    python scripts/run_scheduler.py
"""

import json
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from backend.config import settings
from backend.ingestion.knowledge_tree import KnowledgeTree
from backend.ingestion.pipeline import DiscoveryPipeline
from backend.ingestion.transcriber import transcribe_video
from backend.ingestion.video_registry import VideoRegistry

_TRANSCRIPTION_QUEUE_KEY = "transcription_queue"
_QUEUE_TIMEOUT_SECONDS = 5
_CONFIDENCE_THRESHOLD = 0.7       # Nodes below this get 5 more videos queued
_ZERO_RETRIEVAL_DAYS = 7          # Nodes with no retrievals in N days flagged
_AUTO_TRIGGER_VIDEO_COUNT = 5     # Videos queued per low-confidence node

VALID_DESTINATIONS = {"japan", "thailand", "italy", "turkey", "south_korea"}


# ── Weekly job ─────────────────────────────────────────────────────────────────

def run_weekly_discovery() -> None:
    """Full discovery run: all destinations × all nodes × all sources."""
    print(f"\n[scheduler] === Weekly discovery started {_now()} ===")

    pipeline = DiscoveryPipeline()

    if not pipeline.acquire_lock():
        print("[scheduler] Another discovery run is in progress — skipping.")
        return

    try:
        summaries = pipeline.run_all_destinations()
        total_queued = sum(s["queued"] for s in summaries)
        print(f"[scheduler] Discovery complete. {total_queued} videos queued.")

        # Drain transcription queue
        drain_transcription_queue(pipeline)

        # Run auto-triggers
        run_auto_triggers(pipeline)

    finally:
        pipeline.release_lock()

    print(f"[scheduler] === Weekly discovery finished {_now()} ===\n")


def drain_transcription_queue(pipeline: DiscoveryPipeline) -> None:
    """Process all items in the Redis transcription queue."""
    if pipeline._redis is None:
        print("[scheduler] Redis unavailable — cannot drain queue.")
        return

    registry = pipeline._registry
    processed = 0
    failed = 0

    print(f"[scheduler] Draining transcription queue ({pipeline.queue_depth()} items)...")

    while True:
        try:
            item = pipeline._redis.brpop(_TRANSCRIPTION_QUEUE_KEY, timeout=_QUEUE_TIMEOUT_SECONDS)
        except Exception as e:
            print(f"[scheduler] Redis error while draining: {e}")
            break

        if item is None:
            break  # Queue empty

        try:
            data = json.loads(item[1])
            video_id = data["video_id"]

            if registry.is_ingested(video_id):
                continue

            # Transcribe → chunk → embed → index
            segments = transcribe_video(
                video_id=video_id,
                destination=data.get("destination", ""),
                tree_node=data.get("tree_node", ""),
                provenance_score=data.get("provenance_score", 0.0),
                sources=data.get("sources", []),
            )

            _ingest_segments(segments)
            registry.mark_ingested(video_id)
            processed += 1
            print(f"[scheduler] Ingested {video_id} ({len(segments)} segments)")

        except Exception as e:
            failed += 1
            print(f"[scheduler] Failed to process queue item: {e}")

    registry.save()
    print(f"[scheduler] Queue drained: {processed} ingested, {failed} failed.")


def _ingest_segments(segments: list[dict]) -> None:
    """Chunk → embed → index a list of transcript segments."""
    from backend.ingestion.chunker import chunk_document
    from backend.ingestion.embedder import Embedder
    from backend.ingestion.indexer import Indexer

    embedder = Embedder()
    indexer = Indexer()

    all_chunks = []
    for seg in segments:
        all_chunks.extend(chunk_document(seg))

    if all_chunks:
        embedder.embed_chunks(all_chunks)
        indexer.upsert_chunks(all_chunks)


# ── Auto-triggers ──────────────────────────────────────────────────────────────

def run_auto_triggers(pipeline: DiscoveryPipeline) -> None:
    """Check node performance metrics and queue more content for thin nodes."""
    print("[scheduler] Running auto-triggers...")
    triggered = 0

    for dest in sorted(VALID_DESTINATIONS):
        try:
            tree = KnowledgeTree.load(dest)

            # Low confidence nodes → queue more videos
            for node in tree.get_low_confidence_nodes(threshold=_CONFIDENCE_THRESHOLD):
                print(
                    f"[scheduler] Auto-trigger: {node.node_id} "
                    f"(confidence={node.avg_confidence:.2f}) — queuing "
                    f"{_AUTO_TRIGGER_VIDEO_COUNT} more videos"
                )
                # Run targeted discovery for just this node
                pipeline._run_node(node, sources=["youtube_api", "trends_search"])
                triggered += 1

            # Zero-retrieval nodes → flag in report (don't auto-retire)
            inactive = tree.get_inactive_nodes(days=_ZERO_RETRIEVAL_DAYS)
            if inactive:
                print(
                    f"[scheduler] {dest}: {len(inactive)} inactive nodes "
                    f"(0 retrievals in {_ZERO_RETRIEVAL_DAYS}d) — flagged for monthly review"
                )

        except Exception as e:
            print(f"[scheduler] Auto-trigger error for {dest}: {e}")

    print(f"[scheduler] Auto-triggers complete: {triggered} nodes triggered.")


# ── Monthly job ────────────────────────────────────────────────────────────────

def run_monthly_rebalance() -> None:
    """Generate rebalancing report for human review."""
    print(f"\n[scheduler] === Monthly rebalance report {_now()} ===")

    reports_dir = Path(__file__).parent.parent.parent / "docs" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    month_str = datetime.now().strftime("%Y-%m")
    report_path = reports_dir / f"{month_str}-rebalance.md"

    lines = [
        f"# Rebalancing Report — {month_str}",
        f"\nGenerated: {_now()}",
        "\n---\n",
        "## Instructions",
        "Review the proposals below, then run:",
        "```",
        "python scripts/apply_rebalance.py --approve",
        "```",
        "\n---\n",
    ]

    registry = VideoRegistry.load()

    for dest in sorted(VALID_DESTINATIONS):
        try:
            tree = KnowledgeTree.load(dest)

            # Update current_videos count from registry
            for node in tree.nodes:
                ingested = sum(
                    1 for e in registry._entries.values()
                    if e.tree_node == node.node_id and e.already_ingested
                )
                tree.update_metrics(node.node_id, current_videos=ingested)

            tree.rebalance_budgets()
            lines.append(tree.generate_rebalancing_report())
            lines.append("\n---\n")

        except Exception as e:
            lines.append(f"## {dest}\nError generating report: {e}\n")

    report_content = "\n".join(lines)
    report_path.write_text(report_content)

    print(f"[scheduler] Report written to: {report_path}")
    print("[scheduler] Run: python scripts/apply_rebalance.py --approve")
    print(f"[scheduler] === Monthly report complete {_now()} ===\n")


# ── Scheduler entry point ──────────────────────────────────────────────────────

def start_scheduler() -> None:
    """Start the blocking APScheduler with weekly + monthly jobs."""
    scheduler = BlockingScheduler(timezone="Australia/Sydney")

    # Weekly: every Monday at 2am AEST
    scheduler.add_job(
        run_weekly_discovery,
        trigger=CronTrigger(day_of_week="mon", hour=2, minute=0),
        id="weekly_discovery",
        name="Weekly discovery + transcription",
        max_instances=1,
        coalesce=True,  # Skip missed runs rather than running multiple times
        misfire_grace_time=3600,
    )

    # Monthly: 1st of each month at 6am AEST
    scheduler.add_job(
        run_monthly_rebalance,
        trigger=CronTrigger(day=1, hour=6, minute=0),
        id="monthly_rebalance",
        name="Monthly rebalancing report",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=3600,
    )

    # Graceful shutdown on SIGTERM/SIGINT
    def _shutdown(signum, frame):
        print("\n[scheduler] Shutting down...")
        scheduler.shutdown(wait=False)
        sys.exit(0)

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    print("[scheduler] Started. Jobs:")
    print("  - Weekly discovery:    Monday 2am AEST")
    print("  - Monthly rebalance:   1st of month 6am AEST")
    print("Press Ctrl+C to stop.\n")

    scheduler.start()


# ── Helpers ────────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


if __name__ == "__main__":
    start_scheduler()
