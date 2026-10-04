"""Load inspectable catalog files from sample_data/."""

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class EquipmentCatalogRow(BaseModel):
    code: str
    name: str
    equipment_type: str
    model: str
    manufacturer: str
    location: str
    status: str
    installed_at: str
    attributes: dict[str, Any] = Field(default_factory=dict)


class MaintenanceCatalogRow(BaseModel):
    equipment_code: str
    offset_days: int
    hour_utc: int
    maintenance_type: str
    title: str
    description: str
    technician: str
    result: str
    next_due_offset_days: int | None = None


class WorkOrderCatalogRow(BaseModel):
    equipment_code: str
    number: str
    title: str
    description: str
    status: str
    priority: str
    created_offset_days: int
    completed_offset_days: int | None = None


def sample_data_root() -> Path:
    """Resolve the repo (or image) sample_data directory."""
    repo_candidate = Path(__file__).resolve().parents[3] / "sample_data"
    cwd_candidate = Path.cwd() / "sample_data"
    if (repo_candidate / "equipment" / "registry.json").is_file():
        return repo_candidate
    if (cwd_candidate / "equipment" / "registry.json").is_file():
        return cwd_candidate
    msg = "sample_data/equipment/registry.json was not found"
    raise FileNotFoundError(msg)


def load_equipment_catalog() -> list[EquipmentCatalogRow]:
    path = sample_data_root() / "equipment" / "registry.json"
    return _load_rows(path, EquipmentCatalogRow)


def load_maintenance_catalog() -> list[MaintenanceCatalogRow]:
    path = sample_data_root() / "maintenance" / "records.json"
    return _load_rows(path, MaintenanceCatalogRow)


def load_work_order_catalog() -> list[WorkOrderCatalogRow]:
    path = sample_data_root() / "maintenance" / "work_orders.json"
    return _load_rows(path, WorkOrderCatalogRow)


def _load_rows[TModel: BaseModel](path: Path, model: type[TModel]) -> list[TModel]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        msg = f"{path} must contain a JSON array"
        raise ValueError(msg)
    return [model.model_validate(item) for item in payload]
