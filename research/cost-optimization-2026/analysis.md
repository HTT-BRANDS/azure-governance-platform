# Cost Optimization — Multi-Dimensional Analysis

## Current Architecture Baseline

| Component | Prod | Staging | Monthly |
|-----------|------|---------|---------|
| App Service B1 (1 core, 1.75GB) | $13.14 | $13.14 | $26.28 |
| Azure SQL S0 (10 DTU) | $15.00 | $15.00 | $30.00 |
| Container Registry (Standard) | $5.00 | — | $5.00 |
| Key Vault | $0.03 | $0.03 | $0.06 |
| Storage/Bandwidth | $2.00 | — | $2.00 |
| Storage Account (GRS) | — | $5.00 | $5.00 |
| Log Analytics + App Insights | — | $5.00 | $5.00 |
| **TOTAL** | **$35.17** | **$38.17** | **$73.34** |

---

## Architecture Option 1: Container Apps + SQL Free Tier + GHCR

### Cost Breakdown: $0-5/mo

| Component | Cost | Notes |
|-----------|------|-------|
| Container Apps (consumption) | $0 | Within free grants (est. ~35K of 180K vCPU-sec used) |
| Azure SQL Database (free offer) | $0 | 100K vCore-sec free, 32GB storage (DB is 6.25MB) |
| GitHub Container Registry | $0 | Currently free for container images |
| Key Vault | $0.03 | Minimal operations |
| Storage (Functions backing) | $1-2 | Minimal blob storage for Container Apps |
| **TOTAL** | **$0-5** | **Savings: $68-73/mo (93-100%)** |

### Free Tier Capacity vs. Actual Usage

**Container Apps Free Grants (per subscription/month):**
- 180,000 vCPU-seconds (= 50 hours of 1 vCPU)
- 360,000 GiB-seconds (= 100 hours of 1 GiB RAM)
- 2,000,000 requests

**Estimated Usage for Governance Platform:**
- Web requests: ~100 page loads/day × 2 sec = 200 sec/day = 6,000 vCPU-sec/mo
- Background sync jobs (if moved to timer-triggered Container Apps jobs):
  - Cost sync (24h): 30 runs × 30 sec = 900 sec/mo
  - Compliance sync (4h): 180 runs × 30 sec = 5,400 sec/mo
  - Resource sync (1h): 720 runs × 30 sec = 21,600 sec/mo
  - Identity sync (24h): 30 runs × 30 sec = 900 sec/mo
- **Total estimated: ~35,000 vCPU-seconds/month (19% of free grant)**

**Azure SQL Free Offer Usage:**
- 100,000 vCore-seconds = ~27.8 hours of continuous 1 vCore
- With serverless auto-pause, only consumes during active queries
- Est. 1,000 queries/day × 0.05 sec avg = 50 sec/day = 1,500 vCore-sec/mo
- **Only 1.5% of free allowance used**
- 32GB storage limit vs. 6.25MB actual = 0.02% utilization

### Multi-Dimensional Assessment

| Dimension | Rating | Notes |
|-----------|--------|-------|
| **Cost** | ⭐⭐⭐⭐⭐ | Near-zero ongoing cost |
| **Security** | ⭐⭐⭐⭐ | Managed platform, Azure AD auth works, Key Vault supported |
| **Complexity** | ⭐⭐⭐ | Moderate migration effort from App Service |
| **Stability** | ⭐⭐⭐⭐ | Container Apps GA since 2023, production-ready |
| **Performance** | ⭐⭐⭐ | Cold starts 1-3 sec (scale-to-zero); SQL cold start 30-60 sec after auto-pause |
| **Maintenance** | ⭐⭐⭐⭐ | Managed platform, less infra to manage |
| **Compatibility** | ⭐⭐⭐⭐ | Docker containers work as-is, but APScheduler needs rearchitecture |

### Critical Caveats

1. **Cold Starts**: Scale-to-zero means 1-3 second startup on first request after idle period
2. **APScheduler**: Background scheduler won't work with scale-to-zero; must be replaced with:
   - Container Apps Jobs (scheduled/cron) — recommended
   - Azure Functions timer triggers
   - Or set min replicas = 1 (adds ~$2-5/mo idle cost)
