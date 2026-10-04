"""Retrieval over fictional manuals. No paid embedding API."""

import pytest
from forgeflow.domain.seed.constants import CNC_CODE, DEMO_CLOCK
from forgeflow.domain.seed.generate import generate_plant
from forgeflow.mcp.runtime import build_tool_gateway
from forgeflow.mcp.schemas import SEARCH_DOCUMENTATION
from forgeflow.retrieval.corpus import load_sample_manuals, manuals_index
from forgeflow.services.snapshot import InMemoryIndustrialReader


def test_sample_manuals_include_cnc_cooling() -> None:
    titles = {item.title for item in load_sample_manuals()}
    assert "FX-400 Coolant Loop Service Manual" in titles


@pytest.mark.asyncio
async def test_cnc_query_retrieves_cooling_manual() -> None:
    index = manuals_index()
    hits = await index.search(
        "CNC-042 cooling coolant overheating TEMP_HIGH",
        equipment_id=CNC_CODE,
        limit=3,
    )
    assert hits
    assert any("cnc-042-cooling.md" in hit.source_path for hit in hits)
    assert any("coolant" in hit.content.lower() for hit in hits)


@pytest.mark.asyncio
async def test_search_documentation_mcp_tool() -> None:
    reader = InMemoryIndustrialReader(generate_plant(now=DEMO_CLOCK))
    gateway = build_tool_gateway(reader)
    result = await gateway.call(
        SEARCH_DOCUMENTATION,
        {"query": "CNC-042 coolant strainer inspection", "equipment_id": CNC_CODE, "limit": 3},
    )
    assert result["count"] >= 1
    paths = [item["source_path"] for item in result["items"]]
    assert any("cnc-042-cooling.md" in path for path in paths)
