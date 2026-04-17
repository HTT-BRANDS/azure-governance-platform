# ADR 0001: Disposition of blue-green-deploy.yml

**Status:** Proposed — awaiting Tyler decision
**Date:** 2026-04-17
**Deciders:** Tyler Granlund (final), solutions-architect-6b4067 (recommendation)
**Related:** a1sb (incident — silent prod outage from dev-stage image), bd-6699 (CI a1sb guard), bd-yil1 (guard extension), bd-hofd (this ADR)

---

## Context

On April 17, 2026, we discovered that production had been running a **development-stage Docker image** for weeks (incident a1sb). The root cause was `docker/build-push-action` in `.github/workflows/blue-green-deploy.yml` missing the `target:` field, which caused Docker to default to the last Dockerfile stage (`development`). That dev image — lacking `libodbc.so.2` — was pushed to GHCR and picked up by production. Every database query crashed.

The `target:` bug is now fixed (commits `6a7306a` + `1c1bd54`), and a CI guard (bd-6699, commit `cc233f1`) asserts version/user/entrypoint/ODBC invariants on every build.

**However, the workflow still has a second, unfixed class of the same problem.** The `deploy-staging`, `validate`, `swap`, `rollback`, and `notify` jobs in `blue-green-deploy.yml` reference two GitHub repository variables — `${{ vars.AZURE_WEBAPP_NAME }}` and `${{ vars.RESOURCE_GROUP }}` — that have **never been set**. These jobs have been failing silently on every push to main since the workflow was created. There is zero alerting on the failure.

This is the same footgun pattern that caused a1sb: CI silently doing the wrong thing because default/missing config was not caught. This ADR decides what to do about it.

---

## Current State Audit

### Workflow Inventory

| Workflow | Trigger | Builds Image? | Tags Pushed to GHCR | Deploys To | Status |
|---|---|---|---|---|---|
| `ci.yml` | push to main, PRs | No | — | — | ✅ Working |
| `deploy-staging.yml` | push to main | Yes (`target: production`) | `:staging`, `:sha-<full-sha>` | `app-governance-staging-xnczpwyv` | ✅ Working |
| `deploy-production.yml` | manual dispatch only | Yes (`target: production`) | `:latest`, `:sha-<full-sha>` | `app-governance-prod` | ✅ Working |
| **`blue-green-deploy.yml`** | **push to main** | **Yes (`target: production`)** | **`:latest`, `:main`, `:<short-sha>`** | **Intended: slot swap** | **❌ Deploy jobs broken** |
| `container-registry-migration.yml` | manual dispatch | No (copies) | Mirrors ACR→GHCR | — | ✅ One-time tool |
| `security-scan.yml` | push, PRs, daily cron | No | — | — | ✅ Working |
| `backup.yml` | daily cron, manual | No | — | — | ✅ Working |
| `pages.yml` | push (docs changes) | No | — | GitHub Pages | ✅ Working |
| `accessibility.yml` | after staging deploy | No | — | — | ✅ Working |
| `dependency-update.yml` | weekly cron | No | — | — | ✅ Working |
| `project-sync.yml` | PR/issue events | No | — | — | ✅ Working |
| `topology-diagram.yml` | push, nightly cron | No | — | — | ✅ Working |
| `topology-export.yml` | weekly Monday | No | — | — | ✅ Working |
| `weekly-ops.yml` | weekly Monday | No | — | — | ✅ Working |
| `gh-pages-tests.yml` | docs changes, weekly | No | — | — | ✅ Working |

### Double-Build Problem

Every push to `main` triggers **two** full Docker image builds:

1. `deploy-staging.yml` → builds image → pushes `:staging` + `:sha-<sha>` → deploys to staging ✅
2. `blue-green-deploy.yml` → builds image → pushes `:latest` + `:main` + `:<short-sha>` → deploy jobs FAIL ❌

This wastes approximately 10–15 minutes of GitHub Actions CI time per push to main.

### Broken/Silent-Failing Jobs

