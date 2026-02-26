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
async def get_identity_summary(db: Session = Depends(get_db)):
    """Get aggregated identity summary across all tenants."""
    service = IdentityService(db)
    return service.get_identity_summary()


@router.get("/privileged", response_model=list[PrivilegedAccount])
async def get_privileged_accounts(
    tenant_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Get privileged account details."""
    service = IdentityService(db)
    return service.get_privileged_accounts(tenant_id=tenant_id)


@router.get("/guests", response_model=list[GuestAccount])
async def get_guest_accounts(
    tenant_id: str | None = Query(default=None),
    stale_only: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    """Get guest account details."""
    service = IdentityService(db)
    return service.get_guest_accounts(tenant_id=tenant_id, stale_only=stale_only)


@router.get("/stale", response_model=list[StaleAccount])
async def get_stale_accounts(
    days_inactive: int = Query(default=30, ge=7, le=365),
    tenant_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Get stale account details."""
    service = IdentityService(db)
    return service.get_stale_accounts(
        days_inactive=days_inactive, tenant_id=tenant_id
    )
