"""Base utilities and exceptions for Azure preflight checks.

This module provides shared utilities, exceptions, and constants used across
all Azure preflight check modules.
"""

import logging
import time
from datetime import UTC, datetime
from typing import Any

from app.api.services.azure_client import azure_client_manager
from app.core.config import get_settings
from app.preflight.models import CheckCategory, CheckResult, CheckStatus

logger = logging.getLogger(__name__)
settings = get_settings()

# Azure Management API scope
AZURE_MANAGEMENT_SCOPE = "https://management.azure.com/.default"
GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"
GRAPH_SCOPES = ["https://graph.microsoft.com/.default"]

# Required Microsoft Graph API permissions
REQUIRED_GRAPH_PERMISSIONS = [
    "User.Read.All",
    "Group.Read.All",
    "Directory.Read.All",
    "RoleManagement.Read.All",
    "Policy.Read.All",
    "AuditLog.Read.All",
    "Reports.Read.All",
]

# Required Azure RBAC roles per subscription
REQUIRED_AZURE_ROLES = [
    "Reader",
    "Cost Management Reader",
    "Security Reader",
]


class AzureCheckError(Exception):
    """Base exception for Azure preflight check errors."""

    def __init__(self, message: str, error_code: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}


def _sanitize_error(error: Exception) -> dict[str, Any]:
    """Sanitize error details to remove any sensitive information.

    Args:
        error: The exception to sanitize

    Returns:
        Dictionary with safe error information (no secrets, tokens, etc.)
    """
    error_str = str(error)

    # Remove any potential secrets from error messages
    sanitized = error_str
    for pattern in ["client_secret", "password", "token", "key", "credential"]:
        # Simple sanitization - in production, use more sophisticated patterns
        if pattern.lower() in sanitized.lower():
            sanitized = f"[REDACTED - {pattern} removed from error]"

    return {
        "error_type": type(error).__name__,
        "error_message": sanitized,
        "safe_to_display": True,
    }


def _parse_aad_error(error_message: str) -> tuple[str, list[str]]:
    """Parse Azure AD error codes and provide recommendations.

    Args:
        error_message: The error message from Azure AD

    Returns:
        Tuple of (error_code, recommendations)
    """
    recommendations: list[str] = []

    if "AADSTS7000215" in error_message:
        error_code = "invalid_client_secret"
        recommendations = [
            "The client secret is invalid or expired",
            "Navigate to Azure Portal > App Registrations > Your App > Certificates & Secrets",
            "Create a new client secret and update the application configuration",
            "Remember to grant admin consent for API permissions after updating",
        ]
    elif "AADSTS700016" in error_message:
        error_code = "application_not_found"
        recommendations = [
            "The application (client) ID is not found in the tenant",
            "Verify the client_id in your configuration is correct",
            "Ensure the app registration exists in the target tenant",
            "For multi-tenant apps, ensure the app is provisioned in this tenant",
        ]
    elif "AADSTS65001" in error_message:
        error_code = "admin_consent_required"
        recommendations = [
            "Admin consent has not been granted for the required permissions",
            "Navigate to Azure Portal > Enterprise Applications > Your App > Permissions",
            "Click 'Grant admin consent for [Tenant]' for all required permissions",
            "Required permissions: " + ", ".join(REQUIRED_GRAPH_PERMISSIONS[:3]) + "...",
        ]
    elif "AADSTS7000112" in error_message:
        error_code = "invalid_client_id"
        recommendations = [
            "The client ID (application ID) is invalid",
            "Verify the client_id matches your App Registration",
            "Check for typos or copy-paste errors in the client ID",
        ]
    elif "AADSTS900023" in error_message:
        error_code = "invalid_tenant_id"
        recommendations = [
            "The tenant ID is invalid or the tenant was not found",
            "Verify the tenant_id is a valid GUID",
            "Ensure the tenant still exists and is accessible",
        ]
    elif "AuthorizationFailed" in error_message:
        error_code = "authorization_failed"
        recommendations = [
            "The application lacks required RBAC permissions",
            "Navigate to Subscription > Access Control (IAM) > Role Assignments",
            "Add role assignments: Reader, Cost Management Reader, Security Reader",
            "Wait 5-10 minutes for role assignments to propagate",
        ]
    elif "NoSubscriptionsFound" in error_message:
        error_code = "no_subscriptions"
        recommendations = [
            "No subscriptions were found for the authenticated principal",
            "Verify the service principal has access to at least one subscription",
            "Check that subscriptions are not disabled or suspended",
            "Ensure the tenant has active Azure subscriptions",
        ]
    else:
        error_code = "unknown_authentication_error"
        recommendations = [
            "An unexpected authentication error occurred",
            "Verify all credentials (tenant_id, client_id, client_secret) are correct",
            "Check Azure service health dashboard for outages",
            "Review application logs for additional context",
        ]

    return error_code, recommendations


