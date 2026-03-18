"""Unit tests for preflight check models.

Tests the Pydantic models and enums in app/preflight/models.py.

Traces: PF-001, PF-002 — Preflight check result models, report
aggregation, and status enums.
"""

from datetime import datetime
from enum import StrEnum

from app.preflight.models import (
    CategorySummary,
    CheckCategory,
    CheckResult,
    CheckStatus,
    PreflightCheckRequest,
    PreflightReport,
    PreflightStatusResponse,
    TenantCheckSummary,
)

# ---------------------------------------------------------------------------
# CheckStatus enum
# ---------------------------------------------------------------------------


class TestCheckStatus:
    """Tests for CheckStatus StrEnum."""

    def test_is_str_enum(self):
        assert issubclass(CheckStatus, StrEnum)

    def test_member_count(self):
        assert len(CheckStatus) == 5

    def test_values(self):
        assert CheckStatus.PASS == "pass"
        assert CheckStatus.WARNING == "warning"
        assert CheckStatus.FAIL == "fail"
        assert CheckStatus.SKIPPED == "skipped"
        assert CheckStatus.RUNNING == "running"


# ---------------------------------------------------------------------------
# CheckCategory enum
# ---------------------------------------------------------------------------


class TestCheckCategory:
    """Tests for CheckCategory StrEnum."""

    def test_is_str_enum(self):
        assert issubclass(CheckCategory, StrEnum)

    def test_has_azure_categories(self):
        azure_cats = [c for c in CheckCategory if c.value.startswith("azure_")]
        assert len(azure_cats) >= 6

    def test_has_riverside_category(self):
        assert CheckCategory.RIVERSIDE == "riverside"

    def test_has_mfa_category(self):
        assert CheckCategory.MFA_COMPLIANCE == "mfa_compliance"

    def test_has_database_category(self):
        assert CheckCategory.DATABASE == "database"


# ---------------------------------------------------------------------------
# CheckResult model
# ---------------------------------------------------------------------------


class TestCheckResult:
    """Tests for CheckResult Pydantic model."""

    def _make_result(self, status: CheckStatus = CheckStatus.PASS, **kwargs) -> CheckResult:
        defaults = {
            "check_id": "test_check",
            "name": "Test Check",
            "category": CheckCategory.SYSTEM,
            "status": status,
            "message": "All good",
        }
        defaults.update(kwargs)
        return CheckResult(**defaults)

    def test_valid_creation(self):
        r = self._make_result()
        assert r.check_id == "test_check"
        assert r.status == CheckStatus.PASS

    def test_defaults(self):
        r = self._make_result()
        assert r.details == {}
        assert r.duration_ms == 0
        assert r.recommendations == []
        assert r.tenant_id is None
        assert isinstance(r.timestamp, datetime)

    def test_is_pass(self):
        assert self._make_result(CheckStatus.PASS).is_pass() is True
        assert self._make_result(CheckStatus.FAIL).is_pass() is False

    def test_is_warning(self):
        assert self._make_result(CheckStatus.WARNING).is_warning() is True
        assert self._make_result(CheckStatus.PASS).is_warning() is False

    def test_is_fail(self):
        assert self._make_result(CheckStatus.FAIL).is_fail() is True
        assert self._make_result(CheckStatus.PASS).is_fail() is False

    def test_is_skipped(self):
        assert self._make_result(CheckStatus.SKIPPED).is_skipped() is True

    def test_is_success_pass(self):
        assert self._make_result(CheckStatus.PASS).is_success() is True

    def test_is_success_warning(self):
        assert self._make_result(CheckStatus.WARNING).is_success() is True

    def test_is_success_fail(self):
        assert self._make_result(CheckStatus.FAIL).is_success() is False

    def test_with_details_and_recommendations(self):
        r = self._make_result(
            details={"key": "value"},
            recommendations=["Fix this", "Check that"],
        )
        assert r.details["key"] == "value"
        assert len(r.recommendations) == 2

    def test_from_attributes_config(self):
        assert CheckResult.model_config.get("from_attributes") is True


# ---------------------------------------------------------------------------
# PreflightReport model
# ---------------------------------------------------------------------------


