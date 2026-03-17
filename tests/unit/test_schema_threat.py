"""Unit tests for Riverside threat data tracking schemas.

Tests Pydantic schemas in app/schemas/riverside/threat.py.

Traces: RC-010 — Threat data validation for Riverside
security monitoring and dashboard reporting.
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas.riverside.threat import (
    RiversideThreatDataBase,
    RiversideThreatDataResponse,
)

# ---------------------------------------------------------------------------
# RiversideThreatDataBase
# ---------------------------------------------------------------------------


class TestThreatDataBase:
    """Tests for RiversideThreatDataBase schema."""

    def test_valid_creation(self):
        """Should create with valid data."""
        schema = RiversideThreatDataBase(
            threat_score=25.5,
            vulnerability_count=12,
            malicious_domain_alerts=3,
            peer_comparison_percentile=75,
            snapshot_date=datetime(2025, 1, 15),
        )
        assert schema.threat_score == 25.5
        assert schema.vulnerability_count == 12
        assert schema.malicious_domain_alerts == 3
        assert schema.peer_comparison_percentile == 75

    def test_defaults(self):
        """Optional/default fields should have correct defaults."""
        schema = RiversideThreatDataBase(
            snapshot_date=datetime(2025, 1, 15),
        )
        assert schema.threat_score is None
        assert schema.vulnerability_count == 0
        assert schema.malicious_domain_alerts == 0
        assert schema.peer_comparison_percentile is None

    def test_snapshot_date_required(self):
        """Should reject missing snapshot_date."""
        with pytest.raises(ValidationError):
            RiversideThreatDataBase()

    def test_threat_score_min_0(self):
        """Should reject negative threat score."""
        with pytest.raises(ValidationError) as exc_info:
            RiversideThreatDataBase(
                threat_score=-1.0,
                snapshot_date=datetime(2025, 1, 15),
            )
        assert "threat_score" in str(exc_info.value)

    def test_threat_score_max_100(self):
        """Should reject threat score above 100."""
        with pytest.raises(ValidationError) as exc_info:
            RiversideThreatDataBase(
                threat_score=100.1,
                snapshot_date=datetime(2025, 1, 15),
            )
        assert "threat_score" in str(exc_info.value)

    def test_threat_score_boundary_0(self):
        """Should accept threat_score of exactly 0."""
        schema = RiversideThreatDataBase(
            threat_score=0.0,
            snapshot_date=datetime(2025, 1, 15),
        )
        assert schema.threat_score == 0.0

    def test_threat_score_boundary_100(self):
        """Should accept threat_score of exactly 100."""
        schema = RiversideThreatDataBase(
            threat_score=100.0,
            snapshot_date=datetime(2025, 1, 15),
        )
        assert schema.threat_score == 100.0

    def test_threat_score_none_allowed(self):
        """threat_score should accept None."""
        schema = RiversideThreatDataBase(
            threat_score=None,
            snapshot_date=datetime(2025, 1, 15),
        )
        assert schema.threat_score is None

    def test_vulnerability_count_non_negative(self):
        """Should reject negative vulnerability count."""
        with pytest.raises(ValidationError):
            RiversideThreatDataBase(
                vulnerability_count=-1,
                snapshot_date=datetime(2025, 1, 15),
            )

    def test_malicious_domain_alerts_non_negative(self):
        """Should reject negative malicious domain alert count."""
        with pytest.raises(ValidationError):
            RiversideThreatDataBase(
                malicious_domain_alerts=-1,
                snapshot_date=datetime(2025, 1, 15),
            )

    def test_peer_comparison_min_0(self):
        """Should reject negative peer comparison percentile."""
        with pytest.raises(ValidationError):
            RiversideThreatDataBase(
                peer_comparison_percentile=-1,
                snapshot_date=datetime(2025, 1, 15),
            )

    def test_peer_comparison_max_100(self):
        """Should reject peer comparison percentile above 100."""
        with pytest.raises(ValidationError):
            RiversideThreatDataBase(
                peer_comparison_percentile=101,
                snapshot_date=datetime(2025, 1, 15),
            )

    def test_peer_comparison_boundary_0(self):
        """Should accept percentile of exactly 0."""
        schema = RiversideThreatDataBase(
            peer_comparison_percentile=0,
            snapshot_date=datetime(2025, 1, 15),
        )
        assert schema.peer_comparison_percentile == 0

    def test_peer_comparison_boundary_100(self):
        """Should accept percentile of exactly 100."""
        schema = RiversideThreatDataBase(
            peer_comparison_percentile=100,
            snapshot_date=datetime(2025, 1, 15),
        )
        assert schema.peer_comparison_percentile == 100


# ---------------------------------------------------------------------------
# RiversideThreatDataResponse
# ---------------------------------------------------------------------------


class TestThreatDataResponse:
    """Tests for RiversideThreatDataResponse schema."""

    def test_valid_response(self):
        """Should create a valid response with all required fields."""
        resp = RiversideThreatDataResponse(
            id=1,
            tenant_id="12345678-1234-1234-1234-123456789abc",
            threat_score=25.5,
            vulnerability_count=12,
            malicious_domain_alerts=3,
            peer_comparison_percentile=75,
            snapshot_date=datetime(2025, 1, 15),
            created_at=datetime(2025, 1, 15),
        )
        assert resp.id == 1
        assert resp.tenant_id == "12345678-1234-1234-1234-123456789abc"
        assert resp.threat_score == 25.5

    def test_inherits_base_validation(self):
        """Should enforce base schema validation (e.g., threat_score range)."""
        with pytest.raises(ValidationError):
            RiversideThreatDataResponse(
                id=1,
                tenant_id="12345678-1234-1234-1234-123456789abc",
                threat_score=200.0,  # exceeds max
                snapshot_date=datetime(2025, 1, 15),
                created_at=datetime(2025, 1, 15),
            )

    def test_tenant_id_length_validation(self):
        """Should reject tenant_id not matching 36 char length."""
        with pytest.raises(ValidationError) as exc_info:
            RiversideThreatDataResponse(
                id=1,
                tenant_id="too-short",
                snapshot_date=datetime(2025, 1, 15),
                created_at=datetime(2025, 1, 15),
            )
        assert "tenant_id" in str(exc_info.value)

    def test_id_required(self):
        """Should reject missing id."""
        with pytest.raises(ValidationError):
            RiversideThreatDataResponse(
                tenant_id="12345678-1234-1234-1234-123456789abc",
                snapshot_date=datetime(2025, 1, 15),
                created_at=datetime(2025, 1, 15),
            )

    def test_created_at_required(self):
        """Should reject missing created_at."""
        with pytest.raises(ValidationError):
            RiversideThreatDataResponse(
                id=1,
                tenant_id="12345678-1234-1234-1234-123456789abc",
                snapshot_date=datetime(2025, 1, 15),
            )

    def test_from_attributes_config(self):
        """Should have from_attributes=True for ORM compatibility."""
        assert RiversideThreatDataResponse.model_config.get("from_attributes") is True

    def test_minimal_response(self):
        """Should work with minimal fields (defaults for optional base fields)."""
        resp = RiversideThreatDataResponse(
            id=42,
            tenant_id="12345678-1234-1234-1234-123456789abc",
            snapshot_date=datetime(2025, 6, 1),
            created_at=datetime(2025, 6, 1),
        )
        assert resp.id == 42
        assert resp.threat_score is None
        assert resp.vulnerability_count == 0
        assert resp.malicious_domain_alerts == 0
        assert resp.peer_comparison_percentile is None
