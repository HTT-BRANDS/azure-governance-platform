"""Unit tests for Sui Generis device compliance service.

Tests the placeholder service and API routes for Sui Generis device compliance.

Traces: RC-030, RC-031 (Phase 2 - Sui Generis integration)
"""


class TestSuiGenerisService:
    """Tests for SuiGenerisService."""

    def test_status_returns_coming_soon(self):
        """Service status should return coming_soon status."""
        from app.api.services.sui_generis_service import SuiGenerisService

        service = SuiGenerisService()
        status = service.get_status()

        assert status["status"] == "coming_soon"
        assert "message" in status
        assert "estimated_availability" in status
        assert status["estimated_availability"] == "Q2 2026"

    def test_get_device_compliance_returns_placeholder(self):
        """Device compliance endpoint returns placeholder response."""
        from app.api.services.sui_generis_service import SuiGenerisService

        service = SuiGenerisService()
        result = service.get_device_compliance("test-tenant-123")

        assert result["status"] == "coming_soon"
        assert result["tenant_id"] == "test-tenant-123"
        assert "message" in result

    def test_get_status_includes_features_list(self):
        """Status should include list of planned features."""
        from app.api.services.sui_generis_service import SuiGenerisService

        service = SuiGenerisService()
        status = service.get_status()

        assert "features" in status
        assert isinstance(status["features"], list)
        assert len(status["features"]) > 0
        assert "Device compliance status tracking" in status["features"]
        assert "Risk score aggregation" in status["features"]
        assert "Remediation recommendations" in status["features"]


class TestSuiGenerisRoute:
    """Tests for Sui Generis API routes."""

    def test_route_returns_200_with_status(self, authed_client):
        """Device compliance endpoint returns 200 with status."""
        response = authed_client.get("/api/v1/compliance/device-compliance")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "coming_soon"

    def test_route_requires_auth(self, client):
        """Device compliance endpoint returns 401 without auth."""
        response = client.get("/api/v1/compliance/device-compliance")

        assert response.status_code == 401

    def test_status_endpoint_returns_200(self, authed_client):
        """Device compliance status endpoint returns 200."""
        response = authed_client.get("/api/v1/compliance/device-compliance/status")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "coming_soon"
        assert "features" in data

    def test_get_sui_generis_service_singleton(self):
        """get_sui_generis_service returns singleton instance."""
        from app.api.services.sui_generis_service import (
            SuiGenerisService,
            get_sui_generis_service,
        )

        service1 = get_sui_generis_service()
        service2 = get_sui_generis_service()

        assert isinstance(service1, SuiGenerisService)
        assert service1 is service2
