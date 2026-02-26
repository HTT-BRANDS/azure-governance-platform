"""Riverside device compliance tracking schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class RiversideDeviceComplianceBase(BaseModel):
    """Base schema for Riverside device compliance tracking."""

    total_devices: int = Field(
        default=0,
        ge=0,
        description="Total number of devices",
        examples=[200],
    )
    mdm_enrolled: int = Field(
        default=0,
        ge=0,
        description="Number of devices enrolled in MDM",
        examples=[180],
    )
    edr_covered: int = Field(
        default=0,
        ge=0,
        description="Number of devices with EDR coverage",
        examples=[190],
    )
    encrypted_devices: int = Field(
        default=0,
        ge=0,
        description="Number of encrypted devices",
        examples=[175],
    )
    compliant_devices: int = Field(
        default=0,
        ge=0,
        description="Number of compliant devices",
        examples=[165],
    )
    compliance_percentage: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Percentage of compliant devices",
        examples=[82.5],
    )
    snapshot_date: datetime = Field(
        ...,
        description="Date when this snapshot was taken",
        examples=["2025-01-15T00:00:00Z"],
    )


class RiversideDeviceComplianceResponse(RiversideDeviceComplianceBase):
    """Response schema for Riverside device compliance data."""

    id: int = Field(
        ...,
        description="Unique identifier",
        examples=[1],
    )
    tenant_id: str = Field(
        ...,
        min_length=36,
        max_length=36,
        description="Associated tenant ID",
        examples=["12345678-1234-1234-1234-123456789abc"],
    )
    created_at: datetime = Field(
        ...,
        description="Record creation timestamp",
        examples=["2025-01-15T00:00:00Z"],
    )

    model_config = {"from_attributes": True}
