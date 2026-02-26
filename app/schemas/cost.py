"""Cost-related Pydantic schemas."""

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class CostSummary(BaseModel):
    """Aggregated cost summary across all tenants."""

    total_cost: float = Field(..., description="Total cost across all tenants")
    currency: str = "USD"
    period_start: date
    period_end: date
    tenant_count: int
    subscription_count: int
    cost_change_percent: Optional[float] = Field(
        None, description="Percentage change from previous period"
    )
    top_services: List["ServiceCost"] = Field(default_factory=list)


class ServiceCost(BaseModel):
    """Cost breakdown by service."""

    service_name: str
    cost: float
    percentage_of_total: float


class CostByTenant(BaseModel):
    """Cost breakdown by tenant."""

    tenant_id: str
    tenant_name: str
    total_cost: float
    currency: str = "USD"
    subscription_costs: List["SubscriptionCost"] = Field(default_factory=list)


class SubscriptionCost(BaseModel):
    """Cost per subscription."""

    subscription_id: str
    subscription_name: str
    cost: float


class CostTrend(BaseModel):
    """Cost trend data point."""

    date: date
    cost: float
    forecast: Optional[float] = None


class CostAnomaly(BaseModel):
    """Cost anomaly alert."""

    id: int
    tenant_id: str
    tenant_name: str
    subscription_id: str
    detected_at: datetime
    anomaly_type: str
    description: str
    expected_cost: float
    actual_cost: float
    percentage_change: float
    service_name: Optional[str] = None
    is_acknowledged: bool = False


# Update forward references
CostSummary.model_rebuild()
CostByTenant.model_rebuild()
