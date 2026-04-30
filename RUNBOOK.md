# RUNBOOK — Operating HTT Control Tower Without Tyler

**Purpose:** If Tyler is unavailable for 2+ weeks (PTO, illness, recruitment,
bus), this is the entry-point doc for whoever picks up operational
responsibility. Pairs with `SECRETS_OF_RECORD.md` (bd `9lfn`, Tyler-authored)
and `AGENT_ONBOARDING.md` (bd `2au0`, for any human-or-agent starting fresh).

**Filed under:** Phase 0.5 of `PORTFOLIO_PLATFORM_PLAN_V2.md` — bus-factor
mitigation. Success metric §8: "Bus-factor (humans able to deploy)" → 2.

**Status:** v1 draft 2026-04-28 by code-puppy-ab8d6a. Tyler-knowledge gaps
flagged with `🔴 TYLER-ONLY` markers.

---

## ⚡ Emergency Quick Reference (first 5 minutes)

```bash
# 1. Is the platform up?
curl -sS https://app-governance-prod.azurewebsites.net/health | jq .
curl -sS https://app-governance-staging-xnczpwyv.azurewebsites.net/health | jq .

# 2. Are syncs current?
curl -sS https://app-governance-prod.azurewebsites.net/api/v1/health/data | jq .

# 3. What is bd telling us?
bd ready                        # what's claimable
bd list --status in_progress    # what's in flight

# 4. Are CI pipelines green?
gh run list --workflow=deploy-staging.yml --limit 5
gh run list --workflow=deploy-production.yml --limit 5
```

If all four are healthy: nothing is on fire. Read sections 1–4 below at
your leisure. If anything is unhealthy: jump to §5 (Triage) immediately.

---

## 1. What This Platform Is

HTT Control Tower is a multi-tenant internal governance hub run by HTT Brands.
Single FastAPI instance, App Service B1 in HTT-CORE subscription, serving cost
visibility, identity audits, compliance evidence, resource visibility, lifecycle
workflows, and BI/evidence read models across five Azure tenants (HTT, BCC, FN,
TLL, DCE). It is unrelated to AWS Control Tower; the name is internal-only unless
HTT runs separate legal/name clearance.

**Source of truth for architecture:** `INFRASTRUCTURE_END_TO_END.md`
**Source of truth for current strategic direction:** `PORTFOLIO_PLATFORM_PLAN_V2.md`
**Source of truth for live blockers:** `CURRENT_STATE_ASSESSMENT.md` and `bd ready`

---

## 2. Deployment

### Deploy to staging
Automatic on every push to `main`. Five-job pipeline:
QA gate → security → build → deploy → validate.
- Watch: `gh run watch --workflow=deploy-staging.yml`
- Workflow file: `.github/workflows/deploy-staging.yml`

### Deploy to production
**Manual dispatch only.** Six-job pipeline including smoke test + Teams notify.

```bash
# Dispatch from CLI:
gh workflow run deploy-production.yml --ref main

# Or via GitHub Web UI:
#   Actions → Deploy Production → Run workflow → Branch: main
```

Detailed walkthrough: [`DEPLOYMENT.md`](./DEPLOYMENT.md).

### What "deploy" does mechanically
1. GitHub Actions OIDC-federates into HTT-CORE Azure tenant (no stored secrets).
2. Builds Docker image, pushes to GHCR at `ghcr.io/htt-brands/control-tower`. Existing Azure App Service instances may continue running an older `ghcr.io/htt-brands/azure-governance-platform` image until their next successful deploy.
3. SLSA Build L3 provenance attested + SBOM (Syft/SPDX-JSON) attached as OCI referrer.
4. Cosign 4-claim verification gates the deploy job (subject digest + predicate
   type + cert identity + OIDC issuer). Fails closed if verification fails.
5. App Service container config updated **by digest, not tag** (per bd `7mk8`
   supply-chain hardening).

---

## 3. Rollback

