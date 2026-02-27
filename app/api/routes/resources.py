"""Resource management API routes."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.services.resource_service import ResourceService
from app.core.database import get_db
from app.schemas.resource import (
    IdleResource,
    IdleResourceSummary,
    OrphanedResource,
    ResourceInventory,
    TagResourceRequest,
    TagResourceResponse,
    TaggingCompliance,
)


def get_current_user(request: Request) -> str:
    """Get the current user from request headers or query params."""
    user_id = request.headers.get("X-User-Id")
    if user_id:
        return user_id
    user_id = request.query_params.get("user")
    if user_id:
        return user_id
    return "system"


router = APIRouter(prefix="/api/v1/resources", tags=["resources"])


@router.get("", response_model=ResourceInventory)
async def get_resources(
    tenant_id: str | None = Query(default=None),
    tenant_ids: list[str] | None = Query(default=None),
    resource_type: str | None = Query(default=None),
    limit: int = Query(default=500, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    sort_by: str = Query(default="name"),
    sort_order: str = Query(default="asc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db),
):
    """Get resource inventory with filtering and pagination.

    Args:
        tenant_id: Filter by single tenant (deprecated, use tenant_ids)
        tenant_ids: Filter by specific tenants
        resource_type: Filter by resource type
        limit: Maximum results to return
        offset: Pagination offset
        sort_by: Field to sort by
        sort_order: Sort direction (asc or desc)
    """
    service = ResourceService(db)
    inventory = service.get_resource_inventory(
        tenant_id=tenant_id,
        resource_type=resource_type,
        limit=limit,
    )

    # Apply tenant_ids filter if provided
    if tenant_ids:
        inventory.resources = [r for r in inventory.resources if r.tenant_id in tenant_ids]
        inventory.total_resources = len(inventory.resources)

    return inventory


@router.get("/orphaned", response_model=list[OrphanedResource])
async def get_orphaned_resources(
    tenant_ids: list[str] | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """Get orphaned resources with filtering and pagination.

    Args:
        tenant_ids: Filter by specific tenants
        limit: Maximum results to return
        offset: Pagination offset
    """
    service = ResourceService(db)
    orphaned = service.get_orphaned_resources()

    if tenant_ids:
        orphaned = [o for o in orphaned if o.tenant_name in tenant_ids]

    return orphaned[offset : offset + limit]


@router.get("/idle", response_model=list[IdleResource])
async def get_idle_resources(
    tenant_ids: list[str] | None = Query(default=None),
    idle_type: str | None = Query(default=None),
    is_reviewed: bool | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    sort_by: str = Query(default="estimated_monthly_savings"),
    sort_order: str = Query(default="desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db),
):
    """Get idle resources with filtering and pagination.

    Args:
        tenant_ids: Filter by specific tenants
        idle_type: Filter by idle type (e.g., low_cpu, no_connections)
        is_reviewed: Filter by review status
        limit: Maximum results to return
        offset: Pagination offset
        sort_by: Field to sort by
        sort_order: Sort direction (asc or desc)
    """
    service = ResourceService(db)
    return service.get_idle_resources(
        tenant_ids=tenant_ids,
        idle_type=idle_type,
        is_reviewed=is_reviewed,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get("/idle/summary", response_model=IdleResourceSummary)
async def get_idle_resources_summary(db: Session = Depends(get_db)):
    """Get summary of idle resources."""
    service = ResourceService(db)
    return service.get_idle_resources_summary()


@router.post("/idle/{idle_resource_id}/tag", response_model=TagResourceResponse)
async def tag_idle_resource(
    idle_resource_id: int,
    request_data: TagResourceRequest | None = None,
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Tag an idle resource as reviewed.

    Args:
        idle_resource_id: ID of the idle resource to tag
        request_data: Optional review notes
        user: User performing the tagging
    """
    service = ResourceService(db)
    return service.tag_idle_resource_as_reviewed(
        idle_resource_id=idle_resource_id,
        user=user,
        notes=request_data.notes if request_data else None,
    )


@router.get("/tagging", response_model=TaggingCompliance)
async def get_tagging_compliance(
    required_tags: list[str] | None = Query(default=None),
    tenant_ids: list[str] | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Get tagging compliance summary.

    Args:
        required_tags: List of required tags to check
        tenant_ids: Filter by specific tenants
    """
    service = ResourceService(db)
    return service.get_tagging_compliance(required_tags=required_tags)
