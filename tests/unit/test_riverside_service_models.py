"""Unit tests for Riverside Service data models.

Tests the dataclasses in app/api/services/riverside_service/models.py.

Traces: RC-005 — Riverside service data model integrity, validation,
and serialization for dashboard and reporting data.
"""

from dataclasses import asdict, fields
from datetime import date, datetime

import pytest

from app.api.services.riverside_service.constants import (
    DeadlinePhase,
    MFAStatus,
    RequirementLevel,
    RequirementStatus,
    RiversideRequirementCategory,
)
from app.api.services.riverside_service.models import (
    AggregateMFAStatus,
    GapAnalysis,
    MFAMaturityScore,
    RequirementListItem,
    RiversideComplianceSummary,
    RiversideExecutiveSummary,
    RiversideRequirement,
    RiversideThreatMetrics,
    TenantMaturityScore,
    TenantMFAStatus,
    TenantRequirementTracker,
    TenantRiversideSummary,
)


# ---------------------------------------------------------------------------
# RiversideRequirement
# ---------------------------------------------------------------------------


class TestRiversideRequirement:
    """Tests for the RiversideRequirement dataclass."""

    def test_creation_with_all_fields(self):
        """Should create instance with all required and default fields."""
        req = RiversideRequirement(
            id="MFA-001",
            category=RiversideRequirementCategory.MFA_ENFORCEMENT,
            title="Enforce MFA",
            description="Multi-factor auth required",
            control_source="NIST 800-171",
            control_reference="3.5.3",
            maturity_level=RequirementLevel.EMERGING,
            phase=DeadlinePhase.PHASE_1_Q3_2025,
            target_date=date(2025, 9, 30),
        )
        assert req.id == "MFA-001"
        assert req.category == RiversideRequirementCategory.MFA_ENFORCEMENT
        assert req.title == "Enforce MFA"
        assert req.status == RequirementStatus.NOT_STARTED  # default
        assert req.evidence_count == 0  # default
        assert req.approval_status is None  # default

    def test_default_status_is_not_started(self):
        """Default status should be NOT_STARTED."""
        req = RiversideRequirement(
            id="T-1",
            category=RiversideRequirementCategory.MFA_ENFORCEMENT,
            title="Test",
            description="Test",
            control_source="Test",
            control_reference="Test",
            maturity_level=RequirementLevel.EMERGING,
            phase=DeadlinePhase.PHASE_1_Q3_2025,
            target_date=None,
        )
        assert req.status == RequirementStatus.NOT_STARTED

    def test_override_defaults(self):
        """Should allow overriding default field values."""
        req = RiversideRequirement(
            id="T-2",
            category=RiversideRequirementCategory.THREAT_MANAGEMENT,
            title="Test",
            description="Test",
            control_source="Test",
            control_reference="Test",
            maturity_level=RequirementLevel.LEADING,
            phase=DeadlinePhase.PHASE_3_Q1_2026,
            target_date=date(2026, 3, 31),
            status=RequirementStatus.COMPLETED,
            evidence_count=5,
            approval_status="approved",
        )
        assert req.status == RequirementStatus.COMPLETED
        assert req.evidence_count == 5
        assert req.approval_status == "approved"

    def test_is_dataclass(self):
        """Should be a proper dataclass with expected fields."""
        field_names = {f.name for f in fields(RiversideRequirement)}
        assert "id" in field_names
        assert "category" in field_names
        assert "status" in field_names
        assert "evidence_count" in field_names

    def test_asdict_conversion(self):
        """Should convert to dict via asdict."""
        req = RiversideRequirement(
            id="T-3",
            category=RiversideRequirementCategory.MFA_ENFORCEMENT,
            title="Dict Test",
            description="Test",
            control_source="Test",
            control_reference="Test",
            maturity_level=RequirementLevel.EMERGING,
            phase=DeadlinePhase.PHASE_1_Q3_2025,
            target_date=None,
        )
        d = asdict(req)
        assert d["id"] == "T-3"
        assert d["title"] == "Dict Test"


# ---------------------------------------------------------------------------
# GapAnalysis
# ---------------------------------------------------------------------------