### If production is broken and you need to revert NOW
The image pin is by digest, so Azure has the previous-good digest in its
deployment history.

```bash
# Option A: Re-run a previous successful production workflow
gh run list --workflow=deploy-production.yml --status=success --limit 5
gh run rerun <run-id>

# Option B: Set the App Service container directly to a previous digest
az webapp config container set \
  --name app-governance-prod \
  --resource-group rg-governance-prod \
  --container-image-name ghcr.io/htt-brands/control-tower@sha256:<digest>
```

### If a feature is broken but the platform is up
Revert the offending commit on `main`, push, then dispatch a production deploy.
Do NOT force-push.

```bash
git revert <bad-commit-sha>
git push origin main
gh workflow run deploy-production.yml --ref main
```

### Database rollback
Azure SQL Basic has 7-day point-in-time restore. Detailed procedure:
[`docs/runbooks/disaster-recovery.md`](./docs/runbooks/disaster-recovery.md).

Formal targets are documented in [`docs/dr/rto-rpo.md`](./docs/dr/rto-rpo.md):
4h business-hours RTO / 8h after-hours RTO, 24h stated RPO, quarterly tests.

### Second rollback human
The successor readiness checklist lives at
[`docs/dr/second-rollback-human-checklist.md`](./docs/dr/second-rollback-human-checklist.md).
Do not treat bd `213e` as complete until Tyler names the human and records a
tabletop exercise there.

---

## 4. Dashboards & Where to Look

| What you want to see | URL |
|---|---|
| Platform health | `/health` |
| Per-tenant per-domain sync freshness | `/api/v1/health/data` |
| Cost dashboard | `/dashboard` (or `/portfolio/<brand>` for parametric route once Phase 4 ships) |
| Riverside compliance | `/riverside` |
| OpenAPI / interactive | `/docs` (auth-gated in prod, public in staging/dev) |

### Azure Portal entry points
- **HTT-CORE subscription:** `app-governance-prod`, `kv-gov-prod`, Azure SQL
  `sqldb-governance-prod`, App Insights `appi-governance-prod`.
- **Other 4 tenants:** federated via Lighthouse delegated access; the
  platform reads them but does not host resources there.

🔴 **TYLER-ONLY:** Direct Azure Portal links / saved queries / pinned
dashboards are in Tyler's account. Document in `SECRETS_OF_RECORD.md`.

---

## 5. Alert Triage

### Where alerts come from
- **App Insights** alerts in HTT-CORE subscription.
- **Microsoft Teams** webhook (`PRODUCTION_TEAMS_WEBHOOK` GitHub secret) for
  deploy failures.
- **GitHub Actions** failures (especially `deploy-staging.yml`,
  `deploy-production.yml`, `backup.yml`, `bicep-drift-detection.yml`).
- **`/api/v1/health/data`** flagged as `any_stale=true` (bd `3cs7` — alert
  not yet wired to governance-alerts).

### Common patterns
| Symptom | Likely cause | First action |
|---|---|---|
| Staging deploy validation timeout | Cold-start (bd `mvxt`, mostly mitigated 2026-04-28) | Retry the failed workflow once; if it fails again, escalate |
| Prod `/api/v1/health` returns 500 | App startup failure (bd `a1sb`) | Check App Insights for boot errors |
| `costs: null` for BCC/FN/TLL | Cost Mgmt Reader role not granted (bd `5xd5`) | Grant role in target subscription |
| Bicep drift detected | Manual portal change OR template drift | Review the rolling drift issue, reconcile |
| Database Backup workflow red before backup starts | Missing OIDC permission (bd `3flq`, closed), missing environment backup secrets, missing `mssqlscripter`, missing ODBC Driver 18, SQL login/server mismatch, or backup upload auth (bd `jzpa`) | Check failed step; if env shows empty `DATABASE_URL` / `AZURE_STORAGE_ACCOUNT`, configure GitHub environment secrets. If `mssqlscripter` is missing, SQLAlchemy fallback should run. If ODBC driver is missing, verify `backup.yml` installed `msodbcsql18`. If upload fails, verify the ephemeral `AZURE_STORAGE_KEY` preparation step and storage account key access. If prod says `Cannot open server`, verify the temporary SQL firewall rule step ran and then verify the prod SQL login/server/database in the source App Service `DATABASE_URL`. |
| Database Backup workflow red at notify step | Broken notify action (bd `fifh`, closed) | Current workflow uses curl MessageCard pattern; re-check webhook config |

