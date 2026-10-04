"""pgvector search over ingested fictional manuals."""

import pytest
from fastapi.testclient import TestClient
from forgeflow.config import get_settings
from forgeflow.db.session import Database
from forgeflow.domain.seed.constants import CNC_CODE
from forgeflow.domain.seed.generate import PlantSnapshot
from forgeflow.retrieval.search import PgVectorSearcher


@pytest.mark.integration
@pytest.mark.asyncio
async def test_pgvector_search_returns_cnc_manual(
    require_postgres: None, seeded_plant: PlantSnapshot
) -> None:
    del seeded_plant
    database = Database(get_settings())
    try:
        async with database.session_factory() as session:
            hits = await PgVectorSearcher(session).search(
                "CNC-042 cooling coolant TEMP_HIGH strainer",
                equipment_id=CNC_CODE,
                limit=3,
            )
        assert hits
        assert any("cnc-042-cooling.md" in hit.source_path for hit in hits)
    finally:
        await database.dispose()


@pytest.mark.integration
def test_seeded_investigation_cites_manual(client: TestClient, seeded_plant: PlantSnapshot) -> None:
    del seeded_plant
    response = client.post(
        "/api/v1/investigations",
        json={"request": "Investigate overheating on CNC-042"},
    )
    assert response.status_code == 200
    body = response.json()
    findings = " ".join(item["statement"] for item in body["report"]["findings"])
    assert "cnc-042-cooling.md" in findings
    assert body["status"] == "awaiting_approval"