class TestGapAnalysis:
    """Tests for the GapAnalysis dataclass."""

    def test_creation(self):
        """Should create GapAnalysis with all fields."""
        gap = GapAnalysis(
            requirement_id="RC-001",
            title="Test Gap",
            category="IAM",
            priority="P0",
            status="not_started",
            tenant_id="t-001",
            tenant_code="HTT",
            due_date="2026-07-08",
            is_overdue=False,
            days_overdue=0,
            risk_level="High",
            description="A critical gap",
        )
        assert gap.requirement_id == "RC-001"
        assert gap.priority == "P0"
        assert gap.is_overdue is False
        assert gap.risk_level == "High"

    def test_overdue_gap(self):
        """Should represent an overdue gap correctly."""
        gap = GapAnalysis(
            requirement_id="RC-002",
            title="Overdue Gap",
            category="GS",
            priority="P1",
            status="in_progress",
            tenant_id="t-001",
            tenant_code="BCC",
            due_date="2025-01-01",
            is_overdue=True,
            days_overdue=30,
            risk_level="Critical",
            description="Overdue",
        )
        assert gap.is_overdue is True
        assert gap.days_overdue == 30
        assert gap.risk_level == "Critical"

    def test_none_due_date(self):
        """Should allow None due_date."""
        gap = GapAnalysis(
            requirement_id="RC-003",
            title="No Due Date",
            category="DS",
            priority="P2",
            status="not_started",
            tenant_id="t-001",
            tenant_code="FN",
            due_date=None,
            is_overdue=False,
            days_overdue=0,
            risk_level="Medium",
            description="No due date set",
        )
        assert gap.due_date is None

    def test_dict_conversion(self):
        """GapAnalysis __dict__ should contain all fields."""
        gap = GapAnalysis(
            requirement_id="RC-004",
            title="Dict Test",
            category="IAM",
            priority="P0",
            status="completed",
            tenant_id="t-001",
            tenant_code="HTT",
            due_date=None,
            is_overdue=False,
            days_overdue=0,
            risk_level="Low",
            description="Done",
        )
        d = gap.__dict__
        assert "requirement_id" in d
        assert "risk_level" in d
        assert d["status"] == "completed"


# ---------------------------------------------------------------------------
# MFAMaturityScore
# ---------------------------------------------------------------------------


class TestMFAMaturityScore:
    """Tests for MFAMaturityScore dataclass."""

    def test_creation(self):
        score = MFAMaturityScore(
            overall_maturity=RequirementLevel.DEVELOPING,
            enrollment_rate_pct=75.0,
            admin_enforcement_pct=100.0,
            privileged_user_enrollment_pct=90.0,
            gap_count=3,
        )
        assert score.overall_maturity == RequirementLevel.DEVELOPING
        assert score.enrollment_rate_pct == 75.0
        assert score.gap_count == 3


# ---------------------------------------------------------------------------
# RiversideThreatMetrics
# ---------------------------------------------------------------------------


class TestRiversideThreatMetrics:
    """Tests for RiversideThreatMetrics dataclass."""

    def test_creation(self):
        metrics = RiversideThreatMetrics(
            phishing_attempts_30d=50,
            malware_detected_30d=5,
            spam_filtered_30d=1000,
            risk_score=25.5,
            trend_direction="improving",
        )
        assert metrics.phishing_attempts_30d == 50
        assert metrics.trend_direction == "improving"


# ---------------------------------------------------------------------------
# RiversideComplianceSummary
# ---------------------------------------------------------------------------


class TestRiversideComplianceSummary:
    """Tests for RiversideComplianceSummary dataclass."""

    def test_creation(self):
        summary = RiversideComplianceSummary(
            overall_compliance_pct=72.5,
            target_compliance_pct=100.0,
            completed_requirements_count=52,
            total_requirements_count=72,
        )
        assert summary.overall_compliance_pct == 72.5
        assert summary.completed_requirements_count == 52

    def test_completion_math(self):
        """Completed requirements should not exceed total."""
        summary = RiversideComplianceSummary(
            overall_compliance_pct=100.0,
            target_compliance_pct=100.0,
            completed_requirements_count=72,
            total_requirements_count=72,
        )
        assert summary.completed_requirements_count <= summary.total_requirements_count


# ---------------------------------------------------------------------------
# TenantRequirementTracker
# ---------------------------------------------------------------------------


class TestTenantRequirementTracker:
    """Tests for TenantRequirementTracker dataclass."""

    def test_creation_with_defaults(self):
        req = RiversideRequirement(
            id="T-1",
            category=RiversideRequirementCategory.MFA_ENFORCEMENT,
            title="Test",
            description="Test",
            control_source="Test",
            control_reference="Test",
            maturity_level=RequirementLevel.EMERGING,
            phase=DeadlinePhase.PHASE_1_Q3_2025,
            target_date=None,
        )
        tracker = TenantRequirementTracker(
            tenant_id="t-001",
            tenant_name="Test Tenant",
            requirement=req,
            status=RequirementStatus.IN_PROGRESS,
        )
        assert tracker.tenant_id == "t-001"
        assert tracker.evidence_submitted == 0  # default
        assert tracker.last_updated is None  # default
        assert tracker.compliance_notes is None  # default


# ---------------------------------------------------------------------------
# AggregateMFAStatus
# ---------------------------------------------------------------------------


