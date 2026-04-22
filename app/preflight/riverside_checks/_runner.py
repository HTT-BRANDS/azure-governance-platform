"""Aggregators for the riverside preflight checks package.

Split from the monolithic app/preflight/riverside_checks.py
(issue 6oj7, 2026-04-22).
"""

from app.preflight.base import BasePreflightCheck
from app.preflight.models import CheckResult, CheckStatus
from app.preflight.riverside_checks.api_endpoint import RiversideAPIEndpointCheck
from app.preflight.riverside_checks.azure_ad_permissions import RiversideAzureADPermissionsCheck
from app.preflight.riverside_checks.database import RiversideDatabaseCheck
from app.preflight.riverside_checks.evidence import RiversideEvidenceCheck
from app.preflight.riverside_checks.mfa_data_source import RiversideMFADataSourceCheck
from app.preflight.riverside_checks.scheduler import RiversideSchedulerCheck


async def run_all_riverside_checks(tenant_id: str | None = None) -> list[CheckResult]:
    """Run all Riverside preflight checks.

    Args:
        tenant_id: Optional tenant ID for tenant-specific checks

    Returns:
        List of CheckResults from all Riverside checks
    """
    checks = [
        RiversideDatabaseCheck(),
        RiversideAPIEndpointCheck(),
        RiversideSchedulerCheck(),
        RiversideAzureADPermissionsCheck(),
        RiversideMFADataSourceCheck(),
        RiversideEvidenceCheck(),
    ]

    results = []
    for check in checks:
        try:
            result = await check.run(tenant_id=tenant_id)
            results.append(result)
        except Exception as e:
            # If a check fails completely, create a failed result
            results.append(
                CheckResult(
                    check_id=check.check_id,
                    name=check.name,
                    category=check.category,
                    status=CheckStatus.FAIL,
                    message=f"Check failed with exception: {str(e)}",
                    details={"error_type": type(e).__name__},
                    recommendations=["Review application logs for details"],
                    tenant_id=tenant_id,
                )
            )

    return results


def get_riverside_checks() -> dict[str, BasePreflightCheck]:
    """Get all Riverside preflight checks.

    Returns:
        Dictionary mapping check_id to check instance
    """
    checks = [
        RiversideDatabaseCheck(),
        RiversideAPIEndpointCheck(),
        RiversideSchedulerCheck(),
        RiversideAzureADPermissionsCheck(),
        RiversideMFADataSourceCheck(),
        RiversideEvidenceCheck(),
    ]

    return {check.check_id: check for check in checks}
