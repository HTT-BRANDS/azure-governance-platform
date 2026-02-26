"""Riverside Company compliance tracking Pydantic schemas.

Pydantic schemas for API request/response validation for Riverside
compliance tracking with the July 8, 2026 deadline across HTT, BCC,
FN, TLL tenants plus DCE standalone.
"""

from datetime import date, datetime
from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

# =============================================================================
# Enums
# =============================================================================

class RequirementCategory(str, Enum):
    """Riverside compliance requirement categories."""

    IAM = "IAM"  # Identity and Access Management
    GS = "GS"  # Group Security
    DS = "DS"  # Domain Security


class RequirementPriority(str, Enum):
    """Riverside compliance requirement priorities."""

    P0 = "P0"  # Critical
    P1 = "P1"  # High
    P2 = "P2"  # Medium


class RequirementStatus(str, Enum):
    """Riverside compliance requirement statuses."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


# =============================================================================
# Riverside Compliance Schemas
# =============================================================================

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


# =============================================================================
# Riverside MFA Schemas
# =============================================================================

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


# =============================================================================
# Riverside Requirement Schemas
# =============================================================================

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


# =============================================================================
# Riverside Device Compliance Schemas
# =============================================================================

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


# =============================================================================
# Riverside Threat Data Schemas
# =============================================================================

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


# =============================================================================
# Dashboard/Executive Summary Schemas
# =============================================================================

class RiversideTenantSummary(BaseModel):
    """Summary data for a single Riverside tenant."""

    tenant_id: str = Field(
        ...,
        min_length=36,
        max_length=36,
        description="Tenant ID",
        examples=["12345678-1234-1234-1234-123456789abc"],
    )
    tenant_name: str = Field(
        ...,
        description="Tenant display name",
        examples=["HTT"],
    )
    overall_maturity_score: float = Field(
        ...,
        ge=0.0,
        le=5.0,
        description="Overall compliance maturity score",
        examples=[2.5],
    )
    requirements_completed: int = Field(
        ...,
        ge=0,
        description="Number of requirements completed",
        examples=[15],
    )
    requirements_total: int = Field(
        ...,
        ge=0,
        description="Total number of requirements",
        examples=[42],
    )
    completion_percentage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Percentage of requirements completed",
        examples=[35.7],
    )
    mfa_coverage_percentage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="MFA coverage percentage",
        examples=[80.0],
    )
    admin_mfa_percentage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Admin MFA coverage percentage",
        examples=[100.0],
    )
    device_compliance_percentage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Device compliance percentage",
        examples=[82.5],
    )
    critical_gaps_count: int = Field(
        ...,
        ge=0,
        description="Number of critical security gaps",
        examples=[5],
    )
    days_until_deadline: int = Field(
        ...,
        description="Days remaining until July 8, 2026 deadline",
        examples=[540],
    )


class RiversideDashboardSummary(BaseModel):
    """Executive dashboard summary across all Riverside tenants."""

    total_tenants: int = Field(
        ...,
        ge=0,
        description="Total number of Riverside tenants",
        examples=[5],
    )
    deadline_date: date = Field(
        ...,
        description="Compliance deadline date",
        examples=["2026-07-08"],
    )
    days_until_deadline: int = Field(
        ...,
        description="Days remaining until deadline",
        examples=[540],
    )
    overall_maturity_average: float = Field(
        ...,
        ge=0.0,
        le=5.0,
        description="Average maturity score across all tenants",
        examples=[2.3],
    )
    overall_maturity_target: float = Field(
        default=3.0,
        ge=0.0,
        le=5.0,
        description="Target maturity score",
        examples=[3.0],
    )
    total_requirements_completed: int = Field(
        ...,
        ge=0,
        description="Total requirements completed across all tenants",
        examples=[75],
    )
    total_requirements: int = Field(
        ...,
        ge=0,
        description="Total requirements across all tenants",
        examples=[210],
    )
    overall_completion_percentage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Overall completion percentage",
        examples=[35.7],
    )
    total_critical_gaps: int = Field(
        ...,
        ge=0,
        description="Total critical gaps across all tenants",
        examples=[23],
    )
    average_mfa_coverage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Average MFA coverage across tenants",
        examples=[78.5],
    )
    average_device_compliance: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Average device compliance across tenants",
        examples=[80.2],
    )
    financial_risk_exposure: str = Field(
        ...,
        description="Total financial risk exposure",
        examples=["$20M"],
    )
    tenant_summaries: list[RiversideTenantSummary] = Field(
        default_factory=list,
        description="Per-tenant summary data",
    )
    requirements_by_category: dict = Field(
        default_factory=dict,
        description="Requirements grouped by category with counts",
        examples=[{"IAM": {"completed": 30, "total": 80}, "GS": {"completed": 25, "total": 70}}],
    )
    requirements_by_priority: dict = Field(
        default_factory=dict,
        description="Requirements grouped by priority with counts",
        examples=[{"P0": {"completed": 10, "total": 20}, "P1": {"completed": 35, "total": 100}}],
    )
    requirements_by_status: dict = Field(
        default_factory=dict,
        description="Requirements grouped by status with counts",
        examples=[{"completed": 75, "in_progress": 50, "not_started": 85}],
    )


# =============================================================================
# Generic Pagination Wrapper
# =============================================================================

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

    items: list[T] = Field(
        default_factory=list,
        description="List of items for the current page",
    )
    total: int = Field(
        ...,
        ge=0,
        description="Total number of items",
        examples=[100],
    )
    page: int = Field(
        ...,
        ge=1,
        description="Current page number",
        examples=[1],
    )
    page_size: int = Field(
        ...,
        ge=1,
        description="Number of items per page",
        examples=[20],
    )
    pages: int = Field(
        ...,
        ge=0,
        description="Total number of pages",
        examples=[5],
    )
    has_next: bool = Field(
        ...,
        description="Whether there is a next page",
        examples=[True],
    )
    has_previous: bool = Field(
        ...,
        description="Whether there is a previous page",
        examples=[False],
    )


# =============================================================================
# Bulk Operations
# =============================================================================

class BulkUpdateItem(BaseModel):
    """Single item for bulk update operation."""

    id: int = Field(
        ...,
        description="ID of the item to update",
        examples=[1],
    )
    updates: dict = Field(
        ...,
        description="Dictionary of fields to update",
        examples=[{"status": "completed", "evidence_notes": "Verified"}],
    )


class BulkUpdateRequest(BaseModel):
    """Request schema for batch update operations."""

    items: list[BulkUpdateItem] = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="List of items to update",
    )


class BulkUpdateResponse(BaseModel):
    """Response schema for batch update operations."""

    processed: int = Field(
        ...,
        ge=0,
        description="Number of items processed",
        examples=[50],
    )
    succeeded: int = Field(
        ...,
        ge=0,
        description="Number of successful updates",
        examples=[48],
    )
    failed: int = Field(
        ...,
        ge=0,
        description="Number of failed updates",
        examples=[2],
    )
    errors: list[dict] = Field(
        default_factory=list,
        description="List of errors if any",
        examples=[[{"id": 5, "error": "Item not found"}]],
    )
