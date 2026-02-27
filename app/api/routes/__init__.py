"""API routes module."""

from app.api.routes.auth import router as auth_router
from app.api.routes.bulk import router as bulk_router
from app.api.routes.compliance import router as compliance_router
from app.api.routes.costs import router as costs_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.exports import router as exports_router
from app.api.routes.identity import router as identity_router
from app.api.routes.monitoring import router as monitoring_router
from app.api.routes.preflight import router as preflight_router
from app.api.routes.recommendations import router as recommendations_router
from app.api.routes.resources import router as resources_router
from app.api.routes.riverside import router as riverside_router
from app.api.routes.sync import router as sync_router
from app.api.routes.tenants import router as tenants_router

__all__ = [
    "auth_router",
    "dashboard_router",
    "costs_router",
    "compliance_router",
    "resources_router",
    "identity_router",
    "tenants_router",
    "sync_router",
    "preflight_router",
    "riverside_router",
    "recommendations_router",
    "exports_router",
    "bulk_router",
    "monitoring_router",
]
