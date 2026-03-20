"""Unit tests for provisioning standards service.

Tests the ProvisioningStandardsService for resource validation
against naming conventions, regions, tags, and SKU restrictions.

Traces: RM-008 (Resource provisioning standards)
"""

from app.api.services.provisioning_standards_service import (
    ProvisioningStandardsService,
    ValidationResult,
)


class TestProvisioningStandardsServiceLoad:
    """Tests for loading provisioning standards from YAML."""

    def test_loads_standards_from_yaml(self):
        """Service loads standards from config/provisioning_standards.yaml."""
        service = ProvisioningStandardsService()
        standards = service.get_standards()

        assert isinstance(standards, dict)
        assert "naming_conventions" in standards
        assert "allowed_regions" in standards
        assert "required_tags" in standards
        assert "sku_restrictions" in standards

    def test_standards_version_present(self):
        """Standards config has a version field."""
        service = ProvisioningStandardsService()
        standards = service.get_standards()

        assert standards.get("version") == "1.0"

    def test_missing_config_returns_empty(self, tmp_path):
        """Service returns empty defaults when config file is missing."""
        service = ProvisioningStandardsService(config_path=tmp_path / "nonexistent.yaml")
        standards = service.get_standards()

        assert isinstance(standards, dict)


class TestNamingValidation:
    """Tests for resource name validation."""

    def test_valid_name_passes(self):
        """A compliant name passes validation."""
        service = ProvisioningStandardsService()
        violations = service.validate_resource_name("prod-eastus-app-governance")

        assert violations == []

    def test_name_too_long_fails(self):
        """Name exceeding max length produces a violation."""
        service = ProvisioningStandardsService()
        long_name = "a" * 100
        violations = service.validate_resource_name(long_name)

        assert len(violations) >= 1
        assert any(v["rule"] == "naming_length" for v in violations)

    def test_uppercase_chars_fail(self):
        """Uppercase characters produce a violation."""
        service = ProvisioningStandardsService()
        violations = service.validate_resource_name("Prod-EastUS-App")

        assert len(violations) >= 1
        assert any(v["rule"] == "naming_characters" for v in violations)

    def test_special_chars_fail(self):
        """Special characters produce a violation."""
        service = ProvisioningStandardsService()
        violations = service.validate_resource_name("prod_eastus_app!")

        assert len(violations) >= 1
        assert any(v["rule"] == "naming_characters" for v in violations)


class TestRegionValidation:
    """Tests for region validation."""

    def test_allowed_region_passes(self):
        """An allowed region passes validation."""
        service = ProvisioningStandardsService()
        violations = service.validate_region("eastus")

        assert violations == []

    def test_disallowed_region_fails(self):
        """A region not in the allowed list produces a violation."""
        service = ProvisioningStandardsService()
        violations = service.validate_region("brazilsouth")

        assert len(violations) >= 1
        assert any(v["rule"] == "region_not_allowed" for v in violations)

    def test_restricted_region_fails(self):
        """A restricted region produces a violation."""
        service = ProvisioningStandardsService()
        violations = service.validate_region("chinaeast")

        assert len(violations) >= 1
        assert any(v["rule"] == "region_restricted" for v in violations)

    def test_secondary_region_passes(self):
        """The secondary allowed region passes."""
        service = ProvisioningStandardsService()
        violations = service.validate_region("westus2")

        assert violations == []


