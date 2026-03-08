#!/usr/bin/env python3
"""One-off Japan ingestion script."""
import json
from pathlib import Path
from backend.ingestion.youtube import fetch_transcripts
from backend.ingestion.reddit import fetch_posts
from backend.ingestion.chunker import chunk_document
from backend.ingestion.embedder import Embedder
from backend.ingestion.indexer import Indexer

def main():
    embedder = Embedder()
    indexer = Indexer()

    # YouTube
    video_ids = json.loads(Path("scripts/japan_video_ids.json").read_text())
    print(f"Fetching {len(video_ids)} YouTube videos...")
    yt_docs = fetch_transcripts(video_ids, destination="japan")
    print(f"Got {len(yt_docs)} transcript segments")

    all_chunks = []
    for doc in yt_docs:
        all_chunks.extend(chunk_document(doc))
    print(f"Created {len(all_chunks)} chunks from YouTube")

    # Reddit
    subreddit_map = json.loads(Path("scripts/subreddit_map.json").read_text())
    reddit_docs = fetch_posts(subreddit_map["japan"], destination="japan")
    for doc in reddit_docs:
        all_chunks.extend(chunk_document(doc))
    print(f"Total chunks after Reddit: {len(all_chunks)}")

    # Embed + index
    embedder.embed_chunks(all_chunks)
    result = indexer.upsert_chunks(all_chunks)
    print(f"Done: {result['upserted']} upserted, {result['skipped']} skipped")

if __name__ == "__main__":
    main()
