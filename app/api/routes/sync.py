"""Sync job management API routes."""

from typing import Literal

from fastapi import APIRouter, HTTPException, status

from app.core.scheduler import get_scheduler, trigger_manual_sync

router = APIRouter(prefix="/api/v1/sync", tags=["sync"])

SyncType = Literal["costs", "compliance", "resources", "identity"]


@router.post("/{sync_type}")
async def trigger_sync(sync_type: SyncType):
    """Trigger a manual sync job."""
    success = await trigger_manual_sync(sync_type)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown sync type: {sync_type}",
        )
    return {"status": "triggered", "sync_type": sync_type}


@router.get("/status")
async def get_sync_status():
    """Get status of sync jobs."""
    scheduler = get_scheduler()
    if not scheduler:
        return {"status": "scheduler_not_initialized", "jobs": []}

    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
        })

    return {"status": "running", "jobs": jobs}
