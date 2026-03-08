"""Pinecone indexer module for the Travel RAG Search Engine."""

from pinecone import Pinecone

from backend.config import settings

_BATCH_SIZE = 100
_METADATA_KEYS = (
    "destination",
    "source_type",
    "url",
    "title",
    "timestamp_seconds",
    "language",
    "chunk_index",
)


class Indexer:
    """Upserts embedded chunks into a Pinecone index with idempotency."""

    def __init__(self) -> None:
        pc = Pinecone(api_key=settings.pinecone_api_key)
        self._index = pc.Index(settings.pinecone_index_name)

    def upsert_chunks(self, chunks: list[dict]) -> dict:
        """Upsert chunks into Pinecone, skipping any that already exist.

        Args:
            chunks: List of chunk dicts, each requiring ``vector_id``,
                ``embedding``, and the metadata keys defined in ``_METADATA_KEYS``.

        Returns:
            ``{"upserted": int, "skipped": int}``
        """
        if not chunks:
            return {"upserted": 0, "skipped": 0}

        # Collect all vector IDs and check which already exist.
        all_ids = [chunk["vector_id"] for chunk in chunks]
        fetch_response = self._index.fetch(ids=all_ids)
        existing_ids: set[str] = set(fetch_response.vectors.keys())

        new_chunks = [c for c in chunks if c["vector_id"] not in existing_ids]
        skipped = len(chunks) - len(new_chunks)

        # Upsert new chunks in batches of _BATCH_SIZE.
        for batch_start in range(0, len(new_chunks), _BATCH_SIZE):
            batch = new_chunks[batch_start : batch_start + _BATCH_SIZE]
            vectors = [
                {
                    "id": chunk["vector_id"],
                    "values": chunk["embedding"],
                    "metadata": {key: chunk.get(key) for key in _METADATA_KEYS},
                }
                for chunk in batch
            ]
            self._index.upsert(vectors=vectors)

        return {"upserted": len(new_chunks), "skipped": skipped}