3. **SQL Serverless Cold Start**: Auto-paused SQL database takes 30-60 seconds to resume
   - Mitigation: Configure auto-pause delay to 1 hour (reduces cold starts)
   - Or keep min vCores = 0.5 (adds small cost but stays within free tier)
4. **Free Tier Limits**: If workload grows beyond free grants, costs increase linearly
   - At 2× current usage: still within free grants
   - At 10× current usage: ~$5-8/mo overflow

---

## Architecture Option 2: Optimized Current Stack (Quick Wins)

### Cost Breakdown: $15-18/mo

| Component | Current | Optimized | Savings |
|-----------|---------|-----------|---------|
| App Service B1 (prod) | $13.14 | $13.14 | $0 |
| Azure SQL S0 (prod) | $15.00 | **$0 (free tier)** | $15.00 |
| ACR Standard | $5.00 | **$0 (GHCR)** | $5.00 |
| Key Vault | $0.03 | $0.03 | $0 |
| Storage/Bandwidth | $2.00 | $2.00 | $0 |
| **Staging (all)** | **$38.17** | **$0 (eliminated)** | **$38.17** |
| **TOTAL** | **$73.34** | **$15.17** | **$58.17** |

### Staging Elimination Strategy

| Current Staging Need | Alternative |
|---------------------|------------|
| Pre-deploy testing | GitHub Actions CI + Docker Compose local testing |
| Integration testing | Ephemeral Container Apps job (spin up, test, destroy) |
| UAT | Feature flags in prod + restricted access |
| Emergency rollback env | App Service deployment slots (free on B1+) |

### Multi-Dimensional Assessment

| Dimension | Rating | Notes |
|-----------|--------|-------|
| **Cost** | ⭐⭐⭐⭐ | 75% savings with minimal changes |
| **Security** | ⭐⭐⭐⭐⭐ | Same security model, no changes needed |
| **Complexity** | ⭐⭐⭐⭐⭐ | Minimal changes — swap DB, swap registry, delete staging |
| **Stability** | ⭐⭐⭐⭐⭐ | Same App Service B1, battle-tested |
| **Performance** | ⭐⭐⭐⭐ | No cold starts, always-on App Service; SQL free tier is serverless (cold start possible) |
| **Maintenance** | ⭐⭐⭐⭐ | Slightly less infra to manage (no staging) |
| **Compatibility** | ⭐⭐⭐⭐⭐ | Everything works as-is with minimal config changes |

### Implementation Risk: LOW

- SQL free tier migration: Create new free DB → migrate schema + data → update connection string
- ACR → GHCR: Update GitHub Actions to push to GHCR, update App Service to pull from GHCR
- Staging deletion: Straightforward resource group deletion

---

## Architecture Option 3: VPS (Hetzner/DigitalOcean)

### Cost Breakdown: $4-6/mo

| Provider | Plan | Specs | Monthly |
|----------|------|-------|---------|
| Hetzner CX22 | Shared | 2 vCPU, 4GB RAM, 40GB SSD | ~€4.51 (~$5) |
| DigitalOcean Basic | Regular | 1 vCPU, 1GB RAM, 25GB SSD | $6.00 |
| DigitalOcean Basic | Regular | 1 vCPU, 2GB RAM, 50GB SSD | $12.00 |

**Chosen option: Hetzner CX22 at ~$5/mo**
- Run Docker Compose (same as current)
- SQLite instead of Azure SQL (already supported in code)
- No ACR needed (build and run locally on VPS)

### Multi-Dimensional Assessment

| Dimension | Rating | Notes |
|-----------|--------|-------|
| **Cost** | ⭐⭐⭐⭐⭐ | $5/mo for more compute than B1 |
| **Security** | ⭐⭐⭐ | Self-managed — must handle OS updates, firewall, SSL, backups |
| **Complexity** | ⭐⭐⭐ | Docker Compose works, but need to set up everything else |
| **Stability** | ⭐⭐⭐ | No managed failover, single point of failure |
| **Performance** | ⭐⭐⭐⭐⭐ | More resources than B1, no cold starts, no shared compute |
| **Maintenance** | ⭐⭐ | OS patches, Docker updates, SSL renewal, backup management |
| **Compatibility** | ⭐⭐⭐ | Azure SDK works from anywhere, but Azure AD redirect URIs need updating; Lighthouse still works |

