"""Unit tests for Riverside-specific preflight checks.

Tests the check classes and factory functions in
app/preflight/riverside_checks.py.

Traces: PF-007, PF-008 — Riverside database connectivity, API endpoints,
scheduler, Azure AD permissions, evidence, and MFA data source checks.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.preflight.models import CheckCategory, CheckStatus
from app.preflight.riverside_checks import (
    RiversideAPIEndpointCheck,
    RiversideAzureADPermissionsCheck,
    RiversideDatabaseCheck,
    RiversideEvidenceCheck,
    RiversideMFADataSourceCheck,
    RiversideSchedulerCheck,
    SeverityLevel,
    get_riverside_checks,
)


# ---------------------------------------------------------------------------
# SeverityLevel
# ---------------------------------------------------------------------------


class TestSeverityLevel:
    """Tests for the Riverside SeverityLevel class."""

    def test_critical(self):
        assert SeverityLevel.CRITICAL == "critical"

    def test_warning(self):
        assert SeverityLevel.WARNING == "warning"

    def test_info(self):
        assert SeverityLevel.INFO == "info"


# ---------------------------------------------------------------------------
# Check Class Initialization
# ---------------------------------------------------------------------------


class TestRiversideCheckInitialization:
    """Tests for Riverside check class constructors."""

    def test_database_check(self):
        check = RiversideDatabaseCheck()
        assert check.check_id == "riverside_database_connectivity"
        assert check.name == "Riverside Database Connectivity"
        assert check.category == CheckCategory.RIVERSIDE

    def test_api_endpoint_check(self):
        check = RiversideAPIEndpointCheck()
        assert check.check_id == "riverside_api_endpoints"
        assert check.name == "Riverside API Endpoint Availability"
        assert check.category == CheckCategory.RIVERSIDE

    def test_scheduler_check(self):
        check = RiversideSchedulerCheck()
        assert check.check_id == "riverside_scheduler"
        assert check.name == "Riverside Scheduler Job Registration"
        assert check.category == CheckCategory.RIVERSIDE

    def test_azure_ad_permissions_check(self):
        check = RiversideAzureADPermissionsCheck()
        assert check.check_id == "riverside_azure_ad_permissions"
        assert check.category == CheckCategory.RIVERSIDE

    def test_evidence_check(self):
        check = RiversideEvidenceCheck()
        assert check.check_id == "riverside_requirement_evidence"
        assert check.category == CheckCategory.RIVERSIDE

    def test_mfa_data_source_check(self):
        check = RiversideMFADataSourceCheck()
        assert check.check_id == "riverside_mfa_data_source"
        assert check.category == CheckCategory.RIVERSIDE


# ---------------------------------------------------------------------------
# get_riverside_checks
# ---------------------------------------------------------------------------


class TestGetRiversideChecks:
    """Tests for get_riverside_checks factory function."""

    def test_returns_dict(self):
        checks = get_riverside_checks()
        assert isinstance(checks, dict)

    def test_contains_all_6_checks(self):
        checks = get_riverside_checks()
        assert len(checks) == 6

    def test_expected_check_ids(self):
        checks = get_riverside_checks()
        expected_ids = {
            "riverside_database_connectivity",
            "riverside_api_endpoints",
            "riverside_scheduler",
            "riverside_azure_ad_permissions",
            "riverside_requirement_evidence",
            "riverside_mfa_data_source",
        }
        assert set(checks.keys()) == expected_ids

    def test_all_are_riverside_category(self):
        for check in get_riverside_checks().values():
            assert check.category == CheckCategory.RIVERSIDE


# ---------------------------------------------------------------------------
# RiversideDatabaseCheck execution
# ---------------------------------------------------------------------------


class TestRiversideDatabaseCheckExecution:
    """Tests for RiversideDatabaseCheck._execute_check."""

    @pytest.mark.asyncio
    async def test_db_exception_returns_fail(self):
        """When SessionLocal() raises, should return FAIL."""
        check = RiversideDatabaseCheck()

        with patch(
            "app.preflight.riverside_checks.SessionLocal",
            side_effect=Exception("Connection refused"),
        ):
            result = await check._execute_check(tenant_id=None)

        assert result.status == CheckStatus.FAIL
        assert "error" in result.message.lower() or "fail" in result.message.lower()


# ---------------------------------------------------------------------------
# Check __repr__
# ---------------------------------------------------------------------------


class TestRiversideCheckRepr:
    """Tests for __repr__ on check classes."""

    def test_database_check_repr(self):
        check = RiversideDatabaseCheck()
        r = repr(check)
        assert "RiversideDatabaseCheck" in r
        assert "riverside_database_connectivity" in r

    def test_scheduler_check_repr(self):
        check = RiversideSchedulerCheck()
        r = repr(check)
        assert "RiversideSchedulerCheck" in r
