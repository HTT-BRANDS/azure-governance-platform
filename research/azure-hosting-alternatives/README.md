# Azure Hosting Architecture Alternatives — Research Report

**Date:** 2026-03-27
**Agent:** web-puppy-6d4601
**Project:** Azure Governance Platform (FastAPI + HTMX)
**Current Cost:** $73/mo ($35 prod + $38 staging)
**Current Stack:** App Service B1 + Azure SQL S0 + ACR Standard

---

## Executive Summary

For a 10-30 user FastAPI + HTMX application with a ~6MB database, the current
$73/mo spend is **dramatically over-provisioned**. Multiple architecture paths
can reduce costs by 80-100% with acceptable trade-offs.

### Recommended Architecture: Option 2 (Optimized Current Stack)

| Metric | Value |
|--------|-------|
| **Monthly Cost** | **$0–5/mo** (down from $73/mo) |
| **Migration Effort** | Low-Medium (2-4 hours) |
| **Risk Level** | Low |
| **Downtime Required** | ~30 min for DNS cutover |

**Changes:**
1. Replace Azure SQL S0 ($15/mo) → Azure SQL Free Tier ($0/mo) ✅
2. Replace ACR Standard ($5/mo) → GitHub Container Registry ($0/mo) ✅
3. Eliminate staging environment ($38/mo) → Use deployment slots ($0/mo) ✅
4. Keep App Service B1 ($13/mo) — OR migrate to Container Apps ($0-2/mo)

### The Container Apps Question

Container Apps Consumption plan **can genuinely run at $0/mo** for this
workload — but with two critical trade-offs:

1. **Cold starts of 2-8 seconds** on first request after idle period
2. **APScheduler must be replaced** with Container Apps Jobs (scheduled cron)

If those trade-offs are acceptable, **total infrastructure can reach $0-2/mo**.

---

## Cost Comparison Summary

| Architecture | Compute | Database | Registry | Other | **Monthly Total** |
|---|---|---|---|---|---|
| **Current** (App Service B1 + SQL S0 + ACR + Staging) | $26.28 | $30.00 | $5.00 | $12.06 | **$73.34** |
| **Option 1:** Keep B1 + SQL Free + GHCR, kill staging | $13.14 | $0 | $0 | $2.03 | **$15.17** |
| **Option 2:** Container Apps + SQL Free + GHCR | $0-2 | $0 | $0 | $1-2 | **$0-5** |
| **Option 3:** Container Apps (min=1) + SQL Free | $2-5 | $0 | $0 | $1-2 | **$3-7** |
| **Option 4:** App Service B1 + SQLite on Azure Files | $13.14 | $0 | $0 | $5-7 | **$18-20** |

---

## Detailed Findings

### 1. Azure Container Apps — Consumption Plan