def _get_credential(tenant_id: str) -> Any:
    """Get Azure credential for a tenant.

    Supports two modes:

    * **OIDC mode** (``settings.use_oidc_federation=True``): no client secret
      required — delegates to ``azure_client_manager.get_credential()`` which
      uses the App Service Managed Identity assertion.
    * **Secret mode**: requires ``AZURE_CLIENT_ID`` and ``AZURE_CLIENT_SECRET``
      to be configured.

    Args:
        tenant_id: Azure AD tenant ID

    Returns:
        TokenCredential ready to authenticate against the tenant

    Raises:
        AzureCheckError: If required credentials are not configured
    """
    if settings.use_oidc_federation:
        # OIDC mode: no client secret needed; azure_client_manager handles it.
        return azure_client_manager.get_credential(tenant_id)

    if not all([settings.azure_client_id, settings.azure_client_secret]):
        raise AzureCheckError(
            message="Azure credentials not configured",
            error_code="credentials_not_configured",
            details={
                "azure_client_id_set": bool(settings.azure_client_id),
                "azure_client_secret_set": bool(settings.azure_client_secret),
            },
        )

    # Import here to avoid dependency issues during module load
    from azure.identity import ClientSecretCredential

    return ClientSecretCredential(
        tenant_id=tenant_id,
        client_id=str(settings.azure_client_id),
        client_secret=str(settings.azure_client_secret),
    )


def _create_check_result(
    check_id: str,
    name: str,
    category: CheckCategory,
    tenant_id: str | None,
    subscription_id: str | None,
    status: CheckStatus,
    message: str,
    start_time: float,
    details: dict[str, Any] | None = None,
    recommendations: list[str] | None = None,
    error_code: str | None = None,
    error: Exception | None = None,
) -> CheckResult:
    """Create a CheckResult with consistent timing and formatting.

    Args:
        check_id: Unique identifier for the check
        name: Human-readable name of the check
        category: Category of the check
        tenant_id: Optional tenant ID
        subscription_id: Optional subscription ID
        status: Check status
        message: Human-readable message
        start_time: When the check started (for duration calculation)
        details: Optional check-specific details
        recommendations: Optional recommendations
        error_code: Optional error code
        error: Optional exception for error details

    Returns:
        Populated CheckResult instance
    """
    duration_ms = (time.perf_counter() - start_time) * 1000

    if error:
        sanitized = _sanitize_error(error)
        details = {**(details or {}), **sanitized}

    return CheckResult(
        check_id=check_id,
        name=name,
        category=category,
        status=status,
        message=message,
        details=details or {},
        duration_ms=duration_ms,
        timestamp=datetime.now(UTC),
        recommendations=recommendations or [],
        tenant_id=tenant_id,
    )


__all__ = [
    "AzureCheckError",
    "_sanitize_error",
    "_parse_aad_error",
    "_get_credential",
    "_create_check_result",
    "AZURE_MANAGEMENT_SCOPE",
    "GRAPH_API_BASE",
    "GRAPH_SCOPES",
    "REQUIRED_GRAPH_PERMISSIONS",
    "REQUIRED_AZURE_ROLES",
]
