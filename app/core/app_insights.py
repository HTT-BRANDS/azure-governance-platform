"""Azure Application Insights integration with custom telemetry.

Provides request telemetry middleware and optional OpenCensus integration
for Azure Application Insights. Includes custom telemetry for:
- Sync operations (duration, success/failure, records processed)
- Authentication events (login/logout, token refresh, failures)
- Performance metrics (API latency, database queries)
- Business metrics (compliance scores, cost changes)

Falls back to structured logging when the OpenCensus SDK is not installed.
"""

import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class TelemetryEventType(Enum):
    """Types of telemetry events tracked."""

    # Sync events
    SYNC_STARTED = "sync.started"
    SYNC_COMPLETED = "sync.completed"
    SYNC_FAILED = "sync.failed"

    # Auth events
    AUTH_LOGIN_SUCCESS = "auth.login.success"
    AUTH_LOGIN_FAILURE = "auth.login.failure"
    AUTH_LOGOUT = "auth.logout"
    AUTH_TOKEN_REFRESH = "auth.token.refresh"
    AUTH_TOKEN_EXPIRED = "auth.token.expired"

    # Performance events
    API_REQUEST = "api.request"
    DB_QUERY = "db.query"
    CACHE_OPERATION = "cache.operation"

    # Dependency tracking
    DEPENDENCY = "dependency"

    # Business events
    COMPLIANCE_VIOLATION = "compliance.violation"
    BUDGET_ALERT = "budget.alert"
    COST_ANOMALY = "cost.anomaly"


@dataclass
class TelemetryEvent:
    """Structured telemetry event data."""

    event_type: TelemetryEventType
    timestamp: float = field(default_factory=time.time)
    duration_ms: float | None = None
    success: bool | None = None
    tenant_id: str | None = None
    user_id: str | None = None
    operation_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    properties: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary for logging/serialization."""
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp,
            "duration_ms": self.duration_ms,
            "success": self.success,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "operation_id": self.operation_id,
            "properties": self.properties,
            "metrics": self.metrics,
        }


class AppInsightsTelemetryClient:
    """Client for sending custom telemetry to Application Insights.

    Supports both Azure Monitor (OpenCensus) and structured logging fallback.
    """

    def __init__(self):
        self.settings = get_settings()
        self.enabled = self.settings.app_insights_enabled
        self._exporter = None
        self._tracer = None

        if self.enabled:
            try:
                from opencensus.ext.azure.trace_exporter import AzureExporter
                from opencensus.trace.samplers import ProbabilitySampler
                from opencensus.trace.tracer import Tracer

                connection_string = self.settings.app_insights_connection_string
                if connection_string:
                    self._exporter = AzureExporter(connection_string=connection_string)
                    self._tracer = Tracer(
                        exporter=self._exporter,
                        sampler=ProbabilitySampler(1.0),
                    )
                    logger.info("App Insights telemetry client initialized")
                else:
                    logger.warning("App Insights enabled but connection string not set")
                    self.enabled = False
            except ImportError:
                logger.warning(
                    "OpenCensus not installed. Using structured logging fallback. "
                    "Install with: pip install opencensus-ext-azure"
                )
                self.enabled = False

    def track_event(self, event: TelemetryEvent) -> None:
        """Track a telemetry event."""
        event_dict = event.to_dict()

        if self.enabled and self._tracer:
            try:
                # Add event as custom property in trace
                with self._tracer.span(name=event.event_type.value) as span:
                    span.add_attribute("event_data", str(event_dict))
                    for key, value in event.properties.items():
                        span.add_attribute(f"prop.{key}", str(value))
                    for key, value in event.metrics.items():
                        span.add_attribute(f"metric.{key}", value)
            except Exception as e:
                logger.debug(f"Failed to send to App Insights: {e}")

        # Always log to structured logging
        log_data = {
            "telemetry_event": event.event_type.value,
            "operation_id": event.operation_id,
            "tenant_id": event.tenant_id,
            "user_id": event.user_id,
            "duration_ms": event.duration_ms,
            "success": event.success,
            **event.properties,
            **{f"metric_{k}": v for k, v in event.metrics.items()},
        }
        logger.info("telemetry_event", extra=log_data)

    def track_metric(
        self, name: str, value: float, properties: dict[str, str] | None = None
    ) -> None:
        """Track a custom metric."""
        if self.enabled and self._tracer:
            try:
                with self._tracer.span(name=f"metric.{name}") as span:
                    span.add_attribute("metric_value", value)
                    if properties:
                        for k, v in properties.items():
                            span.add_attribute(f"prop.{k}", v)
            except Exception as e:
                logger.debug(f"Failed to track metric: {e}")

        logger.info(
            "custom_metric",
            extra={
                "metric_name": name,
                "metric_value": value,
                **(properties or {}),
            },
        )

    def track_exception(
        self,
        exception: Exception,
        properties: dict[str, str] | None = None,
    ) -> None:
        """Track an exception."""
        if self.enabled and self._tracer:
            try:
                with self._tracer.span(name="exception") as span:
                    span.add_attribute("exception_type", type(exception).__name__)
                    span.add_attribute("exception_message", str(exception))
                    if properties:
                        for k, v in properties.items():
                            span.add_attribute(f"prop.{k}", v)
            except Exception as e:
                logger.debug(f"Failed to track exception: {e}")

        logger.exception(
            "tracked_exception",
            extra={
                "exception_type": type(exception).__name__,
                **(properties or {}),
            },
        )


# Global telemetry client instance
telemetry_client = AppInsightsTelemetryClient()


class AppInsightsMiddleware(BaseHTTPMiddleware):
    """Middleware that tracks request duration and logs telemetry.

    Emits structured log lines for every request including method, path,
    status code, and duration in milliseconds. Integrates with telemetry
    client for custom dimensions.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        operation_id = str(uuid.uuid4())[:8]
        request.state.operation_id = operation_id

        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        # Skip noisy health-check logging
        if request.url.path not in ("/health", "/health/detailed", "/metrics"):
            # Extract user context if available
            user_id = getattr(request.state, "user_id", None)
            tenant_id = getattr(request.state, "tenant_id", None)

            # Create telemetry event
            event = TelemetryEvent(
                event_type=TelemetryEventType.API_REQUEST,
                operation_id=operation_id,
                duration_ms=round(duration_ms, 1),
                success=response.status_code < 400,
                user_id=user_id,
                tenant_id=tenant_id,
                properties={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "client_host": request.client.host if request.client else None,
                    "user_agent": request.headers.get("user-agent"),
                },
                metrics={
                    "duration_ms": duration_ms,
                    "response_size_bytes": int(response.headers.get("content-length", 0)),
                },
            )
            telemetry_client.track_event(event)

        # Attach server-timing header for observability
        response.headers["Server-Timing"] = f"total;dur={duration_ms:.1f}"
        response.headers["X-Operation-ID"] = operation_id
        return response


