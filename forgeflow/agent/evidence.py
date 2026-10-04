"""Deterministic evidence evaluation. The model does not invent operational facts."""

from datetime import datetime, timedelta
from statistics import mean
from typing import Any

from forgeflow.agent.models import Confidence, EvidenceBundle, EvidenceItem
from forgeflow.domain.seed.constants import LOOKBACK_DAYS, TEMP_HIGH_CODE

_RECENT_DAYS = 7
_BASELINE_END_OFFSET_DAYS = 23
_TEMP_RISE_MARGIN_C = 8.0
_COOLANT_DROP_MARGIN = 3.0
_MIN_TEMP_HIGH_FOR_CAUSE = 3


def evaluate_evidence(
    *,
    equipment_code: str | None,
    equipment: dict[str, Any] | None,
    telemetry: list[dict[str, Any]],
    alarms: list[dict[str, Any]],
    maintenance: list[dict[str, Any]],
    as_of: datetime,
) -> EvidenceBundle:
    if equipment is None or not equipment_code:
        return EvidenceBundle(
            facts=[
                EvidenceItem(
                    kind="FACT",
                    statement="No equipment record was resolved for this request.",
                    source="get_equipment",
                )
            ],
            evidence_sufficient=False,
            confidence="insufficient",
        )

    window_start = as_of - timedelta(days=LOOKBACK_DAYS)
    recent_start = as_of - timedelta(days=_RECENT_DAYS)
    baseline_end = as_of - timedelta(days=_BASELINE_END_OFFSET_DAYS)

    recent_temps = [
        _float(row.get("temperature"))
        for row in telemetry
        if _in_range(_timestamp(row.get("timestamp")), recent_start, as_of)
    ]
    baseline_temps = [
        _float(row.get("temperature"))
        for row in telemetry
        if _in_range(_timestamp(row.get("timestamp")), window_start, baseline_end)
    ]
    recent_coolant = [
        _float(row.get("coolant_flow"))
        for row in telemetry
        if row.get("coolant_flow") is not None
        and _in_range(_timestamp(row.get("timestamp")), recent_start, as_of)
    ]
    baseline_coolant = [
        _float(row.get("coolant_flow"))
        for row in telemetry
        if row.get("coolant_flow") is not None
        and _in_range(_timestamp(row.get("timestamp")), window_start, baseline_end)
    ]

    recent_mean_temp = _mean(recent_temps)
    baseline_mean_temp = _mean(baseline_temps)
    recent_mean_coolant = _mean(recent_coolant)
    baseline_mean_coolant = _mean(baseline_coolant)

    temp_high = [row for row in alarms if str(row.get("code")) == TEMP_HIGH_CODE]
    overdue = [
        str(row.get("title") or "maintenance")
        for row in maintenance
        if _is_overdue(row.get("next_due_at"), as_of)
    ]
    cooling_overdue = [title for title in overdue if "cooling" in title.lower()]

    facts: list[EvidenceItem] = [
        EvidenceItem(
            kind="FACT",
            statement=(
                f"{equipment_code} returned {len(telemetry)} sensor readings "
                f"and {len(alarms)} alarms in the investigation window."
            ),
            source="get_sensor_history",
        )
    ]
    facts.append(
        EvidenceItem(
            kind="FACT",
            statement=(
                f"{equipment_code} has {len(temp_high)} {TEMP_HIGH_CODE} alarms in the window."
            ),
            source="get_alarm_history",
        )
    )
    if baseline_mean_temp is not None and recent_mean_temp is not None:
        facts.append(
            EvidenceItem(
                kind="FACT",
                statement=(
                    "Mean temperature moved from "
                    f"{baseline_mean_temp:.1f} C in the baseline window "
                    f"to {recent_mean_temp:.1f} C in the last {_RECENT_DAYS} days."
                ),
                source="get_sensor_history",
            )
        )
    if baseline_mean_coolant is not None and recent_mean_coolant is not None:
        facts.append(
            EvidenceItem(
                kind="FACT",
                statement=(
                    f"Mean coolant flow declined from {baseline_mean_coolant:.1f} "
                    f"to {recent_mean_coolant:.1f}."
                ),
                source="get_sensor_history",
            )
        )
    if cooling_overdue:
        facts.append(
            EvidenceItem(
                kind="FACT",
                statement=f"Cooling-related maintenance is overdue: {', '.join(cooling_overdue)}.",
                source="get_maintenance_history",
            )
        )
    elif overdue:
        facts.append(
            EvidenceItem(
                kind="FACT",
                statement=f"Maintenance is overdue: {', '.join(overdue)}.",
                source="get_maintenance_history",
            )
        )

    temp_rose = (
        recent_mean_temp is not None
        and baseline_mean_temp is not None
        and recent_mean_temp > baseline_mean_temp + _TEMP_RISE_MARGIN_C
    )
    coolant_dropped = (
        recent_mean_coolant is not None
        and baseline_mean_coolant is not None
        and recent_mean_coolant < baseline_mean_coolant - _COOLANT_DROP_MARGIN
    )
    cooling_pattern = (
        len(temp_high) >= _MIN_TEMP_HIGH_FOR_CAUSE
        and temp_rose
        and coolant_dropped
        and bool(cooling_overdue)
    )

    inferences: list[EvidenceItem] = []
    recommendations: list[EvidenceItem] = []
    likely_cause: str | None = None
    bundle_confidence: Confidence
    sufficient: bool
    if cooling_pattern:
        likely_cause = (
            "Cooling system degradation: declining coolant flow with rising temperature "
            "and overdue cooling-system inspection."
        )
        inferences.append(
            EvidenceItem(
                kind="INFERENCE",
                statement=likely_cause,
                source="evaluate_evidence",
            )
        )
        recommendations.append(
            EvidenceItem(
                kind="RECOMMENDATION",
                statement=(
                    "Inspect the coolant loop, restore flow, "
                    "and schedule the overdue cooling inspection."
                ),
                source="evaluate_evidence",
            )
        )
        bundle_confidence = "high"
        sufficient = True
    else:
        inferences.append(
            EvidenceItem(
                kind="INFERENCE",
                statement=(
                    "The retrieved operational data does not support a high-confidence root cause."
                ),
                source="evaluate_evidence",
            )
        )
        recommendations.append(
            EvidenceItem(
                kind="RECOMMENDATION",
                statement=(
                    "Collect additional telemetry or inspect the asset "
                    "before taking a write action."
                ),
                source="evaluate_evidence",
            )
        )
        bundle_confidence = "insufficient"
        sufficient = False

    return EvidenceBundle(
        reading_count=len(telemetry),
        alarm_count=len(alarms),
        temp_high_count=len(temp_high),
        baseline_mean_temperature=baseline_mean_temp,
        recent_mean_temperature=recent_mean_temp,
        baseline_mean_coolant_flow=baseline_mean_coolant,
        recent_mean_coolant_flow=recent_mean_coolant,
        overdue_maintenance=overdue,
        facts=facts,
        inferences=inferences,
        recommendations=recommendations,
        evidence_sufficient=sufficient,
        likely_cause=likely_cause,
        confidence=bundle_confidence,
    )


def report_actions(evidence: EvidenceBundle) -> list[str]:
    return [item.statement for item in evidence.recommendations]


def _mean(values: list[float | None]) -> float | None:
    present = [value for value in values if value is not None]
    if not present:
        return None
    return mean(present)


def _float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _timestamp(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _in_range(stamp: datetime | None, start: datetime, end: datetime) -> bool:
    if stamp is None:
        return False
    if stamp.tzinfo is None and start.tzinfo is not None:
        stamp = stamp.replace(tzinfo=start.tzinfo)
    return start <= stamp <= end


def _is_overdue(value: Any, as_of: datetime) -> bool:
    due = _timestamp(value)
    if due is None:
        return False
    if due.tzinfo is None and as_of.tzinfo is not None:
        due = due.replace(tzinfo=as_of.tzinfo)
    return due < as_of
