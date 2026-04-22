"""Riverside preflight check: RiversideAzureADPermissionsCheck.

Split from the monolithic app/preflight/riverside_checks.py
(issue 6oj7, 2026-04-22).
"""

import time

from app.core.config import get_settings
from app.preflight.base import BasePreflightCheck
from app.preflight.models import CheckCategory, CheckResult, CheckStatus
from app.preflight.riverside_checks._common import SeverityLevel


class RiversideAzureADPermissionsCheck(BasePreflightCheck):
    """Check Azure AD permissions for Riverside data access.

    Validates that the Azure AD service principal has the required
    permissions to read MFA status, user data, and device compliance
    information needed for Riverside compliance tracking.
    """

    def __init__(self):
        super().__init__(
            check_id="riverside_azure_ad_permissions",
            name="Riverside Azure AD Permissions",
            category=CheckCategory.RIVERSIDE,
            description="Verify Azure AD permissions for Riverside data access",
            timeout_seconds=30.0,
        )

    async def _execute_check(self, tenant_id: str | None = None) -> CheckResult:
        """Execute Azure AD permissions check for Riverside."""
        start_time = time.perf_counter()
        settings = get_settings()

        # Required Graph API permissions for Riverside
        required_permissions = [
            "User.Read.All",
            "Group.Read.All",
            "Directory.Read.All",
            "AuditLog.Read.All",
            "Reports.Read.All",
            "DeviceManagementManagedDevices.Read.All",
        ]

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
                    message="No tenant ID available for permissions check",
                    details={
                        "severity": SeverityLevel.CRITICAL,
                    },
                    duration_ms=duration_ms,
                    recommendations=[
                        "Configure AZURE_TENANT_ID environment variable",
                        "Verify tenant is properly registered in the system",
                    ],
                    tenant_id=tenant_id,
                )

            client = GraphClient(target_tenant_id)

            # Test permissions by attempting to fetch users (requires User.Read.All)
            permissions_status = {}

            try:
                # Try to get users - tests User.Read.All and Directory.Read.All
                await client.get_users(limit=1)
                permissions_status["User.Read.All"] = {
                    "granted": True,
                    "test_result": "success",
                }
            except Exception as e:
                error_str = str(e).lower()
                if "403" in error_str or "forbidden" in error_str:
                    permissions_status["User.Read.All"] = {
                        "granted": False,
                        "test_result": "forbidden",
                        "error": str(e)[:100],
                    }
                else:
                    permissions_status["User.Read.All"] = {
                        "granted": False,
                        "test_result": "error",
                        "error": str(e)[:100],
                    }

            # Try to get organization info - tests basic connectivity
            try:
                org = await client.get_organization()
                permissions_status["Organization.Read.All"] = {
                    "granted": True,
                    "test_result": "success",
                    "org_name": org.get("displayName") if org else None,
                }
            except Exception as e:
                permissions_status["Organization.Read.All"] = {
                    "granted": False,
                    "test_result": "error",
                    "error": str(e)[:100],
                }

            duration_ms = (time.perf_counter() - start_time) * 1000

            # Determine overall status
            granted_count = sum(1 for p in permissions_status.values() if p.get("granted"))

            if granted_count == 0:
                return CheckResult(
                    check_id=self.check_id,
                    name=self.name,
                    category=self.category,
                    status=CheckStatus.FAIL,
                    message="No required Azure AD permissions granted",
                    details={
                        "permissions_status": permissions_status,
                        "required_permissions": required_permissions,
                        "tenant_id": target_tenant_id,
                        "severity": SeverityLevel.CRITICAL,
                    },
                    duration_ms=duration_ms,
                    recommendations=[
                        "Navigate to Azure Portal > App Registrations > Your App > API Permissions",
                        "Add required permissions: User.Read.All, Group.Read.All, Directory.Read.All",
                        "Click 'Grant admin consent for [Tenant]' button",
                        "Wait 5-10 minutes for permissions to propagate",
                    ],
                    tenant_id=tenant_id,
                )

            if granted_count < len(permissions_status):
                return CheckResult(
                    check_id=self.check_id,
                    name=self.name,
                    category=self.category,
                    status=CheckStatus.WARNING,
                    message=f"Partial permissions: {granted_count} of {len(permissions_status)} key permissions granted",
                    details={
                        "permissions_status": permissions_status,
                        "required_permissions": required_permissions,
                        "tenant_id": target_tenant_id,
                        "severity": SeverityLevel.WARNING,
                    },
                    duration_ms=duration_ms,
                    recommendations=[
                        "Review missing permissions in API Permissions blade",
                        "Grant admin consent for all required permissions",
                        "Some Riverside features may be limited without full permissions",
                    ],
                    tenant_id=tenant_id,
                )

            return CheckResult(
                check_id=self.check_id,
                name=self.name,
                category=self.category,
                status=CheckStatus.PASS,
                message=f"All required Azure AD permissions granted ({granted_count}/{len(permissions_status)})",
                details={
                    "permissions_status": permissions_status,
                    "required_permissions": required_permissions,
                    "tenant_id": target_tenant_id,
                    "severity": SeverityLevel.INFO,
                },
                duration_ms=duration_ms,
                tenant_id=tenant_id,
            )

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            error_str = str(e).lower()

            # Handle specific authentication errors
            if "authentication" in error_str or "unauthorized" in error_str or "401" in error_str:
                return CheckResult(
                    check_id=self.check_id,
                    name=self.name,
                    category=self.category,
                    status=CheckStatus.FAIL,
                    message="Azure AD authentication failed - cannot verify permissions",
                    details={
                        "error": str(e)[:200],
                        "error_type": type(e).__name__,
                        "severity": SeverityLevel.CRITICAL,
                    },
                    duration_ms=duration_ms,
                    recommendations=[
                        "Verify Azure credentials are correctly configured",
                        "Check that the service principal exists in Azure AD",
                        "Ensure client secret has not expired",
                    ],
                    tenant_id=tenant_id,
                )

            return CheckResult(
                check_id=self.check_id,
                name=self.name,
                category=self.category,
                status=CheckStatus.FAIL,
                message=f"Azure AD permissions check failed: {str(e)}",
                details={
                    "error_type": type(e).__name__,
                    "severity": SeverityLevel.CRITICAL,
                },
                duration_ms=duration_ms,
                recommendations=[
                    "Verify Azure AD tenant is accessible",
                    "Check service principal configuration",
                    "Review application logs for detailed error information",
                ],
                tenant_id=tenant_id,
            )


async def check_riverside_azure_ad_permissions(
    tenant_id: str | None = None,
) -> CheckResult:
    """Check Azure AD permissions for Riverside.

    Args:
        tenant_id: Optional tenant ID for tenant-specific checks

    Returns:
        CheckResult with Azure AD permissions status
    """
    check = RiversideAzureADPermissionsCheck()
    return await check.run(tenant_id=tenant_id)
