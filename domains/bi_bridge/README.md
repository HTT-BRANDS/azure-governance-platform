# BI Bridge Domain

> Phase 1 paper boundary per `PORTFOLIO_PLATFORM_PLAN_V2.md` §5. No code has
> moved here yet. This document defines the target bounded context for Phase 1.5
> refactors and Phase 2 DDD relocation.

## Purpose

The BI Bridge domain owns curated data export, dashboard aggregation, reporting
read models, and future federation with sister BI/reporting products such as
`httbi` and `DART`. It is the platform's boundary between operational domain
truth and analytics/reporting consumers.

It answers:

- Which cross-domain data is safe and useful to expose as dashboards or exports?
- What schema/contract do downstream BI consumers receive?
- How are tenant authorization and data minimization enforced for exports?
- Which reports are generated for humans, audits, or recovery evidence?
- How will `httbi` and later `DART` consume portfolio-platform read models
  without becoming lateral imports or database parasites?

## Scope Boundary

BI Bridge does **not** own source-of-truth domain facts. It owns projection,
contract, export, and reporting shape.

- Cost owns cost ledger and forecasts.
- Identity owns users, MFA, admin risk, and access grants.
- Compliance owns controls, evidence interpretation, and readiness scoring.
- Resources owns inventory, recommendations, quotas, and resource-change facts.
- Lifecycle owns tenant/brand/playbook lifecycle state.
- BI Bridge owns the safe, versioned, tenant-authorized reporting surface across
  those domains.

No lateral imports between future domain packages. BI Bridge talks to domain
read-model interfaces like a civilized adult, not by spelunking tables with a
headlamp and bad intentions.

## Entities and Value Objects

| Entity / value object | Current model/schema | Notes |
|---|---|---|
| Export request | `app/api/routes/exports.py:54-258` | Query parameters and tenant filters for cost/resource/compliance CSV exports. |
| Export row | `app/api/routes/exports.py:29-52` | Flattened dictionary converted to CSV; currently unversioned. |
| Dashboard summary | `app/api/routes/dashboard.py:50-105` | Cross-domain summary for portfolio dashboard. |
| Sync dashboard read model | `app/api/routes/dashboard.py:194-420` | SRE/ops dashboard projections from monitoring and tenant sync status. |
| Riverside dashboard DTOs | `app/schemas/riverside/dashboard.py:8-178` | Consumer-specific dashboard summary schemas. |
| Riverside analytics read model | `app/api/services/riverside_analytics.py:42-570` | Requirement/deadline/maturity/threat/compliance metrics for Riverside. |
| Preflight report | `app/preflight/reports.py:21-401` | JSON/Markdown/HTML report projections from preflight checks. |
| Sync recovery report | `scripts/verify_sync_recovery_report.py:36-372` | CLI evidence report used for recovery verification. |

Future V2 concepts:

- Versioned BI dataset contract.
- Domain read-model projection.
- Export manifest.
- Data-sharing agreement per downstream consumer.
- `httbi` bridge adapter.
- `DART` bridge adapter after `httbi` is proven.

Do not create these until their Phase 4 issues are filed. YAGNI, but with a
spreadsheet allergy.

## Invariants

1. **Source domains remain authoritative.** BI Bridge may cache/project data, but
   it never becomes the system of record for cost, identity, compliance,
   resources, or lifecycle.
2. **Every export is tenant-authorized.** Export rows must be filtered by the
   caller's tenant scope before serialization.
3. **Export schemas are contracts.** Once consumed by sister products, exported
   fields need versioning and compatibility rules.
4. **Aggregates are preferred over raw detail.** Raw row-level data requires an
   explicit consumer contract and classification review.
5. **No unbounded dumps by default.** Exports should enforce limits, filters, and
   purpose-specific field sets.
6. **Dashboards are projections, not workflows.** They summarize domain state;
   mutation commands stay with owning domains.
7. **Evidence reports are immutable artifacts once cited.** Regenerated evidence
   must carry timestamp/source inputs and should not silently overwrite audit
   artifacts.
8. **No lateral domain imports.** BI Bridge consumes interfaces/read models, not
   domain internals.

## Current Code Locations

These files currently belong wholly or partly to the BI Bridge bounded context.
Line ranges are current as of 2026-04-29 and guide later refactors.

### HTTP exports and dashboards

| Path | Lines | Domain responsibility |
|---|---:|---|
| `app/api/routes/exports.py` | 1-260 | CSV export routes for cost, resources, and compliance; shared CSV generation helper. |
| `app/api/routes/dashboard.py` | 50-135 | Cross-domain dashboard summary aggregation and main dashboard rendering. |
| `app/api/routes/dashboard.py` | 194-420 | Sync dashboard, tenant sync status projections, alerts, history, and HTMX partials. |
| `app/api/routes/dashboard.py` | 422-437 | DMARC dashboard page rendering; consumer-specific analytics surface. |
| `app/templates/pages/dashboard.html` | 1-end | Portfolio dashboard UI projection. |
| `app/templates/pages/sync_dashboard.html` | 1-end | Sync/SRE dashboard UI projection. |
| `app/templates/pages/riverside_dashboard.html` | 1-end | Riverside-specific dashboard UI projection. |
| `app/templates/pages/dmarc_dashboard.html` | 1-end | DMARC dashboard UI projection. |

### Analytics and report generation