### Escalation
🔴 **TYLER-ONLY:** Escalation tree (HTT IT, Riverside, MSP partners, MS support
case ownership) lives in Tyler's head. Document in `SECRETS_OF_RECORD.md`.

Provisional placeholders:
- **HTT IT lead:** `<TODO>`
- **MSP partner:** `<TODO>`
- **Microsoft support contract:** `<TODO>`
- **Riverside operating partner:** `<TODO>`

---

## 6. Recurring Maintenance Tyler Does

These need to keep happening even when Tyler is unavailable.

| Task | Frequency | Where it lives |
|---|---|---|
| Review `bd ready` | Daily | `bd ready` |
| Review staging deploy results | Per push | GitHub Actions |
| Review weekly Bicep drift detection | Weekly Mon 13:00 UTC | `bicep-drift-detection.yml` rolling issue |
| Review monthly cost report | Monthly | Azure Cost Management |
| Refresh GHCR_PAT | Yearly (set 2026-04-10) | GitHub repo secrets |
| Review `xkgp` `datetime.utcnow` deprecation | Before Python 3.13 release | tech debt |
| Review CI action SHA pins | Quarterly | Dependabot PRs |
| 213e: name a second rollback human | Before 2026-06-22 | bd `213e` (waiver clock!) |

🔴 **TYLER-ONLY:** Some of these may have additional steps (notify Riverside
of cost trends, talk to MSP about Pax8 invoice anomalies, etc.) that aren't
documented. List in `SECRETS_OF_RECORD.md`.

---

## 7. The Five-Tenant Identity Model

