# Cost Optimization — Prioritized Recommendations

## Summary: $73/mo → $0-18/mo

Two-phase approach recommended. Phase 1 is low-risk and delivers most of the savings.

---

## Phase 1: Quick Wins (This Week) — $73 → $15/mo

**Estimated savings: $58/mo ($696/year)**
**Risk: Low | Effort: 4-8 hours | Rollback: Easy**

### Step 1.1: Eliminate Staging Environment (saves $38.17/mo)

The staging environment is 52% of the total bill. For a 10-30 user governance tool with low deployment frequency, a dedicated staging environment is overkill.

```bash
# 1. Verify staging can be safely deleted
az group show --name rg-governance-staging --query "name"

# 2. Export ARM template for disaster recovery
az group export --name rg-governance-staging > staging-backup-template.json

# 3. Delete the entire staging resource group
az group delete --name rg-governance-staging --yes --no-wait
```

**Replacement strategy:**
- **Testing**: GitHub Actions CI runs unit + integration tests on every PR
- **UAT**: App Service deployment slots for blue-green require Standard S1+ (not supported on B1)
- **Emergency staging**: Can spin up Container Apps env in minutes if needed ($0 on free tier)

**Rollback**: Re-deploy from Bicep templates in `infrastructure/` directory.

### Step 1.2: Migrate Azure SQL to Free Tier (saves $15/mo per database)

The free tier offers 100K vCore-seconds and 32GB storage — far exceeding the 6.25MB database needs.

**Important limitation:** Cannot convert existing database. Must create new and migrate.

```bash
# 1. Create new free-tier SQL database
az sql db create \
  --resource-group rg-governance-production \
  --server sql-gov-prod-mylxq53d \
  --name governance-free \
  --edition GeneralPurpose \
  --compute-model Serverless \
  --family Gen5 \
  --capacity 2 \
  --auto-pause-delay 60 \
  --use-free-limit \
  --free-limit-exhaustion-behavior AutoPause

# 2. Export data from current S0 database
# Use Azure Data Studio or sqlpackage
sqlpackage /Action:Export \
  /SourceServerName:sql-gov-prod-mylxq53d.database.windows.net \
  /SourceDatabaseName:governance \
  /TargetFile:governance-backup.bacpac

# 3. Import data to new free database
sqlpackage /Action:Import \
  /TargetServerName:sql-gov-prod-mylxq53d.database.windows.net \
  /TargetDatabaseName:governance-free \
  /SourceFile:governance-backup.bacpac

# 4. Update connection string in App Service
az webapp config connection-string set \
  --resource-group rg-governance-production \
  --name app-governance-prod \
  --connection-string-type SQLAzure \
  --settings DefaultConnection="Server=tcp:sql-gov-prod-mylxq53d.database.windows.net,1433;Database=governance-free;..."

# 5. Verify app health
curl https://app-governance-prod.azurewebsites.net/health

# 6. After validation, delete old S0 database
az sql db delete \
  --resource-group rg-governance-production \
  --server sql-gov-prod-mylxq53d \
  --name governance \
  --yes
```

**Cold start mitigation:** Set auto-pause delay to 60 minutes. With 10-30 users during business hours, the DB rarely auto-pauses during work time. The 30-60 second cold start only occurs after prolonged inactivity (weekends/nights).

### Step 1.3: Migrate ACR → GitHub Container Registry (saves $5/mo)

GHCR is currently free for container images and integrates natively with GitHub Actions.

```yaml
# .github/workflows/build-deploy.yml changes:
# Before:
#   docker push acrgovprod.azurecr.io/azure-governance-platform:$TAG
# After:
    - name: Login to GHCR
      uses: docker/login-action@v3
      with:
        registry: ghcr.io
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    - name: Build and Push
      run: |
        docker build -t ghcr.io/${{ github.repository }}:${{ env.TAG }} .
        docker push ghcr.io/${{ github.repository }}:${{ env.TAG }}
```