| Path | Lines | Domain responsibility |
|---|---:|---|
| `app/api/services/riverside_analytics.py` | 1-570 | Riverside compliance/requirement/deadline/threat metrics and summaries. |
| `app/schemas/riverside/dashboard.py` | 1-178 | Riverside dashboard API/read-model schemas. |
| `app/preflight/reports.py` | 1-401 | Preflight report rendering to JSON/Markdown/HTML, statistics, failed-check recommendations. |
| `scripts/verify_sync_recovery_report.py` | 1-372 | Structured sync recovery evidence report builder and Markdown renderer. |
| `scripts/verify-tenants-report.md` | 1-end | Generated/static tenant verification report artifact. |

### Tests and contracts

| Path | Lines | Domain responsibility |
|---|---:|---|
| `tests/test_api_completeness.py` | 73-91 | Export API parameter/header contract checks. |
| `tests/e2e/api/test_exports_api_e2e.py` | 1-41 | Export endpoint auth/content smoke tests. |
| `docs/openapi-examples/responses/dashboard_summary.json` | 1-end | Dashboard response example/contract. |

### Shared dependencies BI Bridge consumes but does not own

| Path | Lines | Boundary note |
|---|---:|---|
| `app/api/services/cost_service.py` | 1-end | Cost read models. Cost owns semantics. |
| `app/api/services/resource_service.py` | 1-383 | Resource read models. Resources owns semantics. |
| `app/api/services/compliance_service.py` | 1-end | Compliance read models. Compliance owns semantics. |
| `app/api/services/identity_service.py` | 1-end | Identity read models. Identity owns semantics. |
| `app/api/services/monitoring_service.py` | 1-871 | Sync/alert status used by dashboards. Monitoring remains shared/application service. |
| `app/core/authorization.py` | 1-384 | Tenant authorization guard for export/dashboard scope. |
| `app/core/templates.py` | 1-end | Shared Jinja template environment. |

## Inbound Interface Contracts

### HTTP API

Owned route prefix:

- `/api/v1/exports`

Current export routes:

- `GET /api/v1/exports/costs`
  - Inputs: `start_date`, `end_date`, `tenant_ids`.
  - Output: CSV attachment `costs_export_<timestamp>.csv`.
- `GET /api/v1/exports/resources`
  - Inputs: `tenant_ids`, `resource_type`, `include_orphaned`.
  - Output: CSV attachment `resources_export_<timestamp>.csv`.
- `GET /api/v1/exports/compliance`
  - Inputs: `tenant_ids`, `include_non_compliant`.
  - Output: CSV attachment `compliance_export_<timestamp>.csv`.

Owned/reporting UI routes:

- `/dashboard`
- `/sync-dashboard`
- `/dmarc-dashboard`
- dashboard HTMX partials under `/partials/*`

### CLI/reporting commands

- `python scripts/verify_sync_recovery_report.py ...` builds structured recovery
  evidence and Markdown output from App Insights/DB query payloads.
- Preflight report rendering converts a `PreflightReport` to JSON, Markdown, or
  HTML via `app/preflight/reports.py`.

### Future sister-repo contract

Future `httbi` / `DART` bridge adapters should request named, versioned datasets:

- `portfolio_cost_summary.v1`
- `portfolio_resource_inventory_aggregate.v1`
- `portfolio_compliance_posture.v1`
- `portfolio_identity_risk_aggregate.v1`
- `portfolio_lifecycle_status.v1`

Each dataset must declare owner domain, fields, classification, tenant scope,
refresh cadence, retention, and allowed consumers before implementation.

## Outbound Interface Contracts

| Interface | Current concrete implementation | Contract |
|---|---|---|
| Domain read models | Cost/Resource/Compliance/Identity services | Read already-authorized domain DTOs; never mutate source domain state. |
| Tenant authorization | `TenantAuthorization` | Filter export/dashboard rows by caller scope before serialization/rendering. |
| Monitoring/readiness | `MonitoringService`, `SyncJobLog`, `Alert` | Build sync dashboard projections and recovery evidence. |
| CSV serialization | `_generate_csv()` in `exports.py` | Convert flat rows to CSV with deterministic field order per row traversal; future versions should pin schemas. |
| Template rendering | Jinja templates | Render dashboards from read models; no domain mutation in templates. |
| Future httbi/DART | Not implemented | Deliver versioned datasets via explicit bridge adapters/API/export jobs. |

## Explicit Non-Goals

- BI Bridge does not create a warehouse yet.
- BI Bridge does not own raw operational tables.
- BI Bridge does not bypass tenant authorization for convenience. Convenience is
  how you accidentally invent a breach.
- BI Bridge does not own evidence interpretation; Compliance owns that.
- BI Bridge does not own DART or httbi internals; it federates contracts.
- BI Bridge does not decide final platform naming or business framing.

## Phase 1.5 Refactor Guidance

1. Extract CSV serialization and export schemas from `app/api/routes/exports.py`
   before adding more exports.
2. Give exports explicit schema/version definitions before connecting sister
   repos.
3. Split dashboard aggregation from HTML route rendering.
4. Move Riverside-specific analytics behind a consumer adapter boundary; do not
   let one consumer become the platform identity.
5. Ensure every dashboard/export path applies tenant filtering before rows reach
   templates or serializers.
6. Prefer aggregate datasets for Phase 4 `httbi` work; raw row exports require a
   new classification review and Tyler/platform approval.
