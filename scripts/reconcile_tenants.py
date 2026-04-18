"""Reconcile ``config/tenants.yaml`` ↔ DB ``tenants`` table.

This script is the authoritative tool for detecting and fixing drift between
the YAML-declared tenant inventory and the actual rows in the database.

Origin: bd-c7aa (DCE was in YAML but missing from DB, so no sync jobs ran
for it). The underlying class of bug is the same latent-footgun pattern as
a1sb and sf24 — a silent config-vs-reality mismatch that no one noticed
until it caused a symptom.

Usage
-----

Dry run (default — reports drift, makes no changes)::

    python scripts/reconcile_tenants.py

Apply changes (inserts missing tenants)::

    python scripts/reconcile_tenants.py --apply

Verbose output::

    python scripts/reconcile_tenants.py --verbose

The script exits 0 if reconciliation succeeded (including dry-run with no
drift) and 1 if drift exists but --apply was NOT passed. Suitable for a
startup/CI check.
"""

from __future__ import annotations

import argparse
import logging
import sys
import uuid
from dataclasses import dataclass

# Make 'app' importable when running from repo root
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

# Import submodules directly to avoid pulling app.core.__init__ (which
# eagerly imports the scheduler + other heavy deps not needed here).
import importlib  # noqa: E402

_db = importlib.import_module("app.core.database")
_tc = importlib.import_module("app.core.tenants_config")
_tm = importlib.import_module("app.models.tenant")

SessionLocal = _db.SessionLocal
TenantConfig = _tc.TenantConfig
get_active_tenants = _tc.get_active_tenants
Tenant = _tm.Tenant

logger = logging.getLogger("reconcile_tenants")


# ---------------------------------------------------------------------------
# Drift detection
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Drift:
    """Result of comparing YAML tenants to DB tenants."""

    missing_in_db: list[TenantConfig]  # exists in YAML, not in DB
    extra_in_db: list[Tenant]  # exists in DB, not in YAML
    name_mismatches: list[tuple[TenantConfig, Tenant]]  # same tenant_id, different name

    @property
    def has_drift(self) -> bool:
        return bool(self.missing_in_db or self.extra_in_db or self.name_mismatches)


def detect_drift(yaml_tenants: dict[str, TenantConfig], db_tenants: list[Tenant]) -> Drift:
    """Compare YAML and DB tenant inventories. Returns structured drift report."""
    # Index DB tenants by their azure tenant_id (the stable identifier)
    db_by_tid = {t.tenant_id: t for t in db_tenants}

    missing: list[TenantConfig] = []
    mismatches: list[tuple[TenantConfig, Tenant]] = []

    for cfg in yaml_tenants.values():
        db_row = db_by_tid.get(cfg.tenant_id)
        if db_row is None:
            missing.append(cfg)
        elif db_row.name != cfg.name:
            mismatches.append((cfg, db_row))

    yaml_tids = {cfg.tenant_id for cfg in yaml_tenants.values()}
    extra = [t for t in db_tenants if t.tenant_id not in yaml_tids]

    return Drift(missing_in_db=missing, extra_in_db=extra, name_mismatches=mismatches)


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def render_report(drift: Drift) -> str:
    """Human-readable drift summary (stdout-friendly)."""
    lines: list[str] = []
    if drift.missing_in_db:
        lines.append(f"❌ MISSING IN DB ({len(drift.missing_in_db)}):")
        for cfg in drift.missing_in_db:
            lines.append(f"   - {cfg.code} ({cfg.name}) tenant_id={cfg.tenant_id}")
    if drift.extra_in_db:
        lines.append(f"⚠️  EXTRA IN DB ({len(drift.extra_in_db)}) — in DB but not YAML:")
        for t in drift.extra_in_db:
            lines.append(f"   - {t.name} tenant_id={t.tenant_id} (db id={t.id})")
    if drift.name_mismatches:
        lines.append(f"⚠️  NAME MISMATCHES ({len(drift.name_mismatches)}):")
        for cfg, db in drift.name_mismatches:
            lines.append(f"   - tenant_id={cfg.tenant_id}: YAML='{cfg.name}' DB='{db.name}'")
    if not drift.has_drift:
        lines.append("✅ No drift — YAML and DB inventories match.")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Apply
# ---------------------------------------------------------------------------


def apply_inserts(missing: list[TenantConfig]) -> list[str]:
    """Insert tenants that are in YAML but missing from DB. Returns list of inserted codes."""
    inserted: list[str] = []
    with SessionLocal() as session:
        for cfg in missing:
            row = Tenant(
                id=str(uuid.uuid4()),
                name=cfg.name,
                tenant_id=cfg.tenant_id,
                client_id=cfg.app_id,
                description=f"Reconciled from tenants.yaml (code={cfg.code})",
                is_active=cfg.is_active,
                use_lighthouse=False,
                use_oidc=cfg.oidc_enabled,
            )
            session.add(row)
            inserted.append(cfg.code)
            logger.info("Inserted tenant: %s (%s)", cfg.code, cfg.tenant_id)
        session.commit()
    return inserted


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply inserts for tenants missing from DB (default: dry-run)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s [%(name)s] %(message)s",
    )

    yaml_tenants = get_active_tenants()
    logger.info("Loaded %d tenants from YAML", len(yaml_tenants))

    with SessionLocal() as session:
        db_tenants = session.query(Tenant).all()
    logger.info("Loaded %d tenants from DB", len(db_tenants))

    drift = detect_drift(yaml_tenants, db_tenants)
    print(render_report(drift))

    if not drift.has_drift:
        return 0

    # Extras and name mismatches are reported but not auto-fixed —
    # they require human judgment (might be intentional legacy data).
    if drift.extra_in_db or drift.name_mismatches:
        print(
            "\nNote: extras and name mismatches are reported only. Resolve manually after review.",
            file=sys.stderr,
        )

    if not args.apply:
        print(
            "\nDry-run mode. Re-run with --apply to insert missing tenants.",
            file=sys.stderr,
        )
        # Exit 1 to make drift detectable by CI / startup assertions
        return 1

    if drift.missing_in_db:
        inserted = apply_inserts(drift.missing_in_db)
        print(f"\n✅ Inserted {len(inserted)} tenant(s): {', '.join(inserted)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
