# Drift Reconciliation

This note records the safe docs-only reconciliation state for bd
`azure-governance-platform-xzt4.5`. It covers Bicep/live-name drift only; it is
not approval to deploy, rename, re-SKU, or otherwise mutate Azure resources.

## References

- GitHub issue: [HTT-BRANDS/control-tower#11](https://github.com/HTT-BRANDS/control-tower/issues/11)
- GitHub Actions run: [25227246032](https://github.com/HTT-BRANDS/control-tower/actions/runs/25227246032)
- bd parent: `azure-governance-platform-xzt4`
- bd child: `azure-governance-platform-xzt4.5`
- Commit context:
  - `b55ee2b` / `c017007` — optional Bicep name override support
  - `cea4f29` — staging live-name pins
  - `c578c3e` — production live-name pins
  - `6b1d8c7` — closed completed xzt4.3/xzt4.4 child work

## Non-negotiable no-deploy guardrail

Do **not** run subscription/resource-group deployments from this task. In
particular, do **not** run:

```bash
az deployment sub create
```

This task intentionally makes no changes to Bicep or parameter files. Any later
actual deployment must be a separate Tyler-approved task with an explicit plan,
approval gate, and rollback notes. Sneaking infra mutation into a docs cleanup is
how we get haunted dashboards. Bad idea. Very bad.

## Why live-name pins exist

The Bicep defaults still generate conventional names for new environments. The
live staging and production environments already have historical names, random
suffixes, and operational dependencies. Optional name override parameters let the
IaC source of truth point at those live resources without forcing destructive
renames or creating parallel infrastructure.

Default behavior remains unchanged when overrides are blank. Environment params
pin only known live names where needed.

## Live name map

### Staging

| Resource | Live name | Reconciliation decision |
|---|---:|---|
| Resource group | `rg-governance-staging` | Pin existing live name. |
| App Service plan | `asp-governance-staging-xnczpwyvwsaba` | Pin existing live name. |
| Web app | `app-governance-staging-xnczpwyv` | Pin existing live name. |
| Application Insights | `ai-governance-staging-xnczpwyvwsaba` | Pin existing live name. |
| Log Analytics | `log-governance-staging-xnczpwyvwsaba` | Pin existing live name. |
| Key Vault | `kv-gov-staging-xnczpwyv` | Pin existing live name. |
| Storage account | `stgovstagingxnczpwyv` | Pin existing live name. |
| SQL server | `sql-governance-staging-77zfjyem` | Live resource exists, but remains unmanaged by this Bicep path while `enableAzureSql=false`. |
| SQL database | `governance` | Live resource exists, but remains unmanaged by this Bicep path while `enableAzureSql=false`. |

Staging SQL exists in Azure, but the current guardrail is explicit: because
`enableAzureSql=false`, staging SQL is **unmanaged / not managed** by this
reconciliation until Tyler approves a later task to bring it under IaC
management. Do not flip that flag as part of drift cleanup.

### Production

| Resource | Live name | Reconciliation decision |
|---|---:|---|
| Resource group | `rg-governance-production` | Pin existing live name. |
| App Service plan | `asp-governance-production` | Pin existing live name. |
| Web app | `app-governance-prod` | Pin existing live name. |
| Application Insights | `governance-appinsights` | Pin existing live name. |
| Log Analytics | `governance-logs` | Pin existing live name. |
| Key Vault | `kv-gov-prod` | Pin existing live name. |
| Storage account | `stgovprodbkup001` | Pin existing live backup storage name. |
| SQL server | `sql-gov-prod-mylxq53d` | Pin existing live name. |
| SQL database | `governance` | Pin existing live name. |

Production has a deliberate database governance override: live production SQL is
Basic per current cost-governance records, while `parameters.production.json`
still carries `sqlDatabaseSku=Standard_S0`. Treat the live Basic database state
as the protected operational baseline unless Tyler explicitly approves a future
SKU reconciliation. This docs task must not alter production DB SKU, flags,
image, auth settings, region, CORS, or any other behavior.

## Remaining drift classification template

Use this table for follow-up decisions. Keep each row boring and auditable.

| Date | Environment | Resource | Observed live state | IaC state | Classification | Decision | Owner | Evidence |
|---|---|---|---|---|---|---|---|---|
| YYYY-MM-DD | staging/prod | resource name | what Azure shows | what Bicep/params say | name drift / SKU drift / unmanaged live resource / expected override / unknown | accept / pin / defer / remove / Tyler approval required | name | link/run/commit |

Classification guidance:

- **Expected override:** params intentionally pin a live name.
- **Unmanaged live resource:** resource exists but IaC intentionally does not
  manage it yet, such as staging SQL while `enableAzureSql=false`.
- **Governance override:** live state intentionally differs for cost, safety, or
  compliance reasons, such as the production DB SKU baseline.
- **Decision required:** behavior-changing drift that needs Tyler approval before
  any file or Azure mutation.

## Validation checklist for this doc-only task

- Confirm only `infrastructure/DRIFT_RECONCILIATION.md` changed.
- Confirm no Bicep or params changed.
- Confirm the document stays under 600 lines.
- Run a basic Markdown sanity check.
- Commit the doc change only; do not push from this task.

## 2026-05-01 source-of-truth reconciliation phase (Tyler: Bicep owns ideal drift)

Tyler decision for this phase: **"if bicep is ideal, then yes for all of it."**
Interpretation used here: keep/model remaining infrastructure drift in Bicep where it is practical and safer than treating live manual state as permanent. This phase remains **source-only**: no Azure deployment/resource mutation was run; validation used read-only `az ... list/show` and subscription-scope what-if only.

### Source changes made

- Added `storageSku` to `infrastructure/main.bicep` and passed it into `modules/storage.bicep`; dev/staging/production now pin live `Standard_LRS` while the module default remains `Standard_GRS` for new environments.
- Added SQL live-state parameters:
  - `sqlPublicNetworkAccessOverride`
  - `sqlDatabaseMaxSizeBytesOverride`
  - `sqlBackupRedundancyOverride`
  - `sqlAllowAzureServicesFirewallRuleName`
  - `sqlSetAdminPassword`
- Staging now models the existing SQL server/database under Bicep source:
  - `enableAzureSql=true`
  - `sqlServerNameOverride=sql-governance-staging-77zfjyem`
  - `sqlDatabaseNameOverride=governance`
  - `sqlDatabaseSku=Free`
  - live public SQL access, max size, backup redundancy, and firewall-rule name are pinned.
  - `sqlSetAdminPassword=false` prevents a generated `newGuid()` password from rotating the existing server admin during any future reviewed deployment.
- Production SQL source now matches live low-cost posture where this reduces dangerous drift:
  - `sqlDatabaseSku=Basic` instead of `Standard_S0`
  - `sqlPublicNetworkAccessOverride=Enabled` to match live firewall-dependent production access.
  - `sqlSetAdminPassword=false` preserves the existing production SQL admin password unless an explicit future rotation is approved.

### Read-only live inspection findings

No secret values were queried or printed. `storage-access-key` was checked only as secret metadata and returned no visible secret metadata in the inspected output.

| Area | Dev | Staging | Production | Classification |
|---|---|---|---|---|
| Storage root SKU | live `Standard_LRS` | live `Standard_LRS` | live `Standard_LRS` | Source now matches live via `storageSku`; default remains `Standard_GRS` for new envs. |
| Storage child resources | what-if still shows blob service/container and prod file-share creates | same | prod `backups`, `appdata`, `applogs` are creates | Bicep-owned pending deploy where child resources are absent or under-modeled live; no over-edit beyond SKU. |
| Key Vault `storage-access-key` | what-if Create | what-if Create | what-if Create | Bicep-owned pending deploy; secret values remain non-output/non-logged. |
| App Service diagnostics | no live diagnostic setting listed | no live diagnostic setting listed | no live diagnostic setting listed | Bicep-owned pending deploy. Watch ingestion cost; no extra categories beyond existing module. |
| Role assignments | existing RG-scope CI roles are manual | existing RG-scope Contributor roles are manual | existing RG-scope Contributor roles are manual | Bicep owns only deterministic storage-scoped app MI roles; no scope broadening. |
| Staging SQL | n/a for dev source in this phase | live server `sql-governance-staging-77zfjyem`, DB `governance`, SKU `Free`, public access `Enabled`, firewall `AllowAllAzureIps` plus temporary local-debug rules | n/a | Source now models live SQL; admin password rotation is disabled in params. Temporary/local firewall rules remain manual/waived, not broadened in Bicep. |
| Production SQL | n/a | n/a | live server `sql-gov-prod-mylxq53d`, DB `governance`, SKU `Basic`, public access `Enabled`, many AppService IP firewall rules plus temporary rules | Source now matches live SKU/public access; admin password rotation is disabled in params. Per-IP firewall rules remain manual/future issue, not broadened. |

### What-if counts

All what-if runs used:

```bash
az deployment sub what-if --validation-level Template --result-format FullResourcePayloads --no-pretty-print
```

No `az deployment sub create` was run.

| Environment | Before this phase | After this phase | Notes |
|---|---:|---:|---|
| dev | 15/22 drift (create 3, modify 10, unsupported 2) | 15/22 drift (create 3, modify 10, unsupported 2) | Root storage SKU now matches live, but total drift count unchanged because remaining storage/security/tag/diagnostic/app noise is on same resources. |
| staging | 15/21 drift (create 3, modify 10, unsupported 2) | 17/23 drift (create 3, modify 12, unsupported 2) | Count increased because staging SQL is intentionally brought under Bicep source-of-truth; dangerous SKU/public-access/firewall-name mismatches were reduced to tag/highAvailabilityReplicaCount noise. |
| production | 19/34 drift (create 7, modify 10, unsupported 2) | 19/34 drift (create 7, modify 10, unsupported 2) | Dangerous SQL SKU upgrade and public-network-disable deltas are removed; remaining SQL deltas are tags only. |

### Remaining drift classification

| Environment | Resource class | Remaining classification | Decision |
|---|---|---|---|
| dev/staging/production | Resource-group/resource tags, App Insights, Log Analytics, Key Vault tags/settings | Bicep-owned pending deploy or future tag-normalization issue | Keep under xzt4 unless a later phase chooses live-tag matching. |
| dev/staging/production | Key Vault access policy `Unsupported` | What-if/ARM limitation/noise | Waive/classify; do not mutate from this phase. |
| dev/staging/production | App Service `azurestorageaccounts` config `Unsupported` | What-if/ARM limitation/noise; contains storage key path, not printed | Waive/classify; no appsetting/secret value inspection performed. |
| dev/staging/production | App Service diagnostics | Bicep-owned pending deploy | Accept as source-of-truth; review ingestion cost before actual deploy. |
| dev/staging/production | Storage child resources | Bicep-owned pending deploy | Accept as source-of-truth where missing; no deploy. |
| dev/staging/production | Storage-scoped MI role assignments | Bicep-owned pending deploy | Deterministic storage-scope role assignment creates only; no broader-scope role changes. |
| staging | SQL tags / Free-tier HA replica count | Bicep-owned pending deploy / ARM normalization noise | Keep modeled; do not deploy until reviewed. Existing-server admin password rotation is disabled with `sqlSetAdminPassword=false`; any future rotation needs explicit Tyler approval and a stable secure value. |
| staging | Local-debug SQL firewall rules | Manual/waived | Do not model broad or temporary rules in Bicep. |
| production | SQL tags | Bicep-owned pending deploy | SKU/public access now matched to live; no cost increase. Existing-server admin password rotation is disabled with `sqlSetAdminPassword=false`. |
| production | AppService IP and temporary SQL firewall rules | Manual/future issue | Do not broaden scopes/rules in Bicep; split later if desired. |

Acceptance status: duplicate root generated staging/production resources remain eliminated by name pins. Remaining drift is now classified as Bicep-owned pending deploy, match-live source change, waived/manual, or future issue.
