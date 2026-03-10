"""Semantic chunker — splits documents into overlapping token-bounded chunks."""

import re


def _estimate_tokens(text: str) -> float:
    """Approximate token count: word count × 1.3."""
    return len(text.split()) * 1.3


def _split_sentences(text: str) -> list[str]:
    """Split text on sentence boundaries."""
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    return [p for p in parts if p]


def chunk_document(
    doc: dict,
    target_tokens: int = 400,
    overlap_tokens: int = 50,
) -> list[dict]:
    """Split a document dict into overlapping chunks at sentence boundaries.

    Each chunk inherits metadata from the source doc and gets a unique vector_id.
    Chunks smaller than 50 estimated tokens are discarded.
    """
    text = doc.get("text", "")
    sentences = _split_sentences(text)

    source_type = doc.get("source_type", "unknown")
    doc_id = doc.get("video_id") or doc.get("post_id") or "doc"

    # Build chunks by accumulating sentences
    raw_chunks: list[str] = []
    current_sentences: list[str] = []
    current_tokens: float = 0.0

    for sentence in sentences:
        sentence_tokens = _estimate_tokens(sentence)
        if current_tokens + sentence_tokens > target_tokens and current_sentences:
            raw_chunks.append(" ".join(current_sentences))
            # Overlap: keep trailing words from current chunk
            overlap_words: list[str] = []
            overlap_count = 0.0
            for word in reversed(" ".join(current_sentences).split()):
                if overlap_count >= overlap_tokens:
                    break
                overlap_words.insert(0, word)
                overlap_count += 1.3  # 1 word ≈ 1.3 tokens
            current_sentences = [" ".join(overlap_words)] if overlap_words else []
            current_tokens = _estimate_tokens(" ".join(current_sentences))
        current_sentences.append(sentence)
        current_tokens += sentence_tokens

    if current_sentences:
        raw_chunks.append(" ".join(current_sentences))

    # Filter chunks below minimum size — but always keep at least one chunk
    filtered = [c for c in raw_chunks if _estimate_tokens(c) >= 50]
    raw_chunks = filtered if filtered else raw_chunks[:1]

    total = len(raw_chunks)
    chunks = []
    for i, chunk_text in enumerate(raw_chunks):
        chunk = {
            "text": chunk_text,
            "chunk_index": i,
            "total_chunks": total,
            "destination": doc.get("destination", ""),
            "source_type": source_type,
            "url": doc.get("url", ""),
            "title": doc.get("title", ""),
            "timestamp_seconds": doc.get("timestamp_start", 0),
            "language": doc.get("language", "en"),
            "vector_id": f"{source_type}_{doc_id}_{i}",
        }
        # Pass through provenance metadata when present (tree-discovered content)
        for key in ("tree_node", "tier", "provenance_score", "sources"):
            if key in doc:
                chunk[key] = doc[key]
        chunks.append(chunk)

    return chunks
