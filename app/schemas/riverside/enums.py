"""Riverside compliance enums."""

from enum import Enum


class RequirementCategory(str, Enum):
    """Riverside compliance requirement categories."""

    IAM = "IAM"  # Identity and Access Management
    GS = "GS"  # Group Security
    DS = "DS"  # Domain Security


class RequirementPriority(str, Enum):
    """Riverside compliance requirement priorities."""

    P0 = "P0"  # Critical
    P1 = "P1"  # High
    P2 = "P2"  # Medium


class RequirementStatus(str, Enum):
    """Riverside compliance requirement statuses."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
