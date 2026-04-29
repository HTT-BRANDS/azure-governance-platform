# BI Bridge Domain Data Classification

> Required Phase 1 artifact per `PORTFOLIO_PLATFORM_PLAN_V2.md` §5 and the
> V2 red-team remediation for per-domain GDPR/CCPA framing.

## Classification Summary

| Category | Classification | Rationale |
|---|---|---|
| Primary data class | Derived confidential reporting data | Dashboards/exports combine data from multiple domains and can reveal portfolio posture. |
| Personal data | Yes / contextual | Exports may contain owners, reviewers, user IDs, admin emails, tags, tenant names, evidence links, or notes from source domains. |
| Sensitive personal data | Not expected | No protected-class/health/biometric/government-ID data should be exported. If present in source metadata, treat as incident data. |
| Security-sensitive data | Yes | Aggregated control gaps, sync failures, resource inventories, identity risks, and recovery evidence reveal weaknesses. |
| Tenant boundary | Strict | BI projections must enforce tenant scope before serialization, rendering, caching, or downstream delivery. |

## Data Elements

### CSV exports

Current locations:

- `app/api/routes/exports.py:29-258`
- `tests/test_api_completeness.py:73-91`
- `tests/e2e/api/test_exports_api_e2e.py:1-41`

Current export families:

- Costs: dates, tenant IDs/names, costs, currency.
- Resources: resource IDs/names/types, tenant IDs/names, subscription IDs/names,
  resource groups, locations, provisioning state, SKU, orphaned flag, estimated
  monthly cost, tags, last sync time.
- Compliance: tenant IDs/names, subscription IDs, compliance percentages,
  secure score, compliant/non-compliant/exempt counts, policy IDs/names,
  categories, state, recommendations.

Personal data scope:

- Tenant/brand names can identify organizations.
- Resource tags/names can identify owners, employees, vendors, projects, or
  customer contexts.
- Compliance recommendations can include free-form operational detail.

### Dashboards and summaries

Current locations:

- `app/api/routes/dashboard.py:50-135`
- `app/api/routes/dashboard.py:194-420`
- `app/templates/pages/dashboard.html`
- `app/templates/pages/sync_dashboard.html`
- `docs/openapi-examples/responses/dashboard_summary.json`

Data includes cost summaries, compliance summaries, resource inventory snippets,
identity summaries, last sync timestamps, sync status, recent logs, active
alerts, alert stats, tenant sync status, and metrics.

Personal data scope:

- Summary values are usually aggregate, but tenant names, alert messages, sync
  errors, and identity summaries may expose identifiers or operational detail.

### Riverside analytics and consumer-specific dashboards

Current locations:

- `app/api/services/riverside_analytics.py:1-570`
- `app/schemas/riverside/dashboard.py:1-178`
- `app/templates/pages/riverside_dashboard.html`
- `app/templates/pages/dmarc_dashboard.html`

Data includes requirement progress, owners, status, due dates, evidence state,
blockers, deadlines, maturity/compliance metrics, MFA/security posture, tenant
summaries, and threat/risk indicators.

Personal data scope:

- Requirement owners, evidence URLs, blockers, tenant summaries, and security
  posture can identify people and business obligations.
- Riverside is one consumer; these data structures must not become the generic
  portfolio schema by accident. Accidental platform strategy is just tech debt
  wearing a tie.

### Preflight and recovery reports

Current locations:

- `app/preflight/reports.py:1-401`
- `scripts/verify_sync_recovery_report.py:1-372`
- `scripts/verify-tenants-report.md`

Data includes check IDs, categories, status, duration, messages, errors,
recommendations, tenant IDs, recent sync failure signatures, alert summaries,
App Insights/DB query-derived status, and recovery verdicts.

Personal data scope:

- Reports may contain tenant IDs, operator notes, evidence references, and error
  details with contextual identifiers.
- Error messages and signatures can reveal sensitive integration paths.

### Future httbi/DART datasets

Not implemented yet. Any future dataset must classify:

- Field-level personal data.
- Owner domain.
- Consumer(s).
- Tenant scope.
- Refresh cadence.
- Retention.
- Export format and transport.
- Redaction/aggregation rules.

## Sources

| Source | Direction | Notes |
|---|---|---|
| Cost domain read models | Inbound | Cost summaries/trends/tenant costs; Cost remains authoritative. |
| Resources domain read models | Inbound | Inventory/tag/orphaned/resource aggregate projections; Resources remains authoritative. |
| Compliance domain read models | Inbound | Scores, policy posture, requirement/evidence projections; Compliance remains authoritative. |
| Identity domain read models | Inbound | Identity/MFA/admin-risk aggregates; Identity remains authoritative. |
| Lifecycle domain read models | Inbound | Tenant/brand/subscription status; Lifecycle remains authoritative. |
| Monitoring/sync logs | Inbound | Sync status, alerts, recovery evidence. |
| Preflight checks | Inbound | Readiness reports and recommendations. |
| Future sister repos | Outbound consumers | `httbi` first, `DART` later per V2 sequencing. |

