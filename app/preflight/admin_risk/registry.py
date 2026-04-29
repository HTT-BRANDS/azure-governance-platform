"""Strategy registry and orchestration for admin risk checks."""

from collections.abc import Iterable

from app.preflight.admin_risk.compliance import AdminComplianceGapCheck
from app.preflight.admin_risk.inactive import InactiveAdminCheck
from app.preflight.admin_risk.mfa import AdminMfaCheck
from app.preflight.admin_risk.overprivileged import OverprivilegedAccountCheck
from app.preflight.admin_risk.shared import SharedAdminCheck
from app.preflight.base import BasePreflightCheck
from app.preflight.models import CheckResult

AdminRiskCheckStrategy = type[BasePreflightCheck]

ADMIN_RISK_CHECK_STRATEGIES: tuple[AdminRiskCheckStrategy, ...] = (
    AdminMfaCheck,
    OverprivilegedAccountCheck,
    InactiveAdminCheck,
    SharedAdminCheck,
    AdminComplianceGapCheck,
)


def build_admin_risk_checks(
    strategies: Iterable[AdminRiskCheckStrategy] = ADMIN_RISK_CHECK_STRATEGIES,
) -> dict[str, BasePreflightCheck]:
    """Build admin risk check instances from strategy classes."""
    checks = [strategy() for strategy in strategies]
    return {check.check_id: check for check in checks}


def get_admin_risk_checks() -> dict[str, BasePreflightCheck]:
    """Get all admin risk check instances."""
    return build_admin_risk_checks()


async def run_all_admin_risk_checks(tenant_id: str | None = None) -> list[CheckResult]:
    """Run all admin risk checks."""
    results = []

    for check in get_admin_risk_checks().values():
        result = await check.run(tenant_id=tenant_id)
        results.append(result)

    return results
