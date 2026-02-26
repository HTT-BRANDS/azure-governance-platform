"""Riverside requirement schemas."""

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.schemas.riverside.enums import RequirementCategory, RequirementPriority, RequirementStatus


class RiversideRequirementBase(BaseModel):
    """Base schema for Riverside compliance requirements."""

    requirement_id: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Unique requirement identifier (e.g., RC-001)",
        examples=["RC-001"],
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Requirement title",
        examples=["Implement Privileged Access Management"],
    )
    description: str = Field(
        default="",
        description="Detailed requirement description",
        examples=["Deploy and configure PAM solution for privileged accounts"],
    )
    category: RequirementCategory = Field(
        ...,
        description="Requirement category (IAM, GS, DS)",
        examples=["IAM"],
    )
    priority: RequirementPriority = Field(
        ...,
        description="Requirement priority (P0, P1, P2)",
        examples=["P0"],
    )
    status: RequirementStatus = Field(
        default=RequirementStatus.NOT_STARTED,
        description="Current status of the requirement",
        examples=["in_progress"],
    )
    evidence_url: str | None = Field(
        None,
        max_length=500,
        description="URL to evidence documentation",
        examples=["https://example.com/evidence/rc-001"],
    )
    evidence_notes: str | None = Field(
        None,
        description="Notes about evidence provided",
        examples=["PAM solution deployed on 2025-01-10"],
    )
    due_date: date | None = Field(
        None,
        description="Deadline for requirement completion",
        examples=["2026-07-08"],
    )
    owner: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Owner or responsible party",
        examples=["John Doe"],
    )


class RiversideRequirementResponse(RiversideRequirementBase):
    """Response schema for Riverside requirements."""

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
    completed_date: date | None = Field(
        None,
        description="Date when requirement was completed",
        examples=["2025-01-15"],
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


class RiversideRequirementUpdate(BaseModel):
    """Update schema for Riverside requirements."""

    title: str | None = Field(
        None,
        min_length=1,
        max_length=255,
        description="Requirement title",
    )
    description: str | None = Field(
        None,
        description="Detailed requirement description",
    )
    category: RequirementCategory | None = Field(
        None,
        description="Requirement category (IAM, GS, DS)",
    )
    priority: RequirementPriority | None = Field(
        None,
        description="Requirement priority (P0, P1, P2)",
    )
    status: RequirementStatus | None = Field(
        None,
        description="Current status of the requirement",
    )
    evidence_url: str | None = Field(
        None,
        max_length=500,
        description="URL to evidence documentation",
    )
    evidence_notes: str | None = Field(
        None,
        description="Notes about evidence provided",
    )
    due_date: date | None = Field(
        None,
        description="Deadline for requirement completion",
    )
    owner: str | None = Field(
        None,
        min_length=1,
        max_length=255,
        description="Owner or responsible party",
    )


class RiversideRequirementFilter(BaseModel):
    """Filter schema for querying Riverside requirements."""

    tenant_id: str | None = Field(
        None,
        min_length=36,
        max_length=36,
        description="Filter by tenant ID",
    )
    status: RequirementStatus | None = Field(
        None,
        description="Filter by status",
    )
    category: RequirementCategory | None = Field(
        None,
        description="Filter by category",
    )
    priority: RequirementPriority | None = Field(
        None,
        description="Filter by priority",
    )
    due_date_from: date | None = Field(
        None,
        description="Filter by due date (start)",
    )
    due_date_to: date | None = Field(
        None,
        description="Filter by due date (end)",
    )
    owner: str | None = Field(
        None,
        description="Filter by owner",
    )
