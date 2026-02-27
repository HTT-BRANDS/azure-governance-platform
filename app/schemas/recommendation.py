"""Recommendation-related Pydantic schemas."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class RecommendationCategory(str, Enum):
    """Recommendation categories."""

    COST_OPTIMIZATION = "cost_optimization"
    SECURITY = "security"
    PERFORMANCE = "performance"
    RELIABILITY = "reliability"


class RecommendationImpact(str, Enum):
    """Recommendation impact levels."""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class ImplementationEffort(str, Enum):
    """Implementation effort levels."""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class Recommendation(BaseModel):
    """Optimization or governance recommendation."""

    id: int
    tenant_id: str | None = None
    tenant_name: str | None = None
    subscription_id: str | None = None
    category: RecommendationCategory
    recommendation_type: str
    title: str
    description: str
    impact: RecommendationImpact
    potential_savings_monthly: float | None = None
    potential_savings_annual: float | None = None
    resource_id: str | None = None
    resource_name: str | None = None
    resource_type: str | None = None
    current_state: dict | None = None
    recommended_state: dict | None = None
    implementation_effort: ImplementationEffort
    is_dismissed: bool = False
    created_at: datetime
    updated_at: datetime


class RecommendationSummary(BaseModel):
    """Summary of recommendations by category."""

    category: RecommendationCategory
    count: int
    potential_savings_monthly: float
    potential_savings_annual: float
    by_impact: dict[str, int] = Field(default_factory=dict)


class RecommendationsByCategory(BaseModel):
    """Recommendations grouped by category."""

    category: RecommendationCategory
    recommendations: list[Recommendation]
    count: int
    total_potential_savings_monthly: float


class SavingsPotential(BaseModel):
    """Total potential savings across all recommendations."""

    total_potential_savings_monthly: float
    total_potential_savings_annual: float
    by_category: dict[str, float] = Field(default_factory=dict)
    by_tenant: dict[str, float] = Field(default_factory=dict)


class DismissRecommendationRequest(BaseModel):
    """Request to dismiss a recommendation."""

    reason: str | None = None


class DismissRecommendationResponse(BaseModel):
    """Response after dismissing a recommendation."""

    success: bool
    recommendation_id: int
    dismissed_at: datetime


class RecommendationFilterParams(BaseModel):
    """Query parameters for filtering recommendations."""

    category: RecommendationCategory | None = None
    tenant_ids: list[str] | None = None
    impact: RecommendationImpact | None = None
    dismissed: bool | None = None
    limit: int = Field(default=100, ge=1, le=500)
    offset: int = Field(default=0, ge=0)
    sort_by: str = Field(default="created_at")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")
