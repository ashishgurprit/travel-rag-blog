import pytest

SAMPLE_DOC = {
    "text": " ".join(["This is sentence number %d." % i for i in range(200)]),
    "destination": "japan",
    "source_type": "youtube",
    "url": "https://youtube.com/watch?v=abc&t=0s",
    "title": "Japan Travel Guide",
    "timestamp_start": 10.0,
    "video_id": "abc123",
    "language": "en",
}

def test_chunk_sizes_within_bounds():
    """All chunks have token estimate between 50 and 600."""
    from backend.ingestion.chunker import chunk_document
    chunks = chunk_document(SAMPLE_DOC, target_tokens=400, overlap_tokens=50)
    for chunk in chunks:
        token_est = len(chunk["text"].split()) * 1.3
        assert 50 <= token_est <= 600, f"Chunk too small or too large: {token_est}"

def test_required_metadata_preserved():
    """Destination, source_type, url are passed through to every chunk."""
    from backend.ingestion.chunker import chunk_document
    chunks = chunk_document(SAMPLE_DOC)
    for chunk in chunks:
        assert chunk["destination"] == "japan"
        assert chunk["source_type"] == "youtube"
        assert chunk["url"] == SAMPLE_DOC["url"]
        assert chunk["title"] == "Japan Travel Guide"
        assert chunk["language"] == "en"
        assert chunk["timestamp_seconds"] == 10.0

def test_vector_id_unique_within_document():
    """Every chunk in the same document has a unique vector_id."""
    from backend.ingestion.chunker import chunk_document
    chunks = chunk_document(SAMPLE_DOC)
    ids = [c["vector_id"] for c in chunks]
    assert len(ids) == len(set(ids)), "Duplicate vector_ids found"

def test_chunk_index_and_total_chunks():
    """chunk_index is sequential starting at 0; total_chunks matches list length."""
    from backend.ingestion.chunker import chunk_document
    chunks = chunk_document(SAMPLE_DOC)
    assert len(chunks) > 1
    for i, chunk in enumerate(chunks):
        assert chunk["chunk_index"] == i
        assert chunk["total_chunks"] == len(chunks)

def test_small_document_returns_single_chunk():
    """A document with less than target_tokens returns one chunk."""
    from backend.ingestion.chunker import chunk_document
    small_doc = {**SAMPLE_DOC, "text": "This is a very short document. It has two sentences."}
    chunks = chunk_document(small_doc, target_tokens=400)
    assert len(chunks) == 1

def test_minimum_chunk_size_filter():
    """Chunks with < 50 estimated tokens are discarded."""
    from backend.ingestion.chunker import chunk_document
    # A doc where the last chunk would be tiny
    tiny_tail = SAMPLE_DOC.copy()
    # 200-sentence doc will produce normal chunks; the filter shouldn't drop valid ones
    chunks = chunk_document(tiny_tail)
    for chunk in chunks:
        token_est = len(chunk["text"].split()) * 1.3
        assert token_est >= 50
