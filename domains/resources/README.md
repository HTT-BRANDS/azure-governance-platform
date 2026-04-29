# Resources Domain

> Phase 1 paper boundary per `PORTFOLIO_PLATFORM_PLAN_V2.md` §5. No code
> has moved here yet. This document defines the target bounded context for
> Phase 1.5 refactors and Phase 2 DDD relocation.

## Purpose

The Resources domain owns cloud resource inventory, tagging posture, quota
visibility, resource-change history, provisioning standards, optimization
recommendations, and idle/orphaned-resource review. It provides the portfolio's
"what exists, where, and why should we care?" view.

This domain answers:

- Which resources exist in each tenant/subscription/resource group?
- Which resources are orphaned, idle, untagged, or drifting from standards?
- Which resource changes happened over time?
- Which quota limits are close to exhaustion?
- Which resource recommendations need action or dismissal?
- Do proposed resource names, regions, SKUs, and tags meet HTT standards?

## Entities and Value Objects

| Entity / value object | Current model/schema | Notes |
|---|---|---|
| Resource | `app/models/resource.py:11-32` | Azure resource inventory item keyed by Azure resource ID. |
| Resource tag | `app/models/resource.py:35-47` | Tag compliance tracking for resources. |
| Idle resource | `app/models/resource.py:51-71` | Detected idle/orphaned optimization candidate and review state. |
| Resource lifecycle event | `app/models/resource_lifecycle.py:12-54` | Resource create/update/delete/reappeared change facts. |
| Recommendation | `app/models/recommendation.py:11-46` | Optimization/governance recommendation tied to tenant/resource. |
| Resource inventory DTOs | `app/schemas/resource.py:8-260` | Inventory, tagging, idle/orphaned, filtering, and bulk-operation DTOs. |
| Recommendation DTOs | `app/schemas/recommendation.py:9-112` | Recommendation categorization, summaries, savings, dismissal DTOs. |
| Quota DTOs | `app/api/services/quota_service.py:41-126` | Quota item and summary value objects. |
| Provisioning standards DTOs | `app/api/services/provisioning_standards_service.py:25-72` | Validation results and standards summaries. |

## Invariants

1. **Every resource fact is tenant-scoped.** Resource inventory without tenant
   and subscription context is not a valid portfolio fact.
2. **Resource identity is provider identity.** Azure resource IDs are canonical;
   display names are not stable identifiers.
3. **Tags are data.** Tags can contain owners, cost centers, projects, vendors,
   or accidental PII. Treat them as confidential metadata.
4. **Recommendations are advisory until explicitly acted on.** Dismiss/review
   actions are auditable; recommendations must not mutate resources by default.
5. **Provisioning standards are validation rules, not deployment engines.** This
   domain validates naming/region/tags/SKUs; lifecycle owns acquisition/playbook
   orchestration.
6. **Cost values are imported signals, not Cost-domain truth.** Estimated cost or
   savings may appear on resource DTOs, but source-of-truth spend lives in Cost.
7. **Compliance consumes resource evidence through interfaces.** Resources owns
   inventory/tag/change facts; Compliance owns control interpretation.
8. **No lateral domain imports.** Cross-domain access goes through published
   read models/adapters, because spaghetti is food, not architecture.

## Current Code Locations

These files currently belong wholly or partly to the Resources bounded context.
Line ranges are current as of 2026-04-29 and are the source map for later
refactors.

### HTTP routes

| Path | Lines | Domain responsibility |
|---|---:|---|
| `app/api/routes/resources.py` | 1-396 | Resource inventory, orphaned/idle resources, idle summary, review/tagging, tagging compliance, resource changes, resource history. |
| `app/api/routes/quotas.py` | 1-76 | Quota utilization and quota summary routes. |
| `app/api/routes/recommendations.py` | 1-157 | Recommendation listing, category/tenant views, savings potential, summaries, dismissal. |
| `app/api/routes/provisioning_standards.py` | 1-99 | Provisioning standards, resource validation, naming validation, region validation. |
| `app/api/routes/sync.py` | 1-320 | Shared sync API; Resources owns `resources` sync command semantics. |

### Services, sync, and adapters

| Path | Lines | Domain responsibility |
|---|---:|---|
| `app/api/services/resource_service.py` | 1-383 | Inventory summaries, orphaned resource queries, tagging compliance, idle resource review, cache invalidation. |
| `app/api/services/resource_lifecycle_service.py` | 1-160 | Resource lifecycle event recording, change detection, event history, tenant changes. |
| `app/api/services/quota_service.py` | 1-235 | Compute/network quota collection and aggregation. |
| `app/api/services/recommendation_service.py` | 1-254 | Recommendation filtering, grouping, savings potential, summaries, dismissal. |
| `app/api/services/provisioning_standards_service.py` | 1-417 | Naming, region, tag, SKU, and full-resource standards validation. |
| `app/core/sync/resources.py` | 1-286 | Scheduled/manual Azure resource inventory sync. |
| `app/services/backfill_service.py` | 468-566 | Resource-specific historical data processor. Generic backfill engine remains shared/application orchestration. |
| `app/services/lighthouse_client.py` | 227-367 | Delegated Azure resource listing and resource normalization portions. Other methods belong to Cost/Compliance/Identity adapters. |
| `app/preflight/azure/compute.py` | 1-185 | Resource Manager access preflight and compute/resource access checks. |
| `app/preflight/azure/network.py` | 29-173 | Subscription/network access checks relevant to resource inventory; Graph checks belong to Identity. |
| `app/preflight/azure/storage.py` | 72-119 and 237-344 | Azure Policy access checks relevant to resource/compliance evidence; Cost Management checks belong to Cost. |

