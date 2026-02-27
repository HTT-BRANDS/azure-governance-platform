"""Identity governance API routes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.services.identity_service import IdentityService
from app.core.database import get_db
from app.schemas.identity import (
    GuestAccount,
    IdentitySummary,
    PrivilegedAccount,
    StaleAccount,
)

router = APIRouter(prefix="/api/v1/identity", tags=["identity"])


@router.get("/summary", response_model=IdentitySummary)
async def get_identity_summary(
    tenant_ids: list[str] | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Get aggregated identity summary across all tenants.

    Args:
        tenant_ids: Filter by specific tenants
    """
    service = IdentityService(db)
    return service.get_identity_summary()


@router.get("/privileged", response_model=list[PrivilegedAccount])
async def get_privileged_accounts(
    tenant_id: str | None = Query(default=None),
    tenant_ids: list[str] | None = Query(default=None),
    risk_level: str | None = Query(default=None, regex="^(High|Medium|Low)$"),
    mfa_enabled: bool | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    sort_by: str = Query(default="display_name"),
    sort_order: str = Query(default="asc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db),
):
    """Get privileged account details.

    Args:
        tenant_id: Single tenant filter (deprecated, use tenant_ids)
        tenant_ids: Filter by specific tenants
        risk_level: Filter by risk level (High, Medium, Low)
        mfa_enabled: Filter by MFA status
        limit: Maximum results to return
        offset: Pagination offset
        sort_by: Field to sort by
        sort_order: Sort direction (asc or desc)
    """
    service = IdentityService(db)
    accounts = service.get_privileged_accounts(tenant_id=tenant_id)

    if tenant_ids:
        accounts = [a for a in accounts if a.tenant_id in tenant_ids]
    if risk_level:
        accounts = [a for a in accounts if a.risk_level == risk_level]
    if mfa_enabled is not None:
        accounts = [a for a in accounts if a.mfa_enabled == mfa_enabled]

    return accounts[offset : offset + limit]


@router.get("/guests", response_model=list[GuestAccount])
async def get_guest_accounts(
    tenant_id: str | None = Query(default=None),
    tenant_ids: list[str] | None = Query(default=None),
    stale_only: bool = Query(default=False),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """Get guest account details.

    Args:
        tenant_id: Single tenant filter (deprecated, use tenant_ids)
        tenant_ids: Filter by specific tenants
        stale_only: Only show stale guest accounts
        limit: Maximum results to return
        offset: Pagination offset
    """
    service = IdentityService(db)
    guests = service.get_guest_accounts(tenant_id=tenant_id, stale_only=stale_only)

    if tenant_ids:
        guests = [g for g in guests if g.tenant_id in tenant_ids]

    return guests[offset : offset + limit]


@router.get("/stale", response_model=list[StaleAccount])
async def get_stale_accounts(
    days_inactive: int = Query(default=30, ge=7, le=365),
    tenant_id: str | None = Query(default=None),
    tenant_ids: list[str] | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """Get stale account details.

    Args:
        days_inactive: Days since last activity
        tenant_id: Single tenant filter (deprecated, use tenant_ids)
        tenant_ids: Filter by specific tenants
        limit: Maximum results to return
        offset: Pagination offset
    """
    service = IdentityService(db)
    stale = service.get_stale_accounts(
        days_inactive=days_inactive, tenant_id=tenant_id
    )

    if tenant_ids:
        stale = [s for s in stale if s.tenant_id in tenant_ids]

    return stale[offset : offset + limit]


@router.get("/trends")
async def get_identity_trends(
    tenant_ids: list[str] | None = Query(default=None),
    days: int = Query(default=30, ge=7, le=365),
    db: Session = Depends(get_db),
):
    """Get identity metrics trends over time.

    Args:
        tenant_ids: Filter by specific tenants
        days: Number of days of history to analyze

    Returns trends for:
    - MFA adoption rate
    - Guest account count
    - Privileged account count
    - Stale account count
    """
    service = IdentityService(db)
    return service.get_identity_trends(tenant_ids=tenant_ids, days=days)
