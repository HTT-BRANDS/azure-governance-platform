"""Compliance framework reference data routes — CM-003.

Exposes read-only endpoints for SOC2 and NIST CSF framework definitions
loaded from config/compliance_frameworks.yaml.

All endpoints require authentication (get_current_user dependency).
Framework data is global (not tenant-scoped) per ADR-0006.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path, status

from app.api.services.compliance_frameworks_service import (
    ComplianceFrameworksService,
    compliance_frameworks_service,
)
from app.core.auth import User, get_current_user
from app.core.rate_limit import rate_limit

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/compliance/frameworks",
    tags=["compliance-frameworks"],
    dependencies=[Depends(get_current_user), Depends(rate_limit("default"))],
)


def _get_service() -> ComplianceFrameworksService:
    """FastAPI dependency that returns the loaded framework service.

    Raises HTTP 503 if the YAML failed to load at startup.
    """
    if compliance_frameworks_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Compliance frameworks data is unavailable. "
                "Check server logs for YAML loading errors."
            ),
        )
    return compliance_frameworks_service


@router.get("", summary="List all compliance frameworks")
async def list_frameworks(
    current_user: User = Depends(get_current_user),
    svc: ComplianceFrameworksService = Depends(_get_service),
) -> dict[str, Any]:
    """Return summary list of all loaded regulatory frameworks.

    Returns id, name, version, authority, and control_count for each
    framework.  Does not include individual control definitions to keep
    the response compact — use the detail endpoint for full controls.
    """
    frameworks = svc.get_all_frameworks()
    return {
        "frameworks": frameworks,
        "count": len(frameworks),
    }


@router.get(
    "/{framework_id}",
    summary="Get framework detail with all controls",
)
async def get_framework(
    framework_id: str = Path(
        ...,
        description="Framework identifier, e.g. SOC2_2017 or NIST_CSF_2.0",
        examples=["SOC2_2017"],
    ),
    current_user: User = Depends(get_current_user),
    svc: ComplianceFrameworksService = Depends(_get_service),
) -> dict[str, Any]:
    """Return full framework definition including all control entries.

    The response includes framework metadata (name, version, authority,
    source_url) plus the complete ``controls`` mapping.
    """
    try:
        return svc.get_framework(framework_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/{framework_id}/controls/{control_id:path}",
    summary="Get a single control definition",
)
async def get_control(
    framework_id: str = Path(
        ...,
        description="Framework identifier, e.g. SOC2_2017",
        examples=["SOC2_2017"],
    ),
    control_id: str = Path(
        ...,
        description="Control identifier, e.g. CC6.1 or PR.DS-01",
        examples=["CC6.1"],
    ),
    current_user: User = Depends(get_current_user),
    svc: ComplianceFrameworksService = Depends(_get_service),
) -> dict[str, Any]:
    """Return a single control's full definition.

    The control_id path segment uses ``{control_id:path}`` to support
    control IDs that contain forward slashes (none currently, but future-safe).
    """
    try:
        return svc.get_control(framework_id, control_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
