"""In-memory cosine search over hashed embeddings."""

from forgeflow.retrieval.embeddings import HashedEmbeddingProvider, cosine_similarity
from forgeflow.retrieval.search.hits import SearchHit


class IndexedChunk:
    def __init__(self, hit: SearchHit, embedding: list[float]) -> None:
        self.hit = hit
        self.embedding = embedding


class InMemoryDocumentIndex:
    def __init__(
        self,
        chunks: list[IndexedChunk],
        embedder: HashedEmbeddingProvider | None = None,
    ) -> None:
        self._chunks = chunks
        self._embedder = embedder or HashedEmbeddingProvider()

    async def search(
        self,
        query: str,
        *,
        equipment_id: str | None = None,
        limit: int = 5,
    ) -> list[SearchHit]:
        if not query.strip() or not self._chunks:
            return []
        query_vec = self._embedder.embed_query(query)
        scored: list[SearchHit] = []
        for item in self._chunks:
            score = cosine_similarity(query_vec, item.embedding)
            if equipment_id and equipment_id in item.hit.equipment_codes:
                score += 0.2
            scored.append(item.hit.model_copy(update={"score": round(score, 6)}))
        scored.sort(key=lambda hit: hit.score, reverse=True)
        return scored[: max(1, limit)]
