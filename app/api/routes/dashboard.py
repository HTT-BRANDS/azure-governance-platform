"""Dashboard API routes."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.services.cost_service import CostService
from app.api.services.compliance_service import ComplianceService
from app.api.services.resource_service import ResourceService
from app.api.services.identity_service import IdentityService

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
