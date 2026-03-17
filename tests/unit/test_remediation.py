"""Unit tests for Riverside compliance and remediation logic.

Tests calculate_compliance_summary and analyze_mfa_gaps business logic
in app/api/services/riverside_compliance.py with properly mocked DB.

Traces: CM-005 — Remediation suggestions, compliance calculations,
MFA gap analysis, and maturity distribution.
"""

from datetime import date, datetime
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from app.api.services.riverside_compliance import (
    RIVERSIDE_DEADLINE,
    TARGET_MATURITY_SCORE,
    analyze_mfa_gaps,
    calculate_compliance_summary,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_compliance_record(
    tenant_id: str = "t-001",
    maturity: float = 2.5,
    critical_gaps: int = 1,
    reqs_total: int = 10,
    reqs_completed: int = 5,
) -> MagicMock:
    rec = MagicMock()
    rec.tenant_id = tenant_id
    rec.overall_maturity_score = maturity
    rec.critical_gaps_count = critical_gaps
    rec.requirements_total = reqs_total
    rec.requirements_completed = reqs_completed
    rec.created_at = datetime.utcnow()
    return rec


def _make_mfa_record(
    tenant_id: str = "t-001",
    total_users: int = 100,
    mfa_enrolled: int = 80,
    admin_total: int = 10,
    admin_mfa: int = 9,
) -> MagicMock:
    rec = MagicMock()
    rec.tenant_id = tenant_id
    rec.total_users = total_users
    rec.mfa_enrolled_users = mfa_enrolled
    rec.mfa_coverage_percentage = round(mfa_enrolled / total_users * 100, 2) if total_users else 0
    rec.admin_accounts_total = admin_total
    rec.admin_accounts_mfa = admin_mfa
    rec.admin_mfa_percentage = round(admin_mfa / admin_total * 100, 2) if admin_total else 0
    rec.unprotected_users = total_users - mfa_enrolled
    rec.snapshot_date = datetime.utcnow()
    return rec


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestComplianceConstants:
    """Tests for module-level constants."""

    def test_riverside_deadline(self):
        assert RIVERSIDE_DEADLINE == date(2026, 7, 8)

    def test_target_maturity(self):
        assert TARGET_MATURITY_SCORE == 3.0


# ---------------------------------------------------------------------------
# calculate_compliance_summary
# ---------------------------------------------------------------------------


class TestCalculateComplianceSummary:
    """Tests for calculate_compliance_summary function."""

    def test_no_data_raises_value_error(self):
        """Should raise ValueError when no compliance data exists."""
        mock_db = MagicMock(spec=Session)
        # Subquery path → empty result
        mock_db.query.return_value.group_by.return_value.subquery.return_value = MagicMock()
        mock_db.query.return_value.join.return_value.all.return_value = []

        with pytest.raises(ValueError, match="No compliance data"):
            calculate_compliance_summary(mock_db)

    def test_single_tenant_summary(self):
        """Should calculate summary for a single tenant."""
        mock_db = MagicMock(spec=Session)
        record = _make_compliance_record(maturity=2.5, reqs_total=10, reqs_completed=7)

        mock_db.query.return_value.group_by.return_value.subquery.return_value = MagicMock()
        mock_db.query.return_value.join.return_value.all.return_value = [record]

        result = calculate_compliance_summary(mock_db)

        assert result["average_maturity_score"] == 2.5
        assert result["overall_compliance_percentage"] == 70.0
        assert result["tenants_analyzed"] == 1
        assert result["requirements_completed"] == 7
        assert result["requirements_total"] == 10

    def test_maturity_distribution_below_2(self):
        """Should categorize maturity < 2.0 as below_2."""
        mock_db = MagicMock(spec=Session)
        record = _make_compliance_record(maturity=1.5)

        mock_db.query.return_value.group_by.return_value.subquery.return_value = MagicMock()
        mock_db.query.return_value.join.return_value.all.return_value = [record]

        result = calculate_compliance_summary(mock_db)
        assert result["maturity_distribution"]["below_2"] == 1

    def test_maturity_distribution_2_to_3(self):
        """Should categorize 2.0 <= maturity < 3.0 as 2_to_3."""
        mock_db = MagicMock(spec=Session)
        record = _make_compliance_record(maturity=2.5)

        mock_db.query.return_value.group_by.return_value.subquery.return_value = MagicMock()
        mock_db.query.return_value.join.return_value.all.return_value = [record]

        result = calculate_compliance_summary(mock_db)
        assert result["maturity_distribution"]["2_to_3"] == 1

    def test_maturity_distribution_3_to_4(self):
        """Should categorize 3.0 <= maturity < 4.0 as 3_to_4."""
        mock_db = MagicMock(spec=Session)
        record = _make_compliance_record(maturity=3.5)

        mock_db.query.return_value.group_by.return_value.subquery.return_value = MagicMock()
        mock_db.query.return_value.join.return_value.all.return_value = [record]

        result = calculate_compliance_summary(mock_db)
        assert result["maturity_distribution"]["3_to_4"] == 1

    def test_maturity_distribution_above_4(self):
        """Should categorize maturity >= 4.0 as above_4."""
        mock_db = MagicMock(spec=Session)
        record = _make_compliance_record(maturity=4.2)

        mock_db.query.return_value.group_by.return_value.subquery.return_value = MagicMock()
        mock_db.query.return_value.join.return_value.all.return_value = [record]

        result = calculate_compliance_summary(mock_db)
        assert result["maturity_distribution"]["above_4"] == 1

    def test_trend_improving(self):
        """Completion >= 70% → improving."""
        mock_db = MagicMock(spec=Session)
        record = _make_compliance_record(reqs_total=10, reqs_completed=8)

        mock_db.query.return_value.group_by.return_value.subquery.return_value = MagicMock()
        mock_db.query.return_value.join.return_value.all.return_value = [record]

        result = calculate_compliance_summary(mock_db)
        assert result["compliance_trend"] == "improving"

    def test_trend_critical(self):
        """Completion < 30% → critical."""
        mock_db = MagicMock(spec=Session)
        record = _make_compliance_record(reqs_total=10, reqs_completed=2)

        mock_db.query.return_value.group_by.return_value.subquery.return_value = MagicMock()
        mock_db.query.return_value.join.return_value.all.return_value = [record]

        result = calculate_compliance_summary(mock_db)
        assert result["compliance_trend"] == "critical"

    def test_trend_declining(self):
        """30% <= completion < 50% → declining."""
        mock_db = MagicMock(spec=Session)
        record = _make_compliance_record(reqs_total=10, reqs_completed=4)

        mock_db.query.return_value.group_by.return_value.subquery.return_value = MagicMock()
        mock_db.query.return_value.join.return_value.all.return_value = [record]

        result = calculate_compliance_summary(mock_db)
        assert result["compliance_trend"] == "declining"

    def test_trend_stable(self):
        """50% <= completion < 70% → stable."""
        mock_db = MagicMock(spec=Session)
        record = _make_compliance_record(reqs_total=10, reqs_completed=6)

        mock_db.query.return_value.group_by.return_value.subquery.return_value = MagicMock()
        mock_db.query.return_value.join.return_value.all.return_value = [record]

        result = calculate_compliance_summary(mock_db)
        assert result["compliance_trend"] == "stable"

    def test_critical_gaps_aggregated(self):
        """Should sum critical gaps across tenants."""
        mock_db = MagicMock(spec=Session)
        r1 = _make_compliance_record(tenant_id="t-1", critical_gaps=2)
        r2 = _make_compliance_record(tenant_id="t-2", critical_gaps=3)

        mock_db.query.return_value.group_by.return_value.subquery.return_value = MagicMock()
        mock_db.query.return_value.join.return_value.all.return_value = [r1, r2]

        result = calculate_compliance_summary(mock_db)
        assert result["total_critical_gaps"] == 5


# ---------------------------------------------------------------------------
# analyze_mfa_gaps
# ---------------------------------------------------------------------------


class TestAnalyzeMFAGaps:
    """Tests for analyze_mfa_gaps function."""

    def test_no_data_raises_value_error(self):
        """Should raise ValueError when no MFA data exists."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.group_by.return_value.subquery.return_value = MagicMock()
        mock_db.query.return_value.join.return_value.all.return_value = []

        with pytest.raises(ValueError, match="No MFA data"):
            analyze_mfa_gaps(mock_db)

    def test_single_tenant_calculation(self):
        """Should calculate correct percentages for single tenant."""
        mock_db = MagicMock(spec=Session)
        rec = _make_mfa_record(total_users=100, mfa_enrolled=80, admin_total=10, admin_mfa=10)

        mock_db.query.return_value.group_by.return_value.subquery.return_value = MagicMock()
        mock_db.query.return_value.join.return_value.all.return_value = [rec]

        result = analyze_mfa_gaps(mock_db)

        assert result["total_users"] == 100
        assert result["total_unprotected_users"] == 20
        assert result["overall_coverage_percentage"] == 80.0
        assert result["coverage_gap_percentage"] == 20.0
        assert result["admin_coverage_percentage"] == 100.0

    def test_high_risk_tenant_identification(self):
        """Tenants with < 50% coverage should be high-risk."""
        mock_db = MagicMock(spec=Session)
        rec = _make_mfa_record(total_users=100, mfa_enrolled=30)

        mock_db.query.return_value.group_by.return_value.subquery.return_value = MagicMock()
        mock_db.query.return_value.join.return_value.all.return_value = [rec]

        result = analyze_mfa_gaps(mock_db)

        assert result["high_risk_count"] >= 1
        assert len(result["high_risk_tenants"]) >= 1

    def test_recommendations_critical_coverage(self):
        """Coverage < 50% should generate CRITICAL recommendation."""
        mock_db = MagicMock(spec=Session)
        rec = _make_mfa_record(total_users=100, mfa_enrolled=40)

        mock_db.query.return_value.group_by.return_value.subquery.return_value = MagicMock()
        mock_db.query.return_value.join.return_value.all.return_value = [rec]

        result = analyze_mfa_gaps(mock_db)

        assert any("CRITICAL" in r for r in result["recommendations"])

    def test_recommendations_admin_coverage(self):
        """Admin coverage < 100% should generate URGENT recommendation."""
        mock_db = MagicMock(spec=Session)
        rec = _make_mfa_record(admin_total=10, admin_mfa=8)

        mock_db.query.return_value.group_by.return_value.subquery.return_value = MagicMock()
        mock_db.query.return_value.join.return_value.all.return_value = [rec]

        result = analyze_mfa_gaps(mock_db)

        assert any("URGENT" in r or "admin" in r.lower() for r in result["recommendations"])

    def test_tenant_breakdown_present(self):
        """Result should include per-tenant breakdown."""
        mock_db = MagicMock(spec=Session)
        rec = _make_mfa_record()

        mock_db.query.return_value.group_by.return_value.subquery.return_value = MagicMock()
        mock_db.query.return_value.join.return_value.all.return_value = [rec]

        result = analyze_mfa_gaps(mock_db)

        assert len(result["tenant_breakdown"]) == 1
        assert "coverage_percentage" in result["tenant_breakdown"][0]
        assert "risk_level" in result["tenant_breakdown"][0]

    def test_risk_level_assignment_critical(self):
        """Coverage < 50% → critical risk level."""
        mock_db = MagicMock(spec=Session)
        rec = _make_mfa_record(total_users=100, mfa_enrolled=30)

        mock_db.query.return_value.group_by.return_value.subquery.return_value = MagicMock()
        mock_db.query.return_value.join.return_value.all.return_value = [rec]

        result = analyze_mfa_gaps(mock_db)
        assert result["tenant_breakdown"][0]["risk_level"] == "critical"

    def test_risk_level_assignment_high(self):
        """50% <= coverage < 75% → high risk level."""
        mock_db = MagicMock(spec=Session)
        rec = _make_mfa_record(total_users=100, mfa_enrolled=60)

        mock_db.query.return_value.group_by.return_value.subquery.return_value = MagicMock()
        mock_db.query.return_value.join.return_value.all.return_value = [rec]

        result = analyze_mfa_gaps(mock_db)
        assert result["tenant_breakdown"][0]["risk_level"] == "high"

    def test_risk_level_assignment_medium(self):
        """Coverage >= 75% → medium risk level."""
        mock_db = MagicMock(spec=Session)
        rec = _make_mfa_record(total_users=100, mfa_enrolled=80)

        mock_db.query.return_value.group_by.return_value.subquery.return_value = MagicMock()
        mock_db.query.return_value.join.return_value.all.return_value = [rec]

        result = analyze_mfa_gaps(mock_db)
        assert result["tenant_breakdown"][0]["risk_level"] == "medium"
