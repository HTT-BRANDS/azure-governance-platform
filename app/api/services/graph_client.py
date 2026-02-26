"""Microsoft Graph API client for identity operations."""

import logging
from typing import Dict, List, Optional

import httpx
from azure.identity import ClientSecretCredential

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"
GRAPH_SCOPES = ["https://graph.microsoft.com/.default"]


class GraphClient:
    """Microsoft Graph API client wrapper."""

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self._token: Optional[str] = None
        self._credential: Optional[ClientSecretCredential] = None

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
        params: Optional[Dict] = None,
    ) -> Dict:
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

    async def get_users(self, top: int = 999) -> List[Dict]:
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

    async def get_guest_users(self) -> List[Dict]:
        """Get all guest users."""
        endpoint = "/users"
        params = {
            "$filter": "userType eq 'Guest'",
            "$select": "id,displayName,userPrincipalName,createdDateTime,"
                       "signInActivity,externalUserState",
        }
        data = await self._request("GET", endpoint, params)
        return data.get("value", [])

    async def get_directory_roles(self) -> List[Dict]:
        """Get all directory roles with members."""
        endpoint = "/directoryRoles"
        params = {"$expand": "members"}
        data = await self._request("GET", endpoint, params)
        return data.get("value", [])

    async def get_privileged_role_assignments(self) -> List[Dict]:
        """Get privileged role assignments."""
        endpoint = "/roleManagement/directory/roleAssignments"
        params = {"$expand": "principal,roleDefinition"}
        data = await self._request("GET", endpoint, params)
        return data.get("value", [])

    async def get_conditional_access_policies(self) -> List[Dict]:
        """Get conditional access policies."""
        endpoint = "/identity/conditionalAccess/policies"
        data = await self._request("GET", endpoint)
        return data.get("value", [])

    async def get_mfa_status(self) -> Dict:
        """Get MFA registration status."""
        # This requires Reports.Read.All permission
        endpoint = "/reports/credentialUserRegistrationDetails"
        data = await self._request("GET", endpoint)
        return data

    async def get_service_principals(self) -> List[Dict]:
        """Get service principals."""
        endpoint = "/servicePrincipals"
        params = {
            "$top": 999,
            "$select": "id,displayName,appId,servicePrincipalType,"
                       "accountEnabled,createdDateTime",
        }
        data = await self._request("GET", endpoint, params)
        return data.get("value", [])
