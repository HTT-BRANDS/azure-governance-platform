"""Unit tests for Riverside requirement schemas.

Tests all Pydantic models in app/schemas/riverside/requirements.py.

Traces: RC-009 — Requirement schema validation for API request/response
contracts and filtering.
"""

from datetime import date, datetime

import pytest
from pydantic import ValidationError

from app.schemas.riverside.enums import RequirementCategory, RequirementPriority, RequirementStatus
from app.schemas.riverside.requirements import (
    RiversideRequirementBase,
    RiversideRequirementFilter,
    RiversideRequirementResponse,
    RiversideRequirementUpdate,
)

# ---------------------------------------------------------------------------
# RiversideRequirementBase
# ---------------------------------------------------------------------------


class TestRequirementBase:
    """Tests for RiversideRequirementBase schema."""

    def test_valid_creation(self):
        """Should create with all required fields."""
        req = RiversideRequirementBase(
            requirement_id="RC-001",
            title="Implement PAM",
            category=RequirementCategory.IAM,
            priority=RequirementPriority.P0,
            owner="John Doe",
        )
        assert req.requirement_id == "RC-001"
        assert req.title == "Implement PAM"
        assert req.category == RequirementCategory.IAM
        assert req.priority == RequirementPriority.P0
        assert req.status == RequirementStatus.NOT_STARTED  # default
        assert req.description == ""  # default
        assert req.evidence_url is None
        assert req.evidence_notes is None
        assert req.due_date is None

    def test_all_optional_fields(self):
        """Should accept all optional fields."""
        req = RiversideRequirementBase(
            requirement_id="RC-002",
            title="Deploy DLP",
            description="Deploy Data Loss Prevention across all tenants",
            category=RequirementCategory.DS,
            priority=RequirementPriority.P1,
            status=RequirementStatus.IN_PROGRESS,
            evidence_url="https://example.com/evidence",
            evidence_notes="Deployed on 2025-01-10",
            due_date=date(2026, 7, 8),
            owner="Jane Smith",
        )
        assert req.description == "Deploy Data Loss Prevention across all tenants"
        assert req.status == RequirementStatus.IN_PROGRESS
        assert req.evidence_url == "https://example.com/evidence"
        assert req.due_date == date(2026, 7, 8)

    def test_requirement_id_required(self):
        """Should reject missing requirement_id."""
        with pytest.raises(ValidationError):
            RiversideRequirementBase(
                title="Test",
                category=RequirementCategory.IAM,
                priority=RequirementPriority.P0,
                owner="Owner",
            )

    def test_requirement_id_min_length(self):
        """Should reject empty requirement_id (min_length=1)."""
        with pytest.raises(ValidationError) as exc_info:
            RiversideRequirementBase(
                requirement_id="",
                title="Test",
                category=RequirementCategory.IAM,
                priority=RequirementPriority.P0,
                owner="Owner",
            )
        assert "requirement_id" in str(exc_info.value)

    def test_requirement_id_max_length(self):
        """Should reject requirement_id exceeding 20 chars."""
        with pytest.raises(ValidationError):
            RiversideRequirementBase(
                requirement_id="X" * 21,
                title="Test",
                category=RequirementCategory.IAM,
                priority=RequirementPriority.P0,
                owner="Owner",
            )

    def test_title_required(self):
        """Should reject missing title."""
        with pytest.raises(ValidationError):
            RiversideRequirementBase(
                requirement_id="RC-001",
                category=RequirementCategory.IAM,
                priority=RequirementPriority.P0,
                owner="Owner",
            )

    def test_title_min_length(self):
        """Should reject empty title."""
        with pytest.raises(ValidationError):
            RiversideRequirementBase(
                requirement_id="RC-001",
                title="",
                category=RequirementCategory.IAM,
                priority=RequirementPriority.P0,
                owner="Owner",
            )

    def test_title_max_length(self):
        """Should reject title exceeding 255 chars."""
        with pytest.raises(ValidationError):
            RiversideRequirementBase(
                requirement_id="RC-001",
                title="X" * 256,
                category=RequirementCategory.IAM,
                priority=RequirementPriority.P0,
                owner="Owner",
            )

    def test_owner_required(self):
        """Should reject missing owner."""
        with pytest.raises(ValidationError):
            RiversideRequirementBase(
                requirement_id="RC-001",
                title="Test",
                category=RequirementCategory.IAM,
                priority=RequirementPriority.P0,
            )

    def test_invalid_category_rejected(self):
        """Should reject invalid category value."""
        with pytest.raises(ValidationError):
            RiversideRequirementBase(
                requirement_id="RC-001",
                title="Test",
                category="INVALID",
                priority=RequirementPriority.P0,
                owner="Owner",
            )

    def test_invalid_priority_rejected(self):
        """Should reject invalid priority value."""
        with pytest.raises(ValidationError):
            RiversideRequirementBase(
                requirement_id="RC-001",
                title="Test",
                category=RequirementCategory.IAM,
                priority="P5",
                owner="Owner",
            )

    def test_invalid_status_rejected(self):
        """Should reject invalid status value."""
        with pytest.raises(ValidationError):
            RiversideRequirementBase(
                requirement_id="RC-001",
                title="Test",
                category=RequirementCategory.IAM,
                priority=RequirementPriority.P0,
                status="cancelled",
                owner="Owner",
            )

    def test_evidence_url_max_length(self):
        """Should reject evidence_url exceeding 500 chars."""
        with pytest.raises(ValidationError):
            RiversideRequirementBase(
                requirement_id="RC-001",
                title="Test",
                category=RequirementCategory.IAM,
                priority=RequirementPriority.P0,
                owner="Owner",
                evidence_url="https://example.com/" + "x" * 500,
            )