## Sinks and Recipients

| Sink | Data shared | Controls |
|---|---|---|
| Authenticated platform UI | Dashboards, summaries, sync/alert views | TenantAuthorization and role-aware template data. |
| CSV download | Flattened export rows | Tenant filtering before CSV generation; attachment response. |
| CLI/stdout/Markdown | Recovery and preflight reports | Operator-scoped; scrub before sharing broadly. |
| Email/Teams/alerts | Links or summarized metrics | Avoid raw exports and sensitive row-level details. |
| Future `httbi` | Approved versioned portfolio datasets | Dataset contract and classification required. |
| Future `DART` | Approved federated datasets after httbi is proven | Dataset contract and classification required. |
| Artifact storage | Evidence reports/exports if retained | Retention and access policy required before durable storage. |

## Retention Policy

| Data type | Default retention | Reason |
|---|---:|---|
| On-demand CSV downloads | Not retained server-side by default | Minimize copied cross-domain data. |
| Generated export jobs if later persisted | 30 days unless tied to audit/incident | Short-lived operational sharing. |
| Dashboard cache/projections | Hours to 7 days depending on freshness need | Derived data; source domains retain truth. |
| Preflight reports | 90 days operational; 1 year if attached to onboarding/change record | Troubleshooting and readiness evidence. |
| Recovery evidence reports | 1 year; longer if tied to DR/audit evidence | Incident/recovery audit trail. |
| Riverside consumer analytics | Per Compliance/evidence retention when tied to requirements; otherwise 1 year aggregate | Avoid over-retaining consumer-specific detail. |
| Future BI datasets | Defined per dataset contract | Must not be ad hoc. |

Legal hold, audit, incident response, or contractual requirements override these
defaults. Document owner, purpose, and expiry.

## Breach Notification Scope

A BI Bridge incident is in breach-notification scope when any of the following
are exposed to an unauthorized party:

1. Cross-tenant dashboard data, CSV exports, or downstream BI datasets.
2. Tenant-specific cost/resource/compliance/identity/lifecycle rows or metrics.
3. Personal identifiers embedded in owners, reviewers, admin emails, tags,
   resource names, evidence links, or notes.
4. Security-sensitive posture data such as compliance gaps, identity risks,
   sync failures, alert signatures, recovery reports, or resource inventory.
5. Raw source-domain data delivered to an unapproved consumer or retained beyond
   an approved dataset contract.

Potential notification audiences:

- HTT internal security/IT owner.
- Affected brand/business owner.
- Legal/privacy owner for GDPR/CCPA assessment when personal identifiers are
  involved.
- Affected individuals if identifiable owner/admin/user data is exposed and
  notice is required.
- Evidence consumers only when contractual obligations require it.

## Minimization Rules

1. Prefer aggregate metrics over raw rows for dashboards and sister-repo feeds.
2. Filter by tenant authorization before data enters CSV writers, templates,
   cache entries, or outbound adapters.
3. Define export schemas explicitly before external consumers rely on them.
4. Avoid free-form notes in exports unless the report purpose requires them.
5. Redact provider errors, signatures, tokens, secret names, and internal paths
   from broad reports.
6. Do not persist on-demand exports unless a retention policy and storage control
   are explicitly defined.
7. Keep consumer-specific analytics (`Riverside`, future `DART`) behind adapters;
   do not let one consumer's vocabulary leak into the platform core.
8. Every future httbi/DART dataset needs a version, owner, classification, and
   allowed-consumer list. Otherwise it is just a data swamp with better branding.

## Access Controls

| Actor | Access |
|---|---|
| Portfolio admin/platform engineer | Full authorized dashboards/exports and operational recovery reports. |
| Tenant/brand operator | Own-tenant dashboards/exports only, where route/role permits. |
| Security/compliance owner | Reports and evidence projections needed for audit/incident work. |
| Service principal / scheduler | Generate approved reports/exports only under explicit job identity. |
| Future BI consumer (`httbi`, `DART`) | Approved versioned datasets only; no direct operational DB access. |

## Domain-Specific Risks

| Risk | Mitigation |
|---|---|
| Cross-tenant CSV leak | Enforce tenant filtering before row construction and serialization. |
| Dashboard cache leak | Cache by tenant/role/query scope; invalidate on sync/authorization changes. |
| Export schema drift breaks consumers | Version datasets and publish compatibility rules before sister-repo integration. |
| Consumer-specific coupling | Keep Riverside/httbi/DART behind adapters and dataset contracts. |
| Raw evidence overexposure | Redact/summarize sensitive fields; store evidence reports with explicit retention. |
| BI becomes shadow source of truth | Treat BI projections as derived; source domains remain authoritative. |

## Open Questions

- 🔴 Tyler/platform: Confirm whether on-demand CSV exports should remain
  non-persistent or move to short-lived artifact storage for audit traceability.
- 🔴 Tyler/security: Decide whether tenant operators may download raw resource
  inventory CSVs or only aggregate dashboards.
- 🔴 Tyler/BI: Define first `httbi` dataset contract before Phase 4 starts.
