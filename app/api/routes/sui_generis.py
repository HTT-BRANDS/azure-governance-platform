"""Sui Generis device compliance API routes.

Placeholder endpoints for Sui Generis MSP device compliance integration.

Traces: RC-030, RC-031 (Phase 2 - Sui Generis integration)
"""

from fastapi import APIRouter, Depends

from app.api.services.sui_generis_service import (
    SuiGenerisService,
    get_sui_generis_service,
)
from app.core.auth import User, get_current_user

router = APIRouter(
    prefix="/api/v1/compliance",
    tags=["sui-generis"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/device-compliance")
async def get_device_compliance(
    current_user: User = Depends(get_current_user),
    service: SuiGenerisService = Depends(get_sui_generis_service),
) -> dict:
    """Get Sui Generis device compliance status.

    Placeholder endpoint for Sui Generis device compliance integration.
    Returns status information about the upcoming integration.

    Returns:
        Dictionary with device compliance status.
    """
    return service.get_status()


@router.get("/device-compliance/status")
async def get_device_compliance_status(
    current_user: User = Depends(get_current_user),
    service: SuiGenerisService = Depends(get_sui_generis_service),
) -> dict:
    """Get detailed integration status.

    Returns:
        Dictionary with integration status and feature list.
    """
    return service.get_status()
