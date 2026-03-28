# Multi-Dimensional Analysis — Azure Hosting Alternatives

## Analysis Framework

Each architecture option is evaluated across 7 dimensions on a 1-5 scale,
weighted for this specific project context (internal governance tool,
10-30 users, 6 MB database, FastAPI + HTMX).

---

## Option A: Current Architecture (App Service B1 + SQL S0)

**Monthly cost: $73/mo (with staging) / $35/mo (prod only)**

| Dimension | Score | Weight | Analysis |
|-----------|-------|--------|----------|
| **Security** | 4/5 | 15% | Managed platform, Key Vault integration, OIDC, Managed Identity. No VNet on B1. |
| **Cost** | 2/5 | 25% | $73/mo for 10-30 users and 6 MB database is extremely over-provisioned. |
| **Implementation** | 5/5 | 10% | Already deployed and working. Zero implementation effort. |
| **Stability** | 5/5 | 15% | Battle-tested, mature platform. No cold starts with Always-On (but B1 lacks Always-On). |
| **Optimization** | 2/5 | 10% | B1 provides 1 core/1.75 GB fixed — can't scale down. S0 at 10 DTU for a 6 MB database is wasteful. |
| **Compatibility** | 5/5 | 15% | Perfect compatibility — Docker, ODBC, APScheduler all work as-is. |
| **Maintenance** | 4/5 | 10% | Managed platform. Must maintain staging separately. |
| **Weighted Score** | | | **3.55/5** |

**Key insight:** B1 does NOT have Always-On (only S1+ does). The app idles
after 20 minutes and has cold starts anyway — meaning you pay $13/mo for a
service that still gives you cold starts.

---

## Option B: Optimized Current Stack (B1 + SQL Free + GHCR, no staging)

**Monthly cost: $15/mo**

| Dimension | Score | Weight | Analysis |
|-----------|-------|--------|----------|
| **Security** | 4/5 | 15% | Same as current. Free tier SQL has same security features. |
| **Cost** | 4/5 | 25% | 79% savings. $15/mo is reasonable for the value delivered. |
| **Implementation** | 4/5 | 10% | Low effort — create new DB, migrate data, update connection string, delete staging. |
| **Stability** | 4/5 | 15% | SQL Free Tier is serverless — auto-pauses, ~60s cold start. App Service B1 unchanged. |
| **Optimization** | 3/5 | 10% | Still paying $13/mo for B1 that sits idle most of the time. |
| **Compatibility** | 5/5 | 15% | Everything works as-is. APScheduler keeps running. Only change is DB connection string. |
| **Maintenance** | 5/5 | 10% | Simpler — no staging to maintain. GHCR is lower maintenance than ACR. |
| **Weighted Score** | | | **4.10/5** |

**Best for:** Quick wins with minimal risk. Good stepping stone toward further optimization.

---

## Option C: Container Apps (scale-to-zero) + SQL Free Tier

**Monthly cost: $0-2/mo**

| Dimension | Score | Weight | Analysis |
|-----------|-------|--------|----------|
| **Security** | 4/5 | 15% | Same security model. Managed Identity, Key Vault, TLS certificates all supported. VNet available (bonus vs B1). |
| **Cost** | 5/5 | 25% | Near-zero cost. Free grants massively exceed this workload's needs. |
| **Implementation** | 2/5 | 10% | Significant rearchitecture: APScheduler → Jobs, new Bicep/IaC, deployment pipeline changes. |
| **Stability** | 3/5 | 15% | Double cold start risk (Container Apps 3-8s + SQL 60s). Acceptable for internal tool, not for customer-facing. |
| **Optimization** | 5/5 | 10% | Pay exactly for what you use. Scale to zero when idle. Perfect for bursty internal tools. |
| **Compatibility** | 3/5 | 15% | Docker works. APScheduler must be replaced. SQLAlchemy needs retry logic for 40613. |
| **Maintenance** | 4/5 | 10% | Managed platform. Container Apps Jobs are simpler than APScheduler (declarative vs imperative). |
| **Weighted Score** | | | **3.70/5** |

### Cold Start Deep Dive

**Worst case scenario (both app and DB cold):**

```
User clicks link
  └── DNS resolution                      ~50ms
      └── Container Apps scales 0→1       ~3-8 seconds
          └── FastAPI starts               ~1-2 seconds
              └── SQL query sent
                  └── SQL returns 40613    ~100ms
                      └── Auto-resume      ~60 seconds
                          └── Retry query  ~100ms
                              └── Render   ~200ms
                                  └── Total: ~65-72 seconds
```

**Typical case (DB warm, app cold):**
```
User clicks link
  └── Container Apps scales 0→1           ~3-8 seconds
      └── FastAPI starts                   ~1-2 seconds
          └── SQL query (DB already warm)  ~50ms
              └── Render                    ~200ms
                  └── Total: ~5-10 seconds
```

**Warm case (both warm, min=1):**
```
User clicks link
  └── Container already running           ~0ms
      └── SQL query                        ~50ms
          └── Render                        ~200ms
              └── Total: ~250ms
```