### Key Concerns

1. **Azure AD Integration**: OAuth redirect URIs must point to new hostname
2. **SSL/TLS**: Must set up Let's Encrypt or similar (not Azure-managed)
3. **Backups**: Manual or scripted backup of SQLite database
4. **Monitoring**: No App Insights; need to set up alternatives (Uptime Kuma, etc.)
5. **Compliance**: May not meet enterprise compliance requirements for managed infrastructure
6. **Single Point of Failure**: No automatic failover capability

---

## Architecture Option 4: Azure Functions Consumption

### Cost Breakdown: $1-3/mo

| Component | Cost | Notes |
|-----------|------|-------|
| Functions Consumption | $0 | 1M executions + 400K GB-s free/mo |
| Storage Account | $1-2 | Required for Functions runtime |
| Azure SQL Free Tier | $0 | Same as other options |
| **TOTAL** | **$1-3** | |

### Why This Is NOT Recommended

| Issue | Impact |
|-------|--------|
| **Architecture Mismatch** | FastAPI + HTMX SSR doesn't fit Functions model |
| **Massive Rearchitecture** | Every route becomes a separate Function |
| **Cold Starts** | 5-10 second cold starts on Python Functions |
| **Session Management** | Stateless Functions need external session store |
| **APScheduler** | Must be fully replaced with Durable Functions |
| **HTMX/SSR** | Server-side rendering requires request/response patterns that Functions handle poorly |
| **Development Experience** | Dramatically different local dev workflow |

**Verdict: Maximum savings but prohibitive engineering cost for this app architecture.**

---

## Architecture Option 5: Azure Static Web Apps + Functions API

### Cost Breakdown: $0-9/mo

| Component | Cost | Notes |
|-----------|------|-------|
| Static Web Apps (Free) | $0 | 100GB bandwidth, 0.25GB storage |
| Managed Functions API | Included | Built-in API via Functions |
| Azure SQL Free Tier | $0 | Same as other options |
| **TOTAL** | **$0-9** | Free tier if sufficient, $9 for Standard |

### Why This Is NOT Recommended

| Issue | Impact |
|-------|--------|
| **HTMX/SSR Architecture** | Static Web Apps designed for SPAs, not SSR |
| **0.25GB Deployment Limit** | Python + dependencies exceed this easily |
| **No Docker Support** | Free tier doesn't support custom containers |
| **API Limitations** | Managed Functions API has routing limitations |
| **Session State** | No built-in session management |

**Verdict: Architecture fundamentally incompatible with FastAPI + HTMX SSR.**

---

## Architecture Option 6: Alternative Clouds

### AWS Equivalent

| Component | Service | Monthly |
|-----------|---------|---------|
| Compute | App Runner (scale-to-zero) | $7-10 |
| Database | RDS t4g.micro | $12-15 |
| Container Registry | ECR (500MB free) | $0-1 |
| **TOTAL** | | **$19-26** |

Alternative with DynamoDB free tier: $7-11/mo (but requires schema redesign)

### GCP Equivalent

| Component | Service | Monthly |
|-----------|---------|---------|
| Compute | Cloud Run (scale-to-zero) | $0 (free tier) |
| Database | Cloud SQL (micro) | $7-10 |
| Container Registry | Artifact Registry | $0-1 |
| **TOTAL** | | **$7-11** |

Alternative with Firestore free tier (1GB): $0-1/mo (but requires NoSQL redesign)

### Comparison Summary

| Cloud | Best-Case Monthly | Feasibility | Migration Effort |
|-------|-------------------|-------------|------------------|
| **Azure (optimized)** | **$0-5** | High | Low-Medium |
| GCP Cloud Run | $0-11 | Medium | High |
| AWS App Runner | $7-26 | Medium | High |
| Hetzner VPS | $5 | High | Medium |
| DigitalOcean VPS | $6 | High | Medium |

---