| Job | Workflow | Broken Since | Root Cause | Impact |
|---|---|---|---|---|
| `deploy-staging` | blue-green-deploy.yml | Creation | `${{ vars.AZURE_WEBAPP_NAME }}` empty | `az webapp` commands fail — empty `--name` |
| `validate` | blue-green-deploy.yml | Creation | Depends on `deploy-staging` | Skipped or fails |
| `swap` | blue-green-deploy.yml | Creation | `${{ vars.RESOURCE_GROUP }}` empty | `az webapp deployment slot swap` fails |
| `rollback` | blue-green-deploy.yml | Creation | Same vars | Cannot rollback |
| `notify` | blue-green-deploy.yml | Creation | Upstream failures | Reports failures nobody reads |

### Repository Variables and Secrets

| Reference | Where Used | Set? | Behavior When Unset |
|---|---|---|---|
| `vars.AZURE_WEBAPP_NAME` | blue-green-deploy.yml | **❌ NOT SET** | Empty string → `az` CLI errors |
| `vars.RESOURCE_GROUP` | blue-green-deploy.yml | **❌ NOT SET** | Empty string → `az` CLI errors |
| `vars.TEAMS_WEBHOOK_CONFIGURED` | deploy-production.yml | ❌ Not set | Conditional check — gracefully skipped |
| `vars.PROJECT_URL` | project-sync.yml | Unknown | Conditional check — gracefully skipped |
| `secrets.AZURE_CLIENT_ID` | Multiple | ✅ Set | OIDC auth |
| `secrets.AZURE_TENANT_ID` | Multiple | ✅ Set | OIDC auth |
| `secrets.AZURE_SUBSCRIPTION_ID` | Multiple | ✅ Set | Subscription targeting |
| `secrets.GHCR_PAT` | deploy-staging, deploy-production | ✅ Set | App Service GHCR pull auth |
| `secrets.PRODUCTION_TEAMS_WEBHOOK` | deploy-production.yml | ✅ Set | Teams notification |

### Image Tag Dependency Graph

```
blue-green-deploy.yml (push to main)
  → ghcr.io/htt-brands/azure-governance-platform:latest      ← ALSO pushed by deploy-production.yml
  → ghcr.io/htt-brands/azure-governance-platform:main         ← consumed by: NOTHING
  → ghcr.io/htt-brands/azure-governance-platform:<short-sha>  ← consumed by: NOTHING (was used once during manual a1sb repoint)

deploy-staging.yml (push to main)
  → ghcr.io/htt-brands/azure-governance-platform:staging      ← consumed by: staging App Service
  → ghcr.io/htt-brands/azure-governance-platform:sha-<sha>    ← consumed by: NOTHING (staging uses :staging)

deploy-production.yml (manual dispatch)
  → ghcr.io/htt-brands/azure-governance-platform:latest       ← consumed by: Bicep parameters (initial deploy only)
  → ghcr.io/htt-brands/azure-governance-platform:sha-<sha>    ← consumed by: production App Service (set during deploy)
```

**Key finding:** No automated process consumes the `:latest`, `:main`, or `:<short-sha>` tags produced by `blue-green-deploy.yml`. The `deploy-staging.yml` and `deploy-production.yml` workflows each build and deploy their own images.

### Azure Infrastructure

| Resource | Name | Tier | Monthly Cost | Deployment Slots? |
|---|---|---|---|---|
| App Service Plan (prod) | `asp-governance-production` | **B1** | ~$12.41 | **❌ Not supported on Basic tier** |
| App Service (prod) | `app-governance-prod` | — | Included | N/A |
| App Service Plan (staging) | `asp-governance-staging` | **B1** | ~$12.41 | **❌ Not supported** |
| App Service (staging) | `app-governance-staging-xnczpwyv` | — | Included | N/A |

**No staging slot is provisioned.** No Bicep/Terraform defines a slot. The `blue-green-deploy.yml` deploy jobs attempted to create and use slots on a B1 plan — which Azure would reject even if the vars were set.

### Documentation Errors Found

| Document | Claim | Reality |
|---|---|---|
| `research/cost-optimization-2026/recommendations.md` | "deployment slots free on B1+" | **Wrong.** Slots require Standard S1+ tier. |
| `research/azure-hosting-alternatives/recommendations.md` | "deployment slots free on B1+" | **Wrong.** Same error. |
| `research/cost-optimization-2026/analysis.md` | "Use App Service deployment slots (free on B1+)" | **Wrong.** |
| `INFRASTRUCTURE_END_TO_END.md` | blue-green-deploy.yml trigger is "Manual" | **Wrong.** Actual trigger is `push: branches: [main]` + `workflow_dispatch`. |
| `deploy-staging.yml` (comment in code) | "Staging images get promoted to prod via blue-green swap" | **Wrong.** Production builds its own image via deploy-production.yml. |

