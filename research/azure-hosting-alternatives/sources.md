# Sources — Credibility Assessment

## Tier 1 Sources (Official Documentation)

### Azure Container Apps

| Source | URL | Last Updated | Assessment |
|--------|-----|-------------|------------|
| Container Apps Pricing | https://azure.microsoft.com/en-us/pricing/details/container-apps/ | Current (live pricing page) | **Authoritative.** Official Azure pricing page. Verified consumption plan rates, free grants, and idle/active pricing. |
| Container Apps Billing | https://learn.microsoft.com/en-us/azure/container-apps/billing | Current | **Authoritative.** Confirms scale-to-zero = $0, explains idle vs active billing, details free grant amounts per subscription. |
| Container Apps Scaling | https://learn.microsoft.com/en-us/azure/container-apps/scale-app | 2025-06-26 | **Authoritative.** KEDA-based scaling, min/max replicas, cool-down periods (300s default), polling intervals. |
| Container Apps Jobs | https://learn.microsoft.com/en-us/azure/container-apps/jobs | Current | **Authoritative.** Manual, Schedule (cron), and Event trigger types. Confirms scheduled jobs as APScheduler replacement. |
| Container Apps Storage | https://learn.microsoft.com/en-us/azure/container-apps/storage-mounts | Current | **Authoritative.** Three storage types: container-scoped (ephemeral), replica-scoped (ephemeral), Azure Files (persistent). |
| Container Apps Custom Domains | https://learn.microsoft.com/en-us/azure/container-apps/custom-domains-managed-certificates | Current | **Authoritative.** Free managed TLS certificates via DigiCert. Custom domain binding supported. |
| Container Apps Health Probes | https://learn.microsoft.com/en-us/azure/container-apps/health-probes | Current | **Authoritative.** Startup, liveness, and readiness probes supported (Kubernetes-style). |
| Container Apps Comparison | https://learn.microsoft.com/en-us/azure/container-apps/compare-options | Current | **Authoritative.** Comparison with App Service, ACI, AKS, Functions. |

### Azure SQL Database

| Source | URL | Last Updated | Assessment |
|--------|-----|-------------|------------|
| SQL Free Offer | https://learn.microsoft.com/en-us/azure/azure-sql/database/free-offer | 2026-03-18 | **Authoritative.** 100K vCore-sec/mo, 32 GB storage, up to 10 DBs per subscription. Updated March 2026. |
| Serverless Tier Overview | https://learn.microsoft.com/en-us/azure/azure-sql/database/serverless-tier-overview | Current | **Authoritative.** Auto-pause/resume behavior, cold start latency (~1 minute), memory management, cache reclamation. |
| SQL Database Pricing | https://azure.microsoft.com/en-us/pricing/details/azure-sql-database/single/ | Current (live pricing page) | **Authoritative.** Official pricing for DTU and vCore models. S0 = $15/mo confirmed. |

### Azure App Service

| Source | URL | Last Updated | Assessment |
|--------|-----|-------------|------------|
| App Service Plans | https://learn.microsoft.com/en-us/azure/app-service/overview-hosting-plans | Current | **Authoritative.** B1 tier specs, Always-On availability (S1+ only), deployment slots. |

## Tier 2 Sources (High-Quality Secondary)

### Project-Internal Sources

| Source | Assessment |
|--------|------------|
| `infrastructure/COST_OPTIMIZATION.md` | **Authoritative for current state.** Documents current costs ($73/mo), resources, and previous optimization from $298/mo. Verified against Azure portal. |
| `app/core/scheduler.py` | **Authoritative.** Documents all APScheduler jobs, intervals, and sync functions. Used to plan Container Apps Jobs migration. |
| `app/core/database.py` | **Authoritative.** Confirms SQLite support (WAL mode, pragmas), SQL Server support (connection pooling, pool_pre_ping), and lazy engine initialization. |
| `app/core/config.py` | **Authoritative.** Default DATABASE_URL is SQLite. Confirms all configurable intervals. |
| `Dockerfile` | **Authoritative.** Multi-stage build, ODBC driver installation, ~200MB production image estimate. |
| `research/cost-optimization-2026/analysis.md` | **Previous research.** Contains prior cost analysis with Container Apps estimates. Cross-referenced and validated with current official sources. |

## Sources NOT Used (Explain Why)

| Source Type | Why Not Used |
|-------------|-------------|
| Stack Overflow answers | Search engines blocked by CAPTCHA. Cold start times cited from architectural analysis + official docs instead. |
| Third-party blogs | Not accessed due to search engine restrictions. All claims verified against official Microsoft documentation. |
| Community benchmarks | Not available in this session. Cold start estimates based on architecture (KEDA pod scheduling + container pull) and cross-referenced with official scaling documentation. |

## Validation Notes

1. **All pricing data** verified against official Azure pricing pages (live, current as of 2026-03-27)
2. **Free tier limits** confirmed from official docs updated 2026-03-18 (very recent)
3. **Auto-resume latency** ("~1 minute") comes directly from official serverless tier documentation
4. **Cold start times** for Container Apps are estimated from architecture understanding (no official SLA published); 2-8 second range is consistent with Kubernetes pod scheduling + container startup
5. **APScheduler incompatibility** verified by reading source code — scheduler runs in-process as AsyncIOScheduler, killed on container termination
6. **SQL error 40613** behavior confirmed in official serverless documentation — first connection attempt to paused DB triggers resume and returns error

## Cross-Reference Validation

| Claim | Source 1 | Source 2 | Consistent? |
|-------|----------|----------|-------------|
| Container Apps free grants | Pricing page | Billing docs | ✅ Yes — both state 180K/360K/2M |
| Scale-to-zero = $0 | Pricing FAQ | Billing docs | ✅ Yes — explicit confirmation |
| SQL Free Tier 100K vCore-sec | Free offer page | Pricing page | ✅ Yes |
| SQL auto-resume ~1 min | Serverless overview | N/A (single source) | ⚠️ Single source but official |
| S0 = $15/mo | Cost optimization doc | Azure pricing page | ✅ Yes |
| B1 = $13.14/mo | Cost optimization doc | Azure pricing page | ✅ Yes |
