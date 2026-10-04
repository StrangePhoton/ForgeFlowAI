"""Validated, timed, authorized MCP tool execution over an IndustrialReader."""

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from pydantic import BaseModel, ValidationError

from forgeflow.errors import ForgeFlowError, ToolTimeoutError, ToolValidationError
from forgeflow.mcp.authz import AllowAllAuthorizer, ToolAuthorizer
from forgeflow.mcp.schemas import (
    GET_ALARM_HISTORY,
    GET_EQUIPMENT,
    GET_MAINTENANCE_HISTORY,
    GET_SENSOR_HISTORY,
    AlarmHistoryResult,
    EquipmentIdInput,
    HistoryWindowInput,
    MaintenanceHistoryResult,
    SensorHistoryResult,
)
from forgeflow.observability.logging import get_logger
from forgeflow.services.protocols import IndustrialReader

logger = get_logger(__name__)

Handler = Callable[[BaseModel], Awaitable[dict[str, Any]]]


class ToolRegistry:
    """Deterministic execution layer wrapped by MCP servers."""

    def __init__(
        self,
        reader: IndustrialReader,
        *,
        timeout_seconds: float = 15.0,
        authorizer: ToolAuthorizer | None = None,
    ) -> None:
        self._timeout_seconds = timeout_seconds
        self._authorizer = authorizer or AllowAllAuthorizer()
        self._inputs: dict[str, type[BaseModel]] = {
            GET_EQUIPMENT: EquipmentIdInput,
            GET_SENSOR_HISTORY: HistoryWindowInput,
            GET_ALARM_HISTORY: HistoryWindowInput,
            GET_MAINTENANCE_HISTORY: EquipmentIdInput,
        }
        self._handlers: dict[str, Handler] = {
            GET_EQUIPMENT: self._get_equipment,
            GET_SENSOR_HISTORY: self._get_sensor_history,
            GET_ALARM_HISTORY: self._get_alarm_history,
            GET_MAINTENANCE_HISTORY: self._get_maintenance_history,
        }
        self._reader = reader

    @property
    def timeout_seconds(self) -> float:
        return self._timeout_seconds

    async def invoke(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = arguments or {}
        self._authorizer.authorize(name, payload)
        input_model = self._inputs.get(name)
        handler = self._handlers.get(name)
        if input_model is None or handler is None:
            raise ForgeFlowError(f"Unknown tool {name}", code="unknown_tool", status_code=404)
        try:
            parsed = input_model.model_validate(payload)
        except ValidationError as exc:
            raise ToolValidationError(
                f"Invalid arguments for {name}",
                details={"errors": exc.errors()},
            ) from exc
        try:
            result = await asyncio.wait_for(handler(parsed), timeout=self._timeout_seconds)
        except TimeoutError as exc:
            logger.warning("mcp_tool_timeout", extra={"forgeflow": {"tool": name}})
            raise ToolTimeoutError(f"Tool {name} timed out") from exc
        logger.info("mcp_tool_call", extra={"forgeflow": {"tool": name, "ok": True}})
        return result

    async def _get_equipment(self, payload: BaseModel) -> dict[str, Any]:
        args = EquipmentIdInput.model_validate(payload.model_dump())
        item = await self._reader.get_equipment(args.equipment_id)
        return item.model_dump(mode="json")

    async def _get_sensor_history(self, payload: BaseModel) -> dict[str, Any]:
        args = HistoryWindowInput.model_validate(payload.model_dump())
        items = await self._reader.sensor_history(
            args.equipment_id, start=args.start, end=args.end, limit=args.limit
        )
        return SensorHistoryResult(count=len(items), items=items).model_dump(mode="json")

    async def _get_alarm_history(self, payload: BaseModel) -> dict[str, Any]:
        args = HistoryWindowInput.model_validate(payload.model_dump())
        items = await self._reader.alarm_history(
            args.equipment_id, start=args.start, end=args.end, limit=args.limit
        )
        return AlarmHistoryResult(count=len(items), items=items).model_dump(mode="json")

    async def _get_maintenance_history(self, payload: BaseModel) -> dict[str, Any]:
        args = EquipmentIdInput.model_validate(payload.model_dump())
        items = await self._reader.maintenance_history(args.equipment_id)
        return MaintenanceHistoryResult(count=len(items), items=items).model_dump(mode="json")
