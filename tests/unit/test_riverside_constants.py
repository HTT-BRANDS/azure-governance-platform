"""Unit tests for Riverside Service constants and enums.

Tests the constants, enums, and configuration values in
app/api/services/riverside_service/constants.py.

Traces: RC-004 — Riverside configuration constants integrity.
"""

from datetime import date
from enum import Enum

import pytest

from app.api.services.riverside_service.constants import (
    ADMIN_ROLE_IDS,
    ALL_TENANTS,
    CURRENT_MATURITY_SCORE,
    FINANCIAL_RISK,
    MFA_THRESHOLD_PERCENTAGES,
    RIVERSIDE_DEADLINE,
    RIVERSIDE_SYNC_INTERVAL_HOURS,
    RIVERSIDE_TENANTS,
    TARGET_MATURITY_SCORE,
    DeadlinePhase,
    MFAStatus,
    RequirementLevel,
    RequirementStatus,
    RiversideRequirementCategory,
)

# ---------------------------------------------------------------------------
# Scalar Constants
# ---------------------------------------------------------------------------


class TestScalarConstants:
    """Tests for scalar constant values."""

    def test_riverside_deadline_is_date(self):
        """RIVERSIDE_DEADLINE should be a date object."""
        assert isinstance(RIVERSIDE_DEADLINE, date)

    def test_riverside_deadline_value(self):
        """RIVERSIDE_DEADLINE should be July 8, 2026."""
        assert RIVERSIDE_DEADLINE == date(2026, 7, 8)

    def test_financial_risk_value(self):
        """FINANCIAL_RISK should be $4M."""
        assert FINANCIAL_RISK == "$4M"

    def test_target_maturity_score(self):
        """TARGET_MATURITY_SCORE should be 3.0."""
        assert TARGET_MATURITY_SCORE == 3.0
        assert isinstance(TARGET_MATURITY_SCORE, float)

    def test_current_maturity_score(self):
        """CURRENT_MATURITY_SCORE should be 2.4."""
        assert CURRENT_MATURITY_SCORE == 2.4
        assert isinstance(CURRENT_MATURITY_SCORE, float)

    def test_current_below_target(self):
        """Current maturity should be below target (otherwise why track it?)."""
        assert CURRENT_MATURITY_SCORE < TARGET_MATURITY_SCORE

    def test_sync_interval_hours(self):
        """RIVERSIDE_SYNC_INTERVAL_HOURS should be a positive integer."""
        assert isinstance(RIVERSIDE_SYNC_INTERVAL_HOURS, int)
        assert RIVERSIDE_SYNC_INTERVAL_HOURS > 0
        assert RIVERSIDE_SYNC_INTERVAL_HOURS == 4


# ---------------------------------------------------------------------------
# RequirementLevel Enum
# ---------------------------------------------------------------------------


class TestRequirementLevel:
    """Tests for the RequirementLevel enum."""

    def test_is_enum(self):
        """RequirementLevel should be an Enum subclass."""
        assert issubclass(RequirementLevel, Enum)

    def test_member_count(self):
        """Should have exactly 4 maturity levels."""
        assert len(RequirementLevel) == 4

    def test_emerging(self):
        assert RequirementLevel.EMERGING.value == "Emerging"

    def test_developing(self):
        assert RequirementLevel.DEVELOPING.value == "Developing"

    def test_mature(self):
        assert RequirementLevel.MATURE.value == "Mature"

    def test_leading(self):
        assert RequirementLevel.LEADING.value == "Leading"


# ---------------------------------------------------------------------------
# MFAStatus Enum
# ---------------------------------------------------------------------------


class TestMFAStatus:
    """Tests for the MFAStatus enum."""

    def test_member_count(self):
        """Should have exactly 4 MFA statuses."""
        assert len(MFAStatus) == 4

    def test_enforced(self):
        assert MFAStatus.ENFORCED.value == "Enforced"

    def test_available(self):
        assert MFAStatus.AVAILABLE.value == "Available"

    def test_pending(self):
        assert MFAStatus.PENDING.value == "Pending"

    def test_not_configured(self):
        assert MFAStatus.NOT_CONFIGURED.value == "Not Configured"


# ---------------------------------------------------------------------------
# RequirementStatus Enum
# ---------------------------------------------------------------------------


class TestRequirementStatus:
    """Tests for the RequirementStatus enum."""

    def test_member_count(self):
        """Should have exactly 4 requirement statuses."""
        assert len(RequirementStatus) == 4

    def test_not_started(self):
        assert RequirementStatus.NOT_STARTED.value == "Not Started"

    def test_in_progress(self):
        assert RequirementStatus.IN_PROGRESS.value == "In Progress"

    def test_completed(self):
        assert RequirementStatus.COMPLETED.value == "Completed"

    def test_at_risk(self):
        assert RequirementStatus.AT_RISK.value == "At Risk"


# ---------------------------------------------------------------------------
# DeadlinePhase Enum
# ---------------------------------------------------------------------------


class TestDeadlinePhase:
    """Tests for the DeadlinePhase enum."""

    def test_member_count(self):
        """Should have exactly 3 implementation phases."""
        assert len(DeadlinePhase) == 3

    def test_phase_1(self):
        assert DeadlinePhase.PHASE_1_Q3_2025.value == "Phase 1: Q3 2025"

    def test_phase_2(self):
        assert DeadlinePhase.PHASE_2_Q4_2025.value == "Phase 2: Q4 2025"

    def test_phase_3(self):
        assert DeadlinePhase.PHASE_3_Q1_2026.value == "Phase 3: Q1 2026"


