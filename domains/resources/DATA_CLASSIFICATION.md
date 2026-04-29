# Resources Domain Data Classification

> Required Phase 1 artifact per `PORTFOLIO_PLATFORM_PLAN_V2.md` §5 and the
> V2 red-team remediation for per-domain GDPR/CCPA framing.

## Classification Summary

| Category | Classification | Rationale |
|---|---|---|
| Primary data class | Confidential infrastructure inventory data | Resource IDs, names, topology, tags, quotas, and recommendations reveal platform structure and attack/optimization paths. |
| Personal data | Possible / contextual | Resource names, tags, owners, review actors, notes, and project labels can identify people or teams. |
| Sensitive personal data | Not expected | No health, biometric, government ID, or protected-class data should be stored. If found in tags/names/notes, treat as incident data. |
| Security-sensitive data | Yes | Inventory, quota limits, provisioning drift, idle/orphaned resources, and recommendations can expose weak points. |
| Tenant boundary | Strict | Resource facts must be scoped to authorized tenants/subscriptions unless intentionally aggregated for portfolio admins. |

## Data Elements

### Resource inventory

Current locations:

- `app/models/resource.py:11-32`
- `app/schemas/resource.py:8-63`
- `app/api/services/resource_service.py:38-138`
- `app/core/sync/resources.py:1-286`

Fields include Azure resource ID, tenant ID/name, subscription ID/name, resource
group, resource type, resource name, location, provisioning state, SKU, kind,
tags, orphaned state, estimated monthly cost, and sync timestamp.

Personal data scope:

- Resource names, resource groups, tags, and subscription names may contain
  employee names, email handles, vendor names, customer references, ticket IDs,
  or project names.
- Azure resource IDs expose topology and should be treated as confidential even
  when not personal data.

### Tags and tagging compliance

Current locations:

- `app/models/resource.py:35-47`
- `app/schemas/resource.py:64-84`
- `app/api/services/resource_service.py:190-251`
- `app/api/services/provisioning_standards_service.py:192-264`

Fields include tag names/values, required-tag state, missing tag lists, and
compliance percentages.

Personal data scope:

- `owner`, `createdBy`, `requestor`, `department`, `project`, or free-form tags
  can identify individuals or teams.
- Tags can also reveal confidential acquisitions, vendors, campaigns, or
  incident names. People put nonsense in tags; our job is to classify the
  nonsense, not pretend it is clean.

### Idle/orphaned resources and review actions

Current locations:

- `app/models/resource.py:51-71`
- `app/schemas/resource.py:85-126` and `240-260`
- `app/api/services/resource_service.py:139-381`
- `app/api/routes/resources.py:162-293`

Fields include idle/orphaned reason, detected timestamp, idle days, estimated
monthly savings, reviewed state, reviewer, review timestamp, and review notes.

Personal data scope:

- `reviewed_by` and review notes can identify operators.
- Notes may include owner names, operational context, or remediation rationale.

### Recommendations

Current locations:

- `app/models/recommendation.py:11-46`
- `app/schemas/recommendation.py:9-112`
- `app/api/services/recommendation_service.py:1-254`
- `app/api/routes/recommendations.py:1-157`

Fields include tenant/subscription IDs, category, type, title, description,
impact, potential savings, resource ID/name/type, current/recommended state,
implementation effort, dismissed state, dismissed actor, timestamp, and reason.

Personal data scope:

- Resource names, current/recommended state JSON, dismissal actor, and dismissal
  reason may identify people or reveal sensitive infrastructure state.

### Resource lifecycle events

Current locations:

- `app/models/resource_lifecycle.py:1-54`
- `app/api/services/resource_lifecycle_service.py:1-160`
- `app/api/routes/resources.py:322-396`

Fields include resource ID/name/type, tenant/subscription ID, event type,
detection timestamp, previous/current state JSON, changed fields, and sync run
ID.

Personal data scope:

- Previous/current state may include tags, owners, or names that identify people
  or projects.
- Change history can reveal deployment timing and operational behavior.

### Quotas and provisioning standards

Current locations:

- `app/api/services/quota_service.py:1-235`
- `app/api/routes/quotas.py:1-76`
- `app/api/services/provisioning_standards_service.py:1-417`
- `app/api/routes/provisioning_standards.py:1-99`

Fields include quota names/limits/current usage, locations, validation results,
violations, warnings, required tags, allowed regions, SKU rules, and naming
patterns.

Personal data scope:

- Usually not direct PII.
- Validation inputs can include resource names/tags with personal or project
  data.
- Quota limits and failures are security/operations-sensitive.

## Sources

| Source | Direction | Notes |
|---|---|---|
| Azure Resource Manager / Resource Graph | Inbound | Resource inventory, metadata, tags, state. |
| Azure quota APIs | Inbound | Compute/network quota limits and usage. |
| Azure Policy / preflight checks | Inbound | Access validation and policy/resource signals; control scoring belongs to Compliance. |
| Lighthouse/delegated access | Inbound | Resource listing through delegated subscriptions. Delegation truth belongs to Identity/shared adapters. |
| Local operators | Inbound | Review notes, recommendation dismissals, provisioning validation input. |
| Cost read model | Inbound | Estimated cost/savings signals; spend truth remains Cost. |

## Sinks and Recipients

