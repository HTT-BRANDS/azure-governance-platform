"""Unit tests for MFA compliance preflight checks.

Tests the check classes and helper functions in
app/preflight/mfa_checks.py.

Traces: PF-005, PF-006 — MFA tenant data availability, admin enrollment,
user enrollment, gap reporting checks.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.preflight.mfa_checks import (
    MFAAdminEnrollmentCheck,
    MFAGapReportCheck,
    MFATenantDataCheck,
    MFAUserEnrollmentCheck,
    SeverityLevel,
    get_mfa_checks,
)
from app.preflight.models import CheckCategory, CheckStatus

# ---------------------------------------------------------------------------
# SeverityLevel
# ---------------------------------------------------------------------------


class TestSeverityLevel:
    """Tests for the SeverityLevel class."""

    def test_critical(self):
        assert SeverityLevel.CRITICAL == "critical"

    def test_warning(self):
        assert SeverityLevel.WARNING == "warning"

    def test_info(self):
        assert SeverityLevel.INFO == "info"

    def test_is_str_subclass(self):
        assert isinstance(SeverityLevel.CRITICAL, str)


# ---------------------------------------------------------------------------
# Check Class Initialization
# ---------------------------------------------------------------------------


class TestMFACheckInitialization:
    """Tests for MFA check class constructors."""

    def test_tenant_data_check(self):
        check = MFATenantDataCheck()
        assert check.check_id == "mfa_tenant_data"
        assert check.name == "MFA Tenant Data Availability"
        assert check.category == CheckCategory.MFA_COMPLIANCE
        assert check.timeout_seconds == 15.0

    def test_admin_enrollment_check(self):
        check = MFAAdminEnrollmentCheck()
        assert check.check_id == "mfa_admin_enrollment"
        assert check.name == "MFA Admin Enrollment Compliance"
        assert check.category == CheckCategory.MFA_COMPLIANCE

    def test_user_enrollment_check(self):
        check = MFAUserEnrollmentCheck()
        assert check.check_id == "mfa_user_enrollment"
        assert check.name == "MFA User Enrollment Compliance"
        assert check.category == CheckCategory.MFA_COMPLIANCE

    def test_gap_report_check(self):
        check = MFAGapReportCheck()
        assert check.check_id == "mfa_gap_report"
        assert check.name == "MFA Gap Analysis Report"
        assert check.category == CheckCategory.MFA_COMPLIANCE


# ---------------------------------------------------------------------------
# get_mfa_checks
# ---------------------------------------------------------------------------


class TestGetMFAChecks:
    """Tests for get_mfa_checks factory function."""

    def test_returns_dict(self):
        checks = get_mfa_checks()
        assert isinstance(checks, dict)

    def test_contains_all_checks(self):
        checks = get_mfa_checks()
        assert "mfa_tenant_data" in checks
        assert "mfa_admin_enrollment" in checks
        assert "mfa_user_enrollment" in checks
        assert "mfa_gap_report" in checks

    def test_check_count(self):
        checks = get_mfa_checks()
        assert len(checks) == 4

    def test_values_are_check_instances(self):
        checks = get_mfa_checks()
        assert isinstance(checks["mfa_tenant_data"], MFATenantDataCheck)
        assert isinstance(checks["mfa_admin_enrollment"], MFAAdminEnrollmentCheck)


# ---------------------------------------------------------------------------
# MFATenantDataCheck execution
# ---------------------------------------------------------------------------


class TestMFATenantDataCheckExecution:
    """Tests for MFATenantDataCheck._execute_check."""

    @pytest.mark.asyncio
    async def test_no_data_returns_fail(self):
        """When no MFA data exists, should return FAIL."""
        check = MFATenantDataCheck()
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.order_by.return_value.first.return_value = None
        mock_query.count.return_value = 0
        mock_query.filter.return_value = mock_query
        mock_db.query.return_value = mock_query

        with patch("app.preflight.mfa_checks.SessionLocal", return_value=mock_db):
            result = await check._execute_check(tenant_id="t-001")

        assert result.status == CheckStatus.FAIL
        assert "No MFA data" in result.message
        assert result.details["severity"] == SeverityLevel.CRITICAL

    @pytest.mark.asyncio
    async def test_db_exception_returns_fail(self):
        """When DB raises an error, should return FAIL with error details."""
        check = MFATenantDataCheck()

        with patch("app.preflight.mfa_checks.SessionLocal", side_effect=Exception("DB down")):
            result = await check._execute_check(tenant_id="t-001")

        assert result.status == CheckStatus.FAIL
        assert "failed" in result.message.lower()