### APScheduler Migration Assessment

The current `app/core/scheduler.py` defines 10 scheduled jobs using
`AsyncIOScheduler` with `IntervalTrigger` and `CronTrigger`.

**Migration complexity: MEDIUM**

The actual sync functions are already well-separated:
- `app/core/sync/costs.py` → `sync_costs()`
- `app/core/sync/compliance.py` → `sync_compliance()`
- `app/core/sync/resources.py` → `sync_resources()`
- etc.

Each function is a standalone async function that:
1. Opens a database session
2. Calls Azure APIs
3. Writes results to the database
4. Closes the session

**To convert to Container Apps Jobs:**
1. Create a CLI entrypoint: `python -m app.jobs.run_sync --job=costs`
2. Each job creates a DB session, runs the sync, exits
3. Define 10 Container Apps Jobs with cron schedules
4. Remove `scheduler.py` entirely

**Key risk:** The Riverside sync functions use `sync_all_tenants()` which
imports from `app.services.riverside_sync`. This has dependencies on the
full app initialization. May need a lightweight "job mode" startup.

---

## Option D: Container Apps (min=1) + SQL Free Tier

**Monthly cost: $3-7/mo**

| Dimension | Score | Weight | Analysis |
|-----------|-------|--------|----------|
| **Security** | 4/5 | 15% | Same as Option C. |
| **Cost** | 5/5 | 25% | Still 90%+ savings. Idle rate ($0.000003/vCPU-sec) is very cheap. |
| **Implementation** | 2/5 | 10% | Same as Option C — still need APScheduler migration. |
| **Stability** | 4/5 | 15% | No container cold start (always warm). SQL cold start still possible but less frequent with periodic health checks. |
| **Optimization** | 4/5 | 10% | Slightly wasteful (paying idle for 0.25 vCPU 24/7) but trivial amount. |
| **Compatibility** | 3/5 | 15% | Same as Option C. |
| **Maintenance** | 4/5 | 10% | Same as Option C. |
| **Weighted Score** | | | **3.80/5** |

**This is the "Goldilocks" option** — near-zero cost but no cold starts for the web app.

---

## Option E: App Service B1 + SQLite on Azure Files

**Monthly cost: $18-20/mo**

| Dimension | Score | Weight | Analysis |
|-----------|-------|--------|----------|
| **Security** | 3/5 | 15% | No managed database security (encryption at rest handled by Azure Files, but no SQL-level security). |
| **Cost** | 3/5 | 25% | Saves $15/mo on SQL. But still paying $13/mo for B1 + $5/mo Azure Files. |
| **Implementation** | 4/5 | 10% | Codebase already supports SQLite. Just change DATABASE_URL and ensure /home mount works. |
| **Stability** | 3/5 | 15% | WAL mode unreliable over SMB. Single-instance only. No automatic backup. |
| **Optimization** | 3/5 | 10% | Eliminates SQL overhead but introduces SMB latency (1-5ms per I/O). |
| **Compatibility** | 4/5 | 15% | Already supported in code. WAL over SMB is the main risk. ODBC driver no longer needed. |
| **Maintenance** | 2/5 | 10% | Manual backups. No PITR. Must script SQLite backup to blob storage. Schema migrations via Alembic work but less tested for SQLite. |
| **Weighted Score** | | | **3.15/5** |

**Not recommended** when Azure SQL Free Tier exists at $0/mo with managed
backups, PITR, and proper concurrency.

---

## Weighted Score Summary

| Option | Cost | Security | Implement | Stability | Optimize | Compat | Maintain | **Score** |
|--------|------|----------|-----------|-----------|----------|--------|----------|-----------|
| **B: Optimized Current** | 4 | 4 | 4 | 4 | 3 | 5 | 5 | **4.10** |
| **D: CA min=1 + SQL Free** | 5 | 4 | 2 | 4 | 4 | 3 | 4 | **3.80** |
| **C: CA zero + SQL Free** | 5 | 4 | 2 | 3 | 5 | 3 | 4 | **3.70** |
| **A: Current** | 2 | 4 | 5 | 5 | 2 | 5 | 4 | **3.55** |
| **E: B1 + SQLite** | 3 | 3 | 4 | 3 | 3 | 4 | 2 | **3.15** |

---

## Recommended Path

### Immediate (This Week): Option B — $15/mo
1. Delete staging environment → save $38/mo
2. Switch ACR → GHCR → save $5/mo
3. Migrate SQL S0 → SQL Free Tier → save $15/mo

### Future (When convenient): Option D — $3-7/mo
4. Migrate App Service B1 → Container Apps (min=1) → save $13/mo
5. Replace APScheduler → Container Apps Jobs

### Why Option B first, then D:
- **Option B** captures 79% of the savings with ~2 hours of work and zero risk
- **Option D** captures the remaining 21% but requires 5-8 hours and APScheduler refactoring
- Doing B first gives immediate relief while planning the Container Apps migration properly
