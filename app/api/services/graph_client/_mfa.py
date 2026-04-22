"""MFA mixin for GraphClient: MFA status + registration details.

Split from the monolithic graph_client.py (issue 6oj7, 2026-04-22).
This is a pure mixin — it relies on self.tenant_id and self._request
being provided by _GraphClientCore via MRO composition.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.api.services.graph_client._constants import (
    ADMIN_ROLE_TEMPLATE_IDS,
    GRAPH_API_BASE,
)
from app.api.services.graph_client._models import (
    MFAError,
    MFAMethodDetails,
    TenantMFASummary,
    UserMFAStatus,
)
from app.core.circuit_breaker import GRAPH_API_BREAKER, circuit_breaker
from app.core.config import get_settings
from app.core.retry import GRAPH_API_POLICY, retry_with_backoff

logger = logging.getLogger(__name__)
settings = get_settings()


class _MFAMixin:
    """Mixin: MFA status, auth methods, registration details, tenant summary."""

    @circuit_breaker(GRAPH_API_BREAKER)
    @retry_with_backoff(GRAPH_API_POLICY)
    async def get_mfa_status(self) -> dict:
        """Get MFA registration status."""
        # This requires Reports.Read.All permission
        endpoint = "/reports/authenticationMethods/userRegistrationDetails"
        data = await self._request("GET", endpoint)
        return data

    @circuit_breaker(GRAPH_API_BREAKER)
    @retry_with_backoff(GRAPH_API_POLICY)
    async def get_user_auth_methods(self, user_id: str) -> list[dict]:
        """Get authentication methods for a specific user.

        Retrieves all registered authentication methods for a user including:
        - Microsoft Authenticator app
        - Phone (SMS/call)
        - Email
        - FIDO2 security keys
        - Windows Hello
        - Hardware tokens
        - Temporary Access Pass

        Args:
            user_id: The Azure AD user ID (GUID)

        Returns:
            List of authentication method dictionaries

        Raises:
            MFAError: If authentication methods cannot be retrieved
        """
        try:
            endpoint = f"/users/{user_id}/authentication/methods"
            data = await self._request("GET", endpoint)
            return data.get("value", [])
        except Exception as e:
            logger.error(f"Failed to get auth methods for user {user_id}: {e}")
            raise MFAError(f"Failed to get auth methods: {e}", user_id) from e

    @circuit_breaker(GRAPH_API_BREAKER)
    @retry_with_backoff(GRAPH_API_POLICY)
    async def get_user_mfa_details(self, user_id: str) -> UserMFAStatus | None:
        """Get detailed MFA status for a specific user.

        Fetches user information and their authentication methods to build
        a complete picture of their MFA registration status.

        Args:
            user_id: The Azure AD user ID (GUID)

        Returns:
            UserMFAStatus object with complete MFA details, or None if user not found

        Raises:
            MFAError: If MFA details cannot be retrieved
        """
        try:
            # Get user basic info
            user_endpoint = f"/users/{user_id}"
            user_params = {"$select": "id,displayName,userPrincipalName,signInActivity"}
            user_data = await self._request("GET", user_endpoint, user_params)

            if not user_data:
                return None

            # Get authentication methods
            auth_methods = await self.get_user_auth_methods(user_id)

            # Parse authentication methods
            parsed_methods: list[MFAMethodDetails] = []
            methods_registered: list[str] = []
            default_method: str | None = None

            for method in auth_methods:
                method_type = method.get("@odata.type", "").replace("#microsoft.graph.", "")
                is_default = method.get("isDefault", False)
                is_enabled = method.get("isEnabled", True)

                method_details = MFAMethodDetails(
                    method_type=method_type,
                    is_default=is_default,
                    is_enabled=is_enabled,
                )

                # Extract method-specific details
                if "phoneAuthenticationMethod" in method_type:
                    method_details.phone_number = method.get("phoneNumber")
                    method_details.display_name = method.get("phoneType", "Phone")
                    methods_registered.append("phone")
                elif "emailAuthenticationMethod" in method_type:
                    method_details.email_address = method.get("emailAddress")
                    methods_registered.append("email")
                elif "microsoftAuthenticatorAuthenticationMethod" in method_type:
                    method_details.display_name = method.get(
                        "displayName", "Microsoft Authenticator"
                    )
                    method_details.app_id = method.get("authenticatorAppId")
                    methods_registered.append("microsoftAuthenticator")
                elif "fido2AuthenticationMethod" in method_type:
                    method_details.display_name = method.get("model", "FIDO2 Security Key")
                    methods_registered.append("fido2")
                elif "windowsHelloForBusinessAuthenticationMethod" in method_type:
                    method_details.display_name = method.get("displayName", "Windows Hello")
                    methods_registered.append("windowsHello")
                elif "softwareOathAuthenticationMethod" in method_type:
                    method_details.display_name = method.get("displayName", "Hardware Token")
                    methods_registered.append("softwareOath")
                elif "temporaryAccessPassAuthenticationMethod" in method_type:
                    method_details.display_name = "Temporary Access Pass"
                    methods_registered.append("temporaryAccessPass")

                parsed_methods.append(method_details)

                if is_default:
                    default_method = method_type

            # Determine if MFA is registered
            # MFA is considered registered if user has at least one non-password method
            non_password_methods = [m for m in methods_registered if m != "password"]
            is_mfa_registered = len(non_password_methods) > 0

            return UserMFAStatus(
                user_id=user_id,
                user_principal_name=user_data.get("userPrincipalName", ""),
                display_name=user_data.get("displayName", ""),
                is_mfa_registered=is_mfa_registered,
                methods_registered=list(set(methods_registered)),
                auth_methods=parsed_methods,
                default_method=default_method,
                last_updated=user_data.get("signInActivity", {}).get("lastSignInDateTime"),
            )

        except MFAError:
            raise
        except Exception as e:
            logger.error(f"Failed to get MFA details for user {user_id}: {e}")
            raise MFAError(f"Failed to get MFA details: {e}", user_id) from e

    @circuit_breaker(GRAPH_API_BREAKER)
    @retry_with_backoff(GRAPH_API_POLICY)
    async def get_mfa_registration_details(
        self,
        filter_param: str | None = None,
    ) -> list[dict]:
        """Get MFA registration details for all users.

        Uses the reporting API to get credential user registration details.
        This endpoint requires Reports.Read.All permission.

        Args:
            filter_param: Optional OData filter string

        Returns:
            List of user MFA registration details
        """
        endpoint = "/reports/authenticationMethods/userRegistrationDetails"
        params: dict[str, Any] = {}
        if filter_param:
            params["$filter"] = filter_param

        data = await self._request("GET", endpoint, params)
        return data.get("value", [])

    @circuit_breaker(GRAPH_API_BREAKER)
    @retry_with_backoff(GRAPH_API_POLICY)
    async def get_mfa_registration_details_paginated(
        self,
        batch_size: int = 100,
        filter_param: str | None = None,
    ) -> list[dict]:
        """Get MFA registration details with pagination support.

        Handles large user bases by paginating through results.
        Respects rate limits with built-in delays.

        Args:
            batch_size: Number of users per page (max 999)
            filter_param: Optional OData filter string

        Returns:
            List of all user MFA registration details
        """

        all_registrations: list[dict] = []
        endpoint = "/reports/authenticationMethods/userRegistrationDetails"
        params: dict[str, Any] = {"$top": min(batch_size, 999)}
        if filter_param:
            params["$filter"] = filter_param

        while endpoint:
            try:
                data = await self._request("GET", endpoint, params)
                registrations = data.get("value", [])
                all_registrations.extend(registrations)

                logger.debug(f"Retrieved {len(registrations)} MFA registration records")

                # Handle pagination
                next_link = data.get("@odata.nextLink")
                if next_link:
                    endpoint = next_link.replace(GRAPH_API_BASE, "")
                    params = None
                    # Rate limiting compliance - small delay between pages
                    await asyncio.sleep(0.1)
                else:
                    endpoint = None

            except Exception as e:
                logger.error(f"Error fetching MFA registration details: {e}")
                raise

        logger.info(f"Retrieved total of {len(all_registrations)} MFA registration records")
        return all_registrations

    @circuit_breaker(GRAPH_API_BREAKER)
    @retry_with_backoff(GRAPH_API_POLICY)
    async def get_tenant_mfa_summary(
        self,
        include_details: bool = False,
        batch_size: int = 100,
    ) -> TenantMFASummary:
        """Get comprehensive MFA summary for the tenant.

        Aggregates MFA data across all users to provide tenant-level statistics.

        Args:
            include_details: If True, include list of users without MFA
            batch_size: Number of users to process per batch

        Returns:
            TenantMFASummary with complete MFA statistics
        """

        # Get all users with their admin status
        users = await self.get_users(top=batch_size)

        # Get directory roles for admin identification
        directory_roles = await self.get_directory_roles()

        # Build set of admin user IDs
        admin_user_ids: set[str] = set()
        for role in directory_roles:
            role_template_id = role.get("roleTemplateId", "")
            if role_template_id in ADMIN_ROLE_TEMPLATE_IDS:
                for member in role.get("members", []):
                    user_id = member.get("id")
                    if user_id:
                        admin_user_ids.add(user_id)

        # Get MFA registrations
        mfa_registrations = await self.get_mfa_registration_details_paginated(batch_size=batch_size)

        # Build registration lookup
        registration_lookup: dict[str, dict] = {
            reg.get("userPrincipalName", "").lower(): reg for reg in mfa_registrations
        }

        # Calculate statistics
        total_users = len(users)
        mfa_registered = 0
        admin_total = len(admin_user_ids)
        admin_mfa = 0
        method_breakdown: dict[str, int] = {}
        users_without_mfa: list[dict] = []

        for user in users:
            upn = user.get("userPrincipalName", "").lower()
            user_id = user.get("id", "")
            is_admin = user_id in admin_user_ids

            reg = registration_lookup.get(upn, {})
            is_mfa_registered = reg.get("isMfaRegistered", False)
            methods = reg.get("methodsRegistered", []) if reg else []

            if is_mfa_registered:
                mfa_registered += 1
                if is_admin:
                    admin_mfa += 1

                # Count methods
                for method in methods:
                    method_type = method.lower() if isinstance(method, str) else str(method)
                    method_breakdown[method_type] = method_breakdown.get(method_type, 0) + 1
            else:
                if include_details:
                    users_without_mfa.append(
                        {
                            "user_id": user_id,
                            "user_principal_name": upn,
                            "display_name": user.get("displayName", ""),
                            "is_admin": is_admin,
                        }
                    )

            # Rate limiting compliance
            await asyncio.sleep(0.01)

        # Calculate percentages
        mfa_coverage_pct = (mfa_registered / total_users * 100) if total_users > 0 else 0.0
        admin_mfa_pct = (admin_mfa / admin_total * 100) if admin_total > 0 else 0.0

        return TenantMFASummary(
            tenant_id=self.tenant_id,
            total_users=total_users,
            mfa_registered_users=mfa_registered,
            mfa_coverage_percentage=round(mfa_coverage_pct, 2),
            admin_accounts_total=admin_total,
            admin_accounts_mfa=admin_mfa,
            admin_mfa_percentage=round(admin_mfa_pct, 2),
            method_breakdown=method_breakdown,
            users_without_mfa=users_without_mfa,
        )