# ---------------------------------------------------------------------------
# RiversideRequirementResponse
# ---------------------------------------------------------------------------


class TestRequirementResponse:
    """Tests for RiversideRequirementResponse schema."""

    def test_valid_response(self):
        """Should create a valid response with all fields."""
        resp = RiversideRequirementResponse(
            id=1,
            requirement_id="RC-001",
            title="Implement PAM",
            category=RequirementCategory.IAM,
            priority=RequirementPriority.P0,
            owner="John Doe",
            tenant_id="12345678-1234-1234-1234-123456789abc",
            created_at=datetime(2025, 1, 1),
            updated_at=datetime(2025, 1, 15, 10, 30),
        )
        assert resp.id == 1
        assert resp.tenant_id == "12345678-1234-1234-1234-123456789abc"
        assert resp.completed_date is None  # default

    def test_with_completed_date(self):
        """Should accept a completed_date."""
        resp = RiversideRequirementResponse(
            id=2,
            requirement_id="RC-002",
            title="Test",
            category=RequirementCategory.GS,
            priority=RequirementPriority.P1,
            status=RequirementStatus.COMPLETED,
            owner="Jane",
            tenant_id="12345678-1234-1234-1234-123456789abc",
            completed_date=date(2025, 1, 15),
            created_at=datetime(2025, 1, 1),
            updated_at=datetime(2025, 1, 15),
        )
        assert resp.completed_date == date(2025, 1, 15)

    def test_tenant_id_validation(self):
        """Should reject tenant_id not matching length constraints."""
        with pytest.raises(ValidationError):
            RiversideRequirementResponse(
                id=1,
                requirement_id="RC-001",
                title="Test",
                category=RequirementCategory.IAM,
                priority=RequirementPriority.P0,
                owner="Owner",
                tenant_id="short",
                created_at=datetime(2025, 1, 1),
                updated_at=datetime(2025, 1, 15),
            )

    def test_from_attributes_enabled(self):
        """Should have from_attributes=True for ORM compatibility."""
        assert RiversideRequirementResponse.model_config.get("from_attributes") is True


# ---------------------------------------------------------------------------
# RiversideRequirementUpdate
# ---------------------------------------------------------------------------