class TestAggregateMFAStatus:
    """Tests for AggregateMFAStatus dataclass."""

    def test_creation_with_defaults(self):
        status = AggregateMFAStatus(
            total_users=1000,
            mfa_enforced_users=800,
            mfa_available_users=100,
            mfa_pending_users=50,
            mfa_not_configured_users=50,
            enforced_rate_pct=80.0,
        )
        assert status.total_users == 1000
        assert status.admin_mfa_status == {}  # default_factory

    def test_with_admin_status(self):
        status = AggregateMFAStatus(
            total_users=100,
            mfa_enforced_users=80,
            mfa_available_users=10,
            mfa_pending_users=5,
            mfa_not_configured_users=5,
            enforced_rate_pct=80.0,
            admin_mfa_status={"admin1": MFAStatus.ENFORCED},
        )
        assert status.admin_mfa_status["admin1"] == MFAStatus.ENFORCED


# ---------------------------------------------------------------------------
# TenantMFAStatus / TenantMaturityScore / RequirementListItem
# ---------------------------------------------------------------------------


class TestTenantMFAStatus:
    """Tests for TenantMFAStatus dataclass."""

    def test_creation(self):
        status = TenantMFAStatus(
            tenant_id="t-001",
            tenant_code="HTT",
            tenant_name="Head-To-Toe",
            total_users=450,
            mfa_enrolled=380,
            mfa_coverage_pct=84.4,
            admin_accounts=25,
            admin_mfa=25,
            admin_mfa_pct=100.0,
            unprotected_users=70,
            snapshot_date="2025-01-15",
        )
        assert status.tenant_code == "HTT"
        assert status.unprotected_users == 70


class TestTenantMaturityScore:
    """Tests for TenantMaturityScore dataclass."""

    def test_creation(self):
        score = TenantMaturityScore(
            tenant_id="t-001",
            tenant_code="HTT",
            tenant_name="Head-To-Toe",
            overall_maturity=2.5,
            target_maturity=3.0,
            domain_scores={"IAM": 3.0, "GS": 2.0, "DS": 2.5},
            critical_gaps=2,
            last_assessment="2025-01-15",
        )
        assert score.domain_scores["IAM"] == 3.0
        assert score.critical_gaps == 2


class TestRequirementListItem:
    """Tests for RequirementListItem dataclass."""

    def test_creation(self):
        item = RequirementListItem(
            id=1,
            requirement_id="RC-001",
            title="PAM Implementation",
            description="Deploy PAM solution",
            category="IAM",
            priority="P0",
            status="in_progress",
            tenant_id="t-001",
            tenant_code="HTT",
            due_date="2026-07-08",
            completed_date=None,
            owner="John Doe",
            evidence_url=None,
            evidence_notes=None,
            created_at="2025-01-01T00:00:00",
            updated_at="2025-01-15T10:30:00",
        )
        assert item.id == 1
        assert item.requirement_id == "RC-001"
        assert item.completed_date is None


# ---------------------------------------------------------------------------
# RiversideExecutiveSummary and TenantRiversideSummary
# ---------------------------------------------------------------------------


class TestExecutiveSummary:
    """Tests for the top-level executive summary dataclasses."""

    def test_executive_summary_creation(self):
        """Should create a complete executive summary."""
        mfa = MFAMaturityScore(
            overall_maturity=RequirementLevel.DEVELOPING,
            enrollment_rate_pct=75.0,
            admin_enforcement_pct=100.0,
            privileged_user_enrollment_pct=90.0,
            gap_count=3,
        )
        summary = RiversideExecutiveSummary(
            overall_compliance_pct=72.5,
            phases_complete=["Phase 1"],
            completion_by_tenant=[],
            mfa_maturity=mfa,
            key_gaps=["MFA coverage below 80%"],
            critical_alerts=["3 tenants below target"],
            last_updated=datetime(2025, 1, 15, 10, 0),
        )
        assert summary.overall_compliance_pct == 72.5
        assert len(summary.phases_complete) == 1
        assert summary.mfa_maturity.gap_count == 3

    def test_tenant_riverside_summary_creation(self):
        """Should create a per-tenant summary."""
        mfa = MFAMaturityScore(
            overall_maturity=RequirementLevel.MATURE,
            enrollment_rate_pct=90.0,
            admin_enforcement_pct=100.0,
            privileged_user_enrollment_pct=95.0,
            gap_count=1,
        )
        threat = RiversideThreatMetrics(
            phishing_attempts_30d=10,
            malware_detected_30d=0,
            spam_filtered_30d=500,
            risk_score=15.0,
            trend_direction="stable",
        )
        tenant_summary = TenantRiversideSummary(
            tenant_id="t-001",
            tenant_name="Head-To-Toe",
            overall_compliance_pct=85.0,
            phase_1_completion_pct=100.0,
            phase_2_completion_pct=80.0,
            phase_3_completion_pct=50.0,
            mfa_maturity=mfa,
            threat_metrics=threat,
            critical_issues_count=1,
        )
        assert tenant_summary.phase_1_completion_pct == 100.0
        assert tenant_summary.critical_issues_count == 1
