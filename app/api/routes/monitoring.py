"""Performance monitoring API routes."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import User, get_current_user, require_roles
from app.core.authorization import (
    TenantAuthorization,
    get_tenant_authorization,
    validate_tenant_access,
)
from app.core.database import get_db
from app.core.monitoring import (
    get_cache_stats,
    get_performance_dashboard,
    performance_monitor,
    reset_metrics,
)

router = APIRouter(
    prefix="/monitoring",
    tags=["monitoring"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/performance")
async def get_performance_metrics() -> dict[str, Any]:
    """Get comprehensive performance metrics.

    Returns cache stats, sync job performance, and query metrics.
    """
    return get_performance_dashboard()


@router.get("/cache")
async def get_cache_metrics() -> dict[str, Any]:
    """Get cache hit/miss metrics and statistics."""
    return get_cache_stats()


@router.get("/sync-jobs")
async def get_sync_job_metrics(
    job_type: str | None = None,
    tenant_id: str | None = None,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """Get sync job performance metrics.

    Args:
        job_type: Filter by job type (e.g., 'resources', 'costs')
        tenant_id: Filter by tenant ID
        limit: Maximum number of records to return
    """
    return performance_monitor.get_sync_metrics(job_type, tenant_id, limit)


@router.get("/queries")
async def get_query_metrics(
    slow_only: bool = False,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Get query performance metrics.

    Args:
        slow_only: Only return slow queries (above threshold)
        limit: Maximum number of records to return
    """
    return performance_monitor.get_query_metrics(slow_only, limit)


@router.post("/reset")
async def reset_performance_metrics() -> dict[str, str]:
    """Reset all performance metrics. Use with caution!"""
    reset_metrics()
    return {"status": "Metrics reset successfully"}


@router.get("/health")
async def health_check() -> dict[str, Any]:
    """Quick health check with basic performance indicators."""
    cache_metrics = get_cache_stats()
    perf_summary = get_performance_dashboard()

    # Determine health status based on cache hit rate
    hit_rate = cache_metrics.get("hit_rate_percent", 0)
    if hit_rate < 50:
        cache_health = "poor"
    elif hit_rate < 80:
        cache_health = "fair"
    else:
        cache_health = "good"

    return {
        "status": "healthy",
        "cache_health": cache_health,
        "cache_hit_rate": hit_rate,
        "total_sync_jobs": perf_summary["sync_jobs"]["total_jobs"],
        "total_queries": perf_summary["queries"]["total_queries"],
        "slow_queries": perf_summary["queries"]["slow_queries"],
    }
