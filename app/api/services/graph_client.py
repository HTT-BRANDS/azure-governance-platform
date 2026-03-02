"""Microsoft Graph API client for identity operations.

This module provides a comprehensive Graph API client with:
- MFA data collection methods
- Pagination support for large user bases
- Rate limiting compliance
- Error handling and retry logic
- Circuit breaker pattern for resilience
"""

import logging
from dataclasses import dataclass
from typing import Any

import httpx
from azure.identity import ClientSecretCredential

from app.core.circuit_breaker import GRAPH_API_BREAKER, CircuitBreakerError, circuit_breaker
from app.core.config import get_settings
from app.core.retry import GRAPH_API_POLICY, retry_with_backoff

logger = logging.getLogger(__name__)
settings = get_settings()

GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"
GRAPH_BETA_API_BASE = "https://graph.microsoft.com/beta"
GRAPH_SCOPES = ["https://graph.microsoft.com/.default"]


@dataclass
class MFAMethodDetails:
    """MFA method details for a user."""

    method_type: str
    is_default: bool
    is_enabled: bool
    phone_number: str | None = None
    email_address: str | None = None
    display_name: str | None = None
    app_id: str | None = None


@dataclass
class UserMFAStatus:
    """Complete MFA status for a user."""

    user_id: str
    user_principal_name: str
    display_name: str
    is_mfa_registered: bool
    methods_registered: list[str]
    auth_methods: list[MFAMethodDetails]
    default_method: str | None
    last_updated: str | None


@dataclass
class TenantMFASummary:
    """MFA summary statistics for a tenant."""

    tenant_id: str
    total_users: int
    mfa_registered_users: int
    mfa_coverage_percentage: float
    admin_accounts_total: int
    admin_accounts_mfa: int
    admin_mfa_percentage: float
    method_breakdown: dict[str, int]
    users_without_mfa: list[dict[str, Any]]


class MFAError(Exception):
    """Exception raised when MFA data collection fails."""

    def __init__(self, message: str, user_id: str | None = None) -> None:
        super().__init__(message)
        self.user_id = user_id


