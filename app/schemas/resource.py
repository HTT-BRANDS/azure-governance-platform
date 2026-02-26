"""Resource-related Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class ResourceItem(BaseModel):
    """Individual resource in inventory."""

    id: str
    tenant_id: str
    tenant_name: str
    subscription_id: str
    subscription_name: str
    resource_group: str
    resource_type: str
    name: str
    location: str
    provisioning_state: str | None = None
    sku: str | None = None
    tags: dict[str, str] = Field(default_factory=dict)
    is_orphaned: bool = False
    estimated_monthly_cost: float | None = None
    last_synced: datetime


class ResourceInventory(BaseModel):
    """Resource inventory summary."""

    total_resources: int
    resources_by_type: dict[str, int] = Field(default_factory=dict)
    resources_by_location: dict[str, int] = Field(default_factory=dict)
    resources_by_tenant: dict[str, int] = Field(default_factory=dict)
    orphaned_resources: int
    orphaned_estimated_cost: float
    resources: list[ResourceItem] = Field(default_factory=list)


class TaggingCompliance(BaseModel):
    """Tagging compliance summary."""

    total_resources: int
    fully_tagged: int
    partially_tagged: int
    untagged: int
    compliance_percent: float
    required_tags: list[str] = Field(default_factory=list)
    missing_tags_by_resource: list["MissingTags"] = Field(default_factory=list)


class MissingTags(BaseModel):
    """Resources with missing required tags."""

    resource_id: str
    resource_name: str
    resource_type: str
    missing_tags: list[str]


class OrphanedResource(BaseModel):
    """Orphaned resource details."""

    resource_id: str
    resource_name: str
    resource_type: str
    tenant_name: str
    subscription_name: str
    estimated_monthly_cost: float | None
    days_inactive: int
    reason: str  # no_activity, no_dependencies, etc.


# Update forward references
TaggingCompliance.model_rebuild()
