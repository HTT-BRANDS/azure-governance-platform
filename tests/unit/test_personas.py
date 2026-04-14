"""Unit tests for the persona resolution layer."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from app.core import personas as personas_mod
from app.core.auth import User


@pytest.fixture(autouse=True)
def _isolated_config(tmp_path, monkeypatch):
    """Point the personas module at a per-test config file."""
    cfg = {
        "personas": {
            "it_admin": {"groups": ["g-it-admin"], "pages": ["*"]},
            "operations": {"groups": ["g-ops"], "pages": ["resources", "compliance"]},
            "finance": {"groups": ["g-finance"], "pages": ["costs", "dashboard"]},
            "marketing": {"groups": ["g-marketing"], "pages": ["identity", "dashboard"]},
        }
    }
    path = tmp_path / "personas.yaml"
    path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    monkeypatch.setattr(personas_mod, "_DEFAULT_CONFIG_PATH", Path(path))
    personas_mod.reload_config()
    yield
    personas_mod.reload_config()


def _user(roles=(), personas=()):
    return User(
        id="u",
        email="e@e.com",
        name="N",
        roles=list(roles),
        tenant_ids=[],
        personas=list(personas),
    )


def test_resolve_personas_matches_groups():
    assert personas_mod.resolve_personas(["g-finance"]) == ["finance"]
    assert personas_mod.resolve_personas(["g-it-admin", "g-ops"]) == ["it_admin", "operations"]


def test_resolve_personas_empty():
    assert personas_mod.resolve_personas([]) == []
    assert personas_mod.resolve_personas(None) == []
    assert personas_mod.resolve_personas(["unknown-group"]) == []


def test_pages_for_personas_star_wins():
    visible = personas_mod.pages_for_personas(["it_admin", "finance"])
    assert visible == {"*"}


def test_pages_for_personas_union():
    visible = personas_mod.pages_for_personas(["finance", "marketing"])
    assert visible == {"costs", "dashboard", "identity"}


def test_has_persona_admin_bypass():
    assert personas_mod.has_persona(_user(roles=["admin"]), "finance") is True


def test_has_persona_direct():
    assert personas_mod.has_persona(_user(personas=["finance"]), "finance") is True
    assert personas_mod.has_persona(_user(personas=["finance"]), "marketing") is False


def test_can_view_page_soft_default_when_no_personas():
    # Users without any persona assigned should still see everything (soft rollout).
    assert personas_mod.can_view_page(_user(), "costs") is True


def test_can_view_page_gates_by_persona():
    u = _user(personas=["marketing"])
    assert personas_mod.can_view_page(u, "identity") is True
    assert personas_mod.can_view_page(u, "costs") is False


def test_can_view_page_admin_bypass():
    u = _user(roles=["admin"], personas=["marketing"])
    assert personas_mod.can_view_page(u, "costs") is True


def test_require_persona_unknown_raises_at_registration():
    with pytest.raises(ValueError):
        personas_mod.require_persona("not-a-persona")


@pytest.mark.asyncio
async def test_require_persona_dependency_passes_admin():
    checker = personas_mod.require_persona("finance")
    result = await checker(_user(roles=["admin"]))
    assert result.roles == ["admin"]


@pytest.mark.asyncio
async def test_require_persona_dependency_rejects_mismatch():
    from fastapi import HTTPException

    checker = personas_mod.require_persona("finance")
    with pytest.raises(HTTPException) as exc:
        await checker(_user(personas=["marketing"]))
    assert exc.value.status_code == 403
