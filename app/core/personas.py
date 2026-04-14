"""Persona resolution and UI gating.

Personas map Entra ID security group memberships to department-level
views (it_admin, operations, finance, marketing). They sit alongside the
existing admin/viewer/operator role model — a user's persona determines
which nav sections they see in the UI; their role still governs what
actions they can take within those sections.

Resolution:
    1. On Azure AD token validation, `groups` claim is read from the JWT.
    2. `resolve_personas(group_ids)` matches group object IDs against the
       mapping in `config/personas.yaml`.
    3. Results are attached to `TokenData.personas` and surfaced as
       `request.state.personas` + `user.personas` for template/route use.

`require_persona(name)` is a FastAPI dependency factory mirroring
`require_roles` in app.core.auth. Admin role always bypasses the check.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from fastapi import Depends, HTTPException, status

from app.core.auth import User, get_current_user

logger = logging.getLogger(__name__)

_DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "personas.yaml"

# Known personas (source of truth). Keep in sync with config/personas.yaml.
KNOWN_PERSONAS: tuple[str, ...] = (
    "it_admin",
    "operations",
    "finance",
    "marketing",
)


@lru_cache(maxsize=1)
def _load_config(config_path: str | None = None) -> dict[str, Any]:
    """Load the personas config file (memoised).

    Returns an empty config on missing file so dev environments without a
    populated ``config/personas.yaml`` don't crash — they just see no
    personas resolved.
    """
    path = Path(config_path) if config_path else _DEFAULT_CONFIG_PATH
    if not path.exists():
        logger.info("personas: config file %s not found — persona layer disabled", path)
        return {"personas": {}}
    try:
        with path.open("r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
    except yaml.YAMLError as exc:
        logger.error("personas: failed to parse %s: %s", path, exc)
        return {"personas": {}}
    if not isinstance(raw, dict) or "personas" not in raw:
        logger.error("personas: malformed config %s — missing top-level 'personas' key", path)
        return {"personas": {}}
    return raw


def reload_config() -> None:
    """Clear the config cache (useful for tests and hot-reloads)."""
    _load_config.cache_clear()


def resolve_personas(group_ids: list[str] | None) -> list[str]:
    """Resolve persona names from Entra ID security group object IDs.

    Args:
        group_ids: Group object IDs from the ``groups`` token claim.

    Returns:
        Sorted list of matching persona names. Empty if no groups match.
    """
    if not group_ids:
        return []

    mapping = _load_config().get("personas", {})
    if not mapping:
        return []

    group_set = {g.lower() for g in group_ids if g}
    matched: set[str] = set()
    for name, cfg in mapping.items():
        if not isinstance(cfg, dict):
            continue
        configured = {str(g).lower() for g in cfg.get("groups", []) if g}
        if configured & group_set:
            matched.add(name)
    return sorted(matched)


def pages_for_personas(personas: list[str]) -> set[str]:
    """Compute the set of nav keys visible for the given personas.

    "*" in any persona's ``pages`` list grants access to everything.
    """
    if not personas:
        return set()

    mapping = _load_config().get("personas", {})
    visible: set[str] = set()
    for name in personas:
        cfg = mapping.get(name)
        if not isinstance(cfg, dict):
            continue
        pages = cfg.get("pages", [])
        if "*" in pages:
            return {"*"}
        visible.update(str(p) for p in pages)
    return visible


def has_persona(user: User, persona: str) -> bool:
    """Return True when the user has the given persona (or is admin)."""
    if "admin" in user.roles:
        return True
    user_personas = getattr(user, "personas", None) or []
    return persona in user_personas


def can_view_page(user: User, page_key: str) -> bool:
    """Return True when the user may see the given nav page key.

    Admins see everything. Users with no personas see everything (soft
    rollout — gating only applies once they've been placed in a persona
    group). This keeps existing users unaffected during the transition.
    """
    if "admin" in user.roles:
        return True
    personas = getattr(user, "personas", None) or []
    if not personas:
        return True  # soft default
    visible = pages_for_personas(personas)
    return "*" in visible or page_key in visible


def require_persona(name: str):
    """FastAPI dependency factory: require a specific persona (or admin).

    Usage::

        @router.get("/finance-only")
        async def _(user: User = Depends(require_persona("finance"))):
            ...
    """
    if name not in KNOWN_PERSONAS:
        # Fail loudly on typos at route-registration time.
        raise ValueError(f"Unknown persona '{name}'. Valid: {', '.join(KNOWN_PERSONAS)}")

    async def _checker(user: User = Depends(get_current_user)) -> User:
        if has_persona(user, name):
            return user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Required persona: {name}",
        )

    return _checker


def require_any_persona(*names: str):
    """FastAPI dependency: require at least one of the given personas."""
    for n in names:
        if n not in KNOWN_PERSONAS:
            raise ValueError(f"Unknown persona '{n}'. Valid: {', '.join(KNOWN_PERSONAS)}")

    async def _checker(user: User = Depends(get_current_user)) -> User:
        if "admin" in user.roles:
            return user
        user_personas = set(getattr(user, "personas", None) or [])
        if user_personas.intersection(names):
            return user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Required any persona: {', '.join(names)}",
        )

    return _checker
