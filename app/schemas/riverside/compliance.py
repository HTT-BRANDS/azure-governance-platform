"""Riverside compliance tracking schemas."""

from datetime import date, datetime

from pydantic import BaseModel, Field


class RiversideComplianceBase(BaseModel):
    """Base schema for Riverside compliance data."""

    overall_maturity_score: float = Field(
        default=0.0,
        ge=0.0,
        le=5.0,
        description="Overall compliance maturity score (0-5 scale)",
        examples=[2.5],
    )
    target_maturity_score: float = Field(
        default=3.0,
        ge=0.0,
        le=5.0,
        description="Target maturity score to achieve (0-5 scale)",
        examples=[3.0],
    )
    deadline_date: date = Field(
        ...,
        description="Compliance deadline date",
        examples=["2026-07-08"],
    )
    financial_risk: str = Field(
        default="$4M",
        max_length=50,
        description="Financial risk associated with non-compliance",
        examples=["$4M"],
    )
    critical_gaps_count: int = Field(
        default=0,
        ge=0,
        description="Number of critical security gaps identified",
        examples=[5],
    )
    requirements_completed: int = Field(
        default=0,
        ge=0,
        description="Number of requirements completed",
        examples=[15],
    )
    requirements_total: int = Field(
        default=0,
        ge=0,
        description="Total number of requirements",
        examples=[42],
    )


class RiversideComplianceResponse(RiversideComplianceBase):
    """Response schema for Riverside compliance data."""

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
    last_assessment_date: datetime | None = Field(
        None,
        description="Date of last compliance assessment",
        examples=["2025-01-15T10:30:00Z"],
    )
    created_at: datetime = Field(
        ...,
        description="Record creation timestamp",
        examples=["2025-01-01T00:00:00Z"],
    )
    updated_at: datetime = Field(
        ...,
        description="Last update timestamp",
        examples=["2025-01-15T10:30:00Z"],
    )

    model_config = {"from_attributes": True}


class RiversideComplianceUpdate(BaseModel):
    """Update schema for Riverside compliance data."""

    overall_maturity_score: float | None = Field(
        None,
        ge=0.0,
        le=5.0,
        description="Overall compliance maturity score (0-5 scale)",
    )
    target_maturity_score: float | None = Field(
        None,
        ge=0.0,
        le=5.0,
        description="Target maturity score to achieve (0-5 scale)",
    )
    deadline_date: date | None = Field(
        None,
        description="Compliance deadline date",
    )
    financial_risk: str | None = Field(
        None,
        max_length=50,
        description="Financial risk associated with non-compliance",
    )
    critical_gaps_count: int | None = Field(
        None,
        ge=0,
        description="Number of critical security gaps identified",
    )
    requirements_completed: int | None = Field(
        None,
        ge=0,
        description="Number of requirements completed",
    )
    requirements_total: int | None = Field(
        None,
        ge=0,
        description="Total number of requirements",
    )
