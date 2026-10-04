"""Search hit returned to MCP tools and the investigation graph."""

from typing import Protocol

from pydantic import BaseModel, Field


class SearchHit(BaseModel):
    document_id: str
    title: str
    source_path: str
    content: str
    score: float
    equipment_codes: list[str] = Field(default_factory=list)
    chunk_index: int = 0


class DocumentSearcher(Protocol):
    async def search(
        self,
        query: str,
        *,
        equipment_id: str | None = None,
        limit: int = 5,
    ) -> list[SearchHit]: ...
