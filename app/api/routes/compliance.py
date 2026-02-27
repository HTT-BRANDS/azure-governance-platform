"""Compliance monitoring API routes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.services.compliance_service import ComplianceService
from app.core.database import get_db
from app.schemas.compliance import ComplianceScore, ComplianceSummary, PolicyStatus

router = APIRouter(prefix="/api/v1/compliance", tags=["compliance"])


@router.get("/summary", response_model=ComplianceSummary)
async def get_compliance_summary(
    tenant_ids: list[str] | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Get aggregated compliance summary across all tenants.

    Args:
        tenant_ids: Filter by specific tenants
    """
    service = ComplianceService(db)
    return service.get_compliance_summary()


@router.get("/scores", response_model=list[ComplianceScore])
async def get_compliance_scores(
    tenant_id: str | None = Query(default=None),
    tenant_ids: list[str] | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """Get compliance scores, optionally filtered by tenant.

    Args:
        tenant_id: Single tenant filter (deprecated, use tenant_ids)
        tenant_ids: Filter by specific tenants
        limit: Maximum results to return
        offset: Pagination offset
    """
    service = ComplianceService(db)
    scores = service.get_scores_by_tenant(tenant_id=tenant_id)

    if tenant_ids:
        scores = [s for s in scores if s.tenant_id in tenant_ids]

    return scores[offset : offset + limit]


@router.get("/non-compliant", response_model=list[PolicyStatus])
async def get_non_compliant_policies(
    tenant_id: str | None = Query(default=None),
    tenant_ids: list[str] | None = Query(default=None),
    severity: str | None = Query(default=None, regex="^(High|Medium|Low)$"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    sort_by: str = Query(default="non_compliant_count"),
    sort_order: str = Query(default="desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db),
):
    """Get non-compliant policy details.

    Args:
        tenant_id: Single tenant filter (deprecated, use tenant_ids)
        tenant_ids: Filter by specific tenants
        severity: Filter by severity level
        limit: Maximum results to return
        offset: Pagination offset
        sort_by: Field to sort by
        sort_order: Sort direction (asc or desc)
    """
    service = ComplianceService(db)
    policies = service.get_non_compliant_policies(tenant_id=tenant_id)

    if tenant_ids:
        policies = [p for p in policies if p.tenant_id in tenant_ids]

    if severity:
        policies = [p for p in policies if p.severity == severity]

    return policies[offset : offset + limit]


@router.get("/trends")
async def get_compliance_trends(
    tenant_ids: list[str] | None = Query(default=None),
    days: int = Query(default=30, ge=7, le=365),
    db: Session = Depends(get_db),
):
    """Get compliance score trends over time.

    Args:
        tenant_ids: Filter by specific tenants
        days: Number of days of history to analyze
    """
    service = ComplianceService(db)
    return service.get_compliance_trends(tenant_ids=tenant_ids, days=days)
