"""Riverside compliance enums."""

from enum import StrEnum


class RequirementCategory(StrEnum):
    """Riverside compliance requirement categories."""

    IAM = "IAM"  # Identity and Access Management
    GS = "GS"  # Group Security
    DS = "DS"  # Domain Security


class RequirementPriority(StrEnum):
    """Riverside compliance requirement priorities."""

    P0 = "P0"  # Critical
    P1 = "P1"  # High
    P2 = "P2"  # Medium


class RequirementStatus(StrEnum):
    """Riverside compliance requirement statuses."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