```bash
# Update App Service to pull from GHCR
az webapp config container set \
  --resource-group rg-governance-production \
  --name app-governance-prod \
  --container-image-name ghcr.io/htt-brands/azure-governance-platform:v1.6.0 \
  --container-registry-url https://ghcr.io \
  --container-registry-user <github-username> \
  --container-registry-password <github-pat-or-token>

# After validation, delete ACR
az acr delete --name acrgovprod --resource-group rg-governance-production --yes
```

### Phase 1 Result

| Component | Before | After | Savings |
|-----------|--------|-------|---------|
| Staging (all) | $38.17 | $0 | $38.17 |
| Azure SQL S0 → Free | $15.00 | $0 | $15.00 |
| ACR Standard → GHCR | $5.00 | $0 | $5.00 |
| App Service B1 | $13.14 | $13.14 | — |
| Key Vault + misc | $2.03 | $2.03 | — |
| **TOTAL** | **$73.34** | **$15.17** | **$58.17** |

---

## Phase 2: Container Apps Migration (Next Month) — $15 → $0-5/mo

**Estimated savings: $10-15/mo additional**
**Risk: Medium | Effort: 2-3 days | Rollback: Keep App Service plan for 30 days**

### Step 2.1: Deploy to Container Apps (Consumption)

```bash
# 1. Create Container Apps Environment
az containerapp env create \
  --name cae-governance-prod \
  --resource-group rg-governance-production \
  --location eastus

# 2. Create Container App
az containerapp create \
  --name ca-governance-prod \
  --resource-group rg-governance-production \
  --environment cae-governance-prod \
  --image ghcr.io/htt-brands/azure-governance-platform:v1.6.0 \
  --target-port 8000 \
  --ingress external \
  --min-replicas 0 \
  --max-replicas 3 \
  --cpu 0.25 \
  --memory 0.5Gi \
  --env-vars \
    ENVIRONMENT=production \
    DATABASE_URL=<free-tier-sql-connection-string> \
    AZURE_TENANT_ID=<tenant-id> \
    AZURE_CLIENT_ID=<client-id> \
    # ... other env vars from current App Service config
```

### Step 2.2: Rearchitect Background Jobs

**Current:** APScheduler runs inside the FastAPI process
**Problem:** Scale-to-zero kills the process, stopping scheduled jobs
**Solution:** Container Apps Jobs (cron-triggered)

```bash
# Create scheduled jobs for each sync
az containerapp job create \
  --name job-cost-sync \
  --resource-group rg-governance-production \
  --environment cae-governance-prod \
  --image ghcr.io/htt-brands/azure-governance-platform:v1.6.0 \
  --trigger-type Schedule \
  --cron-expression "0 2 * * *" \
  --cpu 0.25 --memory 0.5Gi \
  --command "python" "--" "-m" "app.jobs.cost_sync"

az containerapp job create \
  --name job-compliance-sync \
  --resource-group rg-governance-production \
  --environment cae-governance-prod \
  --image ghcr.io/htt-brands/azure-governance-platform:v1.6.0 \
  --trigger-type Schedule \
  --cron-expression "0 */4 * * *" \
  --cpu 0.25 --memory 0.5Gi \
  --command "python" "--" "-m" "app.jobs.compliance_sync"

az containerapp job create \
  --name job-resource-sync \
  --resource-group rg-governance-production \
  --environment cae-governance-prod \
  --image ghcr.io/htt-brands/azure-governance-platform:v1.6.0 \
  --trigger-type Schedule \
  --cron-expression "0 * * * *" \
  --cpu 0.25 --memory 0.5Gi \
  --command "python" "--" "-m" "app.jobs.resource_sync"
```

**Code changes needed:**
- Extract scheduler jobs into standalone entry points (e.g., `app/jobs/cost_sync.py`)
- Make APScheduler conditional (only enable in non-Container Apps environments)
- Ensure database connections work in short-lived job containers

### Step 2.3: DNS Cutover

```bash
# Point custom domain to Container Apps
az containerapp hostname bind \
  --name ca-governance-prod \
  --resource-group rg-governance-production \
  --hostname governance.example.com

# Update Azure AD redirect URIs
# Update CORS_ORIGINS environment variable
```

### Step 2.4: Decommission App Service

