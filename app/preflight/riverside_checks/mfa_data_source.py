"""Riverside preflight check: RiversideMFADataSourceCheck.

Split from the monolithic app/preflight/riverside_checks.py
(issue 6oj7, 2026-04-22).
"""

import time

from app.core.config import get_settings
from app.preflight.base import BasePreflightCheck
from app.preflight.models import CheckCategory, CheckResult, CheckStatus
from app.preflight.riverside_checks._common import SeverityLevel


class RiversideMFADataSourceCheck(BasePreflightCheck):
    """Check MFA data source connectivity.

    Validates connectivity to the MFA data sources used by Riverside,
    including Microsoft Graph API for user MFA status and Azure AD
    authentication methods.
    """

    def __init__(self):
        super().__init__(
            check_id="riverside_mfa_data_source",
            name="Riverside MFA Data Source Connectivity",
            category=CheckCategory.RIVERSIDE,
            description="Verify MFA data source connectivity via Graph API",
            timeout_seconds=30.0,
        )

    async def _execute_check(self, tenant_id: str | None = None) -> CheckResult:
        """Execute MFA data source connectivity check."""
        start_time = time.perf_counter()
        settings = get_settings()

        try:
            from app.api.services.graph_client import GraphClient

            target_tenant_id = tenant_id or settings.azure_tenant_id

            if not target_tenant_id:
                duration_ms = (time.perf_counter() - start_time) * 1000
                return CheckResult(
                    check_id=self.check_id,
                    name=self.name,
                    category=self.category,
                    status=CheckStatus.FAIL,
                    message="No tenant ID available for MFA data source check",
                    details={
                        "severity": SeverityLevel.CRITICAL,
                    },
                    duration_ms=duration_ms,
                    recommendations=[
                        "Configure AZURE_TENANT_ID environment variable",
                        "Verify tenant configuration in the database",
                    ],
                    tenant_id=tenant_id,
                )

            client = GraphClient(target_tenant_id)

            # Test MFA data access by fetching users with authentication methods
            data_source_status = {}

            try:
                # Try to get users - basic connectivity test
                users = await client.get_users(limit=5)
                data_source_status["users_endpoint"] = {
                    "accessible": True,
                    "user_count": len(users) if users else 0,
                }

                # Try to get authentication methods for first user
                if users and len(users) > 0:
                    first_user = users[0]
                    user_id = first_user.get("id")

                    if user_id:
                        try:
                            # This requires UserAuthenticationMethod.Read.All permission
                            auth_methods = await client._make_request(
                                f"/users/{user_id}/authentication/methods"
                            )
                            data_source_status["authentication_methods"] = {
                                "accessible": True,
                                "methods_count": len(auth_methods.get("value", [])),
                            }
                        except Exception as e:
                            error_str = str(e).lower()
                            if "403" in error_str or "forbidden" in error_str:
                                data_source_status["authentication_methods"] = {
                                    "accessible": False,
                                    "reason": "permission_denied",
                                    "note": "UserAuthenticationMethod.Read.All permission required",
                                }
                            else:
                                data_source_status["authentication_methods"] = {
                                    "accessible": False,
                                    "reason": "error",
                                    "error": str(e)[:100],
                                }

            except Exception as e:
                error_str = str(e).lower()
                if "401" in error_str or "unauthorized" in error_str:
                    data_source_status["users_endpoint"] = {
                        "accessible": False,
                        "reason": "authentication_failed",
                    }
                elif "403" in error_str or "forbidden" in error_str:
                    data_source_status["users_endpoint"] = {
                        "accessible": False,
                        "reason": "permission_denied",
                    }
                else:
                    data_source_status["users_endpoint"] = {
                        "accessible": False,
                        "reason": "error",
                        "error": str(e)[:100],
                    }

            duration_ms = (time.perf_counter() - start_time) * 1000

            # Determine overall status
            users_accessible = data_source_status.get("users_endpoint", {}).get("accessible", False)
            auth_methods_accessible = data_source_status.get("authentication_methods", {}).get(
                "accessible", False
            )

            if not users_accessible:
                return CheckResult(
                    check_id=self.check_id,
                    name=self.name,
                    category=self.category,
                    status=CheckStatus.FAIL,
                    message="MFA data source not accessible - cannot retrieve user data",
                    details={
                        "data_source_status": data_source_status,
                        "tenant_id": target_tenant_id,
                        "severity": SeverityLevel.CRITICAL,
                    },
                    duration_ms=duration_ms,
                    recommendations=[
                        "Verify Azure AD authentication is configured correctly",
                        "Ensure service principal has User.Read.All permission",
                        "Grant admin consent for Microsoft Graph API permissions",
                        "Check tenant ID is correct and accessible",
                    ],
                    tenant_id=tenant_id,
                )

            if not auth_methods_accessible:
                return CheckResult(
                    check_id=self.check_id,
                    name=self.name,
                    category=self.category,
                    status=CheckStatus.WARNING,
                    message="Basic user data accessible but authentication methods endpoint limited",
                    details={
                        "data_source_status": data_source_status,
                        "tenant_id": target_tenant_id,
                        "severity": SeverityLevel.WARNING,
                    },
                    duration_ms=duration_ms,
                    recommendations=[
                        "Add UserAuthenticationMethod.Read.All permission for detailed MFA data",
                        "Basic MFA coverage will still work via sign-in activity",
                        "For enhanced MFA reporting, grant the additional permission",
                    ],
                    tenant_id=tenant_id,
                )

            return CheckResult(
                check_id=self.check_id,
                name=self.name,
                category=self.category,
                status=CheckStatus.PASS,
                message="MFA data source fully accessible - user and authentication method data available",
                details={
                    "data_source_status": data_source_status,
                    "tenant_id": target_tenant_id,
                    "severity": SeverityLevel.INFO,
                },
                duration_ms=duration_ms,
                tenant_id=tenant_id,
            )

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            return CheckResult(
                check_id=self.check_id,
                name=self.name,
                category=self.category,
                status=CheckStatus.FAIL,
                message=f"MFA data source check failed: {str(e)}",
                details={
                    "error_type": type(e).__name__,
                    "severity": SeverityLevel.CRITICAL,
                },
                duration_ms=duration_ms,
                recommendations=[
                    "Verify Graph API client is properly configured",
                    "Check Azure AD service principal credentials",
                    "Review application logs for Graph API errors",
                ],
                tenant_id=tenant_id,
            )


async def check_riverside_mfa_data_source(
    tenant_id: str | None = None,
) -> CheckResult:
    """Check MFA data source connectivity.

    Args:
        tenant_id: Optional tenant ID for tenant-specific checks

    Returns:
        CheckResult with MFA data source status
    """
    check = RiversideMFADataSourceCheck()
    return await check.run(tenant_id=tenant_id)
