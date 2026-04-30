---
title: Platform Status
---

# Platform Status

Updated: `2026-04-30T13:18:19.239061+00:00`
Source: GitHub Pages build fallback; no committed `scripts/audit_output.json` was available.

## Current mainline health

| Signal | Status | Evidence |
|---|---|---|
| CI | ✅ Green | Latest pushed mainline docs/DR scaffold passed CI before this page rebuild. |
| Security Scan | ✅ Green | Latest pushed mainline docs/DR scaffold passed security scan. |
| Deploy to Staging | ✅ Green | Latest pushed mainline docs/DR scaffold deployed to staging. |
| Deploy GitHub Pages | ✅ Green | This page was produced by the Pages workflow. |
| GitHub Pages Cross-Browser Tests | ✅ Green | Last mainline Pages test run succeeded. |

## Ready work

| bd | Status | Owner | Notes |
|---|---|---|---|
| `9lfn` | Ready | Tyler | `SECRETS_OF_RECORD.md` skeleton exists; Tyler must fill non-secret inventory rows. |
| `213e` | Ready | Tyler | Second rollback human must be named and tabletop exercise recorded. |
| `jzpa` | In progress | code-puppy-661ed0 | Environment secret names configured; validating production/staging backup workflow and SQLAlchemy fallback. |

## Blocked work

| bd | Blocker |
|---|---|
| `0nup` | Blocked by `213e` second rollback human. |
| `uchp` | Blocked by `213e` before quarterly DR test cycle. |
| `cz89` | BACPAC workflow exists, but staging Azure SQL Free edition does not support ImportExport. Tyler must select validation path in `docs/dr/bacpac-validation-decision.md`. |

## Backup / RPO watch

Scheduled Database Backup run `25145371945` failed on 2026-04-30 in both production and staging after Azure OIDC login succeeded. Logs showed `DATABASE_URL` and `AZURE_STORAGE_ACCOUNT` empty. Those GitHub environment secret names were configured on 2026-04-30. Manual validation then exposed the next code gap: optional `mssqlscripter` was absent in CI, so `backup_database.py` now falls back to SQLAlchemy. This remains tracked as bd `jzpa` until evidence runs pass.

## Audit output

_No tenant audit JSON is currently committed, so this page uses the operational status fallback above instead of rendering tenant consent/UI-fixture tables._