class GraphClient:
    """Microsoft Graph API client wrapper."""

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self._token: str | None = None
        self._credential: ClientSecretCredential | None = None

    def _get_credential(self) -> ClientSecretCredential:
        """Get or create credential."""
        if not self._credential:
            self._credential = ClientSecretCredential(
                tenant_id=self.tenant_id,
                client_id=settings.azure_client_id,
                client_secret=settings.azure_client_secret,
            )
        return self._credential

    def _get_token(self) -> str:
        """Get access token for Graph API."""
        credential = self._get_credential()
        token = credential.get_token(*GRAPH_SCOPES)
        return token.token

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict | None = None,
    ) -> dict:
        """Make authenticated request to Graph API."""
        token = self._get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            url = f"{GRAPH_API_BASE}{endpoint}"
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    @circuit_breaker(GRAPH_API_BREAKER)
    @retry_with_backoff(GRAPH_API_POLICY)
    async def get_users(self, top: int = 999) -> list[dict]:
        """Get all users in the tenant."""
        users = []
        endpoint = "/users"
        params = {
            "$top": top,
            "$select": "id,displayName,userPrincipalName,userType,"
                       "accountEnabled,createdDateTime,signInActivity",
        }

        while endpoint:
            data = await self._request("GET", endpoint, params)
            users.extend(data.get("value", []))

            # Handle pagination
            next_link = data.get("@odata.nextLink")
            if next_link:
                endpoint = next_link.replace(GRAPH_API_BASE, "")
                params = None
            else:
                endpoint = None

        return users

    @circuit_breaker(GRAPH_API_BREAKER)
    @retry_with_backoff(GRAPH_API_POLICY)
    async def get_guest_users(self) -> list[dict]:
        """Get all guest users."""
        endpoint = "/users"
        params = {
            "$filter": "userType eq 'Guest'",
            "$select": "id,displayName,userPrincipalName,createdDateTime,"
                       "signInActivity,externalUserState",
        }
        data = await self._request("GET", endpoint, params)
        return data.get("value", [])

    @circuit_breaker(GRAPH_API_BREAKER)
    @retry_with_backoff(GRAPH_API_POLICY)
    async def get_directory_roles(self) -> list[dict]:
        """Get all directory roles with members."""
        endpoint = "/directoryRoles"
        params = {"$expand": "members"}
        data = await self._request("GET", endpoint, params)
        return data.get("value", [])

    @circuit_breaker(GRAPH_API_BREAKER)
    @retry_with_backoff(GRAPH_API_POLICY)
    async def get_privileged_role_assignments(self) -> list[dict]:
        """Get privileged role assignments."""
        endpoint = "/roleManagement/directory/roleAssignments"
        params = {"$expand": "principal,roleDefinition"}
        data = await self._request("GET", endpoint, params)
        return data.get("value", [])

    @circuit_breaker(GRAPH_API_BREAKER)
    @retry_with_backoff(GRAPH_API_POLICY)
    async def get_conditional_access_policies(self) -> list[dict]:
        """Get conditional access policies."""
        endpoint = "/identity/conditionalAccess/policies"
        data = await self._request("GET", endpoint)
        return data.get("value", [])

    @circuit_breaker(GRAPH_API_BREAKER)
    @retry_with_backoff(GRAPH_API_POLICY)
    async def get_mfa_status(self) -> dict:
        """Get MFA registration status."""
        # This requires Reports.Read.All permission
        endpoint = "/reports/credentialUserRegistrationDetails"
        data = await self._request("GET", endpoint)
        return data

    @circuit_breaker(GRAPH_API_BREAKER)
    @retry_with_backoff(GRAPH_API_POLICY)
    async def get_service_principals(self) -> list[dict]:
        """Get service principals."""
        endpoint = "/servicePrincipals"
        params = {
            "$top": 999,
            "$select": "id,displayName,appId,servicePrincipalType,"
                       "accountEnabled,createdDateTime",
        }
        data = await self._request("GET", endpoint, params)
        return data.get("value", [])

    # ==========================================================================
    # MFA Data Collection Methods
    # ==========================================================================

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
            user_params = {
                "$select": "id,displayName,userPrincipalName,signInActivity"
            }
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
                    method_details.display_name = method.get("displayName", "Microsoft Authenticator")
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
        endpoint = "/reports/credentialUserRegistrationDetails"
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
        import asyncio

        all_registrations: list[dict] = []
        endpoint = "/reports/credentialUserRegistrationDetails"
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
        import asyncio

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
        mfa_registrations = await self.get_mfa_registration_details_paginated(
            batch_size=batch_size
        )

        # Build registration lookup
        registration_lookup: dict[str, dict] = {
            reg.get("userPrincipalName", "").lower(): reg
            for reg in mfa_registrations
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
                    users_without_mfa.append({
                        "user_id": user_id,
                        "user_principal_name": upn,
                        "display_name": user.get("displayName", ""),
                        "is_admin": is_admin,
                    })

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

    @circuit_breaker(GRAPH_API_BREAKER)
    @retry_with_backoff(GRAPH_API_POLICY)
    async def get_users_paginated(
        self,
        batch_size: int = 100,
        select_fields: list[str] | None = None,
        filter_param: str | None = None,
    ) -> list[dict]:
        """Get all users with pagination support.

        Handles large user bases by paginating through results.

        Args:
            batch_size: Number of users per page (max 999)
            select_fields: Fields to select (defaults to standard fields)
            filter_param: Optional OData filter string

        Returns:
            List of all users
        """
        import asyncio

        all_users: list[dict] = []

        if select_fields is None:
            select_fields = [
                "id", "displayName", "userPrincipalName", "userType",
                "accountEnabled", "createdDateTime", "signInActivity"
            ]

        endpoint = "/users"
        params: dict[str, Any] = {
            "$top": min(batch_size, 999),
            "$select": ",".join(select_fields),
        }
        if filter_param:
            params["$filter"] = filter_param

        while endpoint:
            data = await self._request("GET", endpoint, params)
            users = data.get("value", [])
            all_users.extend(users)

            # Handle pagination
            next_link = data.get("@odata.nextLink")
            if next_link:
                endpoint = next_link.replace(GRAPH_API_BASE, "")
                params = None
                # Rate limiting compliance
                await asyncio.sleep(0.1)
            else:
                endpoint = None

        return all_users

    @circuit_breaker(GRAPH_API_BREAKER)
    @retry_with_backoff(GRAPH_API_POLICY)
    async def get_conditional_access_policies_with_details(self) -> list[dict]:
        """Get conditional access policies with detailed configuration.

        Retrieves CA policies including grant controls, conditions, and state.
        Useful for analyzing MFA enforcement policies.

        Returns:
            List of conditional access policies with full details
        """
        endpoint = "/identity/conditionalAccess/policies"
        params = {
            "$expand": "grantControls,conditions,locations",
        }
        data = await self._request("GET", endpoint, params)
        return data.get("value", [])

    @circuit_breaker(GRAPH_API_BREAKER)
    @retry_with_backoff(GRAPH_API_POLICY)
    async def get_sign_in_logs(
        self,
        filter_param: str | None = None,
        top: int = 100,
    ) -> list[dict]:
        """Get Azure AD sign-in logs.

        Requires AuditLog.Read.All and Directory.Read.All permissions.

        Args:
            filter_param: Optional OData filter string
            top: Number of records to retrieve

        Returns:
            List of sign-in log entries
        """
        endpoint = "/auditLogs/signIns"
        params: dict[str, Any] = {"$top": top}
        if filter_param:
            params["$filter"] = filter_param

        data = await self._request("GET", endpoint, params)
        return data.get("value", [])


# Admin role template IDs for identifying privileged users
ADMIN_ROLE_TEMPLATE_IDS = {
    "62e90394-69f5-4237-9190-012177145e10",  # Global Administrator
    "194ae4cb-b126-40b2-bd5b-6091b380977d",  # Security Administrator
    "f28a1f50-f6e7-4571-818b-6a12f2af6b6c",  # SharePoint Administrator
    "29232cdf-9323-42fd-ade2-1d097af3e4de",  # Exchange Administrator
    "b1be1c3e-b65d-4f19-8427-f6fa0d9feb5c",  # Conditional Access Administrator
    "729827e3-9c14-49f7-bb1b-9608f156bbb8",  # Helpdesk Administrator
    "966707d0-3269-4727-9be2-8c3a10f19b9d",  # Password Administrator
    "7be44c8a-adaf-4e2a-84d6-ab2649e08a13",  # Privileged Authentication Administrator
    "e8611ab8-c189-46e8-94e1-60213ab1f814",  # Privileged Role Administrator
    "fe930be7-5e62-47db-91af-98c3a49a38b1",  # User Administrator
    "a9ea8996-122f-4c74-9520-b03e91a63c5a",  # Application Administrator
    "3edaf663-341e-4475-9f94-5c398ef6c070",  # Cloud Application Administrator
}
