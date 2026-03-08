"""YouTube transcript ingestion module."""

import time
from youtube_transcript_api import YouTubeTranscriptApi

_api = YouTubeTranscriptApi()


def fetch_transcripts(video_ids: list[str], destination: str) -> list[dict]:
    """Fetch transcripts for a list of YouTube video IDs.

    Returns one dict per transcript segment. Videos with no transcript are
    skipped gracefully.
    """
    results = []
    for video_id in video_ids:
        try:
            fetched = _api.fetch(video_id)
            segments = [{"text": s.text, "start": s.start, "duration": s.duration} for s in fetched]
            for seg in segments:
                timestamp_start = seg["start"]
                timestamp_end = seg["start"] + seg["duration"]
                results.append({
                    "text": seg["text"],
                    "video_id": video_id,
                    "title": video_id,  # placeholder; real title needs YouTube Data API
                    "timestamp_start": timestamp_start,
                    "timestamp_end": timestamp_end,
                    "url": f"https://www.youtube.com/watch?v={video_id}&t={int(timestamp_start)}s",
                    "destination": destination,
                    "source_type": "youtube",
                    "language": "en",
                })
        except Exception as e:
            print(f"Warning: no transcript for {video_id}: {e}")
        time.sleep(1)
    return results
