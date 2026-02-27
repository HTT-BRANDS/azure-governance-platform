"""Cost management API routes."""

from datetime import date

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.services.cost_service import CostService
from app.core.database import get_db
from app.schemas.cost import (
    BulkAcknowledgeRequest,
    BulkAcknowledgeResponse,
    CostByTenant,
    CostSummary,
    CostTrend,
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


router = APIRouter(prefix="/api/v1/costs", tags=["costs"])


@router.get("/summary", response_model=CostSummary)
async def get_cost_summary(
    period_days: int = Query(default=30, ge=1, le=365),
    tenant_ids: list[str] | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Get aggregated cost summary across all tenants.

    Args:
        period_days: Number of days to look back (used if start_date not provided)
        tenant_ids: Filter by specific tenants
        start_date: Optional explicit start date
        end_date: Optional explicit end date
    """
    service = CostService(db)
    return service.get_cost_summary(period_days=period_days)


@router.get("/by-tenant", response_model=list[CostByTenant])
async def get_costs_by_tenant(
    period_days: int = Query(default=30, ge=1, le=365),
    tenant_ids: list[str] | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Get cost breakdown by tenant.

    Args:
        period_days: Number of days to look back
        tenant_ids: Filter by specific tenants
    """
    service = CostService(db)
    costs = service.get_costs_by_tenant(period_days=period_days)

    if tenant_ids:
        costs = [c for c in costs if c.tenant_id in tenant_ids]

    return costs


@router.get("/trends", response_model=list[CostTrend])
async def get_cost_trends(
    days: int = Query(default=30, ge=7, le=365),
    tenant_ids: list[str] | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Get daily cost trends.

    Args:
        days: Number of days of history
        tenant_ids: Filter by specific tenants
        start_date: Optional explicit start date
        end_date: Optional explicit end date
    """
    service = CostService(db)
    return service.get_cost_trends(days=days)


@router.get("/trends/forecast")
async def get_cost_forecast(
    days: int = Query(default=30, ge=7, le=90),
    db: Session = Depends(get_db),
):
    """Get cost forecast using simple linear projection.

    Args:
        days: Number of days to forecast
    """
    service = CostService(db)
    return service.get_cost_forecast(days=days)


@router.get("/anomalies")
async def get_cost_anomalies(
    acknowledged: bool | None = Query(default=None),
    tenant_ids: list[str] | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    sort_by: str = Query(default="detected_at"),
    sort_order: str = Query(default="desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db),
):
    """Get cost anomalies with filtering and pagination.

    Args:
        acknowledged: Filter by acknowledged status
        tenant_ids: Filter by specific tenants
        limit: Maximum results to return
        offset: Pagination offset
        sort_by: Field to sort by
        sort_order: Sort direction (asc or desc)
    """
    service = CostService(db)
    anomalies = service.get_anomalies(acknowledged=acknowledged)

    if tenant_ids:
        anomalies = [a for a in anomalies if a.tenant_id in tenant_ids]

    return anomalies[offset : offset + limit]


@router.get("/anomalies/trends")
async def get_anomaly_trends(
    months: int = Query(default=6, ge=1, le=24),
    db: Session = Depends(get_db),
):
    """Get anomaly trends over time grouped by month.

    Args:
        months: Number of months to analyze
    """
    service = CostService(db)
    return service.get_anomaly_trends(months=months)


@router.get("/anomalies/by-service")
async def get_anomalies_by_service(
    limit: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Get anomalies grouped by service.

    Args:
        limit: Maximum number of services to return
    """
    service = CostService(db)
    return service.get_anomalies_by_service(limit=limit)


@router.get("/anomalies/top")
async def get_top_anomalies(
    n: int = Query(default=10, ge=1, le=50),
    acknowledged: bool | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Get top N anomalies by impact.

    Args:
        n: Number of top anomalies to return
        acknowledged: Filter by acknowledged status
    """
    service = CostService(db)
    return service.get_top_anomalies(n=n, acknowledged=acknowledged)


@router.post("/anomalies/{anomaly_id}/acknowledge")
async def acknowledge_anomaly(
    anomaly_id: int,
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Acknowledge a cost anomaly."""
    service = CostService(db)
    success = service.acknowledge_anomaly(anomaly_id, user=user)
    return {"success": success}


@router.post("/anomalies/bulk-acknowledge", response_model=BulkAcknowledgeResponse)
async def bulk_acknowledge_anomalies(
    request: BulkAcknowledgeRequest,
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Acknowledge multiple cost anomalies at once.

    Args:
        request: Contains list of anomaly IDs to acknowledge
        user: User performing the acknowledgment
    """
    service = CostService(db)
    return service.bulk_acknowledge_anomalies(request.anomaly_ids, user=user)
