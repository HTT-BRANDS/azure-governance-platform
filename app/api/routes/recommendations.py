"""Recommendations API routes."""

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.services.recommendation_service import RecommendationService
from app.core.database import get_db
from app.schemas.recommendation import (
    DismissRecommendationRequest,
    DismissRecommendationResponse,
    Recommendation,
    RecommendationCategory,
    RecommendationsByCategory,
    RecommendationSummary,
    SavingsPotential,
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


router = APIRouter(prefix="/api/v1/recommendations", tags=["recommendations"])


@router.get("", response_model=list[Recommendation])
async def get_recommendations(
    category: RecommendationCategory | None = Query(default=None),
    tenant_ids: list[str] | None = Query(default=None),
    impact: str | None = Query(default=None, regex="^(Low|Medium|High|Critical)$"),
    dismissed: bool | None = Query(default=False),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    sort_by: str = Query(default="created_at"),
    sort_order: str = Query(default="desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db),
):
    """Get all recommendations with optional filtering.

    Args:
        category: Filter by recommendation category
        tenant_ids: Filter by specific tenants
        impact: Filter by impact level (Low, Medium, High, Critical)
        dismissed: Include dismissed recommendations
        limit: Maximum results to return
        offset: Pagination offset
        sort_by: Field to sort by
        sort_order: Sort direction (asc or desc)
    """
    service = RecommendationService(db)
    return service.get_recommendations(
        category=category,
        tenant_ids=tenant_ids,
        impact=impact,
        dismissed=dismissed,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get("/by-category", response_model=list[RecommendationsByCategory])
async def get_recommendations_by_category(db: Session = Depends(get_db)):
    """Get recommendations grouped by category (cost, security, performance, reliability)."""
    service = RecommendationService(db)
    return service.get_recommendations_by_category()


@router.get("/by-tenant")
async def get_recommendations_by_tenant(db: Session = Depends(get_db)):
    """Get recommendations grouped by tenant."""
    service = RecommendationService(db)
    return service.get_recommendations_by_tenant()


@router.get("/savings-potential", response_model=SavingsPotential)
async def get_savings_potential(db: Session = Depends(get_db)):
    """Get total potential savings across all recommendations."""
    service = RecommendationService(db)
    return service.get_savings_potential()


@router.get("/summary", response_model=list[RecommendationSummary])
async def get_recommendation_summary(db: Session = Depends(get_db)):
    """Get summary statistics by category."""
    service = RecommendationService(db)
    return service.get_recommendation_summary()


@router.post("/{recommendation_id}/dismiss", response_model=DismissRecommendationResponse)
async def dismiss_recommendation(
    recommendation_id: int,
    request_data: DismissRecommendationRequest | None = None,
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Dismiss a recommendation.

    Args:
        recommendation_id: ID of the recommendation to dismiss
        request_data: Optional dismissal reason
        user: User performing the dismissal
    """
    service = RecommendationService(db)
    return service.dismiss_recommendation(
        recommendation_id=recommendation_id,
        user=user,
        reason=request_data.reason if request_data else None,
    )
