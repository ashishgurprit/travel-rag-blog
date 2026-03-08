"""Cross-encoder reranker using BAAI/bge-reranker-base."""


class Reranker:
    """Reranks retrieval results using a cross-encoder model."""

    def __init__(self, model_name: str = "BAAI/bge-reranker-base") -> None:
        self._model_name = model_name
        self._model = None

    def _load_model(self) -> None:
        if self._model is None:
            from FlagEmbedding import FlagReranker  # lazy import avoids load at startup
            self._model = FlagReranker(self._model_name, use_fp16=True)

    def rerank(
        self,
        query: str,
        chunks: list[dict] | None,
        top_n: int = 5,
    ) -> list[dict]:
        """Rerank chunks by cross-encoder score, returning top_n sorted descending.

        Returns [] if chunks is None or empty.
        Adds 'rerank_score' to each returned chunk dict.
        """
        if not chunks:
            return []

        self._load_model()

        pairs = [[query, chunk["text"]] for chunk in chunks]
        scores = self._model.compute_score(pairs, normalize=True)

        for chunk, score in zip(chunks, scores):
            chunk["rerank_score"] = score

        sorted_chunks = sorted(chunks, key=lambda c: c["rerank_score"], reverse=True)
        return sorted_chunks[:top_n]
