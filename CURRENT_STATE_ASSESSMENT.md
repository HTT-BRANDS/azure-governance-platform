# Current State Assessment — HTT Control Tower

**Assessment Date:** 2026-04-30
**HEAD assessed:** `f9f7c60` (`docs(status): close backup validation`) plus rebrand branch audit in progress
**Source of truth for in-flight detail:** [`SESSION_HANDOFF.md`](./SESSION_HANDOFF.md), `bd ready`, and GitHub Actions run history.

> This file is a reality dashboard. If it says "green," it needs a run ID or
> it is just decorative confetti. We are not doing decorative confetti.

---

## TL;DR

HTT Control Tower runtime is up in both environments. Backup/RPO validation is green; Tyler-only continuity work remains.

- Production health: `https://app-governance-prod.azurewebsites.net/health` returns `healthy` / `2.5.0`.
- Staging health: `https://app-governance-staging-xnczpwyv.azurewebsites.net/health` returns `healthy` / `2.5.0`.
- Mainline CI, Security Scan, Pages, browser tests, accessibility, and staging deploy were green for `f9f7c60`.
- GitHub Pages deployed for `246e454`, and cross-browser tests passed after the homepage title compatibility fix.
- Staging deploy run `25168188519` passed QA, security, build/push, deploy, and staging validation.
- Scheduled/manual Database Backup is green and bd `jzpa` is closed: staging schema backup passed end-to-end (`25169438794`), production schema backup passed end-to-end (`25171354807`), and no temporary `GitHubActions-*` SQL firewall rules remained afterward.
- Tyler-only continuity gates remain: `9lfn` secret inventory completion and `213e` second rollback human.

---

## Live environment checks

| Environment | URL | Latest observed status | Notes |
|---|---|---|---|
| Production | <https://app-governance-prod.azurewebsites.net/health> | ✅ `healthy`, version `2.5.0` | Checked 2026-04-30 during this session. |
| Staging | <https://app-governance-staging-xnczpwyv.azurewebsites.net/health> | ✅ `healthy`, version `2.5.0` | The older `xncz` hostname is stale; use `xnczpwyv`. |
| GitHub Pages | <https://htt-brands.github.io/azure-governance-platform/> | ✅ Latest deploy/browser checks passed for `f9f7c60` | URL remains the old repo slug until the GitHub repo rename cutover. Content is being rebranded to Control Tower. |

---

## Latest relevant GitHub Actions

| Workflow | Run | Conclusion | Meaning |
|---|---:|---|---|
| CI | `25168188513` | ✅ success | Source checks passed for `246e454`. |
| Security Scan | `25168188503` | ✅ success | Security scan passed for `246e454` after `UV_VERSION=0.9.27` pin. |
| Deploy GitHub Pages | `25168188577` | ✅ success | Pages content was published for `246e454`. |
| GitHub Pages Cross-Browser Tests | `25168188537` | ✅ success | Homepage title compatibility fix passed all browser/device projects. |
| Deploy to Staging | `25168188519` | ✅ success | QA, security, build/push, deploy, and staging validation passed. |
| Topology Diagram | `25168188576` | ❌ failure | Generated timestamp-only topology diff but bot could not push to protected `main`; local commit includes refreshed diagram. |
| Database Backup production manual | `25171354807` | ✅ success | Schema-only production backup created, uploaded, verified, retention-cleaned, and temporary SQL firewall rule removed. |
| Database Backup staging manual | `25169438794` | ✅ success | Schema-only staging backup created, verified, uploaded, integrity-checked, and cleanup completed after ephemeral `AZURE_STORAGE_KEY` workflow change. |
| Scheduled Database Backup | `25145371945` | ❌ failure | Original prod/staging empty `DATABASE_URL` / `AZURE_STORAGE_ACCOUNT` failure. |

---

## Current work queue

`bd ready` currently shows:

| bd | Priority | Owner | Status |
|---|---|---|---|
| `9lfn` | P1 | Tyler | Ready — finish non-secret `SECRETS_OF_RECORD.md` inventory. |
| `213e` | P2 | Tyler | Ready — name second rollback human before waiver expiry. |

Blocked:

| bd | Blocker |
|---|---|
| `0nup` | Blocked by `213e`. |
| `uchp` | Blocked by `213e`. |
| `cz89` | Blocked operationally by Azure SQL Free ImportExport limitation; see `docs/dr/bacpac-validation-decision.md`. |

---

## Backup / RPO truth

The backup story is green now. The earlier failures remain documented below because receipts matter and amnesia is not observability.

1. `fifh` fixed the broken Teams notify action.
2. `3flq` fixed OIDC permission for Azure login.
3. Run `25145371945` then exposed missing production/staging GitHub environment backup secret names.
4. On 2026-04-30, `DATABASE_URL` and `AZURE_STORAGE_ACCOUNT` were configured for production and staging without printing secret values.
5. Production backup storage account `stgovprodbkup001` was created in `rg-governance-production`.
6. Manual validation runs `25167657417` and `25167659155` then exposed missing runner SQL tooling: optional `mssqlscripter` and ODBC Driver 18.
7. Current code makes `backup_database.py` fall back to SQLAlchemy and updates `backup.yml` to install `msodbcsql18` / `unixodbc-dev` before running `pyodbc`.
8. Validation runs `25168192604`, `25168194585`, and `25168804362` moved past ODBC. Staging created and verified a SQL backup, then failed Blob upload on `AuthorizationPermissionMismatch` even after Storage Blob Data Contributor was granted. The workflow now derives an ephemeral `AZURE_STORAGE_KEY` after OIDC login and passes it only through runner environment.
9. Staging schema backup passed end-to-end in run `25169438794`.
10. Production schema backup then created, uploaded, verified, and completed retention cleanup in run `25171161761`; only the firewall cleanup step failed because `az sql server firewall-rule delete` does not support `--yes`.
11. The leftover firewall rule was removed manually, the unsupported flag was removed from `backup.yml`, and production validation passed end-to-end in run `25171354807`. Post-run checks found no temporary `GitHubActions-*` SQL firewall rules in production or staging. bd `jzpa` is closed.

RPO backup hygiene is complete for the current schema-only validation scope: production and staging evidence runs passed and bd `jzpa` is closed with run IDs.

---

## Public docs / Pages freshness

The public GitHub Pages site now has:

- Portfolio-platform framing on the home page instead of stale Riverside-first positioning.
- A linked Operations → Continuity Status page.
- `docs/status.md` fallback content that shows current CI/backup/continuity state even when `scripts/audit_output.json` is absent.
- Continuity links to `RUNBOOK.md`, `SECRETS_OF_RECORD.md`, RTO/RPO, and BACPAC validation decision docs.

Still verify the Pages cross-browser failure after this update; the site deploy can succeed while the browser check catches broken links or rendering issues. Tiny rude robot, but useful.

---

## Tyler-only decisions still open

Do not decide these on Tyler's behalf:

- `9lfn`: complete `SECRETS_OF_RECORD.md` ownership/access/rotation metadata.
- `213e`: name second rollback human.
- Portfolio platform final name (`PORTFOLIO_PLATFORM_PLAN_V2.md` §11).
- D8 CIEM build-vs-buy, D9 WIGGUM relationship, D10 cross-tenant identity stance.
