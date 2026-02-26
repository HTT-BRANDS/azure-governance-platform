"""Tenant-related Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class TenantCreate(BaseModel):
    """Schema for creating a new tenant."""

    name: str = Field(..., min_length=1, max_length=255)
    tenant_id: str = Field(..., min_length=36, max_length=36)
    client_id: str | None = Field(None, min_length=36, max_length=36)
    client_secret_ref: str | None = Field(None, max_length=500)
    description: str | None = None
    use_lighthouse: bool = False


class TenantUpdate(BaseModel):
    """Schema for updating a tenant."""

    name: str | None = Field(None, min_length=1, max_length=255)
    client_id: str | None = Field(None, min_length=36, max_length=36)
    client_secret_ref: str | None = Field(None, max_length=500)
    description: str | None = None
    is_active: bool | None = None
    use_lighthouse: bool | None = None


class TenantResponse(BaseModel):
    """Schema for tenant response."""

    id: str
    name: str
    tenant_id: str
    description: str | None = None
    is_active: bool
    use_lighthouse: bool
    subscription_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SubscriptionResponse(BaseModel):
    """Schema for subscription response."""

    id: str
    subscription_id: str
    display_name: str
    state: str
    tenant_id: str
    synced_at: datetime | None = None

    model_config = {"from_attributes": True}


class TenantWithSubscriptions(TenantResponse):
    """Tenant response with subscriptions included."""

    subscriptions: list[SubscriptionResponse] = Field(default_factory=list)