class TestRequirementUpdate:
    """Tests for RiversideRequirementUpdate schema."""

    def test_empty_update(self):
        """Should allow creating with no fields (all Optional)."""
        update = RiversideRequirementUpdate()
        assert update.title is None
        assert update.description is None
        assert update.category is None
        assert update.priority is None
        assert update.status is None
        assert update.evidence_url is None
        assert update.evidence_notes is None
        assert update.due_date is None
        assert update.owner is None

    def test_partial_update(self):
        """Should accept a subset of fields for partial updates."""
        update = RiversideRequirementUpdate(
            status=RequirementStatus.COMPLETED,
            evidence_url="https://example.com/evidence/rc-001",
        )
        assert update.status == RequirementStatus.COMPLETED
        assert update.evidence_url == "https://example.com/evidence/rc-001"
        assert update.title is None  # not updated

    def test_title_min_length_validated(self):
        """Should reject empty title when provided."""
        with pytest.raises(ValidationError):
            RiversideRequirementUpdate(title="")

    def test_owner_min_length_validated(self):
        """Should reject empty owner when provided."""
        with pytest.raises(ValidationError):
            RiversideRequirementUpdate(owner="")

    def test_invalid_category_rejected(self):
        """Should reject invalid category on update."""
        with pytest.raises(ValidationError):
            RiversideRequirementUpdate(category="INVALID")

    def test_all_fields_updatable(self):
        """Should accept all fields for a complete update."""
        update = RiversideRequirementUpdate(
            title="Updated Title",
            description="Updated desc",
            category=RequirementCategory.DS,
            priority=RequirementPriority.P2,
            status=RequirementStatus.IN_PROGRESS,
            evidence_url="https://example.com",
            evidence_notes="Updated notes",
            due_date=date(2026, 6, 1),
            owner="New Owner",
        )
        assert update.title == "Updated Title"
        assert update.category == RequirementCategory.DS


# ---------------------------------------------------------------------------
# RiversideRequirementFilter
# ---------------------------------------------------------------------------


class TestRequirementFilter:
    """Tests for RiversideRequirementFilter schema."""

    def test_empty_filter(self):
        """Should allow creating with no filters."""
        f = RiversideRequirementFilter()
        assert f.tenant_id is None
        assert f.status is None
        assert f.category is None
        assert f.priority is None
        assert f.due_date_from is None
        assert f.due_date_to is None
        assert f.owner is None

    def test_filter_by_tenant(self):
        """Should filter by tenant_id."""
        f = RiversideRequirementFilter(
            tenant_id="12345678-1234-1234-1234-123456789abc",
        )
        assert f.tenant_id == "12345678-1234-1234-1234-123456789abc"

    def test_filter_by_status(self):
        """Should filter by status."""
        f = RiversideRequirementFilter(status=RequirementStatus.BLOCKED)
        assert f.status == RequirementStatus.BLOCKED

    def test_filter_by_category_and_priority(self):
        """Should filter by both category and priority."""
        f = RiversideRequirementFilter(
            category=RequirementCategory.IAM,
            priority=RequirementPriority.P0,
        )
        assert f.category == RequirementCategory.IAM
        assert f.priority == RequirementPriority.P0

    def test_filter_by_date_range(self):
        """Should filter by due_date range."""
        f = RiversideRequirementFilter(
            due_date_from=date(2025, 1, 1),
            due_date_to=date(2026, 7, 8),
        )
        assert f.due_date_from == date(2025, 1, 1)
        assert f.due_date_to == date(2026, 7, 8)

    def test_tenant_id_length_validation(self):
        """Should validate tenant_id length constraints."""
        with pytest.raises(ValidationError):
            RiversideRequirementFilter(tenant_id="short")

    def test_invalid_status_filter_rejected(self):
        """Should reject invalid status in filter."""
        with pytest.raises(ValidationError):
            RiversideRequirementFilter(status="invalid_status")

    def test_filter_by_owner(self):
        """Should filter by owner name."""
        f = RiversideRequirementFilter(owner="John Doe")
        assert f.owner == "John Doe"
