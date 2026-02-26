"""Riverside threat data tracking schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class RiversideThreatDataBase(BaseModel):
    """Base schema for Riverside threat data tracking."""

    threat_score: float | None = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Overall threat score (0-100 scale, lower is better)",
        examples=[25.5],
    )
    vulnerability_count: int = Field(
        default=0,
        ge=0,
        description="Number of vulnerabilities identified",
        examples=[12],
    )
    malicious_domain_alerts: int = Field(
        default=0,
        ge=0,
        description="Number of malicious domain alerts",
        examples=[3],
    )
    peer_comparison_percentile: int | None = Field(
        None,
        ge=0,
        le=100,
        description="Percentile ranking compared to peers",
        examples=[75],
    )
    snapshot_date: datetime = Field(
        ...,
        description="Date when this snapshot was taken",
        examples=["2025-01-15T00:00:00Z"],
    )


class RiversideThreatDataResponse(RiversideThreatDataBase):
    """Response schema for Riverside threat data."""

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