class TestTagValidation:
    """Tests for tag validation."""

    def test_all_mandatory_tags_present(self):
        """All mandatory tags present with valid values passes."""
        service = ProvisioningStandardsService()
        tags = {
            "environment": "production",
            "owner": "admin@contoso.com",
            "cost-center": "CC-1234",
            "project": "governance",
        }
        violations, warnings = service.validate_tags(tags)

        assert violations == []

    def test_missing_mandatory_tag_fails(self):
        """Missing a mandatory tag produces a violation."""
        service = ProvisioningStandardsService()
        tags = {"environment": "production"}
        violations, warnings = service.validate_tags(tags)

        assert len(violations) >= 1
        assert any(v["rule"] == "missing_mandatory_tag" for v in violations)

    def test_invalid_tag_value_fails(self):
        """Invalid value for a constrained tag produces a violation."""
        service = ProvisioningStandardsService()
        tags = {
            "environment": "banana",
            "owner": "admin@contoso.com",
            "cost-center": "CC-1234",
            "project": "governance",
        }
        violations, warnings = service.validate_tags(tags)

        assert any(v["rule"] == "invalid_tag_value" for v in violations)

    def test_invalid_tag_pattern_fails(self):
        """Tag value not matching pattern produces a violation."""
        service = ProvisioningStandardsService()
        tags = {
            "environment": "production",
            "owner": "not-an-email",
            "cost-center": "CC-1234",
            "project": "governance",
        }
        violations, warnings = service.validate_tags(tags)

        assert any(v["rule"] == "invalid_tag_pattern" for v in violations)

    def test_missing_recommended_tag_produces_warning(self):
        """Missing a recommended tag produces a warning, not a violation."""
        service = ProvisioningStandardsService()
        tags = {
            "environment": "production",
            "owner": "admin@contoso.com",
            "cost-center": "CC-1234",
            "project": "governance",
        }
        violations, warnings = service.validate_tags(tags)

        assert len(violations) == 0
        assert any(w["rule"] == "missing_recommended_tag" for w in warnings)

    def test_cost_center_pattern_invalid(self):
        """Cost center not matching CC-XXXX pattern fails."""
        service = ProvisioningStandardsService()
        tags = {
            "environment": "production",
            "owner": "admin@contoso.com",
            "cost-center": "WRONG",
            "project": "governance",
        }
        violations, warnings = service.validate_tags(tags)

        assert any(v["rule"] == "invalid_tag_pattern" for v in violations)


class TestSkuValidation:
    """Tests for SKU restriction validation."""

    def test_allowed_vm_sku_passes(self):
        """An allowed VM SKU passes."""
        service = ProvisioningStandardsService()
        violations = service.validate_sku("virtual_machines", "Standard_B2s")

        assert violations == []

    def test_blocked_vm_sku_fails(self):
        """A blocked VM SKU family produces a violation."""
        service = ProvisioningStandardsService()
        violations = service.validate_sku("virtual_machines", "Standard_M64ms")

        assert len(violations) >= 1
        assert any(v["rule"] == "blocked_sku" for v in violations)

    def test_blocked_storage_redundancy_fails(self):
        """Blocked storage redundancy produces a violation."""
        service = ProvisioningStandardsService()
        violations = service.validate_sku("storage_accounts", "GRS")

        assert len(violations) >= 1
        assert any(v["rule"] == "blocked_sku" for v in violations)

    def test_allowed_storage_redundancy_passes(self):
        """Allowed storage redundancy passes."""
        service = ProvisioningStandardsService()
        violations = service.validate_sku("storage_accounts", "LRS")

        assert violations == []

    def test_blocked_app_service_tier_fails(self):
        """Blocked App Service tier produces a violation."""
        service = ProvisioningStandardsService()
        violations = service.validate_sku("app_service_plans", "PremiumV3")

        assert len(violations) >= 1

    def test_unknown_resource_type_passes(self):
        """Unknown resource type has no restrictions."""
        service = ProvisioningStandardsService()
        violations = service.validate_sku("unknown_type", "AnySkuHere")

        assert violations == []


class TestFullResourceValidation:
    """Tests for full resource validation."""

    def test_compliant_resource_passes(self):
        """A fully compliant resource passes all checks."""
        service = ProvisioningStandardsService()
        result = service.validate_resource(
            resource_id="/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.Compute/virtualMachines/prod-eastus-vm-web",
            resource_name="prod-eastus-vm-web",
            resource_type="Microsoft.Compute/virtualMachines",
            region="eastus",
            tags={
                "environment": "production",
                "owner": "admin@contoso.com",
                "cost-center": "CC-1234",
                "project": "governance",
            },
            sku="Standard_B2s",
        )

        assert result.is_compliant is True
        assert result.violation_count == 0

    def test_non_compliant_resource_has_violations(self):
        """A non-compliant resource has violations."""
        service = ProvisioningStandardsService()
        result = service.validate_resource(
            resource_id="/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.Compute/virtualMachines/BadName",
            resource_name="BadName",
            resource_type="Microsoft.Compute/virtualMachines",
            region="brazilsouth",
            tags={},
            sku="Standard_M64ms",
        )

        assert result.is_compliant is False
        assert result.violation_count > 0

    def test_validation_result_has_correct_type(self):
        """ValidationResult is returned."""
        service = ProvisioningStandardsService()
        result = service.validate_resource(
            resource_id="test-id",
            resource_name="test",
            resource_type="test-type",
        )

        assert isinstance(result, ValidationResult)


