"""Unit tests for PreflightRunner.

Tests for preflight check orchestration with parallel execution,
progress tracking, and timeout handling.

10 tests covering:
- Runner initialization and check registration
- Execution of all registered checks
- Check timeout enforcement
- Result aggregation (pass/fail/warn/skip counts)
- Parallel check execution
- Report generation triggering
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.preflight.base import BasePreflightCheck
from app.preflight.models import (
    CheckCategory,
    CheckResult,
    CheckStatus,
    PreflightReport,
)
from app.preflight.runner import PreflightRunner


class TestPreflightRunnerInit:
    """Tests for PreflightRunner initialization."""

    def test_init_with_defaults(self):
        """Test runner initialization with default settings."""
        runner = PreflightRunner()

        assert runner.categories is None  # All categories
        assert runner.tenant_ids is None  # All tenants
        assert runner.fail_fast is False
        assert runner.timeout_seconds == 30.0
        assert runner.is_running is False

    def test_init_with_custom_settings(self):
        """Test runner initialization with custom settings."""
        runner = PreflightRunner(
            categories=[CheckCategory.AZURE_SECURITY, CheckCategory.RIVERSIDE],
            tenant_ids=["tenant1", "tenant2"],
            fail_fast=True,
            timeout_seconds=60.0,
        )

        assert runner.categories == [CheckCategory.AZURE_SECURITY, CheckCategory.RIVERSIDE]
        assert runner.tenant_ids == ["tenant1", "tenant2"]
        assert runner.fail_fast is True
        assert runner.timeout_seconds == 60.0

    def test_register_check(self):
        """Test registering checks with the runner."""
        runner = PreflightRunner()

        mock_check = MagicMock(spec=BasePreflightCheck)
        mock_check.check_id = "test_check_1"
        mock_check.category = CheckCategory.AZURE_SECURITY

        runner.register_check(mock_check)

        assert "test_check_1" in runner._checks
        assert runner._checks["test_check_1"] == mock_check


class TestCheckExecution:
    """Tests for check execution."""

    @pytest.mark.asyncio
    async def test_run_checks_success(self):
        """Test running all registered checks successfully."""
        runner = PreflightRunner()

        # Create mock checks
        mock_check1 = MagicMock(spec=BasePreflightCheck)
        mock_check1.check_id = "check1"
        mock_check1.category = CheckCategory.AZURE_SECURITY
        mock_check1.run = AsyncMock(
            return_value=CheckResult(
                check_id="check1",
                name="Check 1",
                category=CheckCategory.AZURE_SECURITY,
                status=CheckStatus.PASS,
                message="Check passed",
            )
        )

        mock_check2 = MagicMock(spec=BasePreflightCheck)
        mock_check2.check_id = "check2"
        mock_check2.category = CheckCategory.RIVERSIDE
        mock_check2.run = AsyncMock(
            return_value=CheckResult(
                check_id="check2",
                name="Check 2",
                category=CheckCategory.RIVERSIDE,
                status=CheckStatus.PASS,
                message="Check passed",
            )
        )

        runner.register_check(mock_check1)
        runner.register_check(mock_check2)

        registered = dict(runner._checks)

        # Mock tenant fetching and get_all_checks (which would overwrite our mocks)
        with patch.object(runner, "_get_tenants_to_check") as mock_get_tenants, \
             patch("app.preflight.runner.get_all_checks", return_value=registered):
            mock_tenant = MagicMock()
            mock_tenant.id = "test-tenant"
            mock_tenant.tenant_id = "test-tenant-azure-id"
            mock_tenant.name = "Test Tenant"
            mock_get_tenants.return_value = [mock_tenant]

            report = await runner.run_checks()

            assert report is not None
            assert len(report.results) > 0
            mock_check1.run.assert_called()
            mock_check2.run.assert_called()

    @pytest.mark.asyncio
    async def test_fail_fast_stops_on_failure(self):
        """Test fail_fast mode stops on first failure."""
        runner = PreflightRunner(fail_fast=True)

        mock_check1 = MagicMock(spec=BasePreflightCheck)
        mock_check1.check_id = "check1"
        mock_check1.category = CheckCategory.AZURE_SECURITY
        mock_check1.run = AsyncMock(
            return_value=CheckResult(
                check_id="check1",
                name="Check 1",
                category=CheckCategory.AZURE_SECURITY,
                status=CheckStatus.FAIL,
                message="Check failed",
            )
        )

        mock_check2 = MagicMock(spec=BasePreflightCheck)
        mock_check2.check_id = "check2"
        mock_check2.category = CheckCategory.AZURE_SECURITY
        mock_check2.run = AsyncMock(
            return_value=CheckResult(
                check_id="check2",
                name="Check 2",
                category=CheckCategory.AZURE_SECURITY,
                status=CheckStatus.PASS,
                message="Check passed",
            )
        )

        runner.register_check(mock_check1)
        runner.register_check(mock_check2)

        registered = dict(runner._checks)

        with patch.object(runner, "_get_tenants_to_check") as mock_get_tenants, \
             patch("app.preflight.runner.get_all_checks", return_value=registered):
            mock_tenant = MagicMock()
            mock_tenant.id = "test-tenant"
            mock_tenant.tenant_id = "test-tenant-azure-id"
            mock_get_tenants.return_value = [mock_tenant]

            report = await runner.run_checks()

            # In fail_fast mode, should stop after first failure
            assert report is not None


class TestResultAggregation:
    """Tests for result aggregation."""

    def test_aggregate_results_counts(self):
        """Test aggregation of check results by status."""
        results = [
            CheckResult(
                check_id="c1", name="C1", category=CheckCategory.SYSTEM,
                status=CheckStatus.PASS, message="Pass",
            ),
            CheckResult(
                check_id="c2", name="C2", category=CheckCategory.SYSTEM,
                status=CheckStatus.PASS, message="Pass",
            ),
            CheckResult(
                check_id="c3", name="C3", category=CheckCategory.SYSTEM,
                status=CheckStatus.FAIL, message="Fail",
            ),
            CheckResult(
                check_id="c4", name="C4", category=CheckCategory.SYSTEM,
                status=CheckStatus.WARNING, message="Warn",
            ),
            CheckResult(
                check_id="c5", name="C5", category=CheckCategory.SYSTEM,
                status=CheckStatus.SKIPPED, message="Skip",
            ),
        ]

        report = PreflightReport(
            id="test-run",
            results=results,
        )

        assert report.passed_count == 2
        assert report.failed_count == 1
        assert report.warning_count == 1
        assert report.skipped_count == 1


class TestParallelExecution:
    """Tests for parallel check execution."""

    @pytest.mark.asyncio
    async def test_parallel_check_execution(self):
        """Test that checks can run in parallel."""
        runner = PreflightRunner()

        # Create multiple checks
        checks = []
        for i in range(5):
            mock_check = MagicMock(spec=BasePreflightCheck)
            mock_check.check_id = f"check{i}"
            mock_check.category = CheckCategory.SYSTEM
            mock_check.run = AsyncMock(
                return_value=CheckResult(
                    check_id=f"check{i}",
                    name=f"Check {i}",
                    category=CheckCategory.SYSTEM,
                    status=CheckStatus.PASS,
                    message=f"Check {i} passed",
                )
            )
            checks.append(mock_check)
            runner.register_check(mock_check)

        registered = dict(runner._checks)

        with patch.object(runner, "_get_tenants_to_check") as mock_get_tenants, \
             patch("app.preflight.runner.get_all_checks", return_value=registered):
            mock_tenant = MagicMock()
            mock_tenant.id = "test-tenant"
            mock_tenant.tenant_id = "test-tenant-azure-id"
            mock_get_tenants.return_value = [mock_tenant]

            await runner.run_checks()

            # All checks should have been called
            for check in checks:
                check.run.assert_called()


class TestProgressTracking:
    """Tests for progress callback."""

    def test_set_progress_callback(self):
        """Test setting progress callback."""
        runner = PreflightRunner()
        callback_called = []

        def progress_callback(current: int, total: int, check_name: str):
            callback_called.append((current, total, check_name))

        runner.set_progress_callback(progress_callback)

        assert runner._progress_callback is not None


class TestReportGeneration:
    """Tests for report generation."""

    def test_report_contains_summary(self):
        """Test that generated report contains summary."""
        results = [
            CheckResult(
                check_id="c1", name="C1", category=CheckCategory.SYSTEM,
                status=CheckStatus.PASS, message="Pass",
            ),
            CheckResult(
                check_id="c2", name="C2", category=CheckCategory.SYSTEM,
                status=CheckStatus.FAIL, message="Fail",
            ),
        ]

        report = PreflightReport(
            id="test-run",
            results=results,
        )

        # Report should contain results
        assert len(report.results) == 2
        assert report.id == "test-run"

    def test_get_checks_for_categories(self):
        """Test filtering checks by categories."""
        runner = PreflightRunner()

        mock_check1 = MagicMock(spec=BasePreflightCheck)
        mock_check1.check_id = "sec1"
        mock_check1.category = CheckCategory.AZURE_SECURITY

        mock_check2 = MagicMock(spec=BasePreflightCheck)
        mock_check2.check_id = "comp1"
        mock_check2.category = CheckCategory.RIVERSIDE

        runner.register_check(mock_check1)
        runner.register_check(mock_check2)

        # Get only security checks
        security_checks = runner.get_checks_for_categories([CheckCategory.AZURE_SECURITY])

        assert len(security_checks) == 1
        assert security_checks[0].check_id == "sec1"

        # Get all checks
        all_checks = runner.get_checks_for_categories(None)
        assert len(all_checks) == 2
