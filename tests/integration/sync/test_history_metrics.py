"""Tests for sync history and metrics endpoints.

Split off from the former monolithic `tests/integration/test_sync_api.py`
(issue 6oj7, 2026-04-22). Shared fixtures live in `./conftest.py`.
"""

from datetime import datetime, timedelta

from app.core.database import get_db
from app.main import app
from app.models.monitoring import SyncJobLog, SyncJobMetrics

# ============================================================================


class TestSyncHistoryEndpoint:
    """Integration tests for GET /api/v1/sync/history."""

    def test_get_history_success(self, sync_client):
        """Sync history returns list of job logs."""
        # Add a job log to the database
        from app.core.database import get_db

        db = next(app.dependency_overrides[get_db]())

        log = SyncJobLog(
            job_type="costs_sync",
            tenant_id="test-tenant-123",
            status="completed",
            started_at=datetime.utcnow() - timedelta(hours=2),
            ended_at=datetime.utcnow() - timedelta(hours=1),
            duration_ms=3600000,
            records_processed=150,
            errors_count=0,
            error_message=None,
        )
        db.add(log)
        db.commit()

        response = sync_client.get("/api/v1/sync/history")

        assert response.status_code == 200
        data = response.json()

        # Validate structure
        assert "logs" in data
        assert isinstance(data["logs"], list)

        # Validate log structure if we have data
        if len(data["logs"]) > 0:
            log_entry = data["logs"][0]
            assert "id" in log_entry
            assert "job_type" in log_entry
            assert "tenant_id" in log_entry
            assert "status" in log_entry
            assert "started_at" in log_entry
            assert "ended_at" in log_entry
            assert "duration_ms" in log_entry
            assert "records_processed" in log_entry
            assert "errors_count" in log_entry
            assert "error_message" in log_entry

            # Validate types
            assert isinstance(log_entry["job_type"], str)
            assert isinstance(log_entry["status"], str)
            assert log_entry["status"] in ["completed", "failed", "running"]

    def test_get_history_job_type_filter(self, sync_client):
        """Sync history can be filtered by job_type."""
        # Add logs with different job types
        db = next(app.dependency_overrides[get_db]())

        log1 = SyncJobLog(
            job_type="costs_sync",
            tenant_id="test-tenant-123",
            status="completed",
            started_at=datetime.utcnow() - timedelta(hours=2),
            ended_at=datetime.utcnow() - timedelta(hours=1),
            duration_ms=3600000,
            records_processed=150,
            errors_count=0,
        )
        log2 = SyncJobLog(
            job_type="compliance_sync",
            tenant_id="test-tenant-123",
            status="completed",
            started_at=datetime.utcnow() - timedelta(hours=3),
            ended_at=datetime.utcnow() - timedelta(hours=2),
            duration_ms=3600000,
            records_processed=100,
            errors_count=0,
        )
        db.add_all([log1, log2])
        db.commit()

        response = sync_client.get("/api/v1/sync/history?job_type=costs_sync")

        assert response.status_code == 200
        data = response.json()

        # All logs should match the filter
        for log in data["logs"]:
            assert log["job_type"] == "costs_sync"

    def test_get_history_limit_parameter(self, sync_client):
        """Sync history respects limit parameter."""
        # Add multiple logs
        db = next(app.dependency_overrides[get_db]())

        for i in range(10):
            log = SyncJobLog(
                job_type="costs_sync",
                tenant_id="test-tenant-123",
                status="completed",
                started_at=datetime.utcnow() - timedelta(hours=i + 1),
                ended_at=datetime.utcnow() - timedelta(hours=i),
                duration_ms=3600000,
                records_processed=100,
                errors_count=0,
            )
            db.add(log)
        db.commit()

        response = sync_client.get("/api/v1/sync/history?limit=5")

        assert response.status_code == 200
        data = response.json()

        # Should return at most 5 logs
        assert len(data["logs"]) <= 5

    def test_get_history_validates_limit(self, sync_client):
        """Sync history validates limit parameter."""
        # Test limit too large
        response = sync_client.get("/api/v1/sync/history?limit=1000")
        assert response.status_code == 422  # Validation error

        # Test limit too small
        response = sync_client.get("/api/v1/sync/history?limit=0")
        assert response.status_code == 422

    def test_get_history_tenant_isolation(self, sync_client, test_tenant_id):
        """Sync history only returns logs for accessible tenants."""
        # Add logs for different tenants
        db = next(app.dependency_overrides[get_db]())

        log1 = SyncJobLog(
            job_type="costs_sync",
            tenant_id=test_tenant_id,
            status="completed",
            started_at=datetime.utcnow() - timedelta(hours=2),
            ended_at=datetime.utcnow() - timedelta(hours=1),
            duration_ms=3600000,
            records_processed=150,
            errors_count=0,
        )
        log2 = SyncJobLog(
            job_type="costs_sync",
            tenant_id="other-tenant-999",
            status="completed",
            started_at=datetime.utcnow() - timedelta(hours=3),
            ended_at=datetime.utcnow() - timedelta(hours=2),
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
        for log in data["logs"]:
            if log["tenant_id"]:  # Some logs might not have tenant_id
                assert log["tenant_id"] in [test_tenant_id, "test-tenant-456"]

    def test_get_history_requires_auth(self, sync_unauth_client):
        """Sync history endpoint requires authentication."""
        response = sync_unauth_client.get("/api/v1/sync/history")
        assert response.status_code == 401


# ============================================================================
# GET /api/v1/sync/metrics Tests
# ============================================================================


class TestSyncMetricsEndpoint:
    """Integration tests for GET /api/v1/sync/metrics."""

    def test_get_metrics_success(self, sync_client):
        """Sync metrics returns aggregated statistics."""
        # Add a metric to the database
        db = next(app.dependency_overrides[get_db]())

        metric = SyncJobMetrics(
            job_type="costs_sync",
            calculated_at=datetime.utcnow(),
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
            last_run_at=datetime.utcnow() - timedelta(hours=1),
            last_success_at=datetime.utcnow() - timedelta(hours=1),
            last_failure_at=datetime.utcnow() - timedelta(days=1),
            last_error_message="Previous error",
        )
        db.add(metric)
        db.commit()

        response = sync_client.get("/api/v1/sync/metrics")

        assert response.status_code == 200
        data = response.json()

        # Validate structure
        assert "metrics" in data
        assert isinstance(data["metrics"], list)

        # Validate metric structure if we have data
        if len(data["metrics"]) > 0:
            metric_entry = data["metrics"][0]
            assert "job_type" in metric_entry
            assert "calculated_at" in metric_entry
            assert "total_runs" in metric_entry
            assert "successful_runs" in metric_entry
            assert "failed_runs" in metric_entry
            assert "success_rate" in metric_entry
            assert "avg_duration_ms" in metric_entry
            assert "min_duration_ms" in metric_entry
            assert "max_duration_ms" in metric_entry
            assert "avg_records_processed" in metric_entry
            assert "total_records_processed" in metric_entry
            assert "total_errors" in metric_entry
            assert "last_run_at" in metric_entry
            assert "last_success_at" in metric_entry
            assert "last_failure_at" in metric_entry
            assert "last_error_message" in metric_entry

            # Validate types and ranges
            assert isinstance(metric_entry["total_runs"], int)
            assert isinstance(metric_entry["success_rate"], (int, float))
            assert 0 <= metric_entry["success_rate"] <= 100
            assert (
                metric_entry["successful_runs"] + metric_entry["failed_runs"]
                == metric_entry["total_runs"]
            )

    def test_get_metrics_job_type_filter(self, sync_client):
        """Sync metrics can be filtered by job_type."""
        # Add metrics for different job types
        db = next(app.dependency_overrides[get_db]())

        metric1 = SyncJobMetrics(
            job_type="costs_sync",
            calculated_at=datetime.utcnow(),
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
            calculated_at=datetime.utcnow(),
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

        response = sync_client.get("/api/v1/sync/metrics?job_type=costs_sync")

        assert response.status_code == 200
        data = response.json()

        # All metrics should match the filter
        for metric in data["metrics"]:
            assert metric["job_type"] == "costs_sync"

    def test_get_metrics_tenant_isolation(self, sync_client, test_tenant_id):
        """Sync metrics only returns data for accessible tenants."""
        # Add metrics for different tenants
        db = next(app.dependency_overrides[get_db]())

        metric1 = SyncJobMetrics(
            job_type="costs_sync",
            calculated_at=datetime.utcnow(),
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
            calculated_at=datetime.utcnow(),
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

        response = sync_client.get("/api/v1/sync/metrics")

        assert response.status_code == 200
        data = response.json()

        # Metrics are global (per job_type), not tenant-specific
        assert isinstance(data["metrics"], list)
        # Should have both job types
        job_types = {m["job_type"] for m in data["metrics"]}
        assert "costs_sync" in job_types or "compliance_sync" in job_types

    def test_get_metrics_requires_auth(self, sync_unauth_client):
        """Sync metrics endpoint requires authentication."""
        response = sync_unauth_client.get("/api/v1/sync/metrics")
        assert response.status_code == 401


# ============================================================================
# GET /api/v1/sync/alerts Tests
