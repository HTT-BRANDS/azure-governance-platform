"""Compliance monitoring API routes."""


from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.services.compliance_service import ComplianceService
from app.core.database import get_db
from app.schemas.compliance import ComplianceScore, ComplianceSummary, PolicyStatus

router = APIRouter(prefix="/api/v1/compliance", tags=["compliance"])


@router.get("/summary", response_model=ComplianceSummary)
async def get_compliance_summary(db: Session = Depends(get_db)):
    """Get aggregated compliance summary across all tenants."""
    service = ComplianceService(db)
    return service.get_compliance_summary()


@router.get("/scores", response_model=list[ComplianceScore])
async def get_compliance_scores(
    tenant_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Get compliance scores, optionally filtered by tenant."""
    service = ComplianceService(db)
    return service.get_scores_by_tenant(tenant_id=tenant_id)


@router.get("/non-compliant", response_model=list[PolicyStatus])
async def get_non_compliant_policies(
    tenant_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Get non-compliant policy details."""
    service = ComplianceService(db)
    return service.get_non_compliant_policies(tenant_id=tenant_id)
