"""Resource-related Pydantic schemas."""

from datetime import datetime
from typing import Dict, List, Optional

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
    provisioning_state: Optional[str] = None
    sku: Optional[str] = None
    tags: Dict[str, str] = Field(default_factory=dict)
    is_orphaned: bool = False
    estimated_monthly_cost: Optional[float] = None
    last_synced: datetime


class ResourceInventory(BaseModel):
    """Resource inventory summary."""

    total_resources: int
    resources_by_type: Dict[str, int] = Field(default_factory=dict)
    resources_by_location: Dict[str, int] = Field(default_factory=dict)
    resources_by_tenant: Dict[str, int] = Field(default_factory=dict)
    orphaned_resources: int
    orphaned_estimated_cost: float
    resources: List[ResourceItem] = Field(default_factory=list)


class TaggingCompliance(BaseModel):
    """Tagging compliance summary."""

    total_resources: int
    fully_tagged: int
    partially_tagged: int
    untagged: int
    compliance_percent: float
    required_tags: List[str] = Field(default_factory=list)
    missing_tags_by_resource: List["MissingTags"] = Field(default_factory=list)


class MissingTags(BaseModel):
    """Resources with missing required tags."""

    resource_id: str
    resource_name: str
    resource_type: str
    missing_tags: List[str]


class OrphanedResource(BaseModel):
    """Orphaned resource details."""

    resource_id: str
    resource_name: str
    resource_type: str
    tenant_name: str
    subscription_name: str
    estimated_monthly_cost: Optional[float]
    days_inactive: int
    reason: str  # no_activity, no_dependencies, etc.


# Update forward references
TaggingCompliance.model_rebuild()
