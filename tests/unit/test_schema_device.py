"""Unit tests for Riverside device compliance schemas.

Tests Pydantic schemas in app/schemas/riverside/device.py.

Traces: RC-007 — Device compliance data validation for
Riverside dashboard reporting.
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas.riverside.device import (
    RiversideDeviceComplianceBase,
    RiversideDeviceComplianceResponse,
)

# ---------------------------------------------------------------------------
# RiversideDeviceComplianceBase
# ---------------------------------------------------------------------------


class TestDeviceComplianceBase:
    """Tests for RiversideDeviceComplianceBase schema."""

    def test_valid_creation(self):
        """Should create with valid data."""
        schema = RiversideDeviceComplianceBase(
            total_devices=200,
            mdm_enrolled=180,
            edr_covered=190,
            encrypted_devices=175,
            compliant_devices=165,
            compliance_percentage=82.5,
            snapshot_date=datetime(2025, 1, 15),
        )
        assert schema.total_devices == 200
        assert schema.mdm_enrolled == 180
        assert schema.compliance_percentage == 82.5

    def test_defaults_to_zero(self):
        """Integer fields should default to 0."""
        schema = RiversideDeviceComplianceBase(
            snapshot_date=datetime(2025, 1, 15),
        )
        assert schema.total_devices == 0
        assert schema.mdm_enrolled == 0
        assert schema.edr_covered == 0
        assert schema.encrypted_devices == 0
        assert schema.compliant_devices == 0
        assert schema.compliance_percentage == 0.0

    def test_negative_total_devices_rejected(self):
        """Should reject negative device counts (ge=0)."""
        with pytest.raises(ValidationError) as exc_info:
            RiversideDeviceComplianceBase(
                total_devices=-1,
                snapshot_date=datetime(2025, 1, 15),
            )
        assert "total_devices" in str(exc_info.value)

    def test_negative_mdm_enrolled_rejected(self):
        """Should reject negative MDM enrolled count."""
        with pytest.raises(ValidationError):
            RiversideDeviceComplianceBase(
                mdm_enrolled=-5,
                snapshot_date=datetime(2025, 1, 15),
            )

    def test_compliance_percentage_max_100(self):
        """Should reject compliance percentage above 100."""
        with pytest.raises(ValidationError) as exc_info:
            RiversideDeviceComplianceBase(
                compliance_percentage=100.1,
                snapshot_date=datetime(2025, 1, 15),
            )
        assert "compliance_percentage" in str(exc_info.value)

    def test_compliance_percentage_min_0(self):
        """Should reject negative compliance percentage."""
        with pytest.raises(ValidationError):
            RiversideDeviceComplianceBase(
                compliance_percentage=-0.1,
                snapshot_date=datetime(2025, 1, 15),
            )

    def test_snapshot_date_required(self):
        """Should reject missing snapshot_date."""
        with pytest.raises(ValidationError):
            RiversideDeviceComplianceBase()


# ---------------------------------------------------------------------------
# RiversideDeviceComplianceResponse
# ---------------------------------------------------------------------------


class TestDeviceComplianceResponse:
    """Tests for RiversideDeviceComplianceResponse schema."""

    def test_valid_response(self):
        """Should create a valid response with all required fields."""
        resp = RiversideDeviceComplianceResponse(
            id=1,
            tenant_id="12345678-1234-1234-1234-123456789abc",
            total_devices=200,
            mdm_enrolled=180,
            edr_covered=190,
            encrypted_devices=175,
            compliant_devices=165,
            compliance_percentage=82.5,
            snapshot_date=datetime(2025, 1, 15),
            created_at=datetime(2025, 1, 15),
        )
        assert resp.id == 1
        assert resp.tenant_id == "12345678-1234-1234-1234-123456789abc"

    def test_tenant_id_length_validation(self):
        """Should reject tenant_id shorter than 36 characters."""
        with pytest.raises(ValidationError) as exc_info:
            RiversideDeviceComplianceResponse(
                id=1,
                tenant_id="too-short",
                snapshot_date=datetime(2025, 1, 15),
                created_at=datetime(2025, 1, 15),
            )
        assert "tenant_id" in str(exc_info.value)

    def test_tenant_id_max_length_validation(self):
        """Should reject tenant_id longer than 36 characters."""
        with pytest.raises(ValidationError):
            RiversideDeviceComplianceResponse(
                id=1,
                tenant_id="x" * 37,
                snapshot_date=datetime(2025, 1, 15),
                created_at=datetime(2025, 1, 15),
            )

    def test_from_attributes_config(self):
        """Should have from_attributes=True for ORM compatibility."""
        assert RiversideDeviceComplianceResponse.model_config.get("from_attributes") is True

    def test_id_required(self):
        """Should reject missing id field."""
        with pytest.raises(ValidationError):
            RiversideDeviceComplianceResponse(
                tenant_id="12345678-1234-1234-1234-123456789abc",
                snapshot_date=datetime(2025, 1, 15),
                created_at=datetime(2025, 1, 15),
            )
