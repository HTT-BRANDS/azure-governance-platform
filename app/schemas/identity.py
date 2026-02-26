"""Identity-related Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class IdentitySummary(BaseModel):
    """Identity governance summary across tenants."""

    total_users: int
    active_users: int
    guest_users: int
    mfa_enabled_percent: float
    privileged_users: int
    stale_accounts: int
    service_principals: int
    by_tenant: list["TenantIdentitySummary"] = Field(default_factory=list)


class TenantIdentitySummary(BaseModel):
    """Identity summary for a single tenant."""

    tenant_id: str
    tenant_name: str
    total_users: int
    guest_users: int
    mfa_enabled_percent: float
    privileged_users: int
    stale_accounts_30d: int
    stale_accounts_90d: int


class PrivilegedAccount(BaseModel):
    """Privileged account details."""

    tenant_id: str
    tenant_name: str
    user_principal_name: str
    display_name: str
    user_type: str  # Member, Guest
    role_name: str
    role_scope: str
    is_permanent: bool
    mfa_enabled: bool
    last_sign_in: datetime | None = None
    risk_level: str = "Medium"  # Low, Medium, High


class GuestAccount(BaseModel):
    """Guest account details."""

    tenant_id: str
    tenant_name: str
    user_principal_name: str
    display_name: str
    invited_by: str | None = None
    created_at: datetime | None = None
    last_sign_in: datetime | None = None
    is_stale: bool = False
    days_inactive: int = 0


class StaleAccount(BaseModel):
    """Stale account details."""

    tenant_id: str
    tenant_name: str
    user_principal_name: str
    display_name: str
    user_type: str
    last_sign_in: datetime | None = None
    days_inactive: int
    has_licenses: bool
    has_privileged_roles: bool


# Update forward references
IdentitySummary.model_rebuild()
