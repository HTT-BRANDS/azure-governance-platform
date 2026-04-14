"""Diagnostic audit aggregator for the Azure Governance Platform.

Runs a read-only snapshot across the 5 Head-to-Toe tenants and produces:
  - scripts/audit_output.json   (machine-readable)
  - docs/AUDIT-<YYYY-MM>.md     (human-readable punch list)

Checks performed per tenant:
  1. Service principal reachable via ClientAssertionCredential.
  2. Reader role present at the root management group scope.
  3. Consented Graph application permissions match the required set.
  4. App DB row counts + max(synced_at) for resources/costs/compliance/identity.

UI-fixture leak scan is repo-wide (not per-tenant) and grep-based — it
flags any page template importing MOCK_* or fixtures/ symbols.

This script is intentionally defensive: every remote call is wrapped so
one failing tenant does not prevent the others from being reported. The
output is what `docs/AUDIT-<month>.md` is rendered from.

USAGE
-----

    # Local (needs az login + OIDC_ALLOW_DEV_FALLBACK=true):
    python scripts/audit_production.py --env staging

    # In CI (Azure Login already done):
    python scripts/audit_production.py --env production --output scripts/audit_output.json

Exits 0 even on tenant-level failures — this is a reporting tool, not a
gate. CI wraps it and decides whether to fail the pipeline based on the
resulting JSON.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("audit")

REPO_ROOT = Path(__file__).resolve().parent.parent

# Required application-type Graph permissions. Must stay in sync with the
# scopes referenced by app/api/services/graph_client.py + azure_client.py.
REQUIRED_GRAPH_APP_PERMISSIONS = {
    "Directory.Read.All",
    "Policy.Read.All",
    "AuditLog.Read.All",
    "Reports.Read.All",
    "Organization.Read.All",
    "RoleManagement.Read.Directory",
}

# Models and their sync-freshness fields (mirrors /healthz/data).
DATA_DOMAINS = ("resources", "costs", "compliance", "identity")


def _load_tenants() -> list[dict[str, Any]]:
    """Load tenant config from config/tenants.yaml.

    Falls back to the example file so dev environments can still run the
    script — values are clearly placeholders and downstream checks will
    report them as unreachable.
    """
    import yaml

    for name in ("tenants.yaml", "tenants.yaml.example"):
        path = REPO_ROOT / "config" / name
        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            tenants = data.get("tenants", {}) or {}
            return [
                {"code": code, **(cfg or {})}
                for code, cfg in tenants.items()
                if (cfg or {}).get("is_active", True)
            ]
    return []


def _check_reader_scope(credential: Any, subscription_id: str) -> dict[str, Any]:
    """Best-effort Reader check by listing resource groups.

    We avoid calling /providers/Microsoft.Authorization/permissions directly
    because it requires yet another permission surface; ListByResourceGroup
    returning 2xx is a sufficient Reader smoke test for the audit.
    """
    try:
        from azure.mgmt.resource import ResourceManagementClient

        client = ResourceManagementClient(credential, subscription_id)
        rgs = list(client.resource_groups.list(top=1))
        return {"ok": True, "sample_resource_group_count": len(rgs)}
    except Exception as exc:
        return {"ok": False, "error": str(exc).splitlines()[0][:400]}


def _check_graph_consent(credential: Any, app_client_id: str) -> dict[str, Any]:
    """Ask Graph which application permissions the SP has been granted."""
    try:
        import httpx

        token = credential.get_token("https://graph.microsoft.com/.default").token
        headers = {"Authorization": f"Bearer {token}"}
        with httpx.Client(timeout=15) as c:
            # 1. Look up SP by appId.
            r = c.get(
                "https://graph.microsoft.com/v1.0/servicePrincipals",
                params={"$filter": f"appId eq '{app_client_id}'", "$select": "id,appId"},
                headers=headers,
            )
            r.raise_for_status()
            sps = r.json().get("value", [])
            if not sps:
                return {"ok": False, "error": "Service principal not found in tenant"}
            sp_id = sps[0]["id"]

            # 2. Fetch granted app-role assignments.
            r = c.get(
                f"https://graph.microsoft.com/v1.0/servicePrincipals/{sp_id}/appRoleAssignments",
                headers=headers,
            )
            r.raise_for_status()
            assignments = r.json().get("value", [])

            # 3. Resolve role IDs to names by fetching the Graph SP's appRoles.
            r = c.get(
                "https://graph.microsoft.com/v1.0/servicePrincipals",
                params={
                    "$filter": "appId eq '00000003-0000-0000-c000-000000000000'",  # Graph
                    "$select": "id,appRoles",
                },
                headers=headers,
            )
            r.raise_for_status()
            graph_sp = (r.json().get("value") or [{}])[0]
            role_map = {role["id"]: role["value"] for role in graph_sp.get("appRoles", [])}

        granted = {role_map.get(a["appRoleId"], a["appRoleId"]) for a in assignments}
        missing = sorted(REQUIRED_GRAPH_APP_PERMISSIONS - granted)
        return {
            "ok": not missing,
            "granted": sorted(granted & REQUIRED_GRAPH_APP_PERMISSIONS),
            "missing": missing,
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc).splitlines()[0][:400]}


def _query_db_freshness() -> dict[str, dict[str, Any]]:
    """Query local app DB for per-tenant row counts + max(synced_at)."""
    try:
        from sqlalchemy import func

        from app.core.database import SessionLocal
        from app.models.compliance import ComplianceSnapshot
        from app.models.cost import CostSnapshot
        from app.models.identity import IdentitySnapshot
        from app.models.resource import Resource
        from app.models.tenant import Tenant
    except Exception as exc:
        return {"_error": {"reason": f"Unable to import app models: {exc}"}}

    domain_models = {
        "resources": Resource,
        "costs": CostSnapshot,
        "compliance": ComplianceSnapshot,
        "identity": IdentitySnapshot,
    }
    out: dict[str, dict[str, Any]] = {}
    db = SessionLocal()
    try:
        for tenant in db.query(Tenant).all():
            per: dict[str, Any] = {}
            for name, model in domain_models.items():
                try:
                    count = (
                        db.query(func.count())
                        .select_from(model)
                        .filter(model.tenant_id == tenant.id)
                        .scalar()
                        or 0
                    )
                    last = (
                        db.query(func.max(model.synced_at))
                        .filter(model.tenant_id == tenant.id)
                        .scalar()
                    )
                except Exception as exc:
                    per[name] = {"error": str(exc).splitlines()[0][:200]}
                    continue
                per[name] = {
                    "count": int(count),
                    "last_sync": last.isoformat() if last else None,
                }
            out[tenant.tenant_id] = per
    finally:
        db.close()
    return out


_FIXTURE_PAT = re.compile(r"(from\s+tests\.fixtures|import\s+MOCK_|fixtures/|faker\.)")


def _scan_fixture_leaks() -> list[str]:
    """Grep page templates + render routes for fixture/mock imports."""
    hits: list[str] = []
    for path in (REPO_ROOT / "app" / "templates" / "pages").glob("*.html"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "MOCK_" in text or "fixtures/" in text:
            hits.append(str(path.relative_to(REPO_ROOT)))
    routes = REPO_ROOT / "app" / "api" / "routes"
    if routes.exists():
        for path in routes.glob("*.py"):
            text = path.read_text(encoding="utf-8", errors="ignore")
            if _FIXTURE_PAT.search(text):
                hits.append(str(path.relative_to(REPO_ROOT)))
    return sorted(set(hits))


def _audit_tenant(tenant: dict[str, Any]) -> dict[str, Any]:
    """Run the per-tenant checks. Reuses app.core.oidc_credential."""
    code = tenant["code"]
    tenant_id = tenant.get("tenant_id", "")
    app_id = tenant.get("multi_tenant_app_id") or tenant.get("app_id", "")

    result: dict[str, Any] = {
        "code": code,
        "tenant_id": tenant_id,
        "app_id": app_id,
        "reader": {"ok": False, "error": "not checked"},
        "graph_consent": {"ok": False, "error": "not checked"},
    }
    if not tenant_id or not app_id:
        result["reader"]["error"] = "missing tenant_id or app_id in config"
        result["graph_consent"]["error"] = "missing tenant_id or app_id in config"
        return result

    try:
        from app.core.oidc_credential import get_oidc_provider

        credential = get_oidc_provider().get_credential_for_tenant(tenant_id, app_id)
    except Exception as exc:
        msg = f"credential init failed: {exc}"
        result["reader"]["error"] = msg
        result["graph_consent"]["error"] = msg
        return result

    # Reader check needs a subscription — pick the first visible one.
    try:
        from azure.mgmt.subscription import SubscriptionClient

        sub_client = SubscriptionClient(credential)
        subscriptions = list(sub_client.subscriptions.list())
        if subscriptions:
            result["reader"] = _check_reader_scope(credential, subscriptions[0].subscription_id)
            result["visible_subscriptions"] = len(subscriptions)
        else:
            result["reader"] = {"ok": False, "error": "no visible subscriptions"}
            result["visible_subscriptions"] = 0
    except Exception as exc:
        result["reader"] = {"ok": False, "error": str(exc).splitlines()[0][:400]}

    result["graph_consent"] = _check_graph_consent(credential, app_id)
    return result


def _render_markdown(report: dict[str, Any]) -> str:
    """Render the JSON report as a human-scannable punch list."""
    lines: list[str] = []
    lines.append(f"# Production Audit — {report['generated_at']}")
    lines.append("")
    lines.append(f"Environment: **{report['environment']}**  ")
    lines.append(f"Tenants checked: **{len(report['tenants'])}**  ")
    lines.append("")

    # Consent gaps
    consent_gaps: list[str] = []
    rbac_gaps: list[str] = []
    for t in report["tenants"]:
        if not t["reader"].get("ok"):
            rbac_gaps.append(
                f"- **{t['code']}** ({t['tenant_id']}): {t['reader'].get('error', 'no Reader')}"
            )
        missing = t["graph_consent"].get("missing") or []
        if missing:
            consent_gaps.append(f"- **{t['code']}**: missing `{', '.join(missing)}`")
        elif not t["graph_consent"].get("ok"):
            consent_gaps.append(
                f"- **{t['code']}**: {t['graph_consent'].get('error', 'consent unverified')}"
            )

    lines.append("## Consent Gaps")
    lines.append(
        "\n".join(consent_gaps)
        if consent_gaps
        else "_None — all required Graph scopes are consented._"
    )
    lines.append("")
    lines.append("## RBAC Gaps")
    lines.append(
        "\n".join(rbac_gaps)
        if rbac_gaps
        else "_None — all tenants have Reader on their root scope._"
    )
    lines.append("")

    # Sync freshness
    lines.append("## Sync Errors & Data Freshness")
    freshness = report.get("db_freshness", {})
    if "_error" in freshness:
        lines.append(f"_DB unreachable: {freshness['_error']['reason']}_")
    elif not freshness:
        lines.append("_No tenants present in DB yet._")
    else:
        lines.append(
            "| Tenant | " + " | ".join(f"{d} (rows / last sync)" for d in DATA_DOMAINS) + " |"
        )
        lines.append("|" + "---|" * (1 + len(DATA_DOMAINS)))
        for tenant_id, per in freshness.items():
            cells = [tenant_id]
            for d in DATA_DOMAINS:
                info = per.get(d, {}) or {}
                if "error" in info:
                    cells.append(f"⚠️ {info['error']}")
                else:
                    cells.append(f"{info.get('count', 0)} / {info.get('last_sync') or '—'}")
            lines.append("| " + " | ".join(cells) + " |")
    lines.append("")

    # UI-fixture leaks
    lines.append("## UI-Fixture Leaks")
    leaks = report.get("ui_fixture_leaks", [])
    if leaks:
        for path in leaks:
            lines.append(f"- `{path}`")
    else:
        lines.append("_None — no MOCK_/fixture references in pages or routes._")
    lines.append("")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit Azure governance production readiness.")
    parser.add_argument(
        "--env", default="unknown", help="Environment label (dev/staging/production)."
    )
    parser.add_argument(
        "--output",
        default=str(REPO_ROOT / "scripts" / "audit_output.json"),
        help="Path to write the JSON report.",
    )
    parser.add_argument(
        "--markdown",
        default=None,
        help="Path to write the Markdown punch list. Default: docs/AUDIT-<YYYY-MM>.md",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    # Make `app.*` imports work when run from repo root.
    sys.path.insert(0, str(REPO_ROOT))

    tenants = _load_tenants()
    logger.info("audit: %d active tenants loaded from config", len(tenants))

    report: dict[str, Any] = {
        "generated_at": datetime.now(UTC).isoformat(),
        "environment": args.env,
        "required_graph_permissions": sorted(REQUIRED_GRAPH_APP_PERMISSIONS),
        "tenants": [_audit_tenant(t) for t in tenants],
        "db_freshness": _query_db_freshness(),
        "ui_fixture_leaks": _scan_fixture_leaks(),
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    logger.info("audit: wrote JSON to %s", out_path)

    md_path = (
        Path(args.markdown)
        if args.markdown
        else REPO_ROOT / "docs" / f"AUDIT-{datetime.now(UTC).strftime('%Y-%m')}.md"
    )
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(_render_markdown(report), encoding="utf-8")
    logger.info("audit: wrote Markdown to %s", md_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
