"""Tenant-related Pydantic schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class TenantCreate(BaseModel):
    """Schema for creating a new tenant."""

    name: str = Field(..., min_length=1, max_length=255)
    tenant_id: str = Field(..., min_length=36, max_length=36)
    client_id: Optional[str] = Field(None, min_length=36, max_length=36)
    client_secret_ref: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    use_lighthouse: bool = False


class TenantUpdate(BaseModel):
    """Schema for updating a tenant."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    client_id: Optional[str] = Field(None, min_length=36, max_length=36)
    client_secret_ref: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    use_lighthouse: Optional[bool] = None


class TenantResponse(BaseModel):
    """Schema for tenant response."""

    id: str
    name: str
    tenant_id: str
    description: Optional[str] = None
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
    synced_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TenantWithSubscriptions(TenantResponse):
    """Tenant response with subscriptions included."""

    subscriptions: List[SubscriptionResponse] = Field(default_factory=list)
