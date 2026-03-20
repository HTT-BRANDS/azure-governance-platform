"""Threat intelligence service for Riverside/Cybeta data.

Provides threat intelligence data by querying RiversideThreatData model.

Traces: RC-030, RC-031 (Riverside threat data integration)
"""

from datetime import date, datetime
from typing import Any

from sqlalchemy import and_, desc, select
from sqlalchemy.orm import Session

from app.models.riverside import RiversideThreatData


class ThreatIntelService:
    """Service for retrieving threat intelligence data."""

    def get_cybeta_threats(
        self,
        db: Session,
        tenant_ids: list[str] | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get threat intelligence data from Riverside/Cybeta sources.

        Args:
            db: Database session
            tenant_ids: Optional list of tenant IDs to filter
            start_date: Optional start date for date range
            end_date: Optional end date for date range
            limit: Maximum number of records to return

        Returns:
            List of threat records with scores, vulnerability counts, dates
        """
        query = select(RiversideThreatData)

        # Build filters
        filters = []
        if tenant_ids:
            filters.append(RiversideThreatData.tenant_id.in_(tenant_ids))
        if start_date:
            filters.append(
                RiversideThreatData.snapshot_date
                >= datetime.combine(start_date, datetime.min.time())
            )
        if end_date:
            filters.append(
                RiversideThreatData.snapshot_date <= datetime.combine(end_date, datetime.max.time())
            )

        if filters:
            query = query.where(and_(*filters))

        # Order by snapshot date descending (most recent first)
        query = query.order_by(desc(RiversideThreatData.snapshot_date))

        # Apply limit
        query = query.limit(limit)

        results = db.execute(query).scalars().all()

        return [
            {
                "tenant_id": r.tenant_id,
                "threat_score": r.threat_score,
                "vulnerability_count": r.vulnerability_count,
                "malicious_domain_alerts": r.malicious_domain_alerts,
                "peer_comparison_percentile": r.peer_comparison_percentile,
                "snapshot_date": r.snapshot_date.isoformat() if r.snapshot_date else None,
            }
            for r in results
        ]

    def get_threat_summary(self, db: Session, tenant_id: str) -> dict[str, Any]:
        """Get aggregated threat summary for a tenant.

        Gets the latest threat snapshot for the specified tenant and
        returns aggregated summary statistics.

        Args:
            db: Database session
            tenant_id: The tenant ID to get summary for

        Returns:
            Dictionary with aggregated threat summary
        """
        # Get latest threat data for the tenant
        query = (
            select(RiversideThreatData)
            .where(RiversideThreatData.tenant_id == tenant_id)
            .order_by(desc(RiversideThreatData.snapshot_date))
            .limit(1)
        )

        result = db.execute(query).scalars().first()

        if result is None:
            return {
                "tenant_id": tenant_id,
                "status": "no_data",
                "message": "No threat data available for this tenant",
                "latest_threat_score": None,
                "latest_vulnerability_count": 0,
                "latest_snapshot_date": None,
            }

        return {
            "tenant_id": result.tenant_id,
            "status": "available",
            "latest_threat_score": result.threat_score,
            "latest_vulnerability_count": result.vulnerability_count,
            "latest_malicious_domain_alerts": result.malicious_domain_alerts,
            "peer_comparison_percentile": result.peer_comparison_percentile,
            "latest_snapshot_date": result.snapshot_date.isoformat()
            if result.snapshot_date
            else None,
            "message": "Threat data retrieved successfully",
        }


# Singleton instance for dependency injection
_threat_intel_service: ThreatIntelService | None = None


def get_threat_intel_service() -> ThreatIntelService:
    """Get the ThreatIntelService singleton instance.

    Returns:
        The ThreatIntelService instance.
    """
    global _threat_intel_service
    if _threat_intel_service is None:
        _threat_intel_service = ThreatIntelService()
    return _threat_intel_service
