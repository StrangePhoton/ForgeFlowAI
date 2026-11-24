"""Configure the process-wide OpenTelemetry meter and tracer providers once."""

from __future__ import annotations

from opentelemetry import metrics, trace
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider

from forgeflow import __version__
from forgeflow.config import Settings
from forgeflow.observability.metrics import init_instruments

_CONFIGURED = False


def configure_telemetry(settings: Settings) -> None:
    """Bind Prometheus-exported OTel metrics. Safe to call more than once."""
    global _CONFIGURED
    if _CONFIGURED or not settings.otel_enabled:
        return
    resource = Resource.create(
        {
            "service.name": settings.app_name,
            "service.version": __version__,
            "deployment.environment": settings.environment,
        }
    )
    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[PrometheusMetricReader()],
    )
    metrics.set_meter_provider(meter_provider)
    trace.set_tracer_provider(TracerProvider(resource=resource))
    init_instruments()
    _CONFIGURED = True
