# Recommendations — Project-Specific Action Items

## Priority 1: Delete Staging Environment — Save $38/mo

**Effort:** 30 minutes | **Risk:** Low | **Savings:** $38.17/mo

### Why
Staging consumes 52% of total spend ($38 of $73). For 10-30 internal users,
staging is not justified. The existing CI pipeline provides sufficient
pre-deploy validation.

### Steps
```bash
# 1. Verify staging is not actively used
az webapp show --name app-governance-staging-xnczpwyv --resource-group rg-governance-staging

# 2. Delete the entire staging resource group
az group delete --name rg-governance-staging --yes --no-wait

# 3. Remove staging parameters file
rm infrastructure/parameters.staging.json

# 4. Update CI/CD to skip staging deployment
# Edit .github/workflows to remove staging-related jobs
```

### Alternative to Staging
- Use **App Service deployment slots** (free on B1+) for blue-green deployments
- Use **GitHub Actions CI** with `docker-compose up` for integration testing
- For UAT: spin up ephemeral Container Apps environment, test, destroy

---

## Priority 2: Switch ACR Standard → GHCR — Save $5/mo

**Effort:** 30 minutes | **Risk:** Low | **Savings:** $5/mo

### Steps
```bash
# 1. Update GitHub Actions workflow to push to GHCR
# In .github/workflows/deploy.yml, change:
#   registry: acrgovernanceprod.azurecr.io
# To:
#   registry: ghcr.io

# 2. Update App Service to pull from GHCR
az webapp config container set \
  --name app-governance-prod \
  --resource-group rg-governance-production \
  --docker-custom-image-name ghcr.io/YOUR_ORG/azure-governance-platform:latest

# 3. Delete ACR (after verifying GHCR works)
az acr delete --name acrgovernanceprod --resource-group rg-governance-production
```

---

## Priority 3: Migrate SQL S0 → SQL Free Tier — Save $15/mo

**Effort:** 1-2 hours | **Risk:** Low-Medium | **Savings:** $15/mo

### Pre-Migration Checklist
- [ ] Current database size: ~6.25 MB (well under 32 GB limit)
- [ ] Query volume: ~1,000/day (well under 100K vCore-sec/mo)
- [ ] Acceptable: 7-day PITR limit (vs 35 days on S0)
- [ ] Acceptable: ~60-second cold start after auto-pause
- [ ] Acceptable: No geo-redundant backups

### Steps
```bash
# 1. Create free tier database via Azure Portal
# Go to aka.ms/azuresqlhub → "Start free"
# Use existing logical server or create new one

# 2. Run Alembic migrations on new database
DATABASE_URL="mssql+pyodbc://..." alembic upgrade head

# 3. Export data from current S0 database
# Use Azure Data Studio or sqlcmd to export/import
# For 6 MB of data, simple INSERT scripts work fine

# 4. Update connection string in Key Vault
az keyvault secret set \
  --vault-name kv-gov-prod-XXXX \
  --name "database-url" \
  --value "mssql+pyodbc://user:pass@new-server.database.windows.net/governance-db?driver=ODBC+Driver+18+for+SQL+Server"

# 5. Restart app to pick up new connection string
az webapp restart --name app-governance-prod --resource-group rg-governance-production

# 6. Verify
curl -sf https://app-governance-prod.azurewebsites.net/health

# 7. Delete old S0 database (after validation period)
```

### Add Retry Logic for Auto-Resume

The free tier database will auto-pause when idle. On resume, the first
connection returns error 40613. The app needs retry logic.

**Current state:** `pool_pre_ping=True` in `database.py` handles stale
connections, but does NOT handle 40613 (DB paused, not a stale connection).

**Required change in `app/core/database.py`:**

```python
from sqlalchemy import event
from sqlalchemy.exc import OperationalError
import time

@event.listens_for(engine, "handle_error")
def handle_sql_error(context):
    """Retry on Azure SQL auto-resume (error 40613)."""
    if isinstance(context.original_exception, OperationalError):
        error_msg = str(context.original_exception)
        if "40613" in error_msg:
            # Database is resuming from auto-pause
            logger.warning("SQL Database is resuming from auto-pause, waiting...")
            time.sleep(30)  # Wait for resume
            # The connection will be retried by pool_pre_ping
```

Alternatively, configure `connect_args` with connection retry:
```python
# In the ODBC connection string, add retry parameters:
"ConnectRetryCount=3;ConnectRetryInterval=10"
```

### Free Tier Behavior Setting

Choose one of:
- **"Auto-pause until next month"** — DB pauses when free limits hit (safest for cost)
- **"Continue for additional charges"** — DB keeps running, charges standard serverless rates if limits exceeded

**Recommendation:** Start with "auto-pause until next month" since the workload
uses only 1.5% of the free allowance. Switch to "continue" if the monthly
pause becomes disruptive.

---

## Priority 4: Migrate to Container Apps (Future Sprint)

**Effort:** 5-8 hours | **Risk:** Medium | **Savings:** $13/mo

