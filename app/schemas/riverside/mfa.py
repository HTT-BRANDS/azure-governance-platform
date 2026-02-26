"""Riverside MFA tracking schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class RiversideMFABase(BaseModel):
    """Base schema for Riverside MFA tracking."""

    total_users: int = Field(
        default=0,
        ge=0,
        description="Total number of users in tenant",
        examples=[150],
    )
    mfa_enrolled_users: int = Field(
        default=0,
        ge=0,
        description="Number of users enrolled in MFA",
        examples=[120],
    )
    mfa_coverage_percentage: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Percentage of users with MFA enabled",
        examples=[80.0],
    )
    admin_accounts_total: int = Field(
        default=0,
        ge=0,
        description="Total number of admin accounts",
        examples=[10],
    )
    admin_accounts_mfa: int = Field(
        default=0,
        ge=0,
        description="Number of admin accounts with MFA",
        examples=[10],
    )
    admin_mfa_percentage: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Percentage of admin accounts with MFA",
        examples=[100.0],
    )
    unprotected_users: int = Field(
        default=0,
        ge=0,
        description="Number of users without MFA protection",
        examples=[30],
    )
    snapshot_date: datetime = Field(
        ...,
        description="Date when this snapshot was taken",
        examples=["2025-01-15T00:00:00Z"],
    )


class RiversideMFAResponse(RiversideMFABase):
    """Response schema for Riverside MFA data."""

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
