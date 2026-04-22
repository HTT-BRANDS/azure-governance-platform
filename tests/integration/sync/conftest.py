"""Shared fixtures for the Sync API integration test suite.

These fixtures are private to tests/integration/sync/ — they are not in
the global tests/integration/conftest.py because they only make sense for
the sync-API endpoint tests and would pollute the shared namespace.

Split from the former monolithic tests/integration/test_sync_api.py
(issue 6oj7, 2026-04-22). No behavior change — fixtures are byte-identical
to the original versions.
"""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.main import app
from app.models.monitoring import Alert, SyncJobLog, SyncJobMetrics

# ============================================================================
# Fixtures - Custom clients with sync route authentication
# ============================================================================


@pytest.fixture
def sync_client(seeded_db, test_user, mock_authz):
    """Test client with authentication for sync routes."""
    from app.core.auth import get_current_user
    from app.core.authorization import get_tenant_authorization

    def override_get_db():
        try:
            yield seeded_db
        finally:
            pass

    # Use FastAPI's dependency override system
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: test_user
    app.dependency_overrides[get_tenant_authorization] = lambda: mock_authz

    # Clear rate limiter cache and patch to always allow
    from app.core.rate_limit import rate_limiter

    rate_limiter._memory_cache.clear()

    async def mock_check_rate_limit(*args, **kwargs):
        pass  # No-op - always allow

    with patch(
        "app.core.rate_limit.rate_limiter.check_rate_limit", side_effect=mock_check_rate_limit
    ):
        with TestClient(app) as client:
            yield client

    app.dependency_overrides.clear()


@pytest.fixture
def sync_admin_client(seeded_db, admin_user, mock_authz_admin):
    """Test client with admin authentication for sync routes."""
    from app.core.auth import get_current_user
    from app.core.authorization import get_tenant_authorization

    def override_get_db():
        try:
            yield seeded_db
        finally:
            pass

    # Use FastAPI's dependency override system
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[get_tenant_authorization] = lambda: mock_authz_admin

    # Clear rate limiter cache and patch to always allow
    from app.core.rate_limit import rate_limiter

    rate_limiter._memory_cache.clear()

    async def mock_check_rate_limit(*args, **kwargs):
        pass  # No-op - always allow

    with patch(
        "app.core.rate_limit.rate_limiter.check_rate_limit", side_effect=mock_check_rate_limit
    ):
        with TestClient(app) as client:
            yield client

    app.dependency_overrides.clear()


@pytest.fixture
def sync_unauth_client(seeded_db):
    """Test client without authentication for sync routes."""

    def override_get_db():
        try:
            yield seeded_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    # Clear rate limiter cache and patch to always allow
    from app.core.rate_limit import rate_limiter

    rate_limiter._memory_cache.clear()

    async def mock_check_rate_limit(*args, **kwargs):
        pass  # No-op - always allow

    with patch(
        "app.core.rate_limit.rate_limiter.check_rate_limit", side_effect=mock_check_rate_limit
    ):
        with TestClient(app) as client:
            yield client

    app.dependency_overrides.clear()


@pytest.fixture
def db_with_monitoring_data(seeded_db, test_tenant_id, second_tenant_id):
    """Seeded database with monitoring data (job logs, metrics, alerts)."""
    # Add job logs
    job_types = ["costs_sync", "compliance_sync", "resources_sync", "identity_sync"]
    statuses = ["completed", "failed", "running"]

    for i in range(10):
        days_ago = i % 5
        job_type = job_types[i % len(job_types)]
        status = statuses[i % len(statuses)]
        tenant_id = test_tenant_id if i % 2 == 0 else second_tenant_id

        started_at = datetime.utcnow() - timedelta(days=days_ago, hours=i)
        ended_at = started_at + timedelta(minutes=15) if status != "running" else None
        duration_ms = 900000 if status != "running" else None

        log = SyncJobLog(
            job_type=job_type,
            tenant_id=tenant_id,
            status=status,
            started_at=started_at,
            ended_at=ended_at,
            duration_ms=duration_ms,
            records_processed=100 + i * 10 if status == "completed" else 0,
            errors_count=0 if status == "completed" else (i % 3),
            error_message=f"Error {i}" if status == "failed" else None,
        )
        seeded_db.add(log)

    # Add metrics (note: metrics are per job_type only, not per tenant)
    for job_type in job_types:
        metric = SyncJobMetrics(
            job_type=job_type,
            calculated_at=datetime.utcnow(),
            total_runs=50,
            successful_runs=45,
            failed_runs=5,
            success_rate=90.0,
            avg_duration_ms=850000,
            min_duration_ms=500000,
            max_duration_ms=1200000,
            avg_records_processed=150,
            total_records_processed=7500,
            total_errors=10,
            last_run_at=datetime.utcnow() - timedelta(hours=1),
            last_success_at=datetime.utcnow() - timedelta(hours=1),
            last_failure_at=datetime.utcnow() - timedelta(days=1),
            last_error_message="Previous error",
        )
        seeded_db.add(metric)

    # Add alerts
    alert_types = ["high_failure_rate", "long_duration", "no_recent_sync", "sync_error"]
    severities = ["warning", "error", "critical", "info"]

    for i in range(8):
        job_type = job_types[i % len(job_types)]
        alert_type = alert_types[i % len(alert_types)]
        severity = severities[i % len(severities)]
        tenant_id = test_tenant_id if i % 2 == 0 else second_tenant_id
        is_resolved = i < 3  # First 3 are resolved

        alert = Alert(
            alert_type=alert_type,
            severity=severity,
            job_type=job_type,
            tenant_id=tenant_id,
            title=f"Alert {i}: {alert_type}",
            message=f"Test alert message for {job_type}",
            is_resolved=is_resolved,
            created_at=datetime.utcnow() - timedelta(days=i),
            resolved_at=datetime.utcnow() - timedelta(days=i - 1) if is_resolved else None,
            resolved_by="user-123" if is_resolved else None,
        )
        seeded_db.add(alert)

    seeded_db.commit()
    return seeded_db


# ============================================================================
# POST /api/v1/sync/{sync_type} Tests