### Prerequisites
- [ ] Priority 1-3 completed
- [ ] APScheduler jobs documented and tested independently
- [ ] Retry logic for SQL 40613 in place
- [ ] Container image tested with Container Apps locally (if possible)

### Architecture Changes Required

#### 1. Create Container Apps Environment
```bash
az containerapp env create \
  --name cae-governance-prod \
  --resource-group rg-governance-production \
  --location eastus

# Add Azure Files storage mount (for logs, temp files)
az containerapp env storage set \
  --name cae-governance-prod \
  --resource-group rg-governance-production \
  --storage-name governance-storage \
  --azure-file-account-name stgovprodXXXXXX \
  --azure-file-share-name governance-data \
  --azure-file-account-key <KEY> \
  --access-mode ReadWrite
```

#### 2. Deploy Web App
```bash
az containerapp create \
  --name ca-governance-web \
  --resource-group rg-governance-production \
  --environment cae-governance-prod \
  --image ghcr.io/YOUR_ORG/azure-governance-platform:latest \
  --target-port 8000 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 3 \
  --cpu 0.5 \
  --memory 1.0Gi \
  --env-vars \
    ENVIRONMENT=production \
    DATABASE_URL=secretref:database-url \
  --secrets \
    database-url="mssql+pyodbc://..."
```

#### 3. Create Container Apps Jobs (replace APScheduler)

```bash
# Example: Daily cost sync
az containerapp job create \
  --name job-sync-costs \
  --resource-group rg-governance-production \
  --environment cae-governance-prod \
  --image ghcr.io/YOUR_ORG/azure-governance-platform:latest \
  --trigger-type Schedule \
  --cron-expression "0 0 * * *" \
  --cpu 0.25 \
  --memory 0.5Gi \
  --command "python" "-m" "app.jobs.run_sync" "--job" "costs" \
  --env-vars \
    ENVIRONMENT=production \
    DATABASE_URL=secretref:database-url

# Repeat for each sync job with appropriate cron expression
```

#### 4. Create Job Runner Entrypoint

New file: `app/jobs/run_sync.py`
```python
"""CLI entrypoint for Container Apps Jobs — runs sync functions."""
import asyncio
import argparse
import sys
from app.core.database import init_db

async def run_job(job_name: str):
    init_db()
    # Import and run the appropriate sync function
    sync_functions = {
        "costs": "app.core.sync.costs:sync_costs",
        "compliance": "app.core.sync.compliance:sync_compliance",
        "resources": "app.core.sync.resources:sync_resources",
        "identity": "app.core.sync.identity:sync_identity",
        "riverside": "app.core.sync.riverside:sync_riverside",
        "dmarc": "app.core.sync.dmarc:sync_dmarc_dkim",
    }
    # ... import and call function

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", required=True)
    args = parser.parse_args()
    asyncio.run(run_job(args.job))
```

#### 5. Custom Domain + SSL
```bash
az containerapp hostname bind \
  --name ca-governance-web \
  --resource-group rg-governance-production \
  --hostname governance.yourdomain.com \
  --environment cae-governance-prod \
  --validation-method CNAME

# Managed certificate is automatically provisioned
```

#### 6. Remove APScheduler

Once Container Apps Jobs are verified:
- Remove `app/core/scheduler.py`
- Remove `init_scheduler()` call from `app/main.py`
- Remove `apscheduler` from `pyproject.toml`

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| SQL Free Tier auto-pauses unexpectedly | Low | Medium | Monitor vCore consumption; set alerts at 80% usage |
| Container Apps cold start annoys users | Medium | Low | Set min=1 ($2-5/mo) or accept for internal tool |
| APScheduler → Jobs migration breaks sync | Medium | High | Test each job independently before switching; keep old scheduler code for rollback |
| Free tier limits exceeded | Very Low | Low | At 1.5% usage, would need 60× growth to hit limits |
| Azure Files SMB latency for logs | Low | Low | Use container-scoped storage for temp files, Azure Files only for persistent data |
| GHCR availability | Very Low | Medium | GitHub has 99.9% SLA; can fallback to ACR Basic ($5/mo) if needed |

---

## Decision Record

### Why NOT pure SQLite?

SQLite on Azure Files was considered but rejected because:
1. Azure SQL Free Tier costs the same ($0/mo)
2. Azure SQL provides managed backups, PITR, encryption
3. SQLite WAL mode is unreliable over SMB network mounts
4. Azure SQL handles concurrent connections properly
5. The codebase already has Azure SQL support in production

### Why NOT Azure Functions?

Azure Functions was rejected because:
1. FastAPI + HTMX SSR architecture doesn't fit the Functions model
2. Every route would need to become a separate Function
3. 5-10 second cold starts on Python Functions
4. Massive rearchitecture effort for marginal cost savings over Container Apps
5. Session management becomes complex

### Why Container Apps over App Service for future state?

1. Scale-to-zero saves the $13/mo B1 cost
2. Container Apps provides VNet integration (B1 doesn't)
3. Container Apps Jobs is a cleaner solution than in-process APScheduler
4. Better health probe support (startup, liveness, readiness)
5. Revision-based traffic splitting (better than deployment slots)
6. The app is already containerized — no additional work to containerize
