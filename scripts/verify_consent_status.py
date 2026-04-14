"""Verify admin-consent status for the HTT multi-tenant app across tenants.

Single-purpose check that complements `audit_production.py` — useful on its
own when you just want to know "which tenants still need admin consent on
the HTT Brands app?" without running the full audit.

Reuses `app.core.oidc_credential.ClientAssertionCredential` via the
OIDCCredentialProvider singleton, and calls Microsoft Graph to list the
app-role assignments on the service principal in each tenant.

USAGE
-----

    python scripts/verify_consent_status.py                # prints a table
    python scripts/verify_consent_status.py --json         # JSON output
    python scripts/verify_consent_status.py --fail-on-gap  # exit 1 if any gap

Exit codes:
    0 — all tenants have all required Graph permissions consented
    1 — at least one tenant is missing a required permission
    2 — script-level error (bad config, unreachable Graph, etc.)
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

# Keep in sync with scripts/audit_production.py and graph_client.py usage.
REQUIRED = [
    "Directory.Read.All",
    "Policy.Read.All",
    "AuditLog.Read.All",
    "Reports.Read.All",
    "Organization.Read.All",
    "RoleManagement.Read.Directory",
]

logger = logging.getLogger("verify_consent")


def _load_tenants() -> list[dict[str, Any]]:
    import yaml

    for name in ("tenants.yaml", "tenants.yaml.example"):
        path = REPO_ROOT / "config" / name
        if path.exists():
            raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            return [
                {"code": code, **(cfg or {})}
                for code, cfg in (raw.get("tenants") or {}).items()
                if (cfg or {}).get("is_active", True)
            ]
    return []


def _check(credential: Any, app_client_id: str) -> dict[str, Any]:
    import httpx

    token = credential.get_token("https://graph.microsoft.com/.default").token
    headers = {"Authorization": f"Bearer {token}"}
    with httpx.Client(timeout=15) as c:
        r = c.get(
            "https://graph.microsoft.com/v1.0/servicePrincipals",
            params={"$filter": f"appId eq '{app_client_id}'", "$select": "id"},
            headers=headers,
        )
        r.raise_for_status()
        sps = r.json().get("value", [])
        if not sps:
            return {"ok": False, "missing": REQUIRED, "error": "SP not found"}
        sp_id = sps[0]["id"]

        r = c.get(
            f"https://graph.microsoft.com/v1.0/servicePrincipals/{sp_id}/appRoleAssignments",
            headers=headers,
        )
        r.raise_for_status()
        assignments = r.json().get("value", [])

        r = c.get(
            "https://graph.microsoft.com/v1.0/servicePrincipals",
            params={
                "$filter": "appId eq '00000003-0000-0000-c000-000000000000'",
                "$select": "id,appRoles",
            },
            headers=headers,
        )
        r.raise_for_status()
        graph_sp = (r.json().get("value") or [{}])[0]
        role_map = {r_["id"]: r_["value"] for r_ in graph_sp.get("appRoles", [])}

    granted = {role_map.get(a["appRoleId"], a["appRoleId"]) for a in assignments}
    missing = [p for p in REQUIRED if p not in granted]
    return {
        "ok": not missing,
        "granted": sorted(p for p in REQUIRED if p in granted),
        "missing": missing,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Verify Graph admin-consent status per tenant.")
    p.add_argument("--json", action="store_true", help="Emit JSON instead of a table.")
    p.add_argument(
        "--fail-on-gap",
        action="store_true",
        help="Exit 1 if any required scope is missing anywhere.",
    )
    args = p.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    tenants = _load_tenants()
    if not tenants:
        logger.error("No tenants in config/tenants.yaml(.example)")
        return 2

    try:
        from app.core.oidc_credential import get_oidc_provider
    except Exception as exc:
        logger.error("Unable to import OIDC provider: %s", exc)
        return 2

    provider = get_oidc_provider()
    results: list[dict[str, Any]] = []
    any_gap = False

    for t in tenants:
        tenant_id = t.get("tenant_id")
        app_id = t.get("multi_tenant_app_id") or t.get("app_id")
        entry: dict[str, Any] = {"code": t.get("code"), "tenant_id": tenant_id}
        if not tenant_id or not app_id:
            entry.update({"ok": False, "error": "missing tenant_id or app_id"})
            results.append(entry)
            any_gap = True
            continue
        try:
            credential = provider.get_credential_for_tenant(tenant_id, app_id)
            entry.update(_check(credential, app_id))
        except Exception as exc:
            entry.update({"ok": False, "error": str(exc).splitlines()[0][:400]})
        if not entry.get("ok"):
            any_gap = True
        results.append(entry)

    if args.json:
        print(json.dumps({"results": results, "any_gap": any_gap}, indent=2))
    else:
        print(f"{'Tenant':<10} {'Status':<10} {'Missing / Error'}")
        print("-" * 80)
        for r in results:
            status = "OK" if r.get("ok") else "GAP"
            missing = ", ".join(r.get("missing", [])) or r.get("error", "")
            print(f"{r['code']:<10} {status:<10} {missing}")

    if args.fail_on_gap and any_gap:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
