"""Resource management service."""

import json
import logging
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.resource import Resource, ResourceTag
from app.models.tenant import Tenant
from app.schemas.resource import (
    MissingTags,
    OrphanedResource,
    ResourceInventory,
    ResourceItem,
    TaggingCompliance,
)

logger = logging.getLogger(__name__)

# Default required tags for tagging compliance
DEFAULT_REQUIRED_TAGS = ["Environment", "Owner", "CostCenter", "Application"]


class ResourceService:
    """Service for resource management operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_resource_inventory(
        self,
        tenant_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        limit: int = 500,
    ) -> ResourceInventory:
        """Get resource inventory with aggregations."""
        query = self.db.query(Resource)

        if tenant_id:
            query = query.filter(Resource.tenant_id == tenant_id)
        if resource_type:
            query = query.filter(Resource.resource_type.contains(resource_type))

        resources = query.limit(limit).all()

        # Get tenant names for display
        tenants = {t.id: t.name for t in self.db.query(Tenant).all()}

        # Aggregate by type, location, tenant
        by_type: Dict[str, int] = {}
        by_location: Dict[str, int] = {}
        by_tenant: Dict[str, int] = {}
        orphaned_count = 0
        orphaned_cost = 0.0

        items = []
        for r in resources:
            # Type aggregation
            by_type[r.resource_type] = by_type.get(r.resource_type, 0) + 1

            # Location aggregation
            by_location[r.location] = by_location.get(r.location, 0) + 1

            # Tenant aggregation
            tenant_name = tenants.get(r.tenant_id, "Unknown")
            by_tenant[tenant_name] = by_tenant.get(tenant_name, 0) + 1

            # Orphaned tracking
            if r.is_orphaned:
                orphaned_count += 1
                orphaned_cost += r.estimated_monthly_cost or 0

            # Parse tags
            tags = {}
            if r.tags_json:
                try:
                    tags = json.loads(r.tags_json)
                except json.JSONDecodeError:
                    pass

            items.append(
                ResourceItem(
                    id=r.id,
                    tenant_id=r.tenant_id,
                    tenant_name=tenant_name,
                    subscription_id=r.subscription_id,
                    subscription_name=r.subscription_id,  # TODO: lookup
                    resource_group=r.resource_group,
                    resource_type=r.resource_type,
                    name=r.name,
                    location=r.location or "Unknown",
                    provisioning_state=r.provisioning_state,
                    sku=r.sku,
                    tags=tags,
                    is_orphaned=bool(r.is_orphaned),
                    estimated_monthly_cost=r.estimated_monthly_cost,
                    last_synced=r.synced_at,
                )
            )

        return ResourceInventory(
            total_resources=len(resources),
            resources_by_type=by_type,
            resources_by_location=by_location,
            resources_by_tenant=by_tenant,
            orphaned_resources=orphaned_count,
            orphaned_estimated_cost=orphaned_cost,
            resources=items,
        )

    def get_orphaned_resources(self) -> List[OrphanedResource]:
        """Get list of orphaned resources."""
        resources = (
            self.db.query(Resource)
            .filter(Resource.is_orphaned == 1)
            .order_by(Resource.estimated_monthly_cost.desc())
            .limit(100)
            .all()
        )

        tenants = {t.id: t.name for t in self.db.query(Tenant).all()}

        return [
            OrphanedResource(
                resource_id=r.id,
                resource_name=r.name,
                resource_type=r.resource_type,
                tenant_name=tenants.get(r.tenant_id, "Unknown"),
                subscription_name=r.subscription_id,
                estimated_monthly_cost=r.estimated_monthly_cost,
                days_inactive=30,  # TODO: Calculate from activity data
                reason="no_activity",
            )
            for r in resources
        ]

    def get_tagging_compliance(
        self, required_tags: Optional[List[str]] = None
    ) -> TaggingCompliance:
        """Get tagging compliance summary."""
        if not required_tags:
            required_tags = DEFAULT_REQUIRED_TAGS

        resources = self.db.query(Resource).all()

        fully_tagged = 0
        partially_tagged = 0
        untagged = 0
        missing_tags_list = []

        for r in resources:
            tags = {}
            if r.tags_json:
                try:
                    tags = json.loads(r.tags_json)
                except json.JSONDecodeError:
                    pass

            tag_keys = set(tags.keys())
            required_set = set(required_tags)
            missing = required_set - tag_keys

            if len(missing) == 0:
                fully_tagged += 1
            elif len(missing) == len(required_tags):
                untagged += 1
                missing_tags_list.append(
                    MissingTags(
                        resource_id=r.id,
                        resource_name=r.name,
                        resource_type=r.resource_type,
                        missing_tags=list(missing),
                    )
                )
            else:
                partially_tagged += 1
                missing_tags_list.append(
                    MissingTags(
                        resource_id=r.id,
                        resource_name=r.name,
                        resource_type=r.resource_type,
                        missing_tags=list(missing),
                    )
                )

        total = len(resources)
        compliance_percent = (fully_tagged / total * 100) if total > 0 else 0

        return TaggingCompliance(
            total_resources=total,
            fully_tagged=fully_tagged,
            partially_tagged=partially_tagged,
            untagged=untagged,
            compliance_percent=compliance_percent,
            required_tags=required_tags,
            missing_tags_by_resource=missing_tags_list[:100],  # Limit output
        )
