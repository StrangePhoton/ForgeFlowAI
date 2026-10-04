"""Industrial domain enumerations. Stored as strings; validated in application code."""

from enum import StrEnum


class EquipmentType(StrEnum):
    CNC = "cnc"
    PUMP = "pump"
    CONVEYOR = "conveyor"
    PRESS = "press"
    COMPRESSOR = "compressor"


class EquipmentStatus(StrEnum):
    RUNNING = "running"
    IDLE = "idle"
    ALARM = "alarm"
    OFFLINE = "offline"


class SensorStatus(StrEnum):
    RUNNING = "running"
    IDLE = "idle"
    ALARM = "alarm"
    OFFLINE = "offline"


class AlarmSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class MaintenanceType(StrEnum):
    INSPECTION = "inspection"
    PREVENTIVE = "preventive"
    REPAIR = "repair"
    FILTER_CHANGE = "filter_change"


class MaintenanceResult(StrEnum):
    COMPLETED = "completed"
    DEFERRED = "deferred"
    FINDINGS = "findings"


class WorkOrderStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class WorkOrderPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
