"""Unit tests for Riverside governance data models.

Tests enums, dataclasses, and constants defined in
app/api/services/riverside_models.py.

Traces: RC-001 through RC-045
"""

from dataclasses import fields
from datetime import date
from enum import Enum

from app.api.services.riverside_models import (
    MFA_THRESHOLD_PERCENTAGES,
    PHASE_1_TARGET_DATE,
    PHASE_2_TARGET_DATE,
    PHASE_3_TARGET_DATE,
    TENANTS,
    AggregateMFAStatus,
    DeadlinePhase,
    MFAMaturityScore,
    MFAStatus,
    RequirementLevel,
    RequirementStatus,
    RiversideComplianceSummary,
    RiversideRequirement,
    RiversideRequirementCategory,
)

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class TestRequirementLevel:
    """Tests for RequirementLevel enum."""

    def test_is_enum(self):
        assert issubclass(RequirementLevel, Enum)

    def test_members(self):
        assert RequirementLevel.EMERGING.value == "Emerging"
        assert RequirementLevel.DEVELOPING.value == "Developing"
        assert RequirementLevel.MATURE.value == "Mature"
        assert RequirementLevel.LEADING.value == "Leading"

    def test_member_count(self):
        assert len(RequirementLevel) == 4


class TestMFAStatus:
    """Tests for MFAStatus enum."""

    def test_members(self):
        assert MFAStatus.ENFORCED.value == "Enforced"
        assert MFAStatus.AVAILABLE.value == "Available"
        assert MFAStatus.PENDING.value == "Pending"
        assert MFAStatus.NOT_CONFIGURED.value == "Not Configured"

    def test_member_count(self):
        assert len(MFAStatus) == 4


class TestRequirementStatus:
    """Tests for RequirementStatus enum."""

    def test_members(self):
        assert RequirementStatus.NOT_STARTED.value == "Not Started"
        assert RequirementStatus.IN_PROGRESS.value == "In Progress"
        assert RequirementStatus.COMPLETED.value == "Completed"
        assert RequirementStatus.AT_RISK.value == "At Risk"


class TestDeadlinePhase:
    """Tests for DeadlinePhase enum."""

    def test_phase_count(self):
        assert len(DeadlinePhase) == 3

    def test_phase_values(self):
        assert "Q3 2025" in DeadlinePhase.PHASE_1_Q3_2025.value
        assert "Q4 2025" in DeadlinePhase.PHASE_2_Q4_2025.value
        assert "Q1 2026" in DeadlinePhase.PHASE_3_Q1_2026.value


class TestRiversideRequirementCategory:
    """Tests for RiversideRequirementCategory enum."""

    def test_member_count(self):
        assert len(RiversideRequirementCategory) == 8

    def test_key_categories(self):
        assert RiversideRequirementCategory.MFA_ENFORCEMENT.value == "MFA Enforcement"
        assert RiversideRequirementCategory.CONDITIONAL_ACCESS.value == "Conditional Access"
        assert RiversideRequirementCategory.PRIVILEGED_ACCESS.value == "Privileged Access"
        assert RiversideRequirementCategory.THREAT_MANAGEMENT.value == "Threat Management"


# ---------------------------------------------------------------------------
# Dataclass Models
# ---------------------------------------------------------------------------


class TestRiversideRequirement:
    """Tests for RiversideRequirement dataclass."""

    def test_creation_with_defaults(self):
        req = RiversideRequirement(
            id="REQ-001",
            category=RiversideRequirementCategory.MFA_ENFORCEMENT,
            title="Enable MFA for all users",
            description="All users must have MFA enabled",
            control_source="NIST",
            control_reference="IA-2",
            maturity_level=RequirementLevel.MATURE,
            phase=DeadlinePhase.PHASE_1_Q3_2025,
            target_date=date(2025, 9, 30),
        )
        assert req.status == RequirementStatus.NOT_STARTED
        assert req.evidence_count == 0
        assert req.approval_status is None

    def test_creation_with_overrides(self):
        req = RiversideRequirement(
            id="REQ-002",
            category=RiversideRequirementCategory.CONDITIONAL_ACCESS,
            title="Block legacy auth",
            description="Block legacy authentication protocols",
            control_source="CIS",
            control_reference="5.1",
            maturity_level=RequirementLevel.DEVELOPING,
            phase=DeadlinePhase.PHASE_2_Q4_2025,
            target_date=None,
            status=RequirementStatus.IN_PROGRESS,
            evidence_count=3,
        )
        assert req.status == RequirementStatus.IN_PROGRESS
        assert req.evidence_count == 3


class TestRiversideComplianceSummary:
    """Tests for RiversideComplianceSummary dataclass."""

    def test_creation(self):
        summary = RiversideComplianceSummary(
            overall_compliance_pct=65.0,
            target_compliance_pct=100.0,
            completed_requirements_count=47,
            total_requirements_count=72,
        )
        assert summary.overall_compliance_pct == 65.0
        assert summary.total_requirements_count == 72


class TestMFAMaturityScore:
    """Tests for MFAMaturityScore dataclass."""

    def test_creation(self):
        score = MFAMaturityScore(
            overall_maturity=RequirementLevel.DEVELOPING,
            enrollment_rate_pct=75.0,
            admin_enforcement_pct=100.0,
            privileged_user_enrollment_pct=90.0,
            gap_count=5,
        )
        assert score.overall_maturity == RequirementLevel.DEVELOPING
        assert score.gap_count == 5


class TestAggregateMFAStatus:
    """Tests for AggregateMFAStatus dataclass."""

    def test_creation(self):
        agg = AggregateMFAStatus(
            total_users=500,
            mfa_enforced_users=400,
            mfa_available_users=50,
            mfa_pending_users=30,
            mfa_not_configured_users=20,
            enforced_rate_pct=80.0,
            admin_mfa_status={"admin1": MFAStatus.ENFORCED},
        )
        assert agg.total_users == 500
        assert agg.enforced_rate_pct == 80.0

    def test_field_count(self):
        assert len(fields(AggregateMFAStatus)) == 7


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestConstants:
    """Tests for module-level constants."""

    def test_phase_target_dates(self):
        assert PHASE_1_TARGET_DATE == date(2025, 9, 30)
        assert PHASE_2_TARGET_DATE == date(2025, 12, 31)
        assert PHASE_3_TARGET_DATE == date(2026, 3, 31)

    def test_mfa_thresholds(self):
        assert MFA_THRESHOLD_PERCENTAGES["Emerging"] == 25
        assert MFA_THRESHOLD_PERCENTAGES["Developing"] == 50
        assert MFA_THRESHOLD_PERCENTAGES["Mature"] == 75
        assert MFA_THRESHOLD_PERCENTAGES["Leading"] == 95

    def test_tenants_dict(self):
        assert isinstance(TENANTS, dict)
        assert len(TENANTS) == 5
        assert "htt" in TENANTS
