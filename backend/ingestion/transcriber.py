"""Transcription fallback chain for YouTube videos.

4-step priority chain (cheapest/fastest first):

  Step 1: YouTube captions via youtube_transcript_api  [free, instant]
  Step 2: yt-dlp audio download + local Whisper        [free, ~90s/video]
  Step 3: OpenAI Whisper API                           [~$0.20 AUD/min]

The local Whisper model (whisper-large-v3-turbo) is loaded once as a
module-level singleton — loading it per-video would waste 1.5GB reload time.

Output format matches the existing youtube.py segment schema so all
downstream chunking/embedding/indexing works unchanged.

Requires (for local Whisper): pip install transformers torch yt-dlp
Requires (for OpenAI fallback): OPENAI_API_KEY in environment
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from youtube_transcript_api import (
    NoTranscriptFound,
    TranscriptsDisabled,
    YouTubeTranscriptApi,
)

# ── Whisper singleton ──────────────────────────────────────────────────────────
# Loaded lazily on first use — avoids 1.5GB load if captions cover everything.
_whisper_pipe = None
_WHISPER_MODEL = "openai/whisper-large-v3-turbo"


def _get_whisper_pipe():
    """Load and cache the Whisper pipeline (Apple Silicon MPS or CPU)."""
    global _whisper_pipe
    if _whisper_pipe is not None:
        return _whisper_pipe

    try:
        import torch
        from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

        device = "mps" if torch.backends.mps.is_available() else "cpu"
        torch_dtype = torch.float16 if device == "mps" else torch.float32

        print(f"[transcriber] Loading {_WHISPER_MODEL} on {device}...")
        model = AutoModelForSpeechSeq2Seq.from_pretrained(
            _WHISPER_MODEL,
            torch_dtype=torch_dtype,
            low_cpu_mem_usage=True,
            use_safetensors=True,
        )
        model.to(device)
        processor = AutoProcessor.from_pretrained(_WHISPER_MODEL)

        _whisper_pipe = pipeline(
            "automatic-speech-recognition",
            model=model,
            tokenizer=processor.tokenizer,
            feature_extractor=processor.feature_extractor,
            torch_dtype=torch_dtype,
            device=device,
            return_timestamps=True,
            generate_kwargs={"task": "transcribe"},
        )
        print(f"[transcriber] {_WHISPER_MODEL} loaded on {device}.")
        return _whisper_pipe

    except ImportError as e:
        raise ImportError(
            f"Local Whisper requires: pip install transformers torch\nDetails: {e}"
        ) from e


# ── Public API ─────────────────────────────────────────────────────────────────

def transcribe_video(
    video_id: str,
    destination: str,
    tree_node: str = "",
    provenance_score: float = 0.0,
    sources: Optional[list[str]] = None,
    force_method: Optional[str] = None,
) -> list[dict]:
    """Transcribe a YouTube video using the fallback chain.

    Args:
        video_id:         YouTube video ID (11 chars)
        destination:      e.g. "japan"
        tree_node:        e.g. "japan/tokyo/cuisine"
        provenance_score: From VideoRegistry, stored in chunk metadata
        sources:          Discovery sources list, stored in chunk metadata
        force_method:     Override chain: "captions" | "whisper" | "openai_api"

    Returns:
        List of segment dicts matching the existing youtube.py schema:
        {text, video_id, title, timestamp_start, timestamp_end, url,
         destination, source_type, language, tree_node, provenance_score, sources}

    Raises:
        RuntimeError if all methods fail.
    """
    methods = _resolve_method_order(force_method)
    last_error: Optional[Exception] = None

    for method in methods:
        try:
            if method == "captions":
                segments = _fetch_captions(video_id)
            elif method == "whisper":
                segments = _transcribe_with_whisper(video_id)
            elif method == "openai_api":
                segments = _transcribe_with_openai_api(video_id)
            else:
                continue

            # Enrich segments with provenance metadata
            for seg in segments:
                seg["destination"] = destination
                seg["tree_node"] = tree_node
                seg["provenance_score"] = provenance_score
                seg["sources"] = sources or []

            print(
                f"[transcriber] {video_id} → {len(segments)} segments via {method}"
            )
            return segments

        except _SkipToNext as e:
            print(f"[transcriber] {video_id} — {method} unavailable: {e.reason}")
            last_error = e
            continue
        except Exception as e:
            print(f"[transcriber] {video_id} — {method} failed: {e}")
            last_error = e
            continue

    raise RuntimeError(
        f"All transcription methods failed for {video_id}. Last error: {last_error}"
    )


def transcribe_batch(
    entries: list[dict],
    stop_on_error: bool = False,
) -> dict[str, list[dict]]:
    """Transcribe a batch of VideoRegistry entries.

    Args:
        entries: List of dicts with at minimum: video_id, destination,
                 tree_node, provenance_score, sources
        stop_on_error: If True, raise on first failure. Default skips.

    Returns:
        {video_id: [segments]} for successfully transcribed videos.
    """
    results: dict[str, list[dict]] = {}
    for entry in entries:
        vid = entry["video_id"]
        try:
            segments = transcribe_video(
                video_id=vid,
                destination=entry.get("destination", ""),
                tree_node=entry.get("tree_node", ""),
                provenance_score=entry.get("provenance_score", 0.0),
                sources=entry.get("sources", []),
            )
            results[vid] = segments
        except Exception as e:
            print(f"[transcriber] Batch: skipping {vid} — {e}")
            if stop_on_error:
                raise
    return results


# ── Step 1: YouTube captions ───────────────────────────────────────────────────

_yt_api = YouTubeTranscriptApi()


def _fetch_captions(video_id: str) -> list[dict]:
    """Fetch captions via youtube_transcript_api."""
    try:
        fetched = _yt_api.fetch(video_id)
    except (TranscriptsDisabled, NoTranscriptFound) as e:
        raise _SkipToNext(f"no captions: {e}") from e

    return [
        {
            "text": seg.text,
            "video_id": video_id,
            "title": video_id,  # enriched downstream if needed
            "timestamp_start": seg.start,
            "timestamp_end": seg.start + seg.duration,
            "url": f"https://www.youtube.com/watch?v={video_id}&t={int(seg.start)}s",
            "source_type": "youtube",
            "language": "en",
        }
        for seg in fetched
    ]


# ── Step 2: Local Whisper via yt-dlp download ──────────────────────────────────

def _transcribe_with_whisper(video_id: str) -> list[dict]:
    """Download audio with yt-dlp and transcribe locally with Whisper."""
    audio_path = _download_audio(video_id)
    try:
        return _run_whisper(video_id, audio_path)
    finally:
        # Always clean up temp file
        try:
            Path(audio_path).unlink(missing_ok=True)
        except Exception:
            pass


def _download_audio(video_id: str) -> str:
    """Download audio-only to a temp WAV file. Returns path."""
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp.close()
    output_path = tmp.name

    cmd = [
        "yt-dlp",
        "--format", "bestaudio",
        "--extract-audio",
        "--audio-format", "wav",
        "--audio-quality", "0",
        "--no-playlist",
        "--output", output_path,
        "--no-progress",
        f"https://www.youtube.com/watch?v={video_id}",
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    except FileNotFoundError:
        raise _SkipToNext("yt-dlp not installed")
    except subprocess.TimeoutExpired:
        raise _SkipToNext("yt-dlp download timed out")

    if result.returncode != 0:
        raise _SkipToNext(f"yt-dlp exited {result.returncode}: {result.stderr[:200]}")

    # yt-dlp may append .wav extension — find the actual file
    actual = Path(output_path)
    if not actual.exists():
        # yt-dlp may have used a slightly different name
        wav_files = list(Path(tempfile.gettempdir()).glob(f"{actual.stem}*.wav"))
        if wav_files:
            actual = wav_files[0]
        else:
            raise _SkipToNext("Downloaded audio file not found")

    return str(actual)


def _run_whisper(video_id: str, audio_path: str) -> list[dict]:
    """Run the local Whisper pipeline on an audio file."""
    pipe = _get_whisper_pipe()

    output = pipe(
        audio_path,
        chunk_length_s=30,
        stride_length_s=5,
        return_timestamps=True,
    )

    segments = output.get("chunks") or []
    if not segments:
        # Fallback: treat full text as a single segment
        full_text = output.get("text", "").strip()
        if not full_text:
            raise _SkipToNext("Whisper returned empty transcript")
        return [{
            "text": full_text,
            "video_id": video_id,
            "title": video_id,
            "timestamp_start": 0.0,
            "timestamp_end": 0.0,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "source_type": "youtube",
            "language": "en",
        }]

    return [
        {
            "text": chunk["text"].strip(),
            "video_id": video_id,
            "title": video_id,
            "timestamp_start": float((chunk.get("timestamp") or [0, 0])[0] or 0),
            "timestamp_end": float((chunk.get("timestamp") or [0, 0])[1] or 0),
            "url": (
                f"https://www.youtube.com/watch?v={video_id}"
                f"&t={int((chunk.get('timestamp') or [0])[0] or 0)}s"
            ),
            "source_type": "youtube",
            "language": "en",
        }
        for chunk in segments
        if chunk.get("text", "").strip()
    ]


# ── Step 3: OpenAI Whisper API ─────────────────────────────────────────────────

def _transcribe_with_openai_api(video_id: str) -> list[dict]:
    """Last resort: transcribe via OpenAI Whisper API."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise _SkipToNext("OPENAI_API_KEY not set")

    try:
        import openai
    except ImportError:
        raise _SkipToNext("openai package not installed: pip install openai")

    audio_path = _download_audio(video_id)
    try:
        client = openai.OpenAI(api_key=api_key)
        with open(audio_path, "rb") as f:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                response_format="verbose_json",
                timestamp_granularities=["segment"],
            )

        segments = getattr(response, "segments", []) or []
        if not segments:
            text = getattr(response, "text", "").strip()
            if not text:
                raise _SkipToNext("OpenAI API returned empty transcript")
            return [{
                "text": text,
                "video_id": video_id,
                "title": video_id,
                "timestamp_start": 0.0,
                "timestamp_end": 0.0,
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "source_type": "youtube",
                "language": "en",
            }]

        return [
            {
                "text": seg.get("text", "").strip(),
                "video_id": video_id,
                "title": video_id,
                "timestamp_start": float(seg.get("start", 0)),
                "timestamp_end": float(seg.get("end", 0)),
                "url": (
                    f"https://www.youtube.com/watch?v={video_id}"
                    f"&t={int(seg.get('start', 0))}s"
                ),
                "source_type": "youtube",
                "language": "en",
            }
            for seg in segments
            if seg.get("text", "").strip()
        ]
    finally:
        try:
            Path(audio_path).unlink(missing_ok=True)
        except Exception:
            pass


# ── Helpers ────────────────────────────────────────────────────────────────────

def _resolve_method_order(force_method: Optional[str]) -> list[str]:
    if force_method:
        return [force_method]
    return ["captions", "whisper", "openai_api"]


class _SkipToNext(Exception):
    """Internal signal to advance to the next transcription method."""
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)