# =============================================================================
# Backward-compatible re-exports from telemetry_events
# =============================================================================
# Tracker helpers live in telemetry_events.py (split for 600-line fitness).
# Re-exported here so existing ``from app.core.app_insights import …`` still works.
from app.core.telemetry_events import (  # noqa: E402, F401
    track_auth_login_failure,
    track_auth_login_success,
    track_auth_logout,
    track_auth_token_refresh,
    track_budget_alert,
    track_compliance_violation,
    track_cost_anomaly,
    track_dependency,
    track_sync_completed,
    track_sync_failed,
    track_sync_operation,
)

# =============================================================================
# Initialization
# =============================================================================


def init_app_insights(app) -> None:
    """Initialize Application Insights telemetry on the FastAPI app.

    When ``APPLICATIONINSIGHTS_CONNECTION_STRING`` is set **and** the
    ``opencensus`` package is available, a full Azure exporter is
    configured. Otherwise we fall back to the lightweight
    :class:`AppInsightsMiddleware` for structured request logging.

    Also initializes the global telemetry client for custom events.
    """
    settings = get_settings()

    if settings.app_insights_enabled:
        try:
            # Imports are done in __init__ of telemetry_client
            # Just verify that opencensus is available
            from opencensus.ext.azure.trace_exporter import AzureExporter  # noqa: F401

            logger.info("App Insights enabled - telemetry client initialized")
        except ImportError:
            logger.warning(
                "opencensus not installed; using basic request logging. "
                "Install with: pip install opencensus-ext-azure"
            )
    else:
        logger.info("APPLICATIONINSIGHTS_CONNECTION_STRING not set — telemetry disabled")

    app.add_middleware(AppInsightsMiddleware)
    logger.info("App Insights request middleware registered")