class TestSummaryGeneration:
    """Tests for summary generation."""

    def test_summary_with_mixed_results(self):
        """Summary correctly tallies compliant and non-compliant resources."""
        service = ProvisioningStandardsService()

        results = [
            service.validate_resource(
                resource_id="r1",
                resource_name="prod-eastus-app-web",
                resource_type="Microsoft.Web/serverFarms",
                region="eastus",
                tags={
                    "environment": "production",
                    "owner": "admin@contoso.com",
                    "cost-center": "CC-1234",
                    "project": "governance",
                },
            ),
            service.validate_resource(
                resource_id="r2",
                resource_name="BadName!",
                resource_type="Microsoft.Compute/virtualMachines",
                region="chinaeast",
                tags={},
            ),
        ]

        summary = service.generate_summary(results)

        assert summary.total_resources == 2
        assert summary.compliant_resources == 1
        assert summary.non_compliant_resources == 1
        assert summary.compliance_percentage == 50.0

    def test_empty_summary(self):
        """Summary handles empty results list."""
        service = ProvisioningStandardsService()
        summary = service.generate_summary([])

        assert summary.total_resources == 0
        assert summary.compliance_percentage == 0.0

    def test_summary_top_violations(self):
        """Summary lists top violations by count."""
        service = ProvisioningStandardsService()

        results = [
            service.validate_resource(
                resource_id=f"r{i}",
                resource_name="BadName",
                resource_type="test",
                tags={},
            )
            for i in range(5)
        ]

        summary = service.generate_summary(results)
        assert len(summary.top_violations) > 0


class TestProvisioningStandardsRoutes:
    """Tests for Provisioning Standards API routes."""

    def test_get_standards_returns_200(self, authed_client):
        """GET provisioning-standards returns 200 with standards."""
        response = authed_client.get("/api/v1/resources/provisioning-standards")

        assert response.status_code == 200
        data = response.json()
        assert "standards" in data

    def test_validate_resource_returns_200(self, authed_client):
        """POST validate returns 200 with validation result."""
        response = authed_client.post(
            "/api/v1/resources/provisioning-standards/validate",
            json={
                "resource_id": "test-id",
                "resource_name": "prod-eastus-app-web",
                "resource_type": "Microsoft.Web/serverFarms",
                "region": "eastus",
                "tags": {
                    "environment": "production",
                    "owner": "admin@contoso.com",
                    "cost-center": "CC-1234",
                    "project": "governance",
                },
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "is_compliant" in data

    def test_validate_naming_returns_200(self, authed_client):
        """GET naming/validate returns 200."""
        response = authed_client.get(
            "/api/v1/resources/provisioning-standards/naming/validate?name=prod-eastus-app-web"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_compliant"] is True

    def test_validate_region_returns_200(self, authed_client):
        """GET regions/validate returns 200."""
        response = authed_client.get(
            "/api/v1/resources/provisioning-standards/regions/validate?region=eastus"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_compliant"] is True

    def test_routes_require_auth(self, client):
        """All provisioning-standards endpoints require auth."""
        endpoints = [
            ("/api/v1/resources/provisioning-standards", "GET"),
            ("/api/v1/resources/provisioning-standards/naming/validate?name=test", "GET"),
            ("/api/v1/resources/provisioning-standards/regions/validate?region=test", "GET"),
        ]
        for endpoint, method in endpoints:
            if method == "GET":
                response = client.get(endpoint)
            assert response.status_code == 401, f"Expected 401 for {endpoint}"