---

## Options Considered

### Option A: Real Blue-Green Deployment

**Summary:** Set the missing `${{ vars.* }}`, provision an Azure App Service staging slot on production, wire slot swap with health validation. For deeper cost modeling see `docs/COST_MODEL_AND_SCALING.md` (bd-zj9k, forthcoming).

**Implementation sketch:**
1. Upgrade `asp-governance-production` from B1 to S1 (Standard) — B1 does not support deployment slots
2. Create staging slot via Bicep: `resource slot 'Microsoft.Web/sites/slots'`
3. Set repo variables: `vars.AZURE_WEBAPP_NAME = app-governance-prod`, `vars.RESOURCE_GROUP = rg-governance-production`
4. Grant SPN `Website Contributor` role on the slot
5. Configure slot-specific app settings (sticky settings for DB connection strings pointing to staging DB vs prod DB)
6. Add health check validation contract (`/health` must return 200 with `status: healthy`)
7. Consolidate: remove the build step from `blue-green-deploy.yml` — reuse image from `deploy-staging.yml` to avoid triple builds
8. Decide relationship with `deploy-staging.yml` and `deploy-production.yml` — do they become redundant?

**Cost delta:**
- App Service Plan upgrade B1 → S1: **+$56.94/mo** ($12.41 → $69.35, Linux East US pay-as-you-go)
- Slot itself: included with S1 plan (up to 5 slots)
- Estimated total prod infra increase: **~$57/mo** (5.6× current App Service cost)

**Effort:** 12–20 engineering hours + 1–2 weeks calendar time for Bicep changes, SPN permissions, testing, slot configuration, workflow rewrite, and documentation updates.

**Risks:**
- S1 tier cost increase is disproportionate for a 10–30 user internal tool
- Slot swap introduces operational complexity (sticky settings, connection string management)
- Three existing deploy workflows need rationalization — adding more complexity to an already-confused topology
- Health check contract for slot swap needs careful design for Python/uvicorn cold start (30–90 second warmup)

**When it's the right call:** When the platform has paying external users and downtime costs real money. Not today.

### Option B: Build-Only — Strip Deploy Jobs, Keep Build + Guard

**Summary:** Remove the `deploy-staging`, `validate`, `swap`, `rollback`, and `notify` jobs from `blue-green-deploy.yml`. Keep only the `build` job that pushes `:latest`, `:main`, `:<short-sha>` to GHCR with the a1sb guard.

**Implementation sketch:**
1. Delete jobs: `deploy-staging`, `validate`, `swap`, `rollback`, `notify`
2. Remove `vars.AZURE_WEBAPP_NAME` and `vars.RESOURCE_GROUP` references
3. Keep `build` job with `target: production` and a1sb guard
4. Rename workflow to "Build Container Image" or similar

**Cost delta:** $0

**Effort:** 1–2 engineering hours (YAML editing + testing).

**Risks:**
- Still runs a **redundant Docker build** on every push to main (deploy-staging.yml already builds)
- `:latest` tag race: both this workflow and deploy-production.yml push `:latest`, creating ambiguity about which image `:latest` points to at any given time
- `:main` and `:<short-sha>` tags serve no automated purpose — they're unused artifacts
- Leaves a workflow that exists only to build tags nobody uses

**When it's the right call:** If there's a downstream consumer of the `:main` tag that I didn't find, or if a convention requires `:latest` to update on every push (not just on manual prod deploys).

### Option C: Delete blue-green-deploy.yml Entirely

**Summary:** Remove the entire workflow file. Rely exclusively on `deploy-staging.yml` (push to main → staging) and `deploy-production.yml` (manual dispatch → production) for all image building and deployment.

