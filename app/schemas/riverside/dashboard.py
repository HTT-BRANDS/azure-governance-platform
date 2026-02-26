"""Riverside dashboard and executive summary schemas."""

from datetime import date

from pydantic import BaseModel, Field


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