class TestPreflightReport:
    """Tests for PreflightReport Pydantic model."""

    def _make_report(self, results: list[CheckResult] | None = None) -> PreflightReport:
        return PreflightReport(id="report-001", results=results or [])

    def _pass_result(self) -> CheckResult:
        return CheckResult(
            check_id="c1",
            name="C1",
            category=CheckCategory.SYSTEM,
            status=CheckStatus.PASS,
            message="ok",
            duration_ms=10.0,
        )

    def _fail_result(self) -> CheckResult:
        return CheckResult(
            check_id="c2",
            name="C2",
            category=CheckCategory.DATABASE,
            status=CheckStatus.FAIL,
            message="bad",
            duration_ms=20.0,
            recommendations=["Fix the database"],
        )

    def _warning_result(self) -> CheckResult:
        return CheckResult(
            check_id="c3",
            name="C3",
            category=CheckCategory.SYSTEM,
            status=CheckStatus.WARNING,
            message="hmm",
            duration_ms=5.0,
        )

    def _skipped_result(self) -> CheckResult:
        return CheckResult(
            check_id="c4",
            name="C4",
            category=CheckCategory.AZURE_AUTH,
            status=CheckStatus.SKIPPED,
            message="skipped",
        )

    def test_empty_report(self):
        report = self._make_report()
        assert report.passed_count == 0
        assert report.failed_count == 0
        assert report.warning_count == 0
        assert report.skipped_count == 0
        assert report.is_success is True
        assert report.has_failures is False
        assert report.has_warnings is False

    def test_counts(self):
        report = self._make_report(
            [
                self._pass_result(),
                self._fail_result(),
                self._warning_result(),
                self._skipped_result(),
            ]
        )
        assert report.passed_count == 1
        assert report.failed_count == 1
        assert report.warning_count == 1
        assert report.skipped_count == 1

    def test_total_duration(self):
        report = self._make_report([self._pass_result(), self._fail_result()])
        assert report.total_duration_ms == 30.0

    def test_is_success_with_failure(self):
        report = self._make_report([self._pass_result(), self._fail_result()])
        assert report.is_success is False
        assert report.has_failures is True

    def test_is_success_with_warnings_only(self):
        report = self._make_report([self._pass_result(), self._warning_result()])
        assert report.is_success is True
        assert report.has_warnings is True

    def test_get_results_by_category(self):
        report = self._make_report(
            [
                self._pass_result(),
                self._fail_result(),
                self._warning_result(),
            ]
        )
        system_results = report.get_results_by_category(CheckCategory.SYSTEM)
        assert len(system_results) == 2

    def test_get_failed_checks(self):
        report = self._make_report([self._pass_result(), self._fail_result()])
        failed = report.get_failed_checks()
        assert len(failed) == 1
        assert failed[0].check_id == "c2"

    def test_get_all_recommendations(self):
        report = self._make_report([self._pass_result(), self._fail_result()])
        recs = report.get_all_recommendations()
        assert recs == ["Fix the database"]

    def test_get_summary(self):
        report = self._make_report([self._pass_result(), self._fail_result()])
        summary = report.get_summary()
        assert summary["id"] == "report-001"
        assert summary["passed"] == 1
        assert summary["failed"] == 1
        assert summary["total"] == 2
        assert summary["is_success"] is False


# ---------------------------------------------------------------------------
# PreflightCheckRequest model
# ---------------------------------------------------------------------------


class TestPreflightCheckRequest:
    """Tests for PreflightCheckRequest."""

    def test_default_request(self):
        req = PreflightCheckRequest()
        assert req.categories is None
        assert req.tenant_ids is None
        assert req.fail_fast is False
        assert req.timeout_seconds == 30.0

    def test_with_categories(self):
        req = PreflightCheckRequest(
            categories=[CheckCategory.AZURE_AUTH, CheckCategory.DATABASE],
        )
        assert len(req.categories) == 2

    def test_with_fail_fast(self):
        req = PreflightCheckRequest(fail_fast=True)
        assert req.fail_fast is True


# ---------------------------------------------------------------------------
# PreflightStatusResponse model
# ---------------------------------------------------------------------------


class TestPreflightStatusResponse:
    """Tests for PreflightStatusResponse."""

    def test_defaults(self):
        resp = PreflightStatusResponse()
        assert resp.latest_report is None
        assert resp.last_run_at is None
        assert resp.is_running is False


# ---------------------------------------------------------------------------
# TenantCheckSummary / CategorySummary
# ---------------------------------------------------------------------------


class TestTenantCheckSummary:
    """Tests for TenantCheckSummary."""

    def test_creation(self):
        summary = TenantCheckSummary(
            tenant_id="t-001",
            tenant_name="Test Tenant",
            checks_passed=5,
            checks_failed=1,
            checks_warning=2,
            checks_skipped=0,
            overall_status=CheckStatus.FAIL,
            results=[],
        )
        assert summary.tenant_id == "t-001"
        assert summary.overall_status == CheckStatus.FAIL


class TestCategorySummary:
    """Tests for CategorySummary."""

    def test_creation(self):
        summary = CategorySummary(
            category=CheckCategory.AZURE_AUTH,
            display_name="Azure Authentication",
            checks_passed=3,
            checks_failed=0,
            checks_warning=1,
            checks_skipped=0,
            overall_status=CheckStatus.WARNING,
        )
        assert summary.category == CheckCategory.AZURE_AUTH
        assert summary.display_name == "Azure Authentication"
