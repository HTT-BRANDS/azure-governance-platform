"""Telemetry event tracking helpers for sync, auth, business, and dependency operations.

Extracted from app_insights.py to keep modules under 600 lines.
All functions use the global ``telemetry_client`` singleton from
:mod:`app.core.app_insights`.
"""

import time
import uuid
from collections.abc import Callable
from contextlib import contextmanager
from typing import Any

from app.core.app_insights import TelemetryEvent, TelemetryEventType, telemetry_client

# =============================================================================
# Sync Operation Telemetry
# =============================================================================


@contextmanager
def track_sync_operation(
    sync_type: str,
    tenant_id: str | None = None,
    is_full_sync: bool = False,
) -> Callable[[], None]:
    """Context manager to track sync operation telemetry.

    Usage:
        with track_sync_operation("costs", tenant_id="abc123") as complete:
            # Perform sync
            result = sync_costs()
            complete(records_synced=result.count)
    """
    start_time = time.time()
    operation_id = str(uuid.uuid4())[:8]

    # Track start
    start_event = TelemetryEvent(
        event_type=TelemetryEventType.SYNC_STARTED,
        operation_id=operation_id,
        tenant_id=tenant_id,
        properties={
            "sync_type": sync_type,
            "is_full_sync": is_full_sync,
        },
    )
    telemetry_client.track_event(start_event)

    records_synced = 0
    success = False
    error_message = None

    def complete(**kwargs) -> None:
        nonlocal records_synced, success
        records_synced = kwargs.get("records_synced", 0)
        success = kwargs.get("success", True)

    try:
        yield complete
    except Exception as e:
        success = False
        error_message = str(e)
        raise
    finally:
        duration_ms = (time.time() - start_time) * 1000

        # Track completion or failure
        if success:
            complete_event = TelemetryEvent(
                event_type=TelemetryEventType.SYNC_COMPLETED,
                operation_id=operation_id,
                tenant_id=tenant_id,
                duration_ms=duration_ms,
                success=True,
                properties={
                    "sync_type": sync_type,
                    "is_full_sync": is_full_sync,
                    "records_synced": records_synced,
                },
                metrics={
                    "duration_ms": duration_ms,
                    "records_synced": float(records_synced),
                    "records_per_second": records_synced / (duration_ms / 1000)
                    if duration_ms > 0
                    else 0,
                },
            )
            telemetry_client.track_event(complete_event)
        else:
            fail_event = TelemetryEvent(
                event_type=TelemetryEventType.SYNC_FAILED,
                operation_id=operation_id,
                tenant_id=tenant_id,
                duration_ms=duration_ms,
                success=False,
                properties={
                    "sync_type": sync_type,
                    "is_full_sync": is_full_sync,
                    "error": error_message,
                },
                metrics={
                    "duration_ms": duration_ms,
                },
            )
            telemetry_client.track_event(fail_event)


def track_sync_completed(
    sync_type: str,
    tenant_id: str,
    records_synced: int,
    duration_seconds: float,
    is_full_sync: bool = False,
) -> None:
    """Track a completed sync operation."""
    event = TelemetryEvent(
        event_type=TelemetryEventType.SYNC_COMPLETED,
        tenant_id=tenant_id,
        duration_ms=duration_seconds * 1000,
        success=True,
        properties={
            "sync_type": sync_type,
            "is_full_sync": is_full_sync,
            "records_synced": records_synced,
        },
        metrics={
            "duration_ms": duration_seconds * 1000,
            "records_synced": float(records_synced),
            "records_per_second": records_synced / duration_seconds if duration_seconds > 0 else 0,
        },
    )
    telemetry_client.track_event(event)


def track_sync_failed(
    sync_type: str,
    tenant_id: str,
    error: Exception,
    duration_seconds: float,
    is_full_sync: bool = False,
) -> None:
    """Track a failed sync operation."""
    event = TelemetryEvent(
        event_type=TelemetryEventType.SYNC_FAILED,
        tenant_id=tenant_id,
        duration_ms=duration_seconds * 1000,
        success=False,
        properties={
            "sync_type": sync_type,
            "is_full_sync": is_full_sync,
            "error_type": type(error).__name__,
            "error_message": str(error)[:500],  # Truncate long messages
        },
        metrics={
            "duration_ms": duration_seconds * 1000,
        },
    )
    telemetry_client.track_event(event)


# =============================================================================
# Authentication Telemetry
# =============================================================================


def track_auth_login_success(
    user_id: str,
    tenant_id: str,
    auth_method: str = "oauth2",
    mfa_used: bool = False,
) -> None:
    """Track successful authentication."""
    event = TelemetryEvent(
        event_type=TelemetryEventType.AUTH_LOGIN_SUCCESS,
        user_id=user_id,
        tenant_id=tenant_id,
        success=True,
        properties={
            "auth_method": auth_method,
            "mfa_used": mfa_used,
        },
    )
    telemetry_client.track_event(event)


