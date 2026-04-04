"""Unit tests for provisioning standards API routes.

Tests all provisioning-standards endpoints with FastAPI TestClient:
- GET  /api/v1/resources/provisioning-standards
- POST /api/v1/resources/provisioning-standards/validate
- GET  /api/v1/resources/provisioning-standards/naming/validate
- GET  /api/v1/resources/provisioning-standards/regions/validate
"""

from unittest.mock import MagicMock

import pytest

from app.api.services.provisioning_standards_service import (
    ProvisioningStandardsService,
    ValidationResult,
    get_provisioning_standards_service,
)

BASE = "/api/v1/resources/provisioning-standards"


@pytest.fixture()
def mock_service(authed_client):
    """Provide a mock ProvisioningStandardsService via dependency override."""
    from app.main import app

    svc = MagicMock(spec=ProvisioningStandardsService)
    app.dependency_overrides[get_provisioning_standards_service] = lambda: svc
    yield svc
    # authed_client teardown clears all overrides


# ============================================================================
# GET /api/v1/resources/provisioning-standards
# ============================================================================


class TestGetProvisioningStandards:
    """Tests for GET /provisioning-standards."""

    def test_returns_standards(self, authed_client, mock_service):
        """GET returns the full standards configuration dict."""
        mock_service.get_standards.return_value = {
            "version": "1.0",
            "naming_conventions": {"max_length": 63},
            "allowed_regions": {"all_allowed": ["eastus", "westus2"]},
        }

        response = authed_client.get(BASE)

        assert response.status_code == 200
        data = response.json()
        assert "standards" in data
        assert data["standards"]["version"] == "1.0"
        assert "naming_conventions" in data["standards"]

    def test_returns_empty_standards(self, authed_client, mock_service):
        """GET returns empty dict when no standards are configured."""
        mock_service.get_standards.return_value = {}

        response = authed_client.get(BASE)

        assert response.status_code == 200
        assert response.json() == {"standards": {}}

    def test_requires_auth(self, client):
        """GET returns 401 without authentication."""
        response = client.get(BASE)
        assert response.status_code == 401


# ============================================================================
# POST /api/v1/resources/provisioning-standards/validate
# ============================================================================


