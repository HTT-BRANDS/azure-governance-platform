"""Bulk operation API routes."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.services.bulk_service import BulkService
from app.core.database import get_db
from app.schemas.resource import (
    BulkAnomalyAcknowledgeRequest,
    BulkAnomalyAcknowledgeResponse,
    BulkIdleResourceReviewRequest,
    BulkIdleResourceReviewResponse,
    BulkRecommendationDismissRequest,
    BulkRecommendationDismissResponse,
    BulkTagOperation,
    BulkTagResponse,
)

router = APIRouter(prefix="/bulk", tags=["bulk"])


@router.post("/tags/apply", response_model=BulkTagResponse)
async def bulk_apply_tags(
    operation: BulkTagOperation,
    user: str = "api_user",  # TODO: Get from auth
    db: Session = Depends(get_db),
) -> BulkTagResponse:
    """Apply tags to multiple resources.

    Supports both specific resource IDs and filter-based selection.
    """
    service = BulkService(db)
    return await service.bulk_tag_resources(operation, user)


@router.post("/tags/remove", response_model=BulkTagResponse)
async def bulk_remove_tags(
    resource_ids: list[str],
    tag_names: list[str],
    user: str = "api_user",  # TODO: Get from auth
    db: Session = Depends(get_db),
) -> BulkTagResponse:
    """Remove tags from multiple resources."""
    service = BulkService(db)
    return await service.bulk_remove_tags(resource_ids, tag_names, user)


@router.post("/anomalies/acknowledge")
async def bulk_acknowledge_anomalies(
    request: BulkAnomalyAcknowledgeRequest,
    user: str = "api_user",  # TODO: Get from auth
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Acknowledge multiple cost anomalies at once."""
    service = BulkService(db)
    result = await service.bulk_acknowledge_anomalies(
        request.anomaly_ids, user, request.notes
    )
    return result


@router.post("/recommendations/dismiss")
async def bulk_dismiss_recommendations(
    request: BulkRecommendationDismissRequest,
    user: str = "api_user",  # TODO: Get from auth
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Dismiss multiple recommendations at once."""
    service = BulkService(db)
    result = await service.bulk_dismiss_recommendations(
        request.recommendation_ids, user, request.reason
    )
    return result


@router.post("/idle-resources/review")
async def bulk_review_idle_resources(
    request: BulkIdleResourceReviewRequest,
    user: str = "api_user",  # TODO: Get from auth
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Mark multiple idle resources as reviewed."""
    service = BulkService(db)
    result = await service.bulk_review_idle_resources(
        request.idle_resource_ids, user, request.notes
    )
    return result
