"""Sync job management API routes."""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.api.services.monitoring_service import MonitoringService
from app.core.database import get_db
from app.core.scheduler import get_scheduler, trigger_manual_sync

router = APIRouter(prefix="/api/v1/sync", tags=["sync"])
templates = Jinja2Templates(directory="app/templates")

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


@router.get("/status")
async def get_sync_health(db: Session = Depends(get_db)):
    """Get overall sync health status with metrics."""
    monitoring = MonitoringService(db)
    return monitoring.get_overall_status()


@router.get("/history")
async def get_sync_history(
    job_type: str | None = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """Get recent sync job execution history."""
    monitoring = MonitoringService(db)
    logs = monitoring.get_recent_logs(
        job_type=job_type, limit=limit, include_running=False
    )

    return {
        "logs": [
            {
                "id": log.id,
                "job_type": log.job_type,
                "tenant_id": log.tenant_id,
                "status": log.status,
                "started_at": log.started_at.isoformat() if log.started_at else None,
                "ended_at": log.ended_at.isoformat() if log.ended_at else None,
                "duration_ms": log.duration_ms,
                "records_processed": log.records_processed,
                "errors_count": log.errors_count,
                "error_message": log.error_message,
            }
            for log in logs
        ]
    }


@router.get("/metrics")
async def get_sync_metrics(
    job_type: str | None = None,
    db: Session = Depends(get_db),
):
    """Get aggregate sync job metrics."""
    monitoring = MonitoringService(db)
    metrics = monitoring.get_metrics(job_type=job_type)

    return {
        "metrics": [
            {
                "job_type": m.job_type,
                "calculated_at": m.calculated_at.isoformat() if m.calculated_at else None,
                "total_runs": m.total_runs,
                "successful_runs": m.successful_runs,
                "failed_runs": m.failed_runs,
                "success_rate": m.success_rate,
                "avg_duration_ms": m.avg_duration_ms,
                "min_duration_ms": m.min_duration_ms,
                "max_duration_ms": m.max_duration_ms,
                "avg_records_processed": m.avg_records_processed,
                "total_records_processed": m.total_records_processed,
                "total_errors": m.total_errors,
                "last_run_at": m.last_run_at.isoformat() if m.last_run_at else None,
                "last_success_at": m.last_success_at.isoformat() if m.last_success_at else None,
                "last_failure_at": m.last_failure_at.isoformat() if m.last_failure_at else None,
                "last_error_message": m.last_error_message,
            }
            for m in metrics
        ]
    }


@router.get("/alerts")
async def get_sync_alerts(
    job_type: str | None = None,
    severity: str | None = None,
    include_resolved: bool = False,
    db: Session = Depends(get_db),
):
    """Get sync job alerts."""
    monitoring = MonitoringService(db)

    if include_resolved:
        # Get all alerts (not just active)
        from app.models.monitoring import Alert

        query = db.query(Alert)
        if job_type:
            query = query.filter(Alert.job_type == job_type)
        if severity:
            query = query.filter(Alert.severity == severity)
        alerts = query.order_by(Alert.created_at.desc()).limit(100).all()
    else:
        alerts = monitoring.get_active_alerts(job_type=job_type, severity=severity)

    return {
        "alerts": [
            {
                "id": alert.id,
                "alert_type": alert.alert_type,
                "severity": alert.severity,
                "job_type": alert.job_type,
                "tenant_id": alert.tenant_id,
                "title": alert.title,
                "message": alert.message,
                "is_resolved": bool(alert.is_resolved),
                "created_at": alert.created_at.isoformat() if alert.created_at else None,
                "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
                "resolved_by": alert.resolved_by,
            }
            for alert in alerts
        ],
        "stats": monitoring.get_alert_stats() if not include_resolved else None,
    }


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int,
    resolved_by: str = "system",
    db: Session = Depends(get_db),
):
    """Resolve a sync job alert."""
    monitoring = MonitoringService(db)
    try:
        alert = monitoring.resolve_alert(alert_id, resolved_by=resolved_by)
        return {
            "id": alert.id,
            "alert_type": alert.alert_type,
            "is_resolved": bool(alert.is_resolved),
            "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
            "resolved_by": alert.resolved_by,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# HTMX Partials
# ============================================================================


@router.get("/partials/sync-status", response_class=HTMLResponse)
async def sync_status_partial(request: Request, db: Session = Depends(get_db)):
    """HTMX partial: Sync status card."""
    monitoring = MonitoringService(db)
    status = monitoring.get_overall_status()
    metrics = monitoring.get_metrics()

    return templates.TemplateResponse(
        "components/sync_status.html",
        {
            "request": request,
            "status": status,
            "metrics": metrics,
        },
    )


@router.get("/partials/sync-alerts", response_class=HTMLResponse)
async def sync_alerts_partial(request: Request, db: Session = Depends(get_db)):
    """HTMX partial: Recent alerts panel."""
    monitoring = MonitoringService(db)
    alerts = monitoring.get_active_alerts()[:10]  # Limit to 10 most recent
    stats = monitoring.get_alert_stats()

    return templates.TemplateResponse(
        "components/sync_alerts.html",
        {
            "request": request,
            "alerts": alerts,
            "stats": stats,
        },
    )
