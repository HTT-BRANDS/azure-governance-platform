"""Resource management API routes."""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.services.resource_service import ResourceService
from app.schemas.resource import (
    OrphanedResource,
    ResourceInventory,
    TaggingCompliance,
)

router = APIRouter(prefix="/api/v1/resources", tags=["resources"])


@router.get("", response_model=ResourceInventory)
async def get_resources(
    tenant_id: Optional[str] = Query(default=None),
    resource_type: Optional[str] = Query(default=None),
    limit: int = Query(default=500, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Get resource inventory."""
    service = ResourceService(db)
    return service.get_resource_inventory(
        tenant_id=tenant_id,
        resource_type=resource_type,
        limit=limit,
    )


@router.get("/orphaned", response_model=list[OrphanedResource])
async def get_orphaned_resources(db: Session = Depends(get_db)):
    """Get orphaned resources."""
    service = ResourceService(db)
    return service.get_orphaned_resources()


@router.get("/tagging", response_model=TaggingCompliance)
async def get_tagging_compliance(
    required_tags: Optional[List[str]] = Query(default=None),
    db: Session = Depends(get_db),
):
    """Get tagging compliance summary."""
    service = ResourceService(db)
    return service.get_tagging_compliance(required_tags=required_tags)