def track_auth_login_failure(
    user_id: str | None,
    tenant_id: str | None,
    auth_method: str,
    failure_reason: str,
    ip_address: str | None = None,
) -> None:
    """Track failed authentication attempt."""
    event = TelemetryEvent(
        event_type=TelemetryEventType.AUTH_LOGIN_FAILURE,
        user_id=user_id,
        tenant_id=tenant_id,
        success=False,
        properties={
            "auth_method": auth_method,
            "failure_reason": failure_reason,
            "ip_address": ip_address,
        },
    )
    telemetry_client.track_event(event)


def track_auth_logout(user_id: str, tenant_id: str) -> None:
    """Track user logout."""
    event = TelemetryEvent(
        event_type=TelemetryEventType.AUTH_LOGOUT,
        user_id=user_id,
        tenant_id=tenant_id,
        success=True,
    )
    telemetry_client.track_event(event)


def track_auth_token_refresh(user_id: str, tenant_id: str, success: bool) -> None:
    """Track token refresh operation."""
    event = TelemetryEvent(
        event_type=TelemetryEventType.AUTH_TOKEN_REFRESH,
        user_id=user_id,
        tenant_id=tenant_id,
        success=success,
    )
    telemetry_client.track_event(event)


# =============================================================================
# Business Metrics Telemetry
# =============================================================================


def track_compliance_violation(
    tenant_id: str,
    framework: str,
    control_id: str,
    severity: str,
    resource_count: int = 1,
) -> None:
    """Track a compliance violation detection."""
    event = TelemetryEvent(
        event_type=TelemetryEventType.COMPLIANCE_VIOLATION,
        tenant_id=tenant_id,
        properties={
            "framework": framework,
            "control_id": control_id,
            "severity": severity,
        },
        metrics={
            "resource_count": float(resource_count),
        },
    )
    telemetry_client.track_event(event)


def track_budget_alert(
    tenant_id: str,
    budget_id: str,
    budget_name: str,
    threshold_percent: float,
    current_spend: float,
    budget_amount: float,
) -> None:
    """Track a budget threshold alert."""
    event = TelemetryEvent(
        event_type=TelemetryEventType.BUDGET_ALERT,
        tenant_id=tenant_id,
        properties={
            "budget_id": budget_id,
            "budget_name": budget_name,
            "threshold_percent": threshold_percent,
        },
        metrics={
            "current_spend": current_spend,
            "budget_amount": budget_amount,
            "remaining_budget": budget_amount - current_spend,
            "consumed_percent": (current_spend / budget_amount * 100) if budget_amount > 0 else 0,
        },
    )
    telemetry_client.track_event(event)


def track_cost_anomaly(
    tenant_id: str,
    service_name: str,
    expected_cost: float,
    actual_cost: float,
    anomaly_score: float,
) -> None:
    """Track a cost anomaly detection."""
    variance = actual_cost - expected_cost
    event = TelemetryEvent(
        event_type=TelemetryEventType.COST_ANOMALY,
        tenant_id=tenant_id,
        properties={
            "service_name": service_name,
            "variance_direction": "increase" if variance > 0 else "decrease",
        },
        metrics={
            "expected_cost": expected_cost,
            "actual_cost": actual_cost,
            "variance": variance,
            "variance_percent": (variance / expected_cost * 100) if expected_cost > 0 else 0,
            "anomaly_score": anomaly_score,
        },
    )
    telemetry_client.track_event(event)


# =============================================================================
# Dependency Tracking
# =============================================================================


def track_dependency(
    name: str,
    data: str,
    duration: float,
    success: bool,
    dependency_type: str | None = None,
    properties: dict[str, Any] | None = None,
) -> None:
    """Track a dependency call (e.g. database query, HTTP call).

    Args:
        name: Name of the dependency (e.g. "slow_query", "blob_storage").
        data: Details about the call (truncated to 100 chars by callers).
        duration: Duration in milliseconds.
        success: Whether the call succeeded.
        dependency_type: Type of dependency (e.g. "SQL", "HTTP", "BLOB").
        properties: Optional additional key/value properties.
    """
    event = TelemetryEvent(
        event_type=TelemetryEventType.DEPENDENCY,
        duration_ms=duration,
        success=success,
        properties={
            "dependency_name": name,
            "dependency_data": data[:100],
            "dependency_type": dependency_type or "unknown",
            **(properties or {}),
        },
        metrics={
            "duration_ms": duration,
        },
    )
    telemetry_client.track_event(event)
