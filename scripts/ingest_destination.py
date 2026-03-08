#!/usr/bin/env python3
"""Generalized destination ingestion script.

Usage:
    python scripts/ingest_destination.py --destination <name> [--sources youtube reddit] [--limit 100]

Arguments:
    --destination  one of: japan, thailand, italy, turkey, south_korea
    --sources      space-separated list of sources (default: youtube reddit)
    --limit        reddit post limit per subreddit (default: 100)
"""
import argparse
import json
from pathlib import Path

from backend.ingestion.youtube import fetch_transcripts
from backend.ingestion.reddit import fetch_posts
from backend.ingestion.chunker import chunk_document
from backend.ingestion.embedder import Embedder
from backend.ingestion.indexer import Indexer

VALID_DESTINATIONS = {"japan", "thailand", "italy", "turkey", "south_korea"}

# SCRIPTS_DIR is a module-level variable so tests can patch it
SCRIPTS_DIR = Path(__file__).parent


def run_ingestion(destination: str, sources: list[str], limit: int = 100) -> dict:
    """Run the full ingestion pipeline for a single destination.

    Args:
        destination: One of the valid destination names.
        sources:     List of source names to ingest (``"youtube"``, ``"reddit"``).
        limit:       Maximum posts per subreddit for the Reddit source.

    Returns:
        Summary dict with keys: fetched, chunked, embedded, upserted, skipped.
    """
    embedder = Embedder()
    indexer = Indexer()

    all_docs: list[dict] = []

    # ── YouTube ────────────────────────────────────────────────────────────────
    if "youtube" in sources:
        video_ids_path = Path(SCRIPTS_DIR) / f"{destination}_video_ids.json"
        if not video_ids_path.exists():
            print(f"Warning: {video_ids_path} not found — skipping YouTube source.")
        else:
            video_ids: list[str] = json.loads(video_ids_path.read_text())
            if video_ids:
                print(f"[youtube] Fetching transcripts for {len(video_ids)} video(s)...")
                yt_docs = fetch_transcripts(video_ids, destination=destination)
                print(f"[youtube] Got {len(yt_docs)} transcript segment(s).")
                all_docs.extend(yt_docs)
            else:
                print(f"[youtube] No video IDs in {video_ids_path} — skipping.")

    # ── Reddit ─────────────────────────────────────────────────────────────────
    if "reddit" in sources:
        subreddit_map_path = Path(SCRIPTS_DIR) / "subreddit_map.json"
        if not subreddit_map_path.exists():
            print(f"Warning: {subreddit_map_path} not found — skipping Reddit source.")
        else:
            subreddit_map: dict = json.loads(subreddit_map_path.read_text())
            if destination not in subreddit_map:
                print(
                    f"Warning: '{destination}' not found in subreddit_map.json — "
                    "skipping Reddit source."
                )
            else:
                subreddits = subreddit_map[destination]
                print(f"[reddit] Fetching posts from {subreddits} (limit={limit})...")
                reddit_docs = fetch_posts(subreddits, destination=destination, limit=limit)
                print(f"[reddit] Got {len(reddit_docs)} post(s).")
                all_docs.extend(reddit_docs)

    fetched = len(all_docs)

    # ── Chunk ──────────────────────────────────────────────────────────────────
    all_chunks: list[dict] = []
    for doc in all_docs:
        all_chunks.extend(chunk_document(doc))
    chunked = len(all_chunks)
    print(f"[chunker] Created {chunked} chunk(s) from {fetched} document(s).")

    # ── Embed ──────────────────────────────────────────────────────────────────
    if all_chunks:
        all_chunks = embedder.embed_chunks(all_chunks)
    embedded = len(all_chunks)
    print(f"[embedder] Embedded {embedded} chunk(s).")

    # ── Upsert ─────────────────────────────────────────────────────────────────
    result = indexer.upsert_chunks(all_chunks)
    upserted = result["upserted"]
    skipped = result["skipped"]

    # ── Summary ────────────────────────────────────────────────────────────────
    print(
        f"\nSummary for '{destination}':\n"
        f"  fetched={fetched}  chunked={chunked}  embedded={embedded}  "
        f"upserted={upserted}  skipped={skipped}"
    )

    return {
        "fetched": fetched,
        "chunked": chunked,
        "embedded": embedded,
        "upserted": upserted,
        "skipped": skipped,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ingest travel content for a destination into Pinecone."
    )
    parser.add_argument(
        "--destination",
        required=True,
        choices=sorted(VALID_DESTINATIONS),
        help="Destination to ingest (e.g. japan, thailand, italy, turkey, south_korea)",
    )
    parser.add_argument(
        "--sources",
        nargs="+",
        default=["youtube", "reddit"],
        choices=["youtube", "reddit"],
        help="Sources to ingest (default: youtube reddit)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Reddit post limit per subreddit (default: 100)",
    )
    args = parser.parse_args()
    run_ingestion(
        destination=args.destination,
        sources=args.sources,
        limit=args.limit,
    )
