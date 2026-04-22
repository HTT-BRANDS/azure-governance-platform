"""Tests for sync alerts and alert resolution endpoints.

Split off from the former monolithic `tests/integration/test_sync_api.py`
(issue 6oj7, 2026-04-22). Shared fixtures live in `./conftest.py`.
"""

from datetime import datetime, timedelta

from app.core.database import get_db
from app.main import app
from app.models.monitoring import Alert

# ============================================================================


class TestSyncAlertsEndpoint:
    """Integration tests for GET /api/v1/sync/alerts."""

    def test_get_alerts_success(self, sync_client):
        """Sync alerts returns list of active alerts."""
        # Add an alert to the database
        db = next(app.dependency_overrides[get_db]())

        alert = Alert(
            alert_type="high_failure_rate",
            severity="warning",
            job_type="costs_sync",
            tenant_id="test-tenant-123",
            title="High Failure Rate",
            message="Sync job failure rate exceeded threshold",
            is_resolved=False,
            created_at=datetime.utcnow() - timedelta(hours=2),
        )
        db.add(alert)
        db.commit()

        response = sync_client.get("/api/v1/sync/alerts")

        assert response.status_code == 200
        data = response.json()

        # Validate structure
        assert "alerts" in data
        assert "stats" in data
        assert isinstance(data["alerts"], list)

        # Validate alert structure if we have data
        if len(data["alerts"]) > 0:
            alert_entry = data["alerts"][0]
            assert "id" in alert_entry
            assert "alert_type" in alert_entry
            assert "severity" in alert_entry
            assert "job_type" in alert_entry
            assert "tenant_id" in alert_entry
            assert "title" in alert_entry
            assert "message" in alert_entry
            assert "is_resolved" in alert_entry
            assert "created_at" in alert_entry
            assert "resolved_at" in alert_entry
            assert "resolved_by" in alert_entry

            # Validate types
            assert isinstance(alert_entry["severity"], str)
            assert alert_entry["severity"] in ["info", "warning", "error", "critical"]
            assert isinstance(alert_entry["is_resolved"], bool)

    def test_get_alerts_job_type_filter(self, sync_client):
        """Sync alerts can be filtered by job_type."""
        # Add alerts for different job types
        db = next(app.dependency_overrides[get_db]())

        alert1 = Alert(
            alert_type="high_failure_rate",
            severity="warning",
            job_type="costs_sync",
            tenant_id="test-tenant-123",
            title="Costs Alert",
            message="Test alert",
            is_resolved=False,
            created_at=datetime.utcnow(),
        )
        alert2 = Alert(
            alert_type="long_duration",
            severity="info",
            job_type="compliance_sync",
            tenant_id="test-tenant-123",
            title="Compliance Alert",
            message="Test alert",
            is_resolved=False,
            created_at=datetime.utcnow(),
        )
        db.add_all([alert1, alert2])
        db.commit()

        response = sync_client.get("/api/v1/sync/alerts?job_type=costs_sync")

        assert response.status_code == 200
        data = response.json()

        # All alerts should match the filter
        for alert in data["alerts"]:
            assert alert["job_type"] == "costs_sync"

    def test_get_alerts_severity_filter(self, sync_client):
        """Sync alerts can be filtered by severity."""
        # Add alerts with different severities
        db = next(app.dependency_overrides[get_db]())

        alert1 = Alert(
            alert_type="high_failure_rate",
            severity="critical",
            job_type="costs_sync",
            tenant_id="test-tenant-123",
            title="Critical Alert",
            message="Test alert",
            is_resolved=False,
            created_at=datetime.utcnow(),
        )
        alert2 = Alert(
            alert_type="long_duration",
            severity="warning",
            job_type="costs_sync",
            tenant_id="test-tenant-123",
            title="Warning Alert",
            message="Test alert",
            is_resolved=False,
            created_at=datetime.utcnow(),
        )
        db.add_all([alert1, alert2])
        db.commit()

        response = sync_client.get("/api/v1/sync/alerts?severity=critical")

        assert response.status_code == 200
        data = response.json()

        # All alerts should match the filter
        for alert in data["alerts"]:
            assert alert["severity"] == "critical"

    def test_get_alerts_severity_validation(self, sync_client):
        """Sync alerts validates severity parameter."""
        # Invalid severity
        response = sync_client.get("/api/v1/sync/alerts?severity=invalid")
        assert response.status_code == 422  # Validation error

    def test_get_alerts_include_resolved(self, sync_client):
        """Sync alerts can include resolved alerts."""
        # Add both resolved and unresolved alerts
        db = next(app.dependency_overrides[get_db]())

        alert1 = Alert(
            alert_type="high_failure_rate",
            severity="warning",
            job_type="costs_sync",
            tenant_id="test-tenant-123",
            title="Active Alert",
            message="Test alert",
            is_resolved=False,
            created_at=datetime.utcnow(),
        )
        alert2 = Alert(
            alert_type="long_duration",
            severity="info",
            job_type="costs_sync",
            tenant_id="test-tenant-123",
            title="Resolved Alert",
            message="Test alert",
            is_resolved=True,
            created_at=datetime.utcnow() - timedelta(hours=5),
            resolved_at=datetime.utcnow() - timedelta(hours=1),
            resolved_by="user-123",
        )
        db.add_all([alert1, alert2])
        db.commit()

        # Get only active alerts (default)
        response_active = sync_client.get("/api/v1/sync/alerts")
        assert response_active.status_code == 200
        data_active = response_active.json()

        # Get all alerts including resolved
        response_all = sync_client.get("/api/v1/sync/alerts?include_resolved=true")
        assert response_all.status_code == 200
        data_all = response_all.json()

        # All alerts response should have more or equal alerts
        assert len(data_all["alerts"]) >= len(data_active["alerts"])

    def test_get_alerts_tenant_isolation(self, sync_client, test_tenant_id):
        """Sync alerts only returns alerts for accessible tenants."""
        # Add alerts for different tenants
        db = next(app.dependency_overrides[get_db]())

        alert1 = Alert(
            alert_type="high_failure_rate",
            severity="warning",
            job_type="costs_sync",
            tenant_id=test_tenant_id,
            title="Accessible Alert",
            message="Test alert",
            is_resolved=False,
            created_at=datetime.utcnow(),
        )
        alert2 = Alert(
            alert_type="long_duration",
            severity="info",
            job_type="costs_sync",
            tenant_id="other-tenant-999",
            title="Inaccessible Alert",
            message="Test alert",
            is_resolved=False,
            created_at=datetime.utcnow(),
        )
        db.add_all([alert1, alert2])
        db.commit()

        response = sync_client.get("/api/v1/sync/alerts")

        assert response.status_code == 200
        data = response.json()

        # Should only return alerts for accessible tenants
        for alert in data["alerts"]:
            if alert["tenant_id"]:  # Some alerts might not have tenant_id
                assert alert["tenant_id"] in [test_tenant_id, "test-tenant-456"]

    def test_get_alerts_requires_auth(self, sync_unauth_client):
        """Sync alerts endpoint requires authentication."""
        response = sync_unauth_client.get("/api/v1/sync/alerts")
        assert response.status_code == 401


