"""Resource Provisioning Standards API routes.

Endpoints for viewing provisioning standards and validating resources
against those standards.

Traces: RM-008 (Resource provisioning standards)
"""

from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.api.services.provisioning_standards_service import (
    ProvisioningStandardsService,
    get_provisioning_standards_service,
)
from app.core.auth import User, get_current_user

router = APIRouter(
    prefix="/api/v1/resources/provisioning-standards",
    tags=["provisioning-standards"],
    dependencies=[Depends(get_current_user)],
)


class ValidateResourceRequest(BaseModel):
    """Request body for resource validation."""

    resource_id: str = Field(..., description="Azure resource ID")
    resource_name: str = Field(..., description="Resource display name")
    resource_type: str = Field(..., description="Azure resource type")
    region: str = Field(default="", description="Azure region/location")
    tags: dict[str, str] = Field(default_factory=dict, description="Resource tags")
    sku: str = Field(default="", description="Resource SKU name")


@router.get("")
async def get_provisioning_standards(
    current_user: User = Depends(get_current_user),
    service: ProvisioningStandardsService = Depends(get_provisioning_standards_service),
) -> dict[str, Any]:
    """Get the current provisioning standards configuration.

    Returns the full YAML-defined standards including naming conventions,
    allowed regions, required tags, SKU restrictions, and network/encryption standards.
    """
    return {"standards": service.get_standards()}


@router.post("/validate")
async def validate_resource(
    request: ValidateResourceRequest,
    current_user: User = Depends(get_current_user),
    service: ProvisioningStandardsService = Depends(get_provisioning_standards_service),
) -> dict[str, Any]:
    """Validate a single resource against provisioning standards.

    Returns a validation result with any violations and warnings.
    """
    result = service.validate_resource(
        resource_id=request.resource_id,
        resource_name=request.resource_name,
        resource_type=request.resource_type,
        region=request.region,
        tags=request.tags,
        sku=request.sku,
    )
    return result.model_dump()


@router.get("/naming/validate")
async def validate_naming(
    name: str = Query(..., description="Resource name to validate"),
    current_user: User = Depends(get_current_user),
    service: ProvisioningStandardsService = Depends(get_provisioning_standards_service),
) -> dict[str, Any]:
    """Validate a resource name against naming conventions."""
    violations = service.validate_resource_name(name)
    return {
        "name": name,
        "is_compliant": len(violations) == 0,
        "violations": violations,
    }


@router.get("/regions/validate")
async def validate_region(
    region: str = Query(..., description="Azure region to validate"),
    current_user: User = Depends(get_current_user),
    service: ProvisioningStandardsService = Depends(get_provisioning_standards_service),
) -> dict[str, Any]:
    """Validate a region against allowed region standards."""
    violations = service.validate_region(region)
    return {
        "region": region,
        "is_compliant": len(violations) == 0,
        "violations": violations,
    }