### Models and schemas

| Path | Lines | Domain responsibility |
|---|---:|---|
| `app/models/resource.py` | 1-71 | Resource, tag, and idle-resource persistence. |
| `app/models/resource_lifecycle.py` | 1-54 | Resource lifecycle event persistence. |
| `app/models/recommendation.py` | 1-46 | Recommendation persistence. |
| `app/schemas/resource.py` | 1-260 | Resource inventory, tagging, idle/orphaned, filter, and bulk-operation DTOs. |
| `app/schemas/recommendation.py` | 1-112 | Recommendation category/impact/effort, summaries, filters, and dismissal DTOs. |

### Shared dependencies the domain consumes but does not own

| Path | Lines | Boundary note |
|---|---:|---|
| `app/core/authorization.py` | 1-384 | Tenant authorization guard. Resources routes consume it; authz remains shared core. |
| `app/models/tenant.py` | 1-114 | Shared tenant read model. Resources reads tenant names/IDs/subscriptions through an interface. |
| `app/api/services/azure_client.py` | 1-606 | Shared Azure credential/client adapter. Resources should depend on resource-management adapter interfaces. |
| `app/api/services/monitoring_service.py` | 1-871 | Shared sync logs/alerts. Resources emits sync and review status through monitoring. |
| `app/models/monitoring.py` | 15-134 | Shared sync/alert persistence. Resources contributes job types/messages but does not own monitoring. |
| `app/core/cache.py` | 1-1181 | Shared cache decorators/invalidation. Resources uses cache policy; it does not own cache implementation. |

## Inbound Interface Contracts

### HTTP API

Owned route prefixes:

- `/api/v1/resources`
- `/api/v1/quotas`
- `/api/v1/recommendations`
- `/api/v1/provisioning-standards`

Current commands/queries:

- Resource inventory with tenant/resource-type/date pagination filters.
- Orphaned and idle resource views.
- Idle-resource summary and review/tagging commands.
- Tagging compliance and resource change/history queries.
- Quota utilization and summary queries.
- Recommendation list/category/tenant/savings/summary queries and dismissal
  command.
- Provisioning standards queries and validation commands for resource names,
  regions, SKUs, and tags.

### Sync and backfill commands

The scheduler or sync API may request:

- `sync_resources()` to ingest Azure resource inventory.
- Resource historical backfill through the generic backfill engine with job type
  `resources`.
- Resource lifecycle event recording after sync detects creates/updates/deletes.

### Domain events/read models

Resources may publish:

- Tenant resource inventory summary.
- Tagging compliance summary.
- Idle/orphaned resource candidates.
- Resource lifecycle events.
- Quota utilization summary.
- Resource recommendation summary.
- Provisioning-standard validation result.

Cost, Compliance, Identity, Lifecycle, and BI consume these read models through
interfaces only.

## Outbound Interface Contracts

| Interface | Current concrete implementation | Contract |
|---|---|---|
| Azure Resource Manager / Resource Graph | `app/core/sync/resources.py`, `LighthouseAzureClient.list_resources()` | Read resource inventory and metadata by tenant/subscription; no mutation by default. |
| Azure quota APIs | `QuotaService` | Read compute/network quota usage and limits. |
| Azure Policy access preflight | `app/preflight/azure/storage.py` policy checks | Validate policy/resource access; policy interpretation belongs to Compliance. |
| Tenant read model | `Tenant` ORM via `Session` | Read tenant IDs, names, active state, subscriptions, and delegation metadata. No lifecycle mutation. |
| Authorization | `TenantAuthorization` | Filter tenant IDs and validate caller scope before resource data access or review/dismiss actions. |
| Monitoring | `MonitoringService`/`SyncJobLog` | Emit resource sync, backfill, review, and recommendation action status. |
| Cache | `cached`, cache manager | Cache read models by tenant/query scope and invalidate after sync/review actions. |
| Cost signal | Cost read model/interface | Read estimated cost/savings when available; do not own cost ledger. |
| Compliance signal | Compliance interface | Provide resource/tag/policy evidence; do not own control scoring. |

## Explicit Non-Goals

- Resources does not own cost ledger, chargeback, budgets, or financial truth.
- Resources does not own compliance scoring or evidence interpretation.
- Resources does not own identity, MFA, Graph user data, or tenant credential
  resolution.
- Resources does not own acquisition/onboarding playbooks; Lifecycle owns those.
- Resources does not mutate cloud resources by default. Future remediation must
  be explicit, audited, and dry-run capable.

## Phase 1.5 Refactor Guidance

1. Keep route modules thin: authz, validation, service invocation, response.
2. Separate resource inventory normalization from Azure API calls.
3. Keep lifecycle-event detection in Resources, but keep business onboarding
   playbooks in Lifecycle.
4. Split preflight resource checks from identity/cost/compliance checks when
   preflight files are refactored.
5. Treat Lighthouse resource listing as an adapter method; do not let delegated
   access plumbing leak into domain rules.
6. Do not introduce lateral imports from future `domains/cost`,
   `domains/identity`, `domains/compliance`, `domains/lifecycle`, or
   `domains/bi_bridge`.