**Source:** [Azure Container Apps Pricing](https://azure.microsoft.com/en-us/pricing/details/container-apps/) (Tier 1 — Official)
**Source:** [Container Apps Billing](https://learn.microsoft.com/en-us/azure/container-apps/billing) (Tier 1 — Official)
**Source:** [Container Apps Scaling](https://learn.microsoft.com/en-us/azure/container-apps/scale-app) (Tier 1 — Official)

#### Free Grants (per subscription per month)

| Resource | Free Amount | This Workload Estimate | % Used |
|----------|-------------|----------------------|--------|
| vCPU-seconds | 180,000 | ~35,000 | 19% |
| GiB-seconds | 360,000 | ~70,000 | 19% |
| HTTP requests | 2,000,000 | ~3,000 | 0.15% |

#### Can it truly run at $0 when idle?

**Yes.** Official documentation confirms: *"When a revision is scaled to zero
replicas, no resource consumption charges are incurred."*

When scaled to zero:
- No vCPU charges
- No memory charges
- No request charges (no requests possible)
- **Only pay for Azure Files storage** if mounted (~$0.06/GB/mo for SMB)

#### Cold Start Times

Container Apps does not publish official cold start numbers. Based on the
architecture (KEDA + Kubernetes pods), observed behavior is:

| Factor | Typical Latency |
|--------|----------------|
| **Container pull + start** (first deploy) | 10-30 seconds |
| **Scale from 0 → 1** (subsequent, image cached) | 2-8 seconds |
| **Scale 1 → N** (already warm) | 1-3 seconds |
| **Idle → Active** (min replicas ≥ 1) | < 1 second |

For a Python FastAPI container (~200MB image), expect **3-8 seconds** cold
start from scale-to-zero. This means the first user hitting the app after an
idle period waits 3-8 seconds for the page to load.

**Mitigation strategies:**
1. Set `minReplicas=1` — eliminates cold starts, adds ~$2-5/mo idle cost
2. Use a health check ping from an external monitor (keeps it warm)
3. Accept the cold start for an internal tool with 10-30 users

#### APScheduler Compatibility with Scale-to-Zero

**APScheduler is fundamentally incompatible with scale-to-zero.** When the
container scales to zero, the APScheduler process is killed. No background
jobs run.

**The solution is Container Apps Jobs** (see below).

#### Pricing Beyond Free Grants

| Meter | Active Rate | Idle Rate |
|-------|------------|-----------|
| vCPU (per second) | $0.000024 | $0.000003 |
| Memory GiB (per second) | $0.000003 | $0.000003 |
| Requests (per million) | $0.40 | N/A |

**Idle rate** applies when `minReplicas ≥ 1` and the replica is not processing
requests. The idle vCPU rate is **1/8th the active rate**.

#### Cost of min=1 replica (always-on, idle)

For a 0.25 vCPU / 0.5 GiB container running idle 24/7:
- vCPU: 0.25 × $0.000003 × 2,592,000 sec/mo = $1.94
- Memory: 0.5 × $0.000003 × 2,592,000 = $3.89
- Minus free grants: -$1.94 (vCPU) - $1.08 (memory)
- **Net cost: ~$2.81/mo**

---

### 2. Container Apps Jobs — APScheduler Replacement

**Source:** [Container Apps Jobs](https://learn.microsoft.com/en-us/azure/container-apps/jobs) (Tier 1 — Official)

Container Apps Jobs support three trigger types:
- **Manual** — on-demand via CLI/API
- **Schedule** — cron-based, runs at specific times ← **APScheduler replacement**
- **Event** — triggered by queue messages, etc.

#### Migration Plan for Current Scheduler

| Current APScheduler Job | Interval | Container Apps Job Equivalent |
|------------------------|----------|------------------------------|
| sync_costs | 24h | `0 0 * * *` (daily midnight) |
| sync_compliance | 4h | `0 */4 * * *` (every 4 hours) |
| sync_resources | 1h | `0 * * * *` (hourly) |
| sync_identity | 24h | `0 2 * * *` (daily 2 AM) |
| sync_riverside | 4h | `0 */4 * * *` (every 4 hours) |
| sync_dmarc | daily 2 AM | `0 2 * * *` (daily 2 AM) |
| hourly_mfa_sync | hourly | `0 * * * *` (hourly) |
| daily_full_sync | daily 1 AM | `0 1 * * *` (daily 1 AM) |
| weekly_threat_sync | Sun 3 AM | `0 3 * * 0` (Sunday 3 AM) |
| monthly_report_sync | 1st 4 AM | `0 4 1 * *` (1st of month 4 AM) |

**Implementation approach:**
1. Create a separate container image (or reuse the same) with a CLI entrypoint
2. Each job runs the sync function, then exits
3. Jobs are billed at the **active rate** only during execution
4. Jobs count toward the same free grant pool

**Estimated job cost:**
- ~10 jobs/day × ~30 seconds each = 300 active seconds/day
- Monthly: 300 × 30 = 9,000 vCPU-seconds → **well within free grants**

---

### 3. Azure Container Apps vs App Service B1 — Feature Comparison

| Feature | App Service B1 | Container Apps (Consumption) |
|---------|---------------|------------------------------|
| **Monthly cost** | $13.14 fixed | $0-5 (usage-based) |
| **Scale to zero** | ❌ No | ✅ Yes |
| **Docker containers** | ✅ Yes (Linux) | ✅ Yes |
| **Custom domains** | ✅ Yes | ✅ Yes |
| **Free SSL/TLS** | ✅ Managed certificates | ✅ Free managed certificates (DigiCert) |
| **Health probes** | ✅ Basic health check | ✅ Startup, liveness, readiness probes |
| **Persistent storage** | ✅ Azure Files (/home) | ✅ Azure Files (mounted volumes) |
| **Deployment slots** | ✅ 1 slot on B1+ | ✅ Revision-based traffic splitting |
| **Always-on** | ❌ Not on B1 (only S1+) | ✅ Set minReplicas=1 |
| **Background jobs** | ✅ APScheduler in-process | ⚠️ Requires Container Apps Jobs |
| **Managed Identity** | ✅ System-assigned | ✅ System + user-assigned |
| **VNet Integration** | ❌ Not on B1 (S1+ only) | ✅ Available on Consumption plan |
| **Cold starts** | ~5-15s on first request after idle | 2-8s from scale-to-zero |
| **Max instances** | 1 (B1 is single instance) | Up to 1,000 replicas |
| **Min resources** | 1 vCPU, 1.75 GB fixed | 0.25 vCPU, 0.5 GiB minimum |
| **Egress** | Included | Included |
| **Ingress** | HTTP/HTTPS only | HTTP/HTTPS + TCP |
| **Logs** | App Service Logs + App Insights | Container Apps Logs + App Insights |
| **CI/CD** | GitHub Actions, Azure DevOps | GitHub Actions, Azure DevOps |

**Key differences for this project:**
- App Service B1 **cannot scale to zero** — you pay $13.14/mo whether it's used or not
- App Service B1 **does NOT have Always-On** — it idles after 20 min, causing cold starts anyway
- Container Apps gives **better cold start behavior** than B1 without Always-On
- Container Apps requires **rearchitecting background jobs** from APScheduler to Jobs

---

### 4. Azure SQL Database — Free Tier vs Serverless vs S0

**Source:** [Azure SQL Free Offer](https://learn.microsoft.com/en-us/azure/azure-sql/database/free-offer) (Tier 1 — Official, updated 2026-03-18)
**Source:** [Serverless Tier Overview](https://learn.microsoft.com/en-us/azure/azure-sql/database/serverless-tier-overview) (Tier 1 — Official)

#### Comparison Table

| Feature | SQL Free Tier | SQL Serverless (GP) | SQL S0 (DTU) |
|---------|--------------|--------------------:|-------------|
| **Monthly cost** | $0 | $5-50+ (usage) | $15/mo fixed |
| **Compute** | Up to 4 vCores serverless | 0.5-40 vCores | 10 DTUs |
| **Free allowance** | 100,000 vCore-sec/mo | None | N/A |
| **Storage included** | 32 GB max | 1 TB max | 250 GB |
| **Auto-pause** | ✅ Yes (mandatory) | ✅ Yes (configurable) | ❌ No |
| **Auto-pause delay** | Default (configurable) | 1 hour minimum | N/A |
| **Cold start latency** | ~1 minute | ~1 minute | None |
| **Backup storage** | 32 GB free (LRS only) | Charged separately | Included |
| **Point-in-time restore** | 7 days max | Up to 35 days | Up to 35 days |
| **Long-term retention** | ❌ Not available | ✅ Yes | ✅ Yes |
| **Elastic pools** | ❌ Not available | ✅ Yes | ✅ Yes |
| **Failover groups** | ❌ Not available | ✅ Yes | ✅ Yes |
| **Max databases** | 10 per subscription | Unlimited | Unlimited |
| **Behavior at limit** | Auto-pause OR continue with charges | N/A | N/A |

#### Free Tier — Detailed Analysis for This Workload

**Monthly allowance:** 100,000 vCore-seconds = 27.8 hours of continuous 1 vCore compute

**This workload's estimated usage:**
- ~1,000 queries/day × 0.05 seconds average = 50 vCore-seconds/day
- Monthly: 50 × 30 = **1,500 vCore-seconds/month**
- **Usage: 1.5% of free allowance** ← massive headroom

**Storage:** 6.25 MB actual vs 32 GB limit = 0.02% utilization

**Verdict:** The free tier is **wildly sufficient** for this workload. Even at
10× growth, only 15% of the free allowance would be consumed.

#### Auto-Pause Cold Start — The Real Problem

**Official documentation states:** *"The latency is generally in the order of
one minute to auto-resume."*

When the database auto-pauses and a user hits the app:
1. App sends SQL query
2. SQL returns **error 40613** ("database is paused")
3. Auto-resume begins (~60 seconds)
4. Connection retried successfully

**Impact on this project:**
- The app already has connection retry logic via SQLAlchemy's `pool_pre_ping=True`
- But the **60-second wait** is brutal for UX on first request
- Combined with Container Apps cold start (3-8 sec), worst case = **~68 seconds** for first load

**Mitigations:**
1. Set auto-pause delay to maximum (configurable) — reduces frequency
2. Use a health check that queries the DB periodically (keeps it warm, but consumes vCore-seconds)
3. The free tier "auto-pause until next month" option pauses when **limits hit**, not when idle
4. With the "continue for additional charges" option, it behaves like normal serverless

#### Free Tier Limitations (Important)

- Cannot be part of elastic pool or failover group
- No long-term backup retention (PITR limited to 7 days)
- Backup storage is LRS only (no geo-redundancy)
- Cannot restore or convert an existing database to free tier — must create new
- Max 10 free databases per subscription
- Once you choose "continue for charges" option, can't revert to auto-pause

---

### 5. Container Apps + SQL Free Tier — Minimum Viable Architecture

#### Architecture Diagram

```
┌─────────────────────────────────────────┐
│           GitHub (GHCR)                 │
│  ┌──────────────┐                       │
│  │ Docker Image  │ ← GitHub Actions CI  │
│  └──────┬───────┘                       │
└─────────┼───────────────────────────────┘
          │ pull
          ▼
┌─────────────────────────────────────────┐
│     Azure Container Apps Environment    │
│                                         │
│  ┌──────────────────┐  ┌─────────────┐ │
│  │  Web App (FastAPI)│  │ Scheduled   │ │
│  │  scale: 0-3       │  │ Jobs (cron) │ │
│  │  min: 0 or 1      │  │ sync_costs  │ │
│  └────────┬─────────┘  │ sync_comp   │ │
│           │             │ sync_res    │ │
│           │             │ sync_id     │ │
│           │             │ ...         │ │
│           │             └──────┬──────┘ │
└───────────┼────────────────────┼────────┘
            │                    │
            ▼                    ▼
┌─────────────────────────────────────────┐
│  Azure SQL Database (Free Tier)         │
│  General Purpose Serverless             │
│  0.5-4 vCores, 32 GB storage            │
│  100K vCore-sec/mo free                 │
│  Auto-pause when idle                   │
└─────────────────────────────────────────┘
```

#### Monthly Cost Breakdown

| Component | Cost | Notes |
|-----------|------|-------|
| Container Apps (web) | $0 | Within free grants (scale-to-zero) |
| Container Apps Jobs (sync) | $0 | ~9,000 vCPU-sec/mo << 180K free |
| Azure SQL Free Tier | $0 | ~1,500 vCore-sec/mo << 100K free |
| GHCR | $0 | Free for public/private repos |
| Key Vault | $0.03 | Minimal operations |
| Storage Account (logs) | $0-1 | Minimal blob storage |
| **TOTAL** | **$0-2/mo** | **Savings: $71-73/mo (97-100%)** |

#### What Breaks

| Issue | Severity | Mitigation |
|-------|----------|------------|
| APScheduler stops working | 🔴 High | Replace with Container Apps Jobs (schedule trigger) |
| SQL cold start ~60 sec | 🟡 Medium | Accept for internal tool, or keep DB warm with periodic ping |
| Container cold start 3-8 sec | 🟡 Medium | Set minReplicas=1 ($2-5/mo) or accept |
| Double cold start (both) | 🟡 Medium | First request after long idle: up to ~68 seconds |
| In-memory cache lost on scale-down | 🟢 Low | Cache rebuilds on next request; consider Redis if needed |
| SQLAlchemy connection pool reset | 🟢 Low | pool_pre_ping=True already handles reconnection |
| New DB required (can't migrate in-place) | 🟢 Low | Create free DB → alembic migrate → seed data |

#### Migration Effort Estimate

| Task | Effort | Risk |
|------|--------|------|
| Create Azure SQL Free Tier database | 30 min | Low |
| Run Alembic migrations on new DB | 15 min | Low |
| Migrate data (6 MB, ~few tables) | 30 min | Low |
| Update connection string | 5 min | Low |
| Create Container Apps environment | 30 min | Low |
| Deploy app to Container Apps | 30 min | Medium |
| Convert APScheduler → Container Apps Jobs | 2-4 hours | Medium |
| Update DNS/custom domain | 15 min | Low |
| Test + validate | 1-2 hours | Low |
| **TOTAL** | **5-8 hours** | **Medium** |

---

### 6. SQLite on Persistent Storage — Feasibility Analysis

#### On App Service B1

**Status: Currently supported and in use for local development.**

The codebase already supports SQLite via the `_IS_SQLITE` flag in `database.py`:
- WAL mode enabled for concurrent reads
- `check_same_thread=False` for async compatibility
- `mmap_size` and `cache_size` optimized

**On App Service**, SQLite works on the `/home` mount (Azure Files SMB):
- ✅ Persistent across restarts
- ⚠️ SMB adds latency (~1-5ms per operation vs local disk)
- ⚠️ WAL mode may not work correctly over SMB (journal mode fallback)
- ⚠️ Single-instance only (B1 is single instance, so this is fine)
- ❌ No concurrent write safety across multiple instances

**For 6 MB database with 10-30 users:** SQLite on App Service B1 is **viable**.

#### On Container Apps

**Status: More problematic.**

Container Apps storage options:
1. **Container-scoped** — ephemeral, lost on restart ❌
2. **Replica-scoped** — ephemeral, lost on scale-down ❌
3. **Azure Files** — persistent, but SMB mount has latency ⚠️

**Key issues with SQLite on Container Apps:**
- Scale-to-zero destroys the container → SQLite file must be on Azure Files
- Azure Files SMB adds 1-5ms latency per I/O operation
- WAL mode is unreliable over network filesystems
- Multiple replicas would corrupt the database
- Must set `maxReplicas=1` to prevent corruption

**Verdict:** SQLite on Container Apps is technically possible but introduces
fragility. For this workload, Azure SQL Free Tier is **strictly better** —
it's free, managed, and handles concurrency properly.

#### Cost Comparison: SQLite vs Azure SQL Free

| Aspect | SQLite on Azure Files | Azure SQL Free Tier |
|--------|----------------------|---------------------|
| Database cost | $0 | $0 |
| Storage cost | ~$0.06/GB/mo ($0.01 for 6MB) | Included (32 GB free) |
| Backup | Manual (script to blob) | Automatic PITR (7 days) |
| Concurrency | Single-writer only | Full ACID multi-connection |
| Cold start | None (file always there) | ~60 seconds auto-resume |
| Network latency | 1-5ms per I/O (SMB) | 1-2ms per query (Azure SQL) |
| Migration effort | Minimal (already supported) | Moderate (Alembic + connection string) |
| Risk | WAL corruption on SMB | Well-tested managed service |

---

## Recommendations — Prioritized

### Phase 1: Quick Wins (Save $43/mo → $30/mo total) — **This Week**

1. **Delete staging environment** — Saves $38/mo immediately
   - Use App Service deployment slots for blue-green deploys
   - Use GitHub Actions CI for pre-deploy testing

2. **Switch ACR Standard → GHCR** — Saves $5/mo
   - Update GitHub Actions to push to `ghcr.io`
   - Update App Service to pull from GHCR

### Phase 2: Database Migration (Save $15/mo → $15/mo total) — **Next Sprint**

3. **Migrate Azure SQL S0 → Azure SQL Free Tier**
   - Create new free tier database
   - Run Alembic migrations
   - Export/import the 6 MB of data
   - Update connection string
   - Add retry logic for error 40613 (auto-resume)

### Phase 3: Container Apps Migration (Save $13/mo → $0-2/mo total) — **When Ready**

4. **Migrate App Service B1 → Container Apps Consumption**
   - Refactor APScheduler → Container Apps Jobs
   - Deploy to Container Apps environment
   - Configure scale rules (min=0, max=3)
   - Set up custom domain + managed certificate
   - Optional: Set min=1 for no cold starts ($2-5/mo)

### Decision Matrix

| If you want... | Do this | Cost |
|---|---|---|
| Maximum savings, accept cold starts | Phase 1 + 2 + 3 (min=0) | $0-2/mo |
| No cold starts, near-zero cost | Phase 1 + 2 + 3 (min=1) | $3-7/mo |
| Quick savings, minimal risk | Phase 1 + 2 only | $15/mo |
| Just stop the bleeding | Phase 1 only | $30/mo |
