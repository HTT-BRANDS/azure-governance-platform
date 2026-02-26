"""Cost management API routes."""


from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.services.cost_service import CostService
from app.core.database import get_db
from app.schemas.cost import CostByTenant, CostSummary, CostTrend


def get_current_user(request: Request) -> str:
    """Get the current user from request headers or query params.

    Priority:
    1. X-User-Id header (for API clients)
    2. 'user' query parameter (for testing/HTMX)
    3. 'system' fallback (for MVP/legacy compatibility)
    """
    # Check X-User-Id header first
    user_id = request.headers.get("X-User-Id")
    if user_id:
        return user_id

    # Fall back to query param
    user_id = request.query_params.get("user")
    if user_id:
        return user_id

    # Default fallback
    return "system"

router = APIRouter(prefix="/api/v1/costs", tags=["costs"])


@router.get("/summary", response_model=CostSummary)
async def get_cost_summary(
    period_days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """Get aggregated cost summary across all tenants."""
    service = CostService(db)
    return service.get_cost_summary(period_days=period_days)


@router.get("/by-tenant", response_model=list[CostByTenant])
async def get_costs_by_tenant(
    period_days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """Get cost breakdown by tenant."""
    service = CostService(db)
    return service.get_costs_by_tenant(period_days=period_days)


@router.get("/trends", response_model=list[CostTrend])
async def get_cost_trends(
    days: int = Query(default=30, ge=7, le=365),
    db: Session = Depends(get_db),
):
    """Get daily cost trends."""
    service = CostService(db)
    return service.get_cost_trends(days=days)


@router.get("/anomalies")
async def get_cost_anomalies(
    acknowledged: bool | None = None,
    db: Session = Depends(get_db),
):
    """Get cost anomalies."""
    service = CostService(db)
    return service.get_anomalies(acknowledged=acknowledged)


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
