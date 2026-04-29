"""Database session compatibility helpers for admin risk checks."""

from sys import modules
from typing import Any

from app.core.database import SessionLocal


def create_admin_risk_session() -> Any:
    """Create a DB session while preserving the legacy patch seam.

    Historical tests and callers patch ``app.preflight.admin_risk_checks.SessionLocal``.
    The implementation now lives in split modules, so resolve that public symbol
    at call time when the compatibility wrapper has been imported.
    """
    compat_module = modules.get("app.preflight.admin_risk_checks")
    session_factory = getattr(compat_module, "SessionLocal", SessionLocal)
    return session_factory()