```bash
# After 30-day validation period
az webapp delete --name app-governance-prod --resource-group rg-governance-production
az appservice plan delete --name asp-governance-production --resource-group rg-governance-production
```

### Phase 2 Result

| Component | Phase 1 | Phase 2 | Savings |
|-----------|---------|---------|---------|
| App Service B1 → Container Apps | $13.14 | $0 (free grants) | $13.14 |
| Key Vault | $0.03 | $0.03 | — |
| Misc networking/storage | $2.00 | $0-2 | $0-2 |
| **TOTAL** | **$15.17** | **$0-5** | **$10-15** |

---

## Alternative: Phase 2B (Instead of Container Apps)

If rearchitecting background jobs is too much work, consider:

### Keep App Service B1, Use Everything Else from Phase 1

**Result: $15/mo permanently**

This is still a 79% savings from the original $73/mo and requires zero code changes.

---

## Decision Matrix

| Factor | Phase 1 Only | Phase 1 + 2 | VPS Route |
|--------|-------------|-------------|-----------|
| Monthly cost | $15 | $0-5 | $5 |
| Annual cost | $180 | $0-60 | $60 |
| Implementation effort | 4-8 hours | 2-3 days | 1-2 days |
| Code changes | None | Background jobs refactor | Docker Compose config |
| Risk level | Low | Medium | Medium-High |
| Managed infrastructure | ✅ Yes | ✅ Yes | ❌ No |
| Azure AD integration | ✅ Native | ✅ Native | ⚠️ Possible but harder |
| Cold starts | ❌ None | ⚠️ 1-3 sec app + 30-60 sec DB | ❌ None |
| Compliance-ready | ✅ Yes | ✅ Yes | ⚠️ Depends |
| Rollback ease | ✅ Easy | ⚠️ Moderate | ⚠️ Moderate |

---

## Annual Cost Projection

| Scenario | Monthly | Annual | vs. Current |
|----------|---------|--------|-------------|
| **Current** | $73 | $880 | — |
| **Phase 1 only** | $15 | $180 | **Save $700/yr** |
| **Phase 1 + 2** | $0-5 | $0-60 | **Save $820-880/yr** |
| **VPS route** | $5 | $60 | **Save $820/yr** |

---

## Risk Mitigation

### SQL Free Tier Auto-Pause Risk
- **Risk:** Database pauses after inactivity, causing 30-60 sec cold start
- **Mitigation:** Set auto-pause delay to 60 min; users rarely experience during business hours
- **Monitoring:** Set alert when "Free amount remaining" < 10,000 vCore-seconds

### GHCR Policy Change Risk
- **Risk:** GitHub makes container registry paid
- **Mitigation:** 1 month advance notice guaranteed; can switch to ACR Basic ($5/mo) quickly
- **Fallback:** DockerHub free tier (1 private repo) or self-hosted registry

### Container Apps Free Grant Exhaustion Risk
- **Risk:** Usage exceeds free grants as user base grows
- **Mitigation:** At 10× current usage, overflow cost is only ~$5-8/mo
- **Monitoring:** Azure Cost Analysis alerts at $5 threshold

### Staging Elimination Risk
- **Risk:** Production issues not caught before deployment
- **Mitigation:** 
  - Comprehensive CI/CD test suite (unit + integration)
  - App Service deployment slots for blue-green deploys
  - Feature flags for gradual rollout
  - Ephemeral Container Apps env for on-demand UAT

---

## Implementation Timeline

| Week | Action | Expected Savings |
|------|--------|-----------------|
| Week 1 | Delete staging, migrate ACR → GHCR | $43/mo |
| Week 2 | Migrate SQL to free tier | $15/mo |
| Week 3-4 | (Optional) Container Apps migration | $13/mo |
| **Total** | | **$58-73/mo** |


> **Errata (2026-04-17, bd-fuy4):** This document previously claimed App Service deployment slots are 'free on B1+'. That is **factually incorrect** — slots require Standard S1+ tier. Basic (B1/B2/B3) does **not** support slots at all. Corrected inline. Authoritative cost/tier reference: [`docs/COST_MODEL_AND_SCALING.md`](../../docs/COST_MODEL_AND_SCALING.md) §6.2.
