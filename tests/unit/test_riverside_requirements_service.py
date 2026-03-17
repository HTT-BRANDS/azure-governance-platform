"""Unit tests for Riverside Security Requirements catalog.

Tests the requirements catalog in app/api/services/riverside_requirements.py.

Traces: RC-006 — Riverside requirement catalog integrity, category distribution,
phase assignment, and requirement completeness.
"""

from collections import Counter
from datetime import date

import pytest

from app.api.services.riverside_models import (
    PHASE_1_TARGET_DATE,
    PHASE_2_TARGET_DATE,
    PHASE_3_TARGET_DATE,
    DeadlinePhase,
    RequirementLevel,
    RequirementStatus,
    RiversideRequirementCategory,
)
from app.api.services.riverside_requirements import REQUIREMENTS


# ---------------------------------------------------------------------------
# Catalog Integrity
# ---------------------------------------------------------------------------


class TestRequirementsCatalogIntegrity:
    """Tests for the overall requirements catalog."""

    def test_total_requirement_count(self):
        """Should have exactly 72 requirements as specified."""
        assert len(REQUIREMENTS) == 72

    def test_all_ids_unique(self):
        """Every requirement ID should be unique."""
        ids = [r.id for r in REQUIREMENTS]
        assert len(ids) == len(set(ids)), f"Duplicate IDs: {[x for x, c in Counter(ids).items() if c > 1]}"

    def test_all_have_non_empty_title(self):
        """Every requirement must have a non-empty title."""
        for req in REQUIREMENTS:
            assert req.title, f"Requirement {req.id} has empty title"

    def test_all_have_non_empty_description(self):
        """Every requirement must have a non-empty description."""
        for req in REQUIREMENTS:
            assert req.description, f"Requirement {req.id} has empty description"

    def test_all_have_control_source(self):
        """Every requirement must reference a control source."""
        for req in REQUIREMENTS:
            assert req.control_source, f"Requirement {req.id} missing control_source"

    def test_all_have_control_reference(self):
        """Every requirement must have a control reference."""
        for req in REQUIREMENTS:
            assert req.control_reference, f"Requirement {req.id} missing control_reference"

    def test_default_status_is_not_started(self):
        """All requirements should default to NOT_STARTED status."""
        for req in REQUIREMENTS:
            assert req.status == RequirementStatus.NOT_STARTED, (
                f"Requirement {req.id} has status {req.status}"
            )

    def test_default_evidence_count_is_zero(self):
        """All requirements should default to zero evidence."""
        for req in REQUIREMENTS:
            assert req.evidence_count == 0, (
                f"Requirement {req.id} has evidence_count {req.evidence_count}"
            )


# ---------------------------------------------------------------------------
# Category Distribution
# ---------------------------------------------------------------------------


class TestCategoryDistribution:
    """Tests for requirements distribution across categories."""

    def test_all_8_categories_present(self):
        """All 8 RiversideRequirementCategory values should be represented."""
        categories = {r.category for r in REQUIREMENTS}
        assert categories == set(RiversideRequirementCategory)

    def test_9_per_category(self):
        """Each category should have exactly 9 requirements (72 / 8 = 9)."""
        counter = Counter(r.category for r in REQUIREMENTS)
        for cat, count in counter.items():
            assert count == 9, f"Category {cat.value} has {count} requirements, expected 9"

    @pytest.mark.parametrize(
        "prefix,category",
        [
            ("MFA-", RiversideRequirementCategory.MFA_ENFORCEMENT),
            ("CA-", RiversideRequirementCategory.CONDITIONAL_ACCESS),
            ("PIM-", RiversideRequirementCategory.PRIVILEGED_ACCESS),
            ("DC-", RiversideRequirementCategory.DEVICE_COMPLIANCE),
            ("TM-", RiversideRequirementCategory.THREAT_MANAGEMENT),
            ("DLP-", RiversideRequirementCategory.DATA_LOSS_PREVENTION),
            ("LM-", RiversideRequirementCategory.LOGGING_MONITORING),
            ("IR-", RiversideRequirementCategory.INCIDENT_RESPONSE),
        ],
    )
    def test_id_prefix_matches_category(self, prefix: str, category: RiversideRequirementCategory):
        """IDs should use the correct prefix for their category."""
        for req in REQUIREMENTS:
            if req.category == category:
                assert req.id.startswith(prefix), (
                    f"Requirement {req.id} should start with {prefix}"
                )


# ---------------------------------------------------------------------------
# Phase Assignment
# ---------------------------------------------------------------------------


