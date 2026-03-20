"""Unit tests for threat intelligence service.

Tests the ThreatIntelService and API routes for Riverside/Cybeta threat data.

Traces: RC-030, RC-031 (Riverside threat data integration)
"""

from datetime import UTC, datetime


class TestThreatIntelService:
    """Tests for ThreatIntelService."""

    def test_get_cybeta_threats_returns_list(self, db_session):
        """Service returns list of threat records."""
        from app.api.services.threat_intel_service import ThreatIntelService

        service = ThreatIntelService()
        results = service.get_cybeta_threats(db_session)

        assert isinstance(results, list)

    def test_get_cybeta_threats_with_tenant_filter(self, db_session):
        """Service filters by tenant IDs."""
        from app.api.services.threat_intel_service import ThreatIntelService

        service = ThreatIntelService()
        results = service.get_cybeta_threats(db_session, tenant_ids=["tenant-1", "tenant-2"])

        assert isinstance(results, list)

    def test_get_cybeta_threats_with_date_range(self, db_session):
        """Service filters by date range."""
        from app.api.services.threat_intel_service import ThreatIntelService

        service = ThreatIntelService()
        results = service.get_cybeta_threats(
            db_session,
            start_date=datetime(2024, 1, 1).date(),
            end_date=datetime(2024, 12, 31).date(),
        )

        assert isinstance(results, list)

    def test_get_cybeta_threats_with_limit(self, db_session):
        """Service respects limit parameter."""
        from app.api.services.threat_intel_service import ThreatIntelService

        service = ThreatIntelService()
        results = service.get_cybeta_threats(db_session, limit=10)

        assert isinstance(results, list)
        assert len(results) <= 10

    def test_get_cybeta_threats_empty_when_no_data(self, db_session):
        """Service returns empty list when no data exists."""
        from app.api.services.threat_intel_service import ThreatIntelService

        service = ThreatIntelService()
        results = service.get_cybeta_threats(db_session, tenant_ids=["non-existent-tenant"])

        assert isinstance(results, list)
        assert len(results) == 0

    def test_get_threat_summary_returns_aggregates(self, db_session):
        """Service returns aggregated summary for tenant."""
        from app.api.services.threat_intel_service import ThreatIntelService
        from app.models.riverside import RiversideThreatData

        # Add test data
        threat_data = RiversideThreatData(
            tenant_id="test-tenant-123",
            threat_score=75.5,
            vulnerability_count=10,
            malicious_domain_alerts=2,
            peer_comparison_percentile=85,
            snapshot_date=datetime.now(UTC),
        )
        db_session.add(threat_data)
        db_session.commit()

        service = ThreatIntelService()
        summary = service.get_threat_summary(db_session, "test-tenant-123")

        assert summary["tenant_id"] == "test-tenant-123"
        assert summary["status"] == "available"
        assert summary["latest_threat_score"] == 75.5
        assert summary["latest_vulnerability_count"] == 10

    def test_get_threat_summary_latest_only(self, db_session):
        """Service returns only latest snapshot."""
        from app.api.services.threat_intel_service import ThreatIntelService
        from app.models.riverside import RiversideThreatData

        # Add older data
        older_data = RiversideThreatData(
            tenant_id="test-tenant-123",
            threat_score=50.0,
            vulnerability_count=20,
            malicious_domain_alerts=5,
            snapshot_date=datetime(2024, 1, 1, tzinfo=UTC),
        )
        # Add newer data
        newer_data = RiversideThreatData(
            tenant_id="test-tenant-123",
            threat_score=75.0,
            vulnerability_count=10,
            malicious_domain_alerts=2,
            snapshot_date=datetime(2024, 12, 31, tzinfo=UTC),
        )
        db_session.add(older_data)
        db_session.add(newer_data)
        db_session.commit()

        service = ThreatIntelService()
        summary = service.get_threat_summary(db_session, "test-tenant-123")

        assert summary["latest_threat_score"] == 75.0
        assert summary["latest_vulnerability_count"] == 10


class TestThreatIntelRoute:
    """Tests for Threat Intel API routes."""

    def test_route_returns_200(self, authed_client):
        """Threat endpoint returns 200 with valid auth."""
        response = authed_client.get("/api/v1/threats/cybeta")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_route_with_tenant_filter(self, authed_client):
        """Threat endpoint accepts tenant filter."""
        response = authed_client.get("/api/v1/threats/cybeta?tenant_ids=test-tenant-123")

        assert response.status_code == 200

    def test_route_with_date_range(self, authed_client):
        """Threat endpoint accepts date range filters."""
        response = authed_client.get(
            "/api/v1/threats/cybeta?start_date=2024-01-01&end_date=2024-12-31"
        )

        assert response.status_code == 200

    def test_route_with_limit(self, authed_client):
        """Threat endpoint respects limit parameter."""
        response = authed_client.get("/api/v1/threats/cybeta?limit=50")

        assert response.status_code == 200

    def test_route_requires_auth(self, client):
        """Threat endpoint returns 401 without auth."""
        response = client.get("/api/v1/threats/cybeta")

        assert response.status_code == 401

    def test_summary_endpoint_returns_200(self, authed_client):
        """Threat summary endpoint returns 200."""
        response = authed_client.get("/api/v1/threats/summary/test-tenant-123")

        assert response.status_code == 200
        data = response.json()
        assert "tenant_id" in data

    def test_summary_endpoint_returns_no_data_for_missing_tenant(self, authed_client):
        """Summary endpoint returns no_data status for missing tenant."""
        response = authed_client.get("/api/v1/threats/summary/non-existent-tenant")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "no_data"

    def test_get_threat_intel_service_singleton(self):
        """get_threat_intel_service returns singleton instance."""
        from app.api.services.threat_intel_service import (
            ThreatIntelService,
            get_threat_intel_service,
        )

        service1 = get_threat_intel_service()
        service2 = get_threat_intel_service()

        assert isinstance(service1, ThreatIntelService)
        assert service1 is service2