**Implementation sketch:**
1. Delete `.github/workflows/blue-green-deploy.yml`
2. Verify no other workflow references it (confirmed: none do)
3. Verify no external system depends on the `:main` or `:<short-sha>` tags (confirmed: nothing automated)
4. Update documentation: `INFRASTRUCTURE_END_TO_END.md`, `AZURE_DEVOPS_DEPLOYMENT_GUIDE.md`, `SESSION_HANDOFF.md`
5. (Optional) If `:latest` must update on every push to main, add a `type=raw,value=latest` tag line to `deploy-staging.yml`'s build step

**Cost delta:** $0 (saves ~10–15 min CI per push to main)

**Effort:** 1–2 engineering hours (file deletion + doc updates).

**Risks:**
- **`:latest` tag becomes stale between manual prod deploys.** Currently `blue-green-deploy.yml` updates `:latest` on every push; after deletion, only `deploy-production.yml` (manual dispatch) updates it. Mitigation: Add `:latest` to `deploy-staging.yml`'s build tags if needed, or accept that `:latest` is only updated on prod deploys.
- **`:main` tag disappears.** No evidence anything uses it. If a developer is manually pulling `:main` for local testing, they'll need to use `:staging` instead.
- **Loss of short-SHA tags.** Production was manually repointed to a short-SHA tag during a1sb incident response. After deletion, manual incident response would need to use the `sha-<full-sha>` format from `deploy-production.yml` or `deploy-staging.yml`. This is a better convention anyway (unambiguous, matches workflow outputs).

**When it's the right call:** When the existing `deploy-staging.yml` and `deploy-production.yml` fully cover all deploy pathways — which they do.

---

## Decision Matrix

| Criterion | Weight | Option A: Real Blue-Green | Option B: Build-Only | Option C: Delete Entirely |
|---|---|---|---|---|
| Cost | 20% | ❌ +$57/mo (5.6× plan increase) | ✅ $0 | ✅ $0 (saves CI minutes) |
| Operational simplicity | 20% | ❌ Adds slot management, sticky settings | ⚠️ Still has redundant build | ✅ One less workflow, clear topology |
| Rollback capability | 15% | ✅ One-click slot swap | ⚠️ Same as today (redeploy) | ⚠️ Same as today (redeploy) |
| a1sb-class footgun elimination | 20% | ⚠️ Adds new vars that could go unset | ⚠️ Removes broken jobs but keeps redundant build | ✅ Eliminates the entire footgun surface |
| Engineering effort | 10% | ❌ 12–20 hours | ✅ 1–2 hours | ✅ 1–2 hours |
| Production readiness for launch | 15% | ❌ Weeks to provision + test | ✅ Immediate | ✅ Immediate |
| **Weighted Score** (❌=0, ⚠️=0.5, ✅=1, weighted) | | **0.25 (Low)** | **0.73 (Medium)** | **0.93 (High)** |

---

## Recommendation

**Recommended: Option C — Delete `blue-green-deploy.yml` entirely.**

### Rationale

1. **The workflow's deploy jobs have never worked.** They were broken from the day they were written. No configuration was ever set to make them work. Fixing them requires S1 tier (+$57/mo) — a 5.6× increase in App Service costs for a 10–30 user internal tool.

2. **The workflow's build job is fully redundant.** `deploy-staging.yml` already builds and pushes a production-target image with the a1sb guard on every push to main. The same guard is also in `deploy-production.yml`. There is no unique value added by the blue-green workflow's build step.

3. **No automated system depends on the tags it produces.** The `:main` tag is consumed by nothing. The short-SHA tags are consumed by nothing. The `:latest` tag is also pushed by `deploy-production.yml`.

4. **It wastes CI resources.** Every push to main triggers a redundant ~10–15 minute Docker build that produces images nobody uses.

5. **Dead code is a liability, not an asset.** This workflow is the exact artifact that caused the a1sb production outage. Even though the `target:` bug is fixed, keeping a dead workflow around invites future misunderstandings ("why doesn't blue-green work?", "should I fix these vars?", "let me add my deploy here...").

6. **If true blue-green is needed later, it should be designed from scratch.** The current workflow's architecture (building its own image, creating slots inline, no Bicep, no sticky settings) is not how you'd design a proper blue-green pipeline. A future blue-green ADR would start with Bicep-managed slots, a single build pipeline, and proper cost analysis.

### What about the `:latest` tag?

