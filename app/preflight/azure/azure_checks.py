"""Azure-specific preflight checks for governance platform.

This module provides comprehensive validation of Azure tenant connectivity,
API access, and required permissions. Each check function is designed to
be self-contained, async-friendly, and provide actionable error messages.

Two API styles are provided:
1. **Class-based checks** - For integration with PreflightRunner
2. **Function-based checks** - Direct async functions for specific use cases

Example:
    >>> # Using function-based API
    >>> from app.preflight.azure.azure_checks import run_all_azure_checks
    >>> results = await run_all_azure_checks("12345678-1234-1234-1234-123456789012")
    >>>
    >>> # Using class-based API
    >>> from app.preflight.azure.identity import AzureAuthCheck
    >>> check = AzureAuthCheck()
    >>> result = await check.run(tenant_id="12345678-1234-1234-1234-123456789012")

This module re-exports all check classes and functions from the modular
sub-packages for backward compatibility.
"""

import asyncio
import logging
import time
from datetime import UTC, datetime
from typing import Any

from app.preflight.models import CheckCategory, CheckResult, CheckStatus

# Import all check classes and functions from modular sub-packages
from app.preflight.azure.identity import (
    AzureAuthCheck,
    check_azure_authentication,
)
from app.preflight.azure.network import (
    AzureSubscriptionsCheck,
    AzureGraphCheck,
    check_azure_subscriptions,
    check_graph_api_access,
)
from app.preflight.azure.compute import (
    AzureResourcesCheck,
    check_resource_manager_access,
)
from app.preflight.azure.storage import (
    AzureCostManagementCheck,
    AzurePolicyCheck,
    check_cost_management_access,
    check_policy_access,
)
from app.preflight.azure.security import (
    AzureSecurityCheck,
    AzureRBACCheck,
    check_security_center_access,
    check_rbac_permissions,
)
from app.preflight.azure.base import (
    AzureCheckError,
    REQUIRED_GRAPH_PERMISSIONS,
    REQUIRED_AZURE_ROLES,
)

logger = logging.getLogger(__name__)


async def run_all_azure_checks(
    tenant_id: str, subscription_id: str | None = None
) -> list[CheckResult]:
    """Run all Azure checks for a tenant in parallel.

    Executes all preflight checks concurrently for efficiency. If a subscription_id
    is provided, subscription-specific checks are run against that subscription.
    Otherwise, only tenant-level checks are performed.

    Args:
        tenant_id: Azure AD tenant ID to check
        subscription_id: Optional subscription ID for subscription-scoped checks

    Returns:
        List of CheckResult objects for all executed checks

    Example:
        >>> results = await run_all_azure_checks(
        ...     tenant_id="12345678-1234-1234-1234-123456789012",
        ...     subscription_id="87654321-4321-4321-4321-210987654321"
        ... )
        >>> failed = [r for r in results if r.status == CheckStatus.FAIL]
        >>> print(f"Failed checks: {len(failed)}")
    """
    start_time = time.perf_counter()
    logger.info(f"Starting preflight checks for tenant {tenant_id[:8]}...")

    results: list[CheckResult] = []

    # Always run tenant-level checks
    tenant_checks = [
        check_azure_authentication(tenant_id),
        check_azure_subscriptions(tenant_id),
        check_graph_api_access(tenant_id),
    ]

    # Run tenant checks concurrently
    tenant_results = await asyncio.gather(*tenant_checks, return_exceptions=True)

    for result in tenant_results:
        if isinstance(result, Exception):
            logger.error(f"Check failed with exception: {result}")
            results.append(
                CheckResult(
                    check_id="unknown",
                    name="Unknown Check",
                    category=CheckCategory.AZURE_AUTH,
                    status=CheckStatus.FAIL,
                    message=f"Check failed with exception: {type(result).__name__}",
                    details={"error": str(result)},
                    duration_ms=0.0,
                    timestamp=datetime.now(UTC),
                    recommendations=["Check application logs for details"],
                )
            )
        else:
            results.append(result)

    # If we have a subscription ID, run subscription-scoped checks
    if subscription_id:
        logger.info(f"Running subscription-scoped checks for {subscription_id[:8]}...")

        sub_checks = [
            check_cost_management_access(tenant_id, subscription_id),
            check_policy_access(tenant_id, subscription_id),
            check_resource_manager_access(tenant_id, subscription_id),
            check_security_center_access(tenant_id, subscription_id),
            check_rbac_permissions(tenant_id, subscription_id),
        ]

        sub_results = await asyncio.gather(*sub_checks, return_exceptions=True)

        for result in sub_results:
            if isinstance(result, Exception):
                logger.error(f"Subscription check failed with exception: {result}")
                results.append(
                    CheckResult(
                        check_id="unknown",
                        name="Unknown Check",
                        category=CheckCategory.AZURE_RESOURCES,
                        status=CheckStatus.FAIL,
                        message=f"Check failed with exception: {type(result).__name__}",
                        details={"error": str(result)},
                        duration_ms=0.0,
                        timestamp=datetime.now(UTC),
                        recommendations=["Check application logs for details"],
                    )
                )
            else:
                results.append(result)

    total_duration = (time.perf_counter() - start_time) * 1000
    logger.info(
        f"Completed {len(results)} preflight checks in {total_duration:.0f}ms "
        f"for tenant {tenant_id[:8]}..."
    )

    return results


# Export all check classes and functions for backward compatibility
__all__ = [
    # Class-based checks
    "AzureAuthCheck",
    "AzureSubscriptionsCheck",
    "AzureCostManagementCheck",
    "AzureGraphCheck",
    "AzurePolicyCheck",
    "AzureResourcesCheck",
    "AzureSecurityCheck",
    "AzureRBACCheck",
    # Function-based checks
    "check_azure_authentication",
    "check_azure_subscriptions",
    "check_cost_management_access",
    "check_graph_api_access",
    "check_policy_access",
    "check_resource_manager_access",
    "check_rbac_permissions",
    "check_security_center_access",
    "run_all_azure_checks",
    # Error class
    "AzureCheckError",
    # Constants
    "REQUIRED_GRAPH_PERMISSIONS",
    "REQUIRED_AZURE_ROLES",
]