# ---------------------------------------------------------------------------
# RiversideRequirementCategory Enum
# ---------------------------------------------------------------------------


class TestRiversideRequirementCategory:
    """Tests for the RiversideRequirementCategory enum."""

    def test_member_count(self):
        """Should have exactly 8 requirement categories."""
        assert len(RiversideRequirementCategory) == 8

    @pytest.mark.parametrize(
        "member,expected_value",
        [
            ("MFA_ENFORCEMENT", "MFA Enforcement"),
            ("CONDITIONAL_ACCESS", "Conditional Access"),
            ("PRIVILEGED_ACCESS", "Privileged Access"),
            ("DEVICE_COMPLIANCE", "Device Compliance"),
            ("THREAT_MANAGEMENT", "Threat Management"),
            ("DATA_LOSS_PREVENTION", "Data Loss Prevention"),
            ("LOGGING_MONITORING", "Logging & Monitoring"),
            ("INCIDENT_RESPONSE", "Incident Response"),
        ],
    )
    def test_category_values(self, member: str, expected_value: str):
        """Each category should have the correct display value."""
        assert RiversideRequirementCategory[member].value == expected_value


# ---------------------------------------------------------------------------
# MFA_THRESHOLD_PERCENTAGES
# ---------------------------------------------------------------------------


class TestMFAThresholds:
    """Tests for MFA threshold percentage mapping."""

    def test_keys_match_requirement_levels(self):
        """Threshold keys should match RequirementLevel values."""
        expected_keys = {level.value for level in RequirementLevel}
        assert set(MFA_THRESHOLD_PERCENTAGES.keys()) == expected_keys

    def test_thresholds_are_ascending(self):
        """Thresholds should increase with maturity level."""
        ordered_levels = ["Emerging", "Developing", "Mature", "Leading"]
        thresholds = [MFA_THRESHOLD_PERCENTAGES[level] for level in ordered_levels]
        assert thresholds == sorted(thresholds)
        assert len(set(thresholds)) == len(thresholds)  # no duplicates

    def test_threshold_values(self):
        """Specific threshold values should match expectations."""
        assert MFA_THRESHOLD_PERCENTAGES["Emerging"] == 25
        assert MFA_THRESHOLD_PERCENTAGES["Developing"] == 50
        assert MFA_THRESHOLD_PERCENTAGES["Mature"] == 75
        assert MFA_THRESHOLD_PERCENTAGES["Leading"] == 95


# ---------------------------------------------------------------------------
# Tenant Configurations
# ---------------------------------------------------------------------------


class TestTenantConfigurations:
    """Tests for tenant configuration dictionaries."""

    def test_riverside_tenants_count(self):
        """Should have exactly 4 Riverside compliance tenants."""
        assert len(RIVERSIDE_TENANTS) == 4

    def test_riverside_tenant_codes(self):
        """Should contain the correct brand codes."""
        assert set(RIVERSIDE_TENANTS.keys()) == {"HTT", "BCC", "FN", "TLL"}

    def test_all_tenants_includes_riverside(self):
        """ALL_TENANTS should be a superset of RIVERSIDE_TENANTS."""
        for code in RIVERSIDE_TENANTS:
            assert code in ALL_TENANTS
            assert ALL_TENANTS[code] == RIVERSIDE_TENANTS[code]

    def test_all_tenants_includes_dce(self):
        """ALL_TENANTS should include DCE for tracking."""
        assert "DCE" in ALL_TENANTS

    def test_all_tenants_count(self):
        """ALL_TENANTS should have 5 entries (4 Riverside + DCE)."""
        assert len(ALL_TENANTS) == 5

    def test_tenant_codes_uppercase(self):
        """All tenant codes should be uppercase."""
        for code in ALL_TENANTS:
            assert code == code.upper()

    def test_tenant_names_non_empty(self):
        """All tenant names should be non-empty strings."""
        for name in ALL_TENANTS.values():
            assert isinstance(name, str)
            assert len(name) > 0


# ---------------------------------------------------------------------------
# Admin Role IDs
# ---------------------------------------------------------------------------


class TestAdminRoleIDs:
    """Tests for admin role ID constants."""

    def test_admin_role_ids_count(self):
        """Should have exactly 4 admin role IDs."""
        assert len(ADMIN_ROLE_IDS) == 4

    def test_admin_role_ids_are_guids(self):
        """Each admin role ID should be a valid GUID format."""
        import re

        guid_pattern = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
        for role_id in ADMIN_ROLE_IDS:
            assert guid_pattern.match(role_id), f"Invalid GUID: {role_id}"

    def test_admin_role_ids_unique(self):
        """All admin role IDs should be unique."""
        assert len(ADMIN_ROLE_IDS) == len(set(ADMIN_ROLE_IDS))

    def test_global_admin_role_present(self):
        """Global Admin role ID should be in the list."""
        assert "62e90394-69f5-4237-9190-012177145e10" in ADMIN_ROLE_IDS

    def test_security_admin_role_present(self):
        """Security Admin role ID should be in the list."""
        assert "194ae4cb-b126-40b2-bd5b-6091b380977d" in ADMIN_ROLE_IDS