After deleting `blue-green-deploy.yml`, the `:latest` tag will only update when `deploy-production.yml` runs (manual dispatch). For most use cases this is fine — `:latest` *should* represent what's in production. If Tyler wants `:latest` to also update on every push to main, add one line to `deploy-staging.yml`'s build tags:

```yaml
tags: |
  ${{ env.GHCR_REGISTRY }}/${{ env.GHCR_REPOSITORY }}:${{ env.IMAGE_TAG }}
  ${{ env.GHCR_REGISTRY }}/${{ env.GHCR_REPOSITORY }}:sha-${{ github.sha }}
  ${{ env.GHCR_REGISTRY }}/${{ env.GHCR_REPOSITORY }}:latest    # ← optional, if needed
```

---

## Migration Steps (for Option C)

1. **Delete the workflow file:**
   ```bash
   git rm .github/workflows/blue-green-deploy.yml
   ```

2. **Update documentation references** (find-and-replace or manual edit):
   - `INFRASTRUCTURE_END_TO_END.md` — remove row from workflows table
   - `AZURE_DEVOPS_DEPLOYMENT_GUIDE.md` — remove references to `blue-green-deploy.yml` and `gh workflow run blue-green-deploy.yml`
   - `SESSION_HANDOFF.md` — a1sb context is historical, can remain as-is or add note that workflow was deleted per this ADR
   - `docs/decisions/adr-0007-auth-evolution.md` — note that blue-green deploy reference is aspirational, not currently implemented

3. **Fix the misleading code comment** in `deploy-staging.yml`:
   ```yaml
   # Current comment (WRONG):
   # Staging images get promoted to prod via blue-green swap
   
   # Correct comment:
   # Production images are built separately by deploy-production.yml (manual dispatch).
   # This guard ensures staging images are also valid production-stage images.
   ```

4. **Verify CI on the deletion PR** — ensure no workflow depends on `blue-green-deploy.yml` via `workflow_run` trigger (confirmed: `accessibility.yml` depends on `Deploy to Staging`, not on blue-green).

5. **(Optional) Add `:latest` tag to `deploy-staging.yml`** if Tyler wants `:latest` updated on every push.

6. **Clean up stale GHCR tags** — the `:main` tag and accumulated short-SHA tags can be pruned from GHCR via `gh api` or the GHCR UI.

---

## Rollback Plan

If deleting the workflow causes an unforeseen problem:

1. **Restore the file from git history:**
   ```bash
   git checkout HEAD~1 -- .github/workflows/blue-green-deploy.yml
   git commit -m "revert: restore blue-green-deploy.yml"
   git push
   ```

2. The workflow will resume building (and failing to deploy) on the next push to main — exactly as it does today.

3. There is no state to restore — the workflow's deploy jobs have never successfully run.

---

## Open Questions for Tyler

1. **Do you want `:latest` to update on every push to main, or only on manual prod deploys?** If you want it on every push, I'll add one line to `deploy-staging.yml`. If not, no change needed.

2. **Do you want true blue-green deployment capability in the future?** If so, it requires upgrading to S1 tier (+$57/mo). That's a separate ADR when/if you're ready. The current workflow was never going to deliver it on B1.

3. **Should we purge the accumulated short-SHA and `:main` tags from GHCR?** They're harmless but cluttery. Can be done with a one-liner: `gh api` call to delete untagged/unused manifests.

4. **Is there any manual process or script that pulls the `:main` GHCR tag?** I found no automated references, but if you or another developer manually does `docker pull ghcr.io/htt-brands/azure-governance-platform:main` for local development, we should know before deleting the workflow that produces it. *(pending Tyler confirmation before execution)*

---

## Consequences

### What gets better
- **One fewer silently-broken workflow** running on every push to main
- **~10–15 fewer CI minutes wasted per push** (one fewer Docker build)
- **Clearer deploy topology:** `deploy-staging.yml` handles staging, `deploy-production.yml` handles prod. No ambiguity.
- **Eliminates `:latest` tag race condition** between two workflows
- **No more "should we fix the blue-green vars?" temptation** — the dead code is gone
- **Documentation can accurately describe CI/CD** without caveats about broken jobs

### What stays the same
- Staging deploys: still automatic on push to main via `deploy-staging.yml`
- Production deploys: still manual dispatch via `deploy-production.yml` with environment protection
- a1sb guard: still present in both surviving deploy workflows
- Rollback procedure: still "redeploy previous SHA" (same as today — slot swap never worked)

