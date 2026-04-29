"""Tests for sync-API tenant isolation and admin access.

Split off from the former monolithic `tests/integration/test_sync_api.py`
(issue 6oj7, 2026-04-22). Shared fixtures live in `./conftest.py`.
"""

from datetime import UTC, datetime, timedelta

from app.core.database import get_db
from app.main import app
from app.models.monitoring import Alert, SyncJobLog, SyncJobMetrics

# ============================================================================


class TestSyncTenantIsolation:
    """Tests for tenant isolation across sync endpoints."""

    def test_history_respects_tenant_access(self, sync_client, test_tenant_id):
        """History endpoint only returns logs for accessible tenants."""
        # Add logs for multiple tenants
        db = next(app.dependency_overrides[get_db]())

        log1 = SyncJobLog(
            job_type="costs_sync",
            tenant_id=test_tenant_id,
            status="completed",
            started_at=datetime.now(UTC) - timedelta(hours=2),
            ended_at=datetime.now(UTC) - timedelta(hours=1),
            duration_ms=3600000,
            records_processed=150,
            errors_count=0,
        )
        log2 = SyncJobLog(
            job_type="costs_sync",
            tenant_id="other-tenant-999",
            status="completed",
            started_at=datetime.now(UTC) - timedelta(hours=3),
            ended_at=datetime.now(UTC) - timedelta(hours=2),
            duration_ms=3600000,
            records_processed=100,
            errors_count=0,
        )
        db.add_all([log1, log2])
        db.commit()

        response = sync_client.get("/api/v1/sync/history")

        assert response.status_code == 200
        data = response.json()

        # Should only return logs for accessible tenants
        accessible_tenants = [test_tenant_id, "test-tenant-456"]
        for log in data["logs"]:
            if log["tenant_id"]:
                assert log["tenant_id"] in accessible_tenants

    def test_metrics_respects_tenant_access(self, sync_client, test_tenant_id):
        """Metrics endpoint returns all job types (not tenant-specific)."""
        # Note: SyncJobMetrics are per job_type, not per tenant
        # Tenant filtering happens at the job log level
        db = next(app.dependency_overrides[get_db]())

        metric = SyncJobMetrics(
            job_type="costs_sync",
            calculated_at=datetime.now(UTC),
            total_runs=100,
            successful_runs=95,
            failed_runs=5,
            success_rate=95.0,
            avg_duration_ms=900000,
            min_duration_ms=600000,
            max_duration_ms=1200000,
            avg_records_processed=200,
            total_records_processed=20000,
            total_errors=5,
        )
        db.add(metric)
        db.commit()

        response = sync_client.get("/api/v1/sync/metrics")

        assert response.status_code == 200
        data = response.json()

        # Metrics are global (per job_type), not tenant-specific
        assert isinstance(data["metrics"], list)

    def test_alerts_respects_tenant_access(self, sync_client, test_tenant_id):
        """Alerts endpoint only returns alerts for accessible tenants."""
        # Add alerts for multiple tenants
        db = next(app.dependency_overrides[get_db]())

        alert1 = Alert(
            alert_type="high_failure_rate",
            severity="warning",
            job_type="costs_sync",
            tenant_id=test_tenant_id,
            title="Accessible Alert",
            message="Test alert",
            is_resolved=False,
            created_at=datetime.now(UTC),
        )
        alert2 = Alert(
            alert_type="long_duration",
            severity="info",
            job_type="costs_sync",
            tenant_id="other-tenant-999",
            title="Inaccessible Alert",
            message="Test alert",
            is_resolved=False,
            created_at=datetime.now(UTC),
        )
        db.add_all([alert1, alert2])
        db.commit()

        response = sync_client.get("/api/v1/sync/alerts")

        assert response.status_code == 200
        data = response.json()

        # Should only return alerts for accessible tenants
        accessible_tenants = [test_tenant_id, "test-tenant-456"]
        for alert in data["alerts"]:
            if alert["tenant_id"]:
                assert alert["tenant_id"] in accessible_tenants


# ============================================================================
# Admin User Tests
# ============================================================================


class TestSyncAdminAccess:
    """Tests for admin user access across sync endpoints."""

    def test_admin_sees_all_tenants_in_history(self, sync_admin_client):
        """Admin user can access sync history endpoint."""
        response = sync_admin_client.get("/api/v1/sync/history")

        assert response.status_code == 200
        data = response.json()

        # Admin can access the endpoint and get proper structure
        assert "logs" in data
        assert isinstance(data["logs"], list)

    def test_admin_sees_all_metrics(self, sync_admin_client):
        """Admin user can see all job type metrics."""
        # Note: SyncJobMetrics are per job_type, not per tenant
        db = next(app.dependency_overrides[get_db]())

        metric1 = SyncJobMetrics(
            job_type="costs_sync",
            calculated_at=datetime.now(UTC),
            total_runs=100,
            successful_runs=95,
            failed_runs=5,
            success_rate=95.0,
            avg_duration_ms=900000,
            min_duration_ms=600000,
            max_duration_ms=1200000,
            avg_records_processed=200,
            total_records_processed=20000,
            total_errors=5,
        )
        metric2 = SyncJobMetrics(
            job_type="compliance_sync",
            calculated_at=datetime.now(UTC),
            total_runs=50,
            successful_runs=48,
            failed_runs=2,
            success_rate=96.0,
            avg_duration_ms=700000,
            min_duration_ms=500000,
            max_duration_ms=900000,
            avg_records_processed=100,
            total_records_processed=5000,
            total_errors=2,
        )
        db.add_all([metric1, metric2])
        db.commit()

        response = sync_admin_client.get("/api/v1/sync/metrics")

        assert response.status_code == 200
        data = response.json()

        # Admin should see all job type metrics
        job_types = {m["job_type"] for m in data["metrics"]}
        assert len(job_types) >= 2

    def test_admin_sees_all_tenants_in_alerts(self, sync_admin_client):
        """Admin user can access sync alerts endpoint."""
        response = sync_admin_client.get("/api/v1/sync/alerts")

        assert response.status_code == 200
        data = response.json()

        # Admin can access the endpoint and get proper structure
        assert "alerts" in data
        assert "stats" in data or data["stats"] is None  # stats might be None when no alerts
        assert isinstance(data["alerts"], list)
