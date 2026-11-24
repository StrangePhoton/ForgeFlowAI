"""Unauthorized writes fail at the tool layer even after a human grant."""

import pytest
from forgeflow.agent.policies import ApprovalGate
from forgeflow.domain.seed.constants import CNC_CODE, DEMO_CLOCK
from forgeflow.domain.seed.generate import generate_plant
from forgeflow.errors import ToolAuthorizationError
from forgeflow.mcp.runtime import build_tool_gateway
from forgeflow.mcp.schemas import CREATE_WORK_ORDER, GET_EQUIPMENT
from forgeflow.security.accounts import principal_for_role
from forgeflow.security.tool_authz import CompositeAuthorizer, RoleToolAuthorizer
from forgeflow.services.snapshot import InMemoryIndustrialReader


def _args() -> dict[str, str]:
    return {
        "equipment_id": CNC_CODE,
        "title": "Inspect coolant loop",
        "description": "Unauthorized",
        "priority": "high",
        "idempotency_key": "investigation:test:create_work_order",
    }


@pytest.mark.asyncio
async def test_engineer_cannot_create_work_order_even_with_grant() -> None:
    reader = InMemoryIndustrialReader(generate_plant(now=DEMO_CLOCK))
    gate = ApprovalGate()
    gate.grant(_args()["idempotency_key"])
    gateway = build_tool_gateway(
        reader,
        authorizer=CompositeAuthorizer(
            RoleToolAuthorizer(principal_for_role("engineer")),
            gate,
        ),
    )
    with pytest.raises(ToolAuthorizationError):
        await gateway.call(CREATE_WORK_ORDER, _args())
    assert reader._created_work_orders == []


@pytest.mark.asyncio
async def test_manager_still_needs_approval_grant() -> None:
    reader = InMemoryIndustrialReader(generate_plant(now=DEMO_CLOCK))
    gateway = build_tool_gateway(
        reader,
        authorizer=CompositeAuthorizer(
            RoleToolAuthorizer(principal_for_role("maintenance_manager")),
            ApprovalGate(),
        ),
    )
    with pytest.raises(ToolAuthorizationError):
        await gateway.call(CREATE_WORK_ORDER, _args())
    assert reader._created_work_orders == []


@pytest.mark.asyncio
async def test_viewer_can_read_equipment_tool() -> None:
    reader = InMemoryIndustrialReader(generate_plant(now=DEMO_CLOCK))
    gateway = build_tool_gateway(
        reader,
        authorizer=RoleToolAuthorizer(principal_for_role("viewer")),
    )
    payload = await gateway.call(GET_EQUIPMENT, {"equipment_id": CNC_CODE})
    assert payload["code"] == CNC_CODE
