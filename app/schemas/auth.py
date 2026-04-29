"""Authentication API schemas.

Kept separate from route wiring so auth routes stay thin and public schemas can
be reused by services/tests without dragging FastAPI routers along for the ride.
"""

from typing import Any

from pydantic import BaseModel


class TokenResponse(BaseModel):
    """OAuth2 token response."""

    access_token: str | None = None  # Can be None if sent as HttpOnly cookie
    refresh_token: str | None = None  # Can be None if sent as HttpOnly cookie
    token_type: str = "bearer"
    expires_in: int  # Seconds until access token expires
    scope: str | None = None
    cookies_set: bool = True  # Indicates HttpOnly cookies were set server-side


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""

    refresh_token: str


class UserInfoResponse(BaseModel):
    """Current user info response."""

    id: str
    email: str | None = None
    name: str | None = None
    roles: list[str]
    tenant_ids: list[str]
    accessible_tenants: list[dict[str, Any]] = []
    auth_provider: str
    is_active: bool


class AzureADLoginRequest(BaseModel):
    """Azure AD OAuth2 callback request."""

    code: str
    redirect_uri: str
    code_verifier: str | None = None  # PKCE
    state: str | None = None  # OAuth state for audit logging


class LogoutResponse(BaseModel):
    """Logout response."""

    message: str
    revoked: bool


class TenantAccessInfo(BaseModel):
    """Tenant access information."""

    tenant_id: str
    name: str
    role: str
    permissions: dict[str, bool]