# ============================================================================
# POST /api/v1/sync/alerts/{alert_id}/resolve Tests
# ============================================================================


class TestResolveAlertEndpoint:
    """Integration tests for POST /api/v1/sync/alerts/{alert_id}/resolve."""

    def test_resolve_alert_success(self, sync_client):
        """Resolve alert successfully updates alert status."""
        # Add an unresolved alert
        db = next(app.dependency_overrides[get_db]())

        alert = Alert(
            alert_type="high_failure_rate",
            severity="warning",
            job_type="costs_sync",
            tenant_id="test-tenant-123",
            title="Test Alert",
            message="Test alert message",
            is_resolved=False,
            created_at=datetime.utcnow(),
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        alert_id = alert.id

        response = sync_client.post(f"/api/v1/sync/alerts/{alert_id}/resolve?resolved_by=test-user")

        assert response.status_code == 200
        data = response.json()

        # Validate response
        assert "id" in data
        assert "alert_type" in data
        assert "is_resolved" in data
        assert "resolved_at" in data
        assert "resolved_by" in data

        assert data["id"] == alert_id
        assert data["is_resolved"] is True
        assert data["resolved_by"] == "test-user"
        assert data["resolved_at"] is not None

        # Verify alert is marked resolved in database
        db.refresh(alert)
        assert alert.is_resolved == 1  # SQLite stores as integer
        assert alert.resolved_by == "test-user"
        assert alert.resolved_at is not None

    def test_resolve_alert_not_found(self, sync_client):
        """Resolve alert returns 404 for non-existent alert."""
        response = sync_client.post("/api/v1/sync/alerts/99999/resolve")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_resolve_alert_invalid_id(self, sync_client):
        """Resolve alert validates alert_id parameter."""
        # Test invalid ID (negative)
        response = sync_client.post("/api/v1/sync/alerts/-1/resolve")
        assert response.status_code == 422  # Validation error

        # Test invalid ID (zero)
        response = sync_client.post("/api/v1/sync/alerts/0/resolve")
        assert response.status_code == 422

    def test_resolve_alert_validates_resolved_by(self, sync_client):
        """Resolve alert validates resolved_by parameter."""
        # Add an unresolved alert
        db = next(app.dependency_overrides[get_db]())

        alert = Alert(
            alert_type="high_failure_rate",
            severity="warning",
            job_type="costs_sync",
            tenant_id="test-tenant-123",
            title="Test Alert",
            message="Test alert message",
            is_resolved=False,
            created_at=datetime.utcnow(),
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        alert_id = alert.id

        # Test resolved_by too long (> 100 chars)
        long_string = "x" * 101
        response = sync_client.post(
            f"/api/v1/sync/alerts/{alert_id}/resolve?resolved_by={long_string}"
        )
        assert response.status_code == 422  # Validation error

    def test_resolve_alert_requires_auth(self, sync_unauth_client):
        """Resolve alert endpoint requires authentication."""
        response = sync_unauth_client.post("/api/v1/sync/alerts/1/resolve")
        assert response.status_code == 401


# ============================================================================
# Tenant Isolation Tests
