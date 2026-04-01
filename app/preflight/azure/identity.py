"""Azure identity and authentication preflight checks.

This module provides checks for Azure AD authentication, Microsoft Graph API access,
and identity-related permissions.
"""

import asyncio
import logging
import time
from datetime import UTC, datetime

from app.core.config import get_settings
from app.preflight.azure.base import (
    AZURE_MANAGEMENT_SCOPE,
    AzureCheckError,
    _create_check_result,
    _get_credential,
    _parse_aad_error,
)
from app.preflight.base import BasePreflightCheck
from app.preflight.models import CheckCategory, CheckResult, CheckStatus

logger = logging.getLogger(__name__)
settings = get_settings()


class AzureAuthCheck(BasePreflightCheck):
    """Check Azure AD authentication (supports OIDC and ClientSecretCredential)."""

    def __init__(self) -> None:
        super().__init__(
            check_id="azure_authentication",
            name="Azure AD Authentication",
            category=CheckCategory.AZURE_AUTH,
            description="Verify Azure AD authentication is configured and working",
            timeout_seconds=30.0,
        )

    async def _execute_check(self, tenant_id: str | None = None) -> CheckResult:
        """Execute the authentication check."""
        if not tenant_id:
            tenant_id = settings.azure_tenant_id

        if not tenant_id:
            return CheckResult(
                check_id=self.check_id,
                name=self.name,
                category=self.category,
                status=CheckStatus.FAIL,
                message="No tenant ID provided for authentication check",
                recommendations=["Configure AZURE_TENANT_ID environment variable"],
            )

        # Delegate to function-based implementation
        return await check_azure_authentication(tenant_id)


async def check_azure_authentication(tenant_id: str) -> CheckResult:
    """Verify we can get an access token for the tenant.

    This is the most fundamental check - it validates that the application
    can authenticate to Azure AD and obtain a valid access token for the
    Azure Management API.

    Args:
        tenant_id: Azure AD tenant ID to authenticate against

    Returns:
        CheckResult with authentication status and token details

    Example:
        >>> result = await check_azure_authentication("12345678-1234-1234-1234-123456789012")
        >>> print(result.status)  # CheckStatus.PASS if successful
    """
    # Lazy import to avoid namespace package issues in tests
    from azure.core.exceptions import ClientAuthenticationError

    start_time = time.perf_counter()
    check_id = "azure_authentication"
    name = "Azure AD Authentication"
    category = CheckCategory.AZURE_AUTH

    try:
        credential = _get_credential(tenant_id)
        token = await asyncio.to_thread(credential.get_token, AZURE_MANAGEMENT_SCOPE)

        # Calculate token expiration time
        expires_at = datetime.fromtimestamp(token.expires_on)
        expires_in_minutes = int((expires_at - datetime.now(UTC)).total_seconds() / 60)

        details = {
            "token_acquired": True,
            "token_expires_at": expires_at.isoformat(),
            "token_expires_in_minutes": expires_in_minutes,
            "scope": AZURE_MANAGEMENT_SCOPE,
        }

        # Warning if token expires soon
        if expires_in_minutes < 30:
            return _create_check_result(
                check_id=check_id,
                name=name,
                category=category,
                tenant_id=tenant_id,
                subscription_id=None,
                status=CheckStatus.WARNING,
                message=f"Authentication successful but token expires in {expires_in_minutes} minutes",
                start_time=start_time,
                details=details,
                recommendations=[
                    "Token will expire soon - normal renewal will occur automatically",
                    "If issues persist, verify credential configuration",
                ],
            )

        return _create_check_result(
            check_id=check_id,
            name=name,
            category=category,
            tenant_id=tenant_id,
            subscription_id=None,
            status=CheckStatus.PASS,
            message=f"Successfully authenticated to Azure tenant '{tenant_id[:8]}...'",
            start_time=start_time,
            details=details,
        )

    except ClientAuthenticationError as e:
        error_code, recommendations = _parse_aad_error(str(e))
        return _create_check_result(
            check_id=check_id,
            name=name,
            category=category,
            tenant_id=tenant_id,
            subscription_id=None,
            status=CheckStatus.FAIL,
            message=f"Authentication failed: {error_code}",
            start_time=start_time,
            details={"error_type": "ClientAuthenticationError"},
            recommendations=recommendations,
            error_code=error_code,
            error=e,
        )

    except AzureCheckError as e:
        return _create_check_result(
            check_id=check_id,
            name=name,
            category=category,
            tenant_id=tenant_id,
            subscription_id=None,
            status=CheckStatus.FAIL,
            message=f"Configuration error: {e.message}",
            start_time=start_time,
            details=e.details,
            recommendations=[
                "OIDC mode: Set USE_OIDC_FEDERATION=true and configure the Managed Identity",
                "Secret mode: Set AZURE_CLIENT_ID and AZURE_CLIENT_SECRET environment variables",
                "Or configure via .env file or key vault integration",
            ],
            error_code=e.error_code,
            error=e,
        )

    except Exception as e:
        logger.error(
            "Unexpected error in authentication check",
            extra={
                "tenant_prefix": tenant_id[:8] if tenant_id else "unknown",
                "error_type": type(e).__name__,
            },
        )
        return _create_check_result(
            check_id=check_id,
            name=name,
            category=category,
            tenant_id=tenant_id,
            subscription_id=None,
            status=CheckStatus.FAIL,
            message=f"Unexpected error during authentication: {type(e).__name__}",
            start_time=start_time,
            recommendations=[
                "Check application logs for detailed error information",
                "Verify network connectivity to Azure AD (login.microsoftonline.com)",
                "Check Azure service health for authentication service outages",
            ],
            error_code="unexpected_error",
            error=e,
        )


__all__ = [
    "AzureAuthCheck",
    "check_azure_authentication",
]