## Reserved Instances & Savings Plans Analysis

### App Service B1 Reserved Capacity

**Not available.** The Basic tier does not support savings plans or reserved instances.

> "Additional Azure savings such as savings plan and reserved instances are not available with this plan."
> — Azure App Service Pricing Page (verified 2026-03-27)

To get reserved pricing, you'd need to upgrade to Premium v3:
- P0v3 (1 vCPU, 4GB): $62.05/mo PAYG → $25.56/mo (3yr reserved, 59% savings)
- But $25.56 > $13.14 B1, so **reserved P0v3 is more expensive than current B1**

### Azure SQL Reserved Capacity

Available for vCore model (which is what the free tier uses):
- Not relevant since free tier covers the workload entirely
- If exceeding free tier: General Purpose 2 vCore ~$148/mo → $89/mo (1yr reserved)
- At this scale, reserved SQL makes no sense

### Verdict

**Reserved instances are NOT worth it at this scale.** The workload is too small to benefit from reserved capacity, and the free tiers are more than sufficient.

---

## Staging Environment Deep Dive

### Current Staging Cost: $38.17/mo (52% of total)

| Component | Monthly | % of Staging |
|-----------|---------|-------------|
| App Service B1 | $13.14 | 34% |
| SQL S0 | $15.00 | 39% |
| Storage GRS | $5.00 | 13% |
| Log Analytics + App Insights | $5.00 | 13% |
| Key Vault | $0.03 | 0.1% |

### Alternatives to Dedicated Staging

| Alternative | Monthly Cost | Trade-offs |
|-------------|-------------|------------|
| **Eliminate entirely** | $0 | Rely on CI/CD testing + local Docker |
| **On-demand staging** | $0-5 | Spin up Container Apps for UAT, destroy after |
| **Shared prod resources** | $0 | Feature flags + role-based access |
| **Dev/Test subscription** | ~$20 | ~47% savings on some services |
| **App Service deployment slots** | $0 (on B1+) | Built-in A/B deployment |

### Dev/Test Subscription Pricing

Azure Dev/Test pricing offers discounts on specific services:
- App Service: Same price (no dev/test discount for Linux Basic)
- SQL Database: Dev/test pricing available (up to 55% off compute)
- VMs: Up to 55% off Windows VMs (not relevant for Linux)

**Not significant enough to justify maintaining a separate staging environment.**

### Recommended Staging Strategy

1. **Delete the staging resource group entirely** (saves $38.17/mo)
2. **Use GitHub Actions CI** for automated testing before deploy
3. **Use App Service deployment slots** for blue-green deployments (free on B1+)
4. **For UAT**: Deploy to an ephemeral Container Apps environment, run tests, destroy
   - Cost: $0 (within free grants for brief testing sessions)

---

## Free Tier Maximization Summary

| Azure Service | Free Tier | This Workload Needs | Sufficient? |
|---------------|-----------|-------------------|-------------|
| **Azure SQL Database** | 100K vCore-sec/mo, 32GB storage | ~1,500 vCore-sec, 6.25MB | ✅ Yes (1.5% used) |
| **Container Apps** | 180K vCPU-sec, 360K GiB-sec, 2M requests | ~35K vCPU-sec, ~100 requests/day | ✅ Yes (19% used) |
| **Azure Functions** | 1M executions, 400K GB-s | N/A (not recommended) | ✅ Yes |
| **Cosmos DB** | 1,000 RU/s, 25GB | N/A (SQL preferred) | ✅ Yes |
| **Key Vault** | 10K transactions free | ~100 transactions/mo | ✅ Yes |
| **GHCR** | Currently free for containers | 1 Docker image | ✅ Yes |
| **App Service F1** | Shared, 60 CPU min/day, 1GB | Docker container | ❌ No Docker support |
| **Static Web Apps** | 0.25GB storage, 100GB BW | FastAPI+HTMX SSR | ❌ Wrong architecture |

### Theoretical Cost Floor

**$0/month is achievable** using Container Apps consumption (scale-to-zero) + Azure SQL free tier + GHCR + Key Vault.

Realistic floor with minimal storage/networking: **$0-2/month**.
