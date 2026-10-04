"""Persist sample manuals into PostgreSQL with hashed embeddings."""

from datetime import UTC, datetime

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from forgeflow.domain.models import Document, DocumentChunk
from forgeflow.observability.logging import get_logger
from forgeflow.retrieval.corpus import load_sample_manuals
from forgeflow.retrieval.embeddings import HashedEmbeddingProvider

logger = get_logger(__name__)


async def ingest_manuals(
    session: AsyncSession,
    *,
    reset: bool,
    embedder: HashedEmbeddingProvider | None = None,
) -> int:
    provider = embedder or HashedEmbeddingProvider()
    if reset:
        await session.execute(delete(DocumentChunk))
        await session.execute(delete(Document))
    documents = load_sample_manuals()
    now = datetime.now(UTC)
    chunk_count = 0
    for manual in documents:
        session.add(
            Document(
                id=manual.document_id,
                title=manual.title,
                source_path=manual.source_path,
                doc_type=manual.doc_type,
                equipment_codes=list(manual.equipment_codes),
                ingested_at=now,
            )
        )
        embeddings = provider.embed_documents(list(manual.chunks))
        for index, (content, vector) in enumerate(zip(manual.chunks, embeddings, strict=True)):
            session.add(
                DocumentChunk(
                    document_id=manual.document_id,
                    chunk_index=index,
                    content=content,
                    source_path=manual.source_path,
                    chunk_metadata={
                        "title": manual.title,
                        "equipment_codes": list(manual.equipment_codes),
                        "doc_type": manual.doc_type,
                    },
                    embedding=vector,
                )
            )
            chunk_count += 1
    logger.info(
        "manuals_ingested",
        extra={"forgeflow": {"documents": len(documents), "chunks": chunk_count}},
    )
    return chunk_count
