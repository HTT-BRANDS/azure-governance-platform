"""Shared helpers for the riverside preflight checks package.

Split from the monolithic app/preflight/riverside_checks.py
(issue 6oj7, 2026-04-22). SeverityLevel is the only shared type;
everything else (BasePreflightCheck, CheckResult, etc.) lives in
the existing app.preflight base modules.
"""

from __future__ import annotations


class SeverityLevel(str):
    """Severity levels for Riverside checks."""

    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"