class TestPhaseAssignment:
    """Tests for requirements phase and target date assignment."""

    def test_all_3_phases_present(self):
        """All 3 deadline phases should be used."""
        phases = {r.phase for r in REQUIREMENTS}
        assert phases == set(DeadlinePhase)

    def test_phase_1_target_date(self):
        """Phase 1 requirements should have September 30, 2025 target."""
        for req in REQUIREMENTS:
            if req.phase == DeadlinePhase.PHASE_1_Q3_2025:
                assert req.target_date == PHASE_1_TARGET_DATE, (
                    f"Requirement {req.id} has wrong Phase 1 target date"
                )

    def test_phase_2_target_date(self):
        """Phase 2 requirements should have December 31, 2025 target."""
        for req in REQUIREMENTS:
            if req.phase == DeadlinePhase.PHASE_2_Q4_2025:
                assert req.target_date == PHASE_2_TARGET_DATE

    def test_phase_3_target_date(self):
        """Phase 3 requirements should have March 31, 2026 target."""
        for req in REQUIREMENTS:
            if req.phase == DeadlinePhase.PHASE_3_Q1_2026:
                assert req.target_date == PHASE_3_TARGET_DATE

    def test_target_dates_are_chronological(self):
        """Phase target dates should be in chronological order."""
        assert PHASE_1_TARGET_DATE < PHASE_2_TARGET_DATE < PHASE_3_TARGET_DATE


# ---------------------------------------------------------------------------
# Maturity Level Distribution
# ---------------------------------------------------------------------------


class TestMaturityLevelDistribution:
    """Tests for maturity level assignments."""

    def test_all_4_levels_present(self):
        """All 4 maturity levels should be represented."""
        levels = {r.maturity_level for r in REQUIREMENTS}
        assert levels == set(RequirementLevel)

    def test_leading_requirements_in_phase_3(self):
        """Leading-level requirements should be in Phase 3 (most advanced)."""
        for req in REQUIREMENTS:
            if req.maturity_level == RequirementLevel.LEADING:
                assert req.phase == DeadlinePhase.PHASE_3_Q1_2026, (
                    f"Leading requirement {req.id} should be Phase 3"
                )

    def test_emerging_in_early_phases(self):
        """Emerging-level requirements should be in Phase 1 or Phase 2."""
        for req in REQUIREMENTS:
            if req.maturity_level == RequirementLevel.EMERGING:
                assert req.phase in (
                    DeadlinePhase.PHASE_1_Q3_2025,
                    DeadlinePhase.PHASE_2_Q4_2025,
                ), f"Emerging requirement {req.id} should be in Phase 1 or 2"


# ---------------------------------------------------------------------------
# Specific Requirement Spot Checks
# ---------------------------------------------------------------------------


class TestSpecificRequirements:
    """Spot checks for specific critical requirements."""

    def _find_req(self, req_id: str):
        """Find a requirement by ID."""
        for req in REQUIREMENTS:
            if req.id == req_id:
                return req
        pytest.fail(f"Requirement {req_id} not found")

    def test_mfa_001_enforce_admin_mfa(self):
        """MFA-001 should enforce MFA for tenant admins."""
        req = self._find_req("MFA-001")
        assert "MFA" in req.title.upper() or "admin" in req.title.lower()
        assert req.category == RiversideRequirementCategory.MFA_ENFORCEMENT
        assert req.phase == DeadlinePhase.PHASE_1_Q3_2025
        assert req.maturity_level == RequirementLevel.EMERGING

    def test_ca_001_block_legacy_auth(self):
        """CA-001 should block legacy authentication."""
        req = self._find_req("CA-001")
        assert "legacy" in req.title.lower() or "block" in req.title.lower()
        assert req.category == RiversideRequirementCategory.CONDITIONAL_ACCESS

    def test_pim_001_enable_pim(self):
        """PIM-001 should enable PIM for global admin."""
        req = self._find_req("PIM-001")
        assert "PIM" in req.title.upper() or "global admin" in req.title.lower()
        assert req.category == RiversideRequirementCategory.PRIVILEGED_ACCESS

    def test_ir_009_is_leading_phase_3(self):
        """IR-009 (self-healing) should be the most advanced requirement."""
        req = self._find_req("IR-009")
        assert req.maturity_level == RequirementLevel.LEADING
        assert req.phase == DeadlinePhase.PHASE_3_Q1_2026

    def test_sequential_ids_per_category(self):
        """IDs within each category should be sequential (001-009)."""
        by_category: dict[RiversideRequirementCategory, list[str]] = {}
        for req in REQUIREMENTS:
            by_category.setdefault(req.category, []).append(req.id)

        for cat, ids in by_category.items():
            nums = sorted(int(rid.split("-")[1]) for rid in ids)
            assert nums == list(range(1, 10)), (
                f"Category {cat.value} has non-sequential IDs: {ids}"
            )
