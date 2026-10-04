"""Load fictional manuals from sample_data/manuals."""

import json
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid5

from forgeflow.domain.seed.constants import SEED_NAMESPACE
from forgeflow.retrieval.chunking import chunk_text
from forgeflow.retrieval.embeddings import HashedEmbeddingProvider
from forgeflow.retrieval.search.hits import SearchHit
from forgeflow.retrieval.search.memory import IndexedChunk, InMemoryDocumentIndex

MANUALS_DIR = Path(__file__).resolve().parents[2] / "sample_data" / "manuals"


@dataclass(frozen=True)
class ManualDocument:
    document_id: UUID
    title: str
    source_path: str
    doc_type: str
    equipment_codes: tuple[str, ...]
    text: str
    chunks: tuple[str, ...]


def load_sample_manuals() -> list[ManualDocument]:
    catalog_path = MANUALS_DIR / "catalog.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    documents: list[ManualDocument] = []
    for entry in catalog:
        relative = str(entry["path"])
        text = (MANUALS_DIR / relative).read_text(encoding="utf-8")
        document_id = uuid5(SEED_NAMESPACE, f"manual|{relative}")
        chunks = tuple(chunk_text(text))
        documents.append(
            ManualDocument(
                document_id=document_id,
                title=str(entry["title"]),
                source_path=f"sample_data/manuals/{relative}",
                doc_type=str(entry["doc_type"]),
                equipment_codes=tuple(str(code) for code in entry["equipment_codes"]),
                text=text,
                chunks=chunks,
            )
        )
    return documents


def manuals_index(embedder: HashedEmbeddingProvider | None = None) -> InMemoryDocumentIndex:
    provider = embedder or HashedEmbeddingProvider()
    indexed: list[IndexedChunk] = []
    for document in load_sample_manuals():
        embeddings = provider.embed_documents(list(document.chunks))
        for index, (content, vector) in enumerate(zip(document.chunks, embeddings, strict=True)):
            hit = SearchHit(
                document_id=str(document.document_id),
                title=document.title,
                source_path=document.source_path,
                content=content,
                score=0.0,
                equipment_codes=list(document.equipment_codes),
                chunk_index=index,
            )
            indexed.append(IndexedChunk(hit=hit, embedding=vector))
    return InMemoryDocumentIndex(indexed, embedder=provider)
