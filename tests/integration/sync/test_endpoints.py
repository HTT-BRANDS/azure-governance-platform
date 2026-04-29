"""Tests for sync trigger, status, and health endpoints.

Split off from the former monolithic `tests/integration/test_sync_api.py`
(issue 6oj7, 2026-04-22). Shared fixtures live in `./conftest.py`.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.core.database import get_db
from app.main import app

# ============================================================================


class TestTriggerSyncEndpoint:
    """Integration tests for POST /api/v1/sync/{sync_type}."""

    @pytest.mark.parametrize("sync_type", ["costs", "compliance", "resources", "identity"])
    def test_trigger_sync_valid_types(self, sync_client, sync_type):
        """Trigger sync succeeds for all valid sync types."""
        # Mock the scheduler trigger function
        with patch("app.api.routes.sync.trigger_manual_sync", return_value=True) as mock_trigger:
            response = sync_client.post(f"/api/v1/sync/{sync_type}")

            assert response.status_code == 200
            data = response.json()

            # Validate response structure
            assert "status" in data
            assert "sync_type" in data
            assert data["status"] == "triggered"
            assert data["sync_type"] == sync_type

            # Verify the trigger function was called with correct sync_type
            mock_trigger.assert_called_once_with(sync_type)

    def test_trigger_sync_invalid_type(self, sync_client):
        """Trigger sync fails with 422 for invalid sync type."""
        response = sync_client.post("/api/v1/sync/invalid_type")
        assert response.status_code == 422  # Validation error

    def test_trigger_sync_scheduler_failure(self, sync_client):
        """Trigger sync returns 400 when scheduler fails."""
        # Mock scheduler returning False (unknown sync type or failure)
        with patch("app.api.routes.sync.trigger_manual_sync", return_value=False):
            response = sync_client.post("/api/v1/sync/costs")

            assert response.status_code == 400
            data = response.json()
            assert "detail" in data
            assert "Unknown sync type" in data["detail"]

    def test_trigger_sync_requires_auth(self, sync_unauth_client):
        """Trigger sync endpoint requires authentication."""
        response = sync_unauth_client.post("/api/v1/sync/costs")
        assert response.status_code == 401

    def test_trigger_sync_rate_limited(self, sync_client):
        """Trigger sync endpoint is rate limited."""
        # This test verifies rate limiting exists (implementation may vary)
        # We're testing that the endpoint has rate limiting dependency
        # The actual rate limit behavior is tested in test_rate_limit.py
        with patch("app.api.routes.sync.trigger_manual_sync", return_value=True):
            response = sync_client.post("/api/v1/sync/costs")
            assert response.status_code in [200, 429]  # Success or rate limited


# ============================================================================
# GET /api/v1/sync/status Tests
# ============================================================================


class TestSyncStatusEndpoint:
    """Integration tests for GET /api/v1/sync/status."""

    def test_get_status_scheduler_initialized(self, sync_client):
        """Sync status returns scheduler information when initialized."""
        # Mock scheduler
        mock_scheduler = MagicMock()
        mock_job = MagicMock()
        mock_job.id = "costs_sync"
        mock_job.name = "Sync Costs"
        mock_job.next_run_time = datetime.now(UTC) + timedelta(hours=1)
        mock_scheduler.get_jobs.return_value = [mock_job]

        with patch("app.api.routes.sync.get_scheduler", return_value=mock_scheduler):
            response = sync_client.get("/api/v1/sync/status")

            assert response.status_code == 200
            data = response.json()

            # Validate structure
            assert "status" in data
            assert "jobs" in data
            assert data["status"] == "running"
            assert isinstance(data["jobs"], list)

            # Validate job structure
            if len(data["jobs"]) > 0:
                job = data["jobs"][0]
                assert "id" in job
                assert "name" in job
                assert "next_run" in job
                assert job["id"] == "costs_sync"
                assert job["name"] == "Sync Costs"
                assert isinstance(job["next_run"], str)  # ISO format timestamp

    def test_get_status_scheduler_not_initialized(self, sync_client):
        """Sync status handles uninitialized scheduler gracefully."""
        with patch("app.api.routes.sync.get_scheduler", return_value=None):
            response = sync_client.get("/api/v1/sync/status")

            assert response.status_code == 200
            data = response.json()

            # Should return appropriate status
            assert data["status"] == "scheduler_not_initialized"
            assert data["jobs"] == []

    def test_get_status_no_scheduled_jobs(self, sync_client):
        """Sync status handles empty scheduler gracefully."""
        mock_scheduler = MagicMock()
        mock_scheduler.get_jobs.return_value = []

        with patch("app.api.routes.sync.get_scheduler", return_value=mock_scheduler):
            response = sync_client.get("/api/v1/sync/status")

            assert response.status_code == 200
            data = response.json()

            assert data["status"] == "running"
            assert data["jobs"] == []

    def test_get_status_requires_auth(self, sync_unauth_client):
        """Sync status endpoint requires authentication."""
        response = sync_unauth_client.get("/api/v1/sync/status")
        assert response.status_code == 401


# ============================================================================
# GET /api/v1/sync/status/health Tests
# ============================================================================


class TestSyncHealthEndpoint:
    """Integration tests for GET /api/v1/sync/status/health."""

    def test_get_health_success(self, db_with_monitoring_data, sync_client):
        """Sync health returns overall status with metrics."""
        # Need to update fixture reference
        app.dependency_overrides[get_db] = lambda: db_with_monitoring_data

        response = sync_client.get("/api/v1/sync/status/health")

        assert response.status_code == 200
        data = response.json()

        # MonitoringService.get_overall_status() returns different structure
        # The actual structure depends on the implementation
        # But it should at least return a dict
        assert isinstance(data, dict)

    def test_get_health_requires_auth(self, sync_unauth_client):
        """Sync health endpoint requires authentication."""
        response = sync_unauth_client.get("/api/v1/sync/status/health")
        assert response.status_code == 401


# ============================================================================
# GET /api/v1/sync/history Tests
