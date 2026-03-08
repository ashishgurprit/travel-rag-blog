"""Embedding module using intfloat/multilingual-e5-large.

CRITICAL: Always apply "passage: " prefix to document chunks and "query: " prefix
to queries. Omitting these prefixes degrades retrieval quality by ~15-20%.
"""

from sentence_transformers import SentenceTransformer


class Embedder:
    """Wraps multilingual-e5-large with mandatory prefix application."""

    def __init__(self, model_name: str = "intfloat/multilingual-e5-large"):
        self._model_name = model_name
        self._model: SentenceTransformer | None = None

    def _load_model(self) -> None:
        if self._model is None:
            self._model = SentenceTransformer(self._model_name)

    def embed_chunks(self, chunks: list[dict]) -> list[dict]:
        """Embed document chunks in-place, applying 'passage: ' prefix.

        Adds 'embedding' key (list[float], len=1024) to each chunk dict.
        Returns the same list.
        """
        self._load_model()
        texts = [f"passage: {chunk['text']}" for chunk in chunks]
        embeddings = self._model.encode(
            texts,
            batch_size=32,
            normalize_embeddings=True,
        )
        for chunk, emb in zip(chunks, embeddings):
            chunk["embedding"] = emb.tolist()
        return chunks

    def embed_query(self, query: str) -> list[float]:
        """Embed a query string with 'query: ' prefix. Returns normalized vector."""
        self._load_model()
        embedding = self._model.encode(
            f"query: {query}",
            batch_size=32,
            normalize_embeddings=True,
        )
        return embedding.tolist()