| Sink | Data shared | Controls |
|---|---|---|
| Authenticated platform UI/API | Inventory, tags, idle/orphaned resources, quotas, recommendations, standards validation | TenantAuthorization and role checks. |
| Monitoring/alerts | Sync status, review/dismissal results, recommendation summaries | Avoid secrets and minimize raw resource state in broad alerts. |
| Cache | Tenant-scoped inventory/recommendation DTOs | Cache keys must include tenant/auth/query scope and invalidate after sync/review/dismissal. |
| Cost domain | Approved resource dimensions and estimated-savings context | Interface/read model only; Cost owns financial ledger. |
| Compliance domain | Resource/tag/policy evidence | Interface/read model only; Compliance owns control interpretation. |
| Lifecycle domain | Provisioning validation and resource-change evidence | Interface/read model only; Lifecycle owns playbooks. |
| Future BI bridge | Approved aggregate inventory metrics | No raw unfiltered resource dump without separate data contract. |

## Retention Policy

| Data type | Default retention | Reason |
|---|---:|---|
| Current resource inventory | Keep latest plus 90 days of sync snapshots if implemented | Operational truth; old detailed inventory loses value quickly. |
| Resource lifecycle events | 2 years | Change history supports incident response and audit. |
| Tag compliance facts | 1 year detailed; 2 years aggregate | Operational trend value without retaining stale metadata forever. |
| Idle/orphaned resource findings | 1 year after review/resolution | Optimization audit trail and recurrence analysis. |
| Recommendations and dismissals | 2 years | Governance/optimization evidence and dismissal audit. |
| Quota snapshots | 1 year | Capacity trend analysis; older data can be aggregated. |
| Provisioning validation requests/results | 90 days unless attached to change ticket | Avoid retaining free-form resource names/tags unnecessarily. |
| Cache entries | Hours, not days | Cache is not the inventory archive. |

If legal hold, security incident response, or audit requirements apply, the hold
overrides these defaults. Document owner, purpose, and expiry.

## Breach Notification Scope

A Resources-domain incident is in breach-notification scope when any of the
following are exposed to an unauthorized party:

1. Tenant-specific resource inventory, topology, resource IDs, names, locations,
   SKUs, or tags.
2. Tags, names, review notes, or dismissal reasons containing personal data.
3. Idle/orphaned resources, recommendations, quota limits, or provisioning drift
   that expose operational/security weaknesses.
4. Resource lifecycle history showing deployment/deletion timing or previous
   sensitive state.
5. Any credential, token, secret, connection string, provider response header, or
   raw authorization material accidentally logged or persisted.

Potential notification audiences:

- HTT internal security/IT owner.
- Affected brand leadership for brand-specific infrastructure exposure.
- Legal/privacy owner for GDPR/CCPA assessment when identifiers are involved.
- Affected individuals if tags/names/notes expose personal data and notice is
  legally required.
- Evidence consumers only if contractual reporting requires it.

## Minimization Rules

1. Persist normalized resource fields; do not persist full raw Azure payloads by
   default.
2. Treat tags and resource names as potentially sensitive. Redact or summarize in
   broad logs/alerts when exact values are not needed.
3. Never store provider tokens, credentials, or authorization headers in resource
   records, lifecycle events, recommendations, or review notes.
4. Keep review/dismissal notes factual and short; no secrets, HR commentary, or
   personal data unless required.
5. Cache by tenant, role, and query scope. A cached portfolio inventory must not
   leak to a tenant-only user. Yes, cache keys are security controls. Surprise.
6. Future remediation/mutation features must be explicit, audited, dry-run
   capable, and separately classified before launch.
7. Validate provisioning inputs without storing them longer than necessary.

## Access Controls

| Actor | Access |
|---|---|
| Portfolio admin/platform engineer | Read all tenant resource inventory, quotas, standards, recommendations; review/dismiss findings. |
| Tenant/brand operator | Read assigned-tenant inventory and recommendations; review/dismiss only assigned-tenant findings if role permits. |
| Security/compliance owner | Read resource/tag/change evidence needed for control review. |
| Service principal / scheduler | Read Azure inventory/quota APIs and write normalized resource facts. |
| Future BI bridge | Read approved aggregate resource metrics only unless a separate approved data contract exists. |

## Domain-Specific Risks

| Risk | Mitigation |
|---|---|
| Cross-tenant inventory leak | Enforce `TenantAuthorization` before every resource query and review/dismiss command. |
| Infrastructure topology disclosure | Restrict detailed inventory and lifecycle views to authorized operators/admins. |
| PII in tags/resource names | Treat metadata as contextual personal data; minimize export/log exposure. |
| Secret leakage in provider errors | Scrub errors and ban raw token/header persistence. |
| Recommendation dismissal hides real risk | Record actor, reason, timestamp, and tenant/resource scope. |
| Provisioning standards drift | Version standards and expose validation results; do not silently mutate proposed resources. |
| Domain coupling with Cost/Compliance/Lifecycle | Use interfaces/read models; no lateral imports during DDD relocation. |

## Open Questions

- 🔴 Tyler/platform: Confirm whether 2-year resource lifecycle retention is
  sufficient for HTT audit/incident-response expectations.
- 🔴 Tyler/security: Decide whether detailed resource inventory can be exported
  by tenant operators, or only viewed in-app.
- 🔴 Tyler: Confirm future remediation posture: read-only recommendations only,
  or allow audited/dry-run resource mutation commands in later phases.
