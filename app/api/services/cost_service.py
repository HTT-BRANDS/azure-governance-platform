"""Cost management service."""

import logging
from datetime import date, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.cost import CostAnomaly, CostSnapshot
from app.models.tenant import Subscription, Tenant
from app.schemas.cost import CostByTenant, CostSummary, CostTrend, ServiceCost

logger = logging.getLogger(__name__)


class CostService:
    """Service for cost management operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_cost_summary(
        self,
        period_days: int = 30,
    ) -> CostSummary:
        """Get aggregated cost summary across all tenants."""
        end_date = date.today()
        start_date = end_date - timedelta(days=period_days)
        prev_start = start_date - timedelta(days=period_days)

        # Current period costs
        current_costs = (
            self.db.query(CostSnapshot)
            .filter(CostSnapshot.date >= start_date)
            .filter(CostSnapshot.date <= end_date)
            .all()
        )

        # Previous period costs for comparison
        prev_costs = (
            self.db.query(CostSnapshot)
            .filter(CostSnapshot.date >= prev_start)
            .filter(CostSnapshot.date < start_date)
            .all()
        )

        current_total = sum(c.total_cost for c in current_costs)
        prev_total = sum(c.total_cost for c in prev_costs)

        # Calculate change percentage
        change_percent = None
        if prev_total > 0:
            change_percent = ((current_total - prev_total) / prev_total) * 100

        # Get unique counts
        tenant_ids = set(c.tenant_id for c in current_costs)
        sub_ids = set(c.subscription_id for c in current_costs)

        # Top services by cost
        service_costs = {}
        for cost in current_costs:
            if cost.service_name:
                service_costs[cost.service_name] = (
                    service_costs.get(cost.service_name, 0) + cost.total_cost
                )

        top_services = [
            ServiceCost(
                service_name=name,
                cost=cost,
                percentage_of_total=(cost / current_total * 100) if current_total > 0 else 0,
            )
            for name, cost in sorted(
                service_costs.items(), key=lambda x: x[1], reverse=True
            )[:10]
        ]

        return CostSummary(
            total_cost=current_total,
            currency="USD",
            period_start=start_date,
            period_end=end_date,
            tenant_count=len(tenant_ids),
            subscription_count=len(sub_ids),
            cost_change_percent=change_percent,
            top_services=top_services,
        )

    def get_costs_by_tenant(self, period_days: int = 30) -> List[CostByTenant]:
        """Get cost breakdown by tenant."""
        end_date = date.today()
        start_date = end_date - timedelta(days=period_days)

        tenants = self.db.query(Tenant).filter(Tenant.is_active == True).all()
        result = []

        for tenant in tenants:
            costs = (
                self.db.query(CostSnapshot)
                .filter(CostSnapshot.tenant_id == tenant.id)
                .filter(CostSnapshot.date >= start_date)
                .filter(CostSnapshot.date <= end_date)
                .all()
            )

            total = sum(c.total_cost for c in costs)

            result.append(
                CostByTenant(
                    tenant_id=tenant.id,
                    tenant_name=tenant.name,
                    total_cost=total,
                    currency="USD",
                )
            )

        return sorted(result, key=lambda x: x.total_cost, reverse=True)

    def get_cost_trends(self, days: int = 30) -> List[CostTrend]:
        """Get daily cost trends."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        # Aggregate costs by date
        daily_costs = {}
        costs = (
            self.db.query(CostSnapshot)
            .filter(CostSnapshot.date >= start_date)
            .filter(CostSnapshot.date <= end_date)
            .all()
        )

        for cost in costs:
            daily_costs[cost.date] = daily_costs.get(cost.date, 0) + cost.total_cost

        return [
            CostTrend(date=d, cost=c)
            for d, c in sorted(daily_costs.items())
        ]

    def get_anomalies(
        self, acknowledged: Optional[bool] = None
    ) -> List[CostAnomaly]:
        """Get cost anomalies."""
        query = self.db.query(CostAnomaly)

        if acknowledged is not None:
            query = query.filter(CostAnomaly.is_acknowledged == acknowledged)

        return query.order_by(CostAnomaly.detected_at.desc()).limit(50).all()

    def acknowledge_anomaly(self, anomaly_id: int, user: str) -> bool:
        """Acknowledge a cost anomaly."""
        from datetime import datetime

        anomaly = self.db.query(CostAnomaly).filter(CostAnomaly.id == anomaly_id).first()
        if not anomaly:
            return False

        anomaly.is_acknowledged = True
        anomaly.acknowledged_by = user
        anomaly.acknowledged_at = datetime.utcnow()
        self.db.commit()
        return True
