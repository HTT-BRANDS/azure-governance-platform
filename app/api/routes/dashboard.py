"""Dashboard API routes."""

from datetime import datetime

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.api.services.compliance_service import ComplianceService
from app.api.services.cost_service import CostService
from app.api.services.identity_service import IdentityService
from app.api.services.monitoring_service import MonitoringService
from app.api.services.resource_service import ResourceService
from app.core.database import get_db
from app.models.monitoring import Alert, SyncJobLog
from app.models.tenant import Tenant

router = APIRouter(tags=["dashboard"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """Main dashboard page."""
    # Get summary data from all services
    cost_svc = CostService(db)
    compliance_svc = ComplianceService(db)
    resource_svc = ResourceService(db)
    identity_svc = IdentityService(db)

    cost_summary = cost_svc.get_cost_summary()
    compliance_summary = compliance_svc.get_compliance_summary()
    resource_inventory = resource_svc.get_resource_inventory(limit=10)
    identity_summary = identity_svc.get_identity_summary()

    return templates.TemplateResponse(
        "pages/dashboard.html",
        {
            "request": request,
            "cost_summary": cost_summary,
            "compliance_summary": compliance_summary,
            "resource_inventory": resource_inventory,
            "identity_summary": identity_summary,
        },
    )


@router.get("/partials/cost-summary-card", response_class=HTMLResponse)
async def cost_summary_card(request: Request, db: Session = Depends(get_db)):
    """HTMX partial: Cost summary card."""
    cost_svc = CostService(db)
    summary = cost_svc.get_cost_summary()

    return templates.TemplateResponse(
        "components/cost_summary_card.html",
      {"request": request, "summary": summary},
    )


@router.get("/partials/compliance-gauge", response_class=HTMLResponse)
async def compliance_gauge(request: Request, db: Session = Depends(get_db)):
    """HTMX partial: Compliance score gauge."""
    compliance_svc = ComplianceService(db)
    summary = compliance_svc.get_compliance_summary()

    return templates.TemplateResponse(
        "components/compliance_gauge.html",
        {"request": request, "summary": summary},
    )


@router.get("/partials/resource-stats", response_class=HTMLResponse)
async def resource_stats(request: Request, db: Session = Depends(get_db)):
    """HTMX partial: Resource statistics."""
    resource_svc = ResourceService(db)
    inventory = resource_svc.get_resource_inventory()

    return templates.TemplateResponse(
        "components/resource_stats.html",
        {"request": request, "inventory": inventory},
    )


@router.get("/partials/identity-stats", response_class=HTMLResponse)
async def identity_stats(request: Request, db: Session = Depends(get_db)):
    """HTMX partial: Identity statistics."""
    identity_svc = IdentityService(db)
    summary = identity_svc.get_identity_summary()

    return templates.TemplateResponse(
        "components/identity_stats.html",
        {"request": request, "summary": summary},
    )


# ============================================================================
# Sync Dashboard Routes
# ============================================================================


@router.get("/sync-dashboard", response_class=HTMLResponse)
async def sync_dashboard(request: Request, db: Session = Depends(get_db)):
    """Main sync dashboard page for DevOps/SRE monitoring."""
    monitoring = MonitoringService(db)

    # Get overall sync status
    overall_status = monitoring.get_overall_status()

    # Get recent sync history (last 20 jobs)
    recent_logs = monitoring.get_recent_logs(limit=20, include_running=True)

    # Get active alerts
    active_alerts = monitoring.get_active_alerts()[:10]
    alert_stats = monitoring.get_alert_stats()

    # Get tenant sync status
    tenant_status = await _get_tenant_sync_status(db, monitoring)

    # Get metrics for all job types
    metrics = monitoring.get_metrics()

    return templates.TemplateResponse(
        "pages/sync_dashboard.html",
        {
            "request": request,
            "overall_status": overall_status,
            "recent_logs": recent_logs,
            "active_alerts": active_alerts,
            "alert_stats": alert_stats,
            "tenant_status": tenant_status,
            "metrics": metrics,
            "last_refresh": datetime.utcnow(),
        },
    )


async def _get_tenant_sync_status(
    db: Session, monitoring: MonitoringService
) -> list[dict]:
    """Get per-tenant sync status for all sync types."""
    tenants = db.query(Tenant).filter(Tenant.is_active).all()
    sync_types = ["costs", "compliance", "resources", "identity"]

    tenant_status = []
    for tenant in tenants:
        tenant_syncs = []
        overall_health = "healthy"

        for sync_type in sync_types:
            # Get last log for this tenant and sync type
            last_log = (
                db.query(SyncJobLog)
                .filter(
                    SyncJobLog.job_type == sync_type,
                    SyncJobLog.tenant_id == tenant.id,
                )
                .order_by(SyncJobLog.started_at.desc())
                .first()
            )

            if last_log:
                # Calculate staleness
                hours_since_sync = (
                    datetime.utcnow() - last_log.started_at
                ).total_seconds() / 3600
                expected_interval = 24  # hours

                if last_log.status == "failed":
                    status = "error"
                    overall_health = "error" if overall_health == "healthy" else overall_health
                elif hours_since_sync > expected_interval * 2:
                    status = "stale"
                    overall_health = "warning" if overall_health == "healthy" else overall_health
                elif hours_since_sync > expected_interval * 1.5:
                    status = "warning"
                    overall_health = "warning" if overall_health == "healthy" else overall_health
                else:
                    status = "healthy"

                tenant_syncs.append({
                    "sync_type": sync_type,
                    "status": status,
                    "last_run": last_log.started_at,
                    "last_status": last_log.status,
                    "records_processed": last_log.records_processed,
                    "errors_count": last_log.errors_count,
                })
            else:
                tenant_syncs.append({
                    "sync_type": sync_type,
                    "status": "never_run",
                    "last_run": None,
                    "last_status": None,
                    "records_processed": 0,
                    "errors_count": 0,
                })
                if overall_health == "healthy":
                    overall_health = "warning"

        # Count alerts for this tenant
        tenant_alerts = (
            db.query(Alert)
            .filter(
                Alert.tenant_id == tenant.id,
                Alert.is_resolved == 0,
            )
            .count()
        )

        tenant_status.append({
            "tenant": tenant,
            "syncs": tenant_syncs,
            "overall_health": overall_health,
            "alert_count": tenant_alerts,
        })

    return tenant_status


@router.get("/partials/sync-status-card", response_class=HTMLResponse)
async def sync_status_card_partial(request: Request, db: Session = Depends(get_db)):
    """HTMX partial: Live sync status card (refreshes every 30s)."""
    monitoring = MonitoringService(db)
    overall_status = monitoring.get_overall_status()
    metrics = monitoring.get_metrics()

    return templates.TemplateResponse(
        "components/sync/sync_status_card.html",
        {
            "request": request,
            "status": overall_status,
            "metrics": metrics,
            "last_refresh": datetime.utcnow(),
        },
    )


@router.get("/partials/sync-history-table", response_class=HTMLResponse)
async def sync_history_table_partial(
    request: Request, limit: int = 15, db: Session = Depends(get_db)
):
    """HTMX partial: Recent sync jobs table."""
    monitoring = MonitoringService(db)
    recent_logs = monitoring.get_recent_logs(limit=limit, include_running=True)

    return templates.TemplateResponse(
        "components/sync/sync_history_table.html",
        {
            "request": request,
            "logs": recent_logs,
            "last_refresh": datetime.utcnow(),
        },
    )


@router.get("/partials/active-alerts", response_class=HTMLResponse)
async def active_alerts_partial(request: Request, db: Session = Depends(get_db)):
    """HTMX partial: Active alerts panel."""
    monitoring = MonitoringService(db)
    active_alerts = monitoring.get_active_alerts()[:10]
    alert_stats = monitoring.get_alert_stats()

    return templates.TemplateResponse(
        "components/sync/active_alerts.html",
        {
            "request": request,
            "alerts": active_alerts,
            "stats": alert_stats,
            "last_refresh": datetime.utcnow(),
        },
    )


@router.get("/partials/tenant-sync-status", response_class=HTMLResponse)
async def tenant_sync_status_partial(request: Request, db: Session = Depends(get_db)):
    """HTMX partial: Per-tenant sync status grid."""
    monitoring = MonitoringService(db)
    tenant_status = await _get_tenant_sync_status(db, monitoring)

    return templates.TemplateResponse(
        "components/sync/tenant_sync_grid.html",
        {
            "request": request,
            "tenant_status": tenant_status,
            "last_refresh": datetime.utcnow(),
        },
    )