class TestValidateResource:
    """Tests for POST /provisioning-standards/validate."""

    def test_validate_compliant_resource(self, authed_client, mock_service):
        """POST /validate with a compliant resource returns is_compliant=True."""
        mock_service.validate_resource.return_value = ValidationResult(
            resource_id="/subscriptions/sub-1/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm-1",
            resource_name="vm-prod-east-001",
            resource_type="Microsoft.Compute/virtualMachines",
            is_compliant=True,
            violations=[],
            warnings=[],
        )

        payload = {
            "resource_id": "/subscriptions/sub-1/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm-1",
            "resource_name": "vm-prod-east-001",
            "resource_type": "Microsoft.Compute/virtualMachines",
            "region": "eastus",
            "tags": {"environment": "production", "cost-center": "IT"},
            "sku": "Standard_D2s_v3",
        }

        response = authed_client.post(f"{BASE}/validate", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["is_compliant"] is True
        assert data["violations"] == []
        mock_service.validate_resource.assert_called_once()

    def test_validate_non_compliant_resource(self, authed_client, mock_service):
        """POST /validate with violations returns is_compliant=False."""
        mock_service.validate_resource.return_value = ValidationResult(
            resource_id="res-2",
            resource_name="BAD_NAME!",
            resource_type="Microsoft.Compute/virtualMachines",
            is_compliant=False,
            violations=[
                {"rule": "naming_characters", "message": "Invalid characters", "severity": "error"},
            ],
            warnings=[],
        )

        payload = {
            "resource_id": "res-2",
            "resource_name": "BAD_NAME!",
            "resource_type": "Microsoft.Compute/virtualMachines",
        }

        response = authed_client.post(f"{BASE}/validate", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["is_compliant"] is False
        assert len(data["violations"]) == 1
        assert data["violations"][0]["rule"] == "naming_characters"

    def test_validate_missing_required_fields(self, authed_client):
        """POST /validate with empty body returns 422 for missing fields."""
        response = authed_client.post(f"{BASE}/validate", json={})
        assert response.status_code == 422

    def test_validate_requires_auth(self, client):
        """POST /validate returns 401 without authentication."""
        payload = {
            "resource_id": "res-1",
            "resource_name": "test",
            "resource_type": "Microsoft.Compute/virtualMachines",
        }
        response = client.post(f"{BASE}/validate", json=payload)
        assert response.status_code == 401

    def test_validate_response_shape(self, authed_client, mock_service):
        """POST /validate response contains all expected fields."""
        mock_service.validate_resource.return_value = ValidationResult(
            resource_id="res-3",
            resource_name="ok-name",
            resource_type="Microsoft.Storage/storageAccounts",
            is_compliant=True,
            violations=[],
            warnings=[
                {
                    "rule": "missing_recommended_tag",
                    "message": "Missing cost-center",
                    "severity": "warning",
                },
            ],
        )

        payload = {
            "resource_id": "res-3",
            "resource_name": "ok-name",
            "resource_type": "Microsoft.Storage/storageAccounts",
        }

        response = authed_client.post(f"{BASE}/validate", json=payload)
        data = response.json()

        # All fields from ValidationResult must be present
        assert "resource_id" in data
        assert "resource_name" in data
        assert "resource_type" in data
        assert "is_compliant" in data
        assert "violations" in data
        assert "warnings" in data
        assert isinstance(data["warnings"], list)
        assert len(data["warnings"]) == 1

    def test_validate_passes_all_fields_to_service(self, authed_client, mock_service):
        """POST /validate forwards all request fields to the service."""
        mock_service.validate_resource.return_value = ValidationResult(
            resource_id="res-4",
            resource_name="vm-test",
            resource_type="Microsoft.Compute/virtualMachines",
        )

        payload = {
            "resource_id": "res-4",
            "resource_name": "vm-test",
            "resource_type": "Microsoft.Compute/virtualMachines",
            "region": "westus2",
            "tags": {"env": "dev"},
            "sku": "Standard_B2s",
        }

        authed_client.post(f"{BASE}/validate", json=payload)

        mock_service.validate_resource.assert_called_once_with(
            resource_id="res-4",
            resource_name="vm-test",
            resource_type="Microsoft.Compute/virtualMachines",
            region="westus2",
            tags={"env": "dev"},
            sku="Standard_B2s",
        )


# ============================================================================
# GET /api/v1/resources/provisioning-standards/naming/validate
# ============================================================================


class TestValidateNaming:
    """Tests for GET /provisioning-standards/naming/validate."""

    def test_validate_compliant_name(self, authed_client, mock_service):
        """Naming validation returns is_compliant=True for valid names."""
        mock_service.validate_resource_name.return_value = []

        response = authed_client.get(f"{BASE}/naming/validate?name=good-name-123")

        assert response.status_code == 200
        data = response.json()
        assert data["is_compliant"] is True
        assert data["name"] == "good-name-123"
        assert data["violations"] == []

    def test_validate_non_compliant_name(self, authed_client, mock_service):
        """Naming validation returns violations for invalid names."""
        mock_service.validate_resource_name.return_value = [
            {"rule": "naming_characters", "message": "Bad chars", "severity": "error"},
        ]

        response = authed_client.get(f"{BASE}/naming/validate?name=BAD!")

        assert response.status_code == 200
        data = response.json()
        assert data["is_compliant"] is False
        assert len(data["violations"]) == 1

    def test_requires_name_query_param(self, authed_client):
        """Naming validation returns 422 when name param is missing."""
        response = authed_client.get(f"{BASE}/naming/validate")
        assert response.status_code == 422

    def test_naming_requires_auth(self, client):
        """Naming validation returns 401 without authentication."""
        response = client.get(f"{BASE}/naming/validate?name=test")
        assert response.status_code == 401


# ============================================================================
# GET /api/v1/resources/provisioning-standards/regions/validate
# ============================================================================


class TestValidateRegion:
    """Tests for GET /provisioning-standards/regions/validate."""

    def test_validate_allowed_region(self, authed_client, mock_service):
        """Region validation returns is_compliant=True for allowed regions."""
        mock_service.validate_region.return_value = []

        response = authed_client.get(f"{BASE}/regions/validate?region=eastus")

        assert response.status_code == 200
        data = response.json()
        assert data["is_compliant"] is True
        assert data["region"] == "eastus"
        assert data["violations"] == []

    def test_validate_disallowed_region(self, authed_client, mock_service):
        """Region validation returns violations for disallowed regions."""
        mock_service.validate_region.return_value = [
            {"rule": "region_not_allowed", "message": "Not in allowed list", "severity": "error"},
        ]

        response = authed_client.get(f"{BASE}/regions/validate?region=brazilsouth")

        assert response.status_code == 200
        data = response.json()
        assert data["is_compliant"] is False
        assert len(data["violations"]) == 1

    def test_requires_region_query_param(self, authed_client):
        """Region validation returns 422 when region param is missing."""
        response = authed_client.get(f"{BASE}/regions/validate")
        assert response.status_code == 422

    def test_region_requires_auth(self, client):
        """Region validation returns 401 without authentication."""
        response = client.get(f"{BASE}/regions/validate?region=eastus")
        assert response.status_code == 401
