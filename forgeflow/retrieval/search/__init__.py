"""pgvector cosine search."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from forgeflow.domain.models import DocumentChunk
from forgeflow.retrieval.embeddings import HashedEmbeddingProvider
from forgeflow.retrieval.search.hits import SearchHit


class PgVectorSearcher:
    def __init__(
        self,
        session: AsyncSession,
        embedder: HashedEmbeddingProvider | None = None,
    ) -> None:
        self._session = session
        self._embedder = embedder or HashedEmbeddingProvider()

    async def search(
        self,
        query: str,
        *,
        equipment_id: str | None = None,
        limit: int = 5,
    ) -> list[SearchHit]:
        if not query.strip():
            return []
        vector = self._embedder.embed_query(query)
        stmt = (
            select(DocumentChunk)
            .order_by(DocumentChunk.embedding.cosine_distance(vector))
            .limit(max(1, limit) * 3)
        )
        rows = (await self._session.scalars(stmt)).all()
        hits: list[SearchHit] = []
        for row in rows:
            metadata = dict(row.chunk_metadata or {})
            codes = [str(code) for code in metadata.get("equipment_codes", [])]
            score = 1.0
            if equipment_id and equipment_id in codes:
                score += 0.2
            hits.append(
                SearchHit(
                    document_id=str(row.document_id),
                    title=str(metadata.get("title") or row.source_path),
                    source_path=row.source_path,
                    content=row.content,
                    score=score,
                    equipment_codes=codes,
                    chunk_index=row.chunk_index,
                )
            )
        if equipment_id:
            hits.sort(
                key=lambda hit: (equipment_id in hit.equipment_codes, hit.score),
                reverse=True,
            )
        return hits[: max(1, limit)]
