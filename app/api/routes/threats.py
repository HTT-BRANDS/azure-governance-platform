"""Threat intelligence API routes.

Endpoints for retrieving threat intelligence data from Riverside/Cybeta sources.

Traces: RC-030, RC-031 (Riverside threat data integration)
"""

from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.services.threat_intel_service import (
    ThreatIntelService,
    get_threat_intel_service,
)
from app.core.auth import User, get_current_user
from app.core.authorization import (
    TenantAuthorization,
    get_tenant_authorization,
)
from app.core.database import get_db

router = APIRouter(
    prefix="/api/v1/threats",
    tags=["threats"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/cybeta")
async def get_cybeta_threats(
    current_user: User = Depends(get_current_user),
    tenant_ids: list[str] | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    authz: TenantAuthorization = Depends(get_tenant_authorization),
) -> list[dict[str, Any]]:
    """Get threat intelligence data from Riverside/Cybeta sources.

    Retrieves threat intelligence data including vulnerability counts,
    threat scores, and peer comparison metrics.

    Args:
        tenant_ids: Optional list of tenant IDs to filter results
        start_date: Start date for date range filtering
        end_date: End date for date range filtering
        limit: Maximum number of records to return (default 100, max 500)

    Returns:
        List of threat intelligence records
    """
    # Ensure user has access to at least one tenant
    authz.ensure_at_least_one_tenant()

    # Filter tenant IDs to only those user has access to
    filtered_tenant_ids = authz.filter_tenant_ids(tenant_ids)

    service: ThreatIntelService = get_threat_intel_service()
    return service.get_cybeta_threats(
        db=db,
        tenant_ids=filtered_tenant_ids,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )


@router.get("/summary/{tenant_id}")
async def get_threat_summary(
    tenant_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    authz: TenantAuthorization = Depends(get_tenant_authorization),
) -> dict[str, Any]:
    """Get threat summary for a specific tenant.

    Returns the latest threat snapshot and aggregated statistics for
    the specified tenant.

    Args:
        tenant_id: The tenant ID to get summary for

    Returns:
        Dictionary with aggregated threat summary
    """
    # Validate access to the tenant
    authz.validate_access(tenant_id)

    service: ThreatIntelService = get_threat_intel_service()
    return service.get_threat_summary(db=db, tenant_id=tenant_id)