### What gets harder
- **No one-click rollback via slot swap** — but this never worked anyway
- **If blue-green is needed later, it's a fresh build** — but the current workflow was architecturally wrong (B1 can't do slots), so a fresh build is the right path regardless

---

## Surprise Findings — Potential New Issues

The following issues were discovered during this investigation and may warrant separate bd issues:

### ⚠️ Finding 1: Stale Documentation Claims B1 Supports Deployment Slots (P3)
Multiple research documents and recommendations claim "deployment slots free on B1+". This is factually incorrect — Azure App Service deployment slots require Standard (S1) tier or above. If any future decision relies on these docs, it will hit a wall.
- Files: `research/cost-optimization-2026/recommendations.md`, `research/cost-optimization-2026/analysis.md`, `research/azure-hosting-alternatives/recommendations.md`
- Recommendation: Correct these docs or add a prominent warning.

### ⚠️ Finding 2: GHCR Repository Path Inconsistency (P4)
`container-registry-migration.yml` pushes to `ghcr.io/tygranlund/azure-governance-platform` while all other workflows push to `ghcr.io/htt-brands/azure-governance-platform`. The `parameters.production.json` Bicep file also references the `tygranlund/` path. If the repo was transferred from personal to org, the old path may still redirect — but this should be cleaned up.

### ⚠️ Finding 3: `INFRASTRUCTURE_END_TO_END.md` Misrepresents Trigger (P4)
The document claims `blue-green-deploy.yml` trigger is "Manual". The actual trigger is `push: branches: [main]` (automatic on every push) plus `workflow_dispatch`. This misled investigation and could mislead future operators.

---

## STRIDE Security Analysis

| Threat | Applicability | Mitigation |
|---|---|---|
| **Spoofing** | Low. Deleting the workflow does not change authentication posture. OIDC + GHCR_PAT auth unchanged. | No action needed. |
| **Tampering** | Low. Image integrity is maintained by digest pinning in surviving workflows. a1sb guard remains in both. | No action needed. |
| **Repudiation** | Low. GitHub Actions audit log captures all workflow runs. Deletion is tracked in git history. | No action needed. |
| **Information Disclosure** | Neutral. No secrets are added or removed. `${{ vars.* }}` were empty — no data exposed. | No action needed. |
| **Denial of Service** | **Positive impact.** Removing a redundant build reduces CI queue contention and GHCR storage growth. | Benefit of deletion. |
| **Elevation of Privilege** | Neutral. The workflow's permissions (`packages: write`, `id-token: write`) are also held by surviving workflows. No net change. | No action needed. |

---

## References

- **Authoritative cost model:** `docs/COST_MODEL_AND_SCALING.md` (bd-zj9k, forthcoming) — canonical App Service/SQL/Cosmos pricing and 24-month projections. All cost figures in this ADR should reconcile with that document. Supersedes the cost sections of `research/cost-optimization-2026/` and `docs/LAUNCH_READINESS_AND_ROADMAP.md` where they diverge. Until published, `docs/LAUNCH_READINESS_AND_ROADMAP.md` is the interim source of B1 = $12.41/mo.
- Incident a1sb: `SESSION_HANDOFF.md` — production running dev image for weeks
- Azure App Service pricing: [https://azure.microsoft.com/en-us/pricing/details/app-service/linux/](https://azure.microsoft.com/en-us/pricing/details/app-service/linux/)
- Azure deployment slots documentation: [https://learn.microsoft.com/en-us/azure/app-service/deploy-staging-slots](https://learn.microsoft.com/en-us/azure/app-service/deploy-staging-slots) — "Deployment slots are available in the Standard, Premium, and Isolated App Service plan tiers"
- GitHub Actions variables: [https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/store-information-in-variables](https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/store-information-in-variables) — unset `vars.*` evaluate to empty string with no error
- Current infrastructure: `parameters.production.json` — `appServiceSku: "B1"`
- Cost data: `research/cost-optimization-2026/analysis.md`, `infrastructure/COST_OPTIMIZATION.md` (⚠️ both contain the B1-deployment-slots error flagged in the Documentation Errors table above — reconcile against the authoritative cost model)
