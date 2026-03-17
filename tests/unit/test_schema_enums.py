"""Unit tests for Riverside compliance enums.

Tests the StrEnum definitions in app/schemas/riverside/enums.py.

Traces: RC-008 — Enum integrity for requirement categories,
priorities, and statuses used throughout the Riverside module.
"""

from enum import StrEnum

import pytest

from app.schemas.riverside.enums import (
    RequirementCategory,
    RequirementPriority,
    RequirementStatus,
)


# ---------------------------------------------------------------------------
# RequirementCategory
# ---------------------------------------------------------------------------


class TestRequirementCategory:
    """Tests for RequirementCategory StrEnum."""

    def test_is_str_enum(self):
        """Should be a StrEnum subclass."""
        assert issubclass(RequirementCategory, StrEnum)

    def test_member_count(self):
        """Should have exactly 3 categories."""
        assert len(RequirementCategory) == 3

    def test_iam_value(self):
        assert RequirementCategory.IAM == "IAM"

    def test_gs_value(self):
        assert RequirementCategory.GS == "GS"

    def test_ds_value(self):
        assert RequirementCategory.DS == "DS"

    def test_string_equality(self):
        """StrEnum members should compare equal to their string values."""
        assert RequirementCategory.IAM == "IAM"
        assert RequirementCategory.GS == "GS"
        assert RequirementCategory.DS == "DS"

    def test_membership(self):
        """Should support 'in' operator for membership testing."""
        assert "IAM" in RequirementCategory.__members__
        assert "GS" in RequirementCategory.__members__
        assert "DS" in RequirementCategory.__members__

    def test_non_member(self):
        """Non-members should not be in __members__."""
        assert "UNKNOWN" not in RequirementCategory.__members__

    def test_lookup_by_value(self):
        """Should construct from string value."""
        assert RequirementCategory("IAM") == RequirementCategory.IAM

    def test_invalid_value_raises(self):
        """Should raise ValueError for invalid category."""
        with pytest.raises(ValueError):
            RequirementCategory("INVALID")


# ---------------------------------------------------------------------------
# RequirementPriority
# ---------------------------------------------------------------------------


class TestRequirementPriority:
    """Tests for RequirementPriority StrEnum."""

    def test_is_str_enum(self):
        assert issubclass(RequirementPriority, StrEnum)

    def test_member_count(self):
        """Should have exactly 3 priority levels."""
        assert len(RequirementPriority) == 3

    def test_p0_value(self):
        assert RequirementPriority.P0 == "P0"

    def test_p1_value(self):
        assert RequirementPriority.P1 == "P1"

    def test_p2_value(self):
        assert RequirementPriority.P2 == "P2"

    def test_string_equality(self):
        """StrEnum members should compare equal to their string values."""
        assert RequirementPriority.P0 == "P0"
        assert RequirementPriority.P1 == "P1"
        assert RequirementPriority.P2 == "P2"

    def test_lookup_by_value(self):
        assert RequirementPriority("P0") == RequirementPriority.P0
        assert RequirementPriority("P1") == RequirementPriority.P1
        assert RequirementPriority("P2") == RequirementPriority.P2

    def test_invalid_priority_raises(self):
        with pytest.raises(ValueError):
            RequirementPriority("P3")

    @pytest.mark.parametrize("priority", ["P0", "P1", "P2"])
    def test_all_valid_priorities(self, priority: str):
        """All defined priorities should be constructible from strings."""
        assert RequirementPriority(priority).value == priority


# ---------------------------------------------------------------------------
# RequirementStatus
# ---------------------------------------------------------------------------


class TestRequirementStatus:
    """Tests for RequirementStatus StrEnum."""

    def test_is_str_enum(self):
        assert issubclass(RequirementStatus, StrEnum)

    def test_member_count(self):
        """Should have exactly 4 statuses."""
        assert len(RequirementStatus) == 4

    def test_not_started_value(self):
        assert RequirementStatus.NOT_STARTED == "not_started"

    def test_in_progress_value(self):
        assert RequirementStatus.IN_PROGRESS == "in_progress"

    def test_completed_value(self):
        assert RequirementStatus.COMPLETED == "completed"

    def test_blocked_value(self):
        assert RequirementStatus.BLOCKED == "blocked"

    def test_string_equality(self):
        """StrEnum members should compare equal to their string values."""
        assert RequirementStatus.NOT_STARTED == "not_started"
        assert RequirementStatus.COMPLETED == "completed"

    @pytest.mark.parametrize(
        "status",
        ["not_started", "in_progress", "completed", "blocked"],
    )
    def test_all_valid_statuses(self, status: str):
        """All defined statuses should be constructible from strings."""
        assert RequirementStatus(status).value == status

    def test_invalid_status_raises(self):
        with pytest.raises(ValueError):
            RequirementStatus("cancelled")

    def test_values_are_snake_case(self):
        """All status values should use snake_case convention."""
        for status in RequirementStatus:
            assert status.value == status.value.lower()
            assert " " not in status.value


# ---------------------------------------------------------------------------
# Cross-Enum Tests
# ---------------------------------------------------------------------------


class TestEnumCrossValidation:
    """Cross-cutting tests across all enums."""

    def test_no_overlapping_values(self):
        """No enum value should appear in another enum."""
        cat_values = {c.value for c in RequirementCategory}
        pri_values = {p.value for p in RequirementPriority}
        status_values = {s.value for s in RequirementStatus}

        assert cat_values.isdisjoint(pri_values), "Category and Priority overlap"
        assert cat_values.isdisjoint(status_values), "Category and Status overlap"
        assert pri_values.isdisjoint(status_values), "Priority and Status overlap"

    def test_all_enums_are_str_enum(self):
        """All Riverside enums should be StrEnum for JSON serialization."""
        for enum_cls in [RequirementCategory, RequirementPriority, RequirementStatus]:
            assert issubclass(enum_cls, StrEnum), f"{enum_cls.__name__} is not StrEnum"

    def test_enums_are_hashable(self):
        """All enum members should be usable as dict keys."""
        d = {
            RequirementCategory.IAM: "identity",
            RequirementPriority.P0: "critical",
            RequirementStatus.COMPLETED: "done",
        }
        assert d[RequirementCategory.IAM] == "identity"
        assert d[RequirementPriority.P0] == "critical"