**Critical context:** The platform reads from 5 Azure tenants but lives in 1.
- **Home tenant:** HTT-CORE (the platform's UAMI lives here).
- **Read-targeted tenants:** HTT, BCC, FN, TLL, DCE — each has a federated
  app registration trusting HTT-CORE's UAMI via OIDC.

Detailed setup: [`docs/runbooks/oidc-federation-setup.md`](./docs/runbooks/oidc-federation-setup.md).

🔴 **TYLER-ONLY:** Cross-tenant B2B grants (e.g., TLL users in HTT Fabric)
are a known cross-tenant graph. V2 plan §D10 will classify these as
documented vs ad-hoc. Until classification: **do not grant or revoke
cross-tenant B2B access without consulting Tyler or the documented owner.**

---

## 8. Cost Posture

Total platform spend: ~$53/mo as of 2026-04-16.
- Production: ~$18.05/mo
- Staging: ~$12.68/mo
- Dev: ~$22.67/mo

Phased ceilings per V2 §6:
- End of Phase 2: $80/mo
- End of Phase 4: $150/mo
- End of Phase 5: $300–400/mo (driven by Azure OpenAI + Athena scans if
  bridges + AI ship)

Cost emergency: if monthly spend exceeds $200 unexpectedly, the most likely
cause is Azure SQL spinning up dev environment continuously. Check
[`docs/runbooks/resource-cleanup.md`](./docs/runbooks/resource-cleanup.md).

---

## 9. Where Things Live (Repo Geography)

```
control-tower/
├── app/                    # FastAPI application
├── infrastructure/         # Bicep IaC for all 3 environments
├── docs/                   # Detailed docs, ADRs, runbooks
│   ├── adr/                # Architecture decision records
│   ├── runbooks/           # Operational runbooks (THIS RUNBOOK is the
│   │                       #   entry point; deep procedures live in
│   │                       #   docs/runbooks/)
│   └── plans/              # Strategic plans
├── tests/                  # 4,192 tests (pytest --collect-only 2026-04-28)
├── scripts/                # Operational scripts
├── .github/workflows/      # CI/CD pipelines
├── .beads/                 # bd issue tracker DB + JSONL
├── INFRASTRUCTURE_END_TO_END.md           # System topology
├── PORTFOLIO_PLATFORM_PLAN_V2.md          # Strategic plan
├── CURRENT_STATE_ASSESSMENT.md            # Live blocker dashboard
├── SESSION_HANDOFF.md                     # Session-to-session notes
├── RUNBOOK.md                             # ← YOU ARE HERE
├── SECRETS_OF_RECORD.md                   # ← Tyler-authored (bd 9lfn)
├── AGENT_ONBOARDING.md                    # ← Human-or-agent fresh onboarding (bd 2au0)
├── CHANGELOG.md
└── README.md
```

---

## 10. What This Runbook Does NOT Cover (And Why)

- **Adding a new tenant:** Requires Tyler's expertise on cross-tenant
  Lighthouse delegation. See V2 Phase 4d for the future automated path.
- **Adding a new feature:** Read `docs/contracts/`, `app/api/routes/`, and
  the relevant domain. Don't add features without Tyler review.
- **Modifying compliance scoring:** Domain-specific; consult
  `app/services/riverside_sync.py` and the relevant scoring docs.
- **Changing tenant auth model:** Out of scope for emergency operation. If
  you think you need this, you don't. Wait for Tyler.
- **Database schema changes:** Migrations are gated. Don't.

---

## 11. Verifying You Have What You Need (smoke test)

If you can complete this checklist, you are operationally ready to keep
the platform running.

- [ ] You can reach `bd ready` and see the live backlog.
- [ ] You can reach `gh run list --workflow=deploy-staging.yml`.
- [ ] You can reach `curl https://app-governance-prod.azurewebsites.net/health`.
- [ ] You have read access to `kv-gov-prod` Key Vault in Azure Portal.
- [ ] You have `Cost Management Reader` role on the HTT-CORE subscription.
- [ ] You have `Contributor` role on `rg-governance-prod` (for emergency
      Azure CLI work).
- [ ] You can dispatch `deploy-production.yml` (or a designated alternate
      can).
- [ ] You have read `INFRASTRUCTURE_END_TO_END.md` (~30 min).
- [ ] You have read `SECRETS_OF_RECORD.md` once Tyler fills it (bd `9lfn`).
- [ ] If you are the second rollback human, your access/tabletop status is
      recorded in `docs/dr/second-rollback-human-checklist.md`.
- [ ] You know who to escalate to (see §5).

If any of these are unchecked, you are NOT ready. Pair with someone who is.

---

## 12. Open Items (this runbook needs)

These are bd issues that, once closed, complete the runbook:

- [ ] `9lfn` — `SECRETS_OF_RECORD.md` exists as a safe skeleton; Tyler still
      needs to fill the non-secret inventory rows before closure.
- [x] `2au0` — `AGENT_ONBOARDING.md` (separate but complementary doc)
- [x] `0dhj` — Formal RTO/RPO + backup-restore-test cadence
- [ ] `3cs7` — Wire `/api/v1/health/data` `any_stale=true` to Teams alerts
- [ ] `213e` — Name a second rollback human and complete
      `docs/dr/second-rollback-human-checklist.md` tabletop evidence (waiver
      expires 2026-06-22)
- [x] `jzpa` — Scheduled/manual production and staging schema backups validated:
      staging `25169438794`, production `25171354807`. Weekly long-term BACPAC
      export remains separate as blocked bd `cz89`.
- [ ] All 🔴 TYLER-ONLY markers above filled in

When all are checked, this runbook is complete and bus-factor metric
advances from 1 → 2.

---

*Authored by Richard (code-puppy-ab8d6a) for Tyler Granlund, 2026-04-28.*
*v1 — draft. Re-review and expand on every Tyler-PTO event.*
