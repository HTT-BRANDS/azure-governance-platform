# Multi-Dimensional Analysis — Azure Pricing 2026

This file applies the standard research lenses to the gathered pricing data. For raw numbers see [README.md](./README.md).

---

## 1. Cost Analysis

### Minimum Viable Production Stack (monthly, East US)

A typical small-to-mid Python/Node web app — single App Service + managed SQL + Key Vault + monitoring + Redis cache:

| Component | SKU | East US | West US 2 |
|-----------|-----|---------|-----------|
| App Service | **S1** (1 instance, slots supported) | $69.35 | **$58.40** |
| SQL Database | **S1 DTU** (20 DTU) | $29.45 | $29.45 |
| Redis Cache | **Basic C0** (dev) or **Standard C0** (prod SLA) | $16.06 / $40.15 | same |
| Key Vault | Standard (~10K ops/mo) | ~$0.03 | same |
| Application Insights | Workspace-based, ~3 GB/mo (within free 5 GB) | $0.00 | $0.00 |
| Storage (Blob Hot LRS) | 50 GB | $1.04 | $1.04 |
| Alerts (3 metric, 1 log @ 15min) | Azure Monitor | ~$0.60 | ~$0.60 |
| Egress | 30 GB/mo (within 100 GB free) | $0.00 | $0.00 |
| **TOTAL (Basic Redis)** |  | **~$116.53/mo** | **~$105.58/mo** |
| **TOTAL (Standard Redis, SLA)** |  | **~$140.62/mo** | **~$129.67/mo** |

**West US 2 saves $10.95/month (~8%)** because of the Standard App Service price differential.

### Scale-up Cost Curves

| Scenario | Config | Monthly (East US) |
|----------|--------|-------------------|
| Dev/Test (no SLA) | B1 + S0 + Basic C0 + everything else min | **~$44** |
| Small Prod (5 slots available) | **S1** + S1 DTU + Standard C0 + monitoring | **~$140** |
| Mid Prod (autoscale, slots) | **P1v3** + S2 DTU + Standard C1 + monitoring | **~$300** |
| Mid Prod + 1-Yr RI on P1v3 | **P1v3 RI** + rest PAYG | **~$260** (save $40) |
| Mid Prod + 3-Yr RI on P1v3 | **P1v3 3yr RI** + rest PAYG | **~$237** (save $63) |
| High Availability | P1v3 × 2 instances + BC SQL 2vCore + Std C2 Redis | **~$720** |

### Hidden / Easy-to-Miss Costs

| Cost | Gotcha |
|------|--------|
| **Data egress from SQL DB to App Service in a different region** | Inter-region bandwidth = $0.02/GB; can add up if you cross regions |
| **Inter-AZ data transfer** | $0.01/GB each way — matters for zone-redundant deployments |
| **Log Analytics data ingestion > 5 GB/month** | $2.30/GB beyond the free allowance; App Insights can easily ingest 1 GB/day on a chatty app |
| **SQL DB storage overage** | $0.17/GB/month beyond included 250 GB (Standard) / 500 GB (Premium) |
| **Managed HSM** (if you assume it's "just Key Vault") | $3.20/hr minimum = **$2,336/month** — massively different tier from Standard KV |
| **App Service scaled-out slots** | Each running instance (including slot instances) is billed |
| **Application Insights Classic (legacy)** | Non-workspace AI with Multi-step Web Tests: $10/test/month |
| **Blob Storage tiered pricing** | First 50 TB is most expensive; big customers get automatic discounts at 450 TB+ |

---

## 2. Security Analysis

### Tier-by-Tier Security Implications

| Service | Tier | Security Posture |
|---------|------|------------------|
| App Service | B1/B2/B3 | ❌ No private endpoints, ❌ no VNet integration (except from B2+), no slots = no blue/green canary |
| App Service | **S1+** | ✅ VNet integration, ✅ Hybrid Connections, ✅ custom domains with SNI SSL |
| App Service | **P1v3+** | ✅ Private endpoints, ✅ availability zones, ✅ dedicated hardware, ✅ multi-plan isolation |
| SQL DB | DTU tiers | Same security features as vCore (firewall, Entra auth, TDE) |
| SQL DB | Free | ⚠️ No SLA; production use not recommended |
| Redis | Basic | ❌ **No SLA**, no replication — any failure = data loss + downtime |
| Redis | Standard | ✅ 99.9% SLA, primary+replica |
| Redis | (Premium, not in scope) | ✅ 99.95% SLA, VNet support, persistence, clustering |
| Storage | LRS | 3 copies in 1 datacenter — survives server/rack failure only |
| Storage | ZRS | 3 copies across 3 AZs — survives AZ failure |
| Storage | GRS | 6 copies (3 LRS × 2 regions) — survives region disaster |
| Key Vault | Standard | ✅ RBAC, ✅ audit to Log Analytics, soft-delete + purge protection |
| Key Vault | Premium/HSM | + FIPS 140-2 Level 2/3 (for regulated workloads) |

### Cost-Security Trade-offs

- **Going below S1 kills deployment slots** → no safe blue/green deploys → higher risk of production regressions → real security cost.
- **Basic Redis = no SLA** → single-point of failure → avoid for anything touching auth, session state, or security-relevant caching.
- **Storage LRS is ~55% cheaper than GRS** — but GRS protects against regional outages. For audit logs (governance platform!), GRS is usually warranted.
- **Workspace-based App Insights at $2.30/GB** enables log-based alerts, which are higher-value than simple metric alerts for security/audit scenarios.

---

## 3. Implementation Complexity

| Service | Tier-change complexity | Notes |
|---------|------------------------|-------|
| App Service plan scale-up | Near-zero downtime scale-up (B1→S1→P1v3 via portal/CLI) | No app restart if same instance size family |
| App Service DTU→vCore migration (for RI) | **Not applicable** (DTU is a SQL concept) | — |
| SQL DB tier change | Minutes of downtime (fail over to resized DB) | S0→S1: ~1 min unavailability |
| SQL DB DTU→vCore | Database copy + cut-over; **needed for RI** | Plan: 1–2 hours validation |
| Redis tier change | **Cannot change Basic→Standard in-place** — must recreate; app reconnects to new FQDN | Use ARM/Bicep idempotency, swap endpoints |
| Storage redundancy change | LRS↔ZRS/GRS: in-place via portal; allow migration period (hours-days) | No data loss, background process |
| App Service RI purchase | Portal/CLI; attaches to subscription scope; automatically covers matching SKU | Reversible within 72 hr (Azure cancellation window) |
| SQL DB RI purchase | Scope to subscription or shared; covers **any matching vCore Gen5 GP** DB in that scope | Family-flexible within tier |

**Reservation purchase complexity (both AS and SQL):**
1. Establish baseline usage (need ≥ 1-year continuous utilization of the SKU)
2. Decide scope: single subscription vs shared (recommended: shared for enterprise)
3. Decide upfront vs monthly payment (same total cost)
4. Monitor utilization in Cost Management; < 80% utilization = poor ROI
5. 72-hour cancel window; after that, exchange (SQL only) or sell via Marketplace

---

## 4. Stability & Maturity

| SKU | Launch | Deprecation Risk |
|-----|--------|-------------------|
| App Service Basic/Standard | 2014 | Low — extremely mature, no deprecation signals |
| App Service Premium v1/v2 | 2016/2018 | **Medium** — Microsoft is steering customers to v3 |
| App Service **Premium v3** | 2020 | **Low (current default)** |
| App Service **Premium v4** | 2024 | **Low (newest; higher density than v3)** |
| SQL DB DTU | 2014 | **Medium** — Microsoft actively promotes vCore as the modern model; DTU remains supported but gets fewer features (no Hyperscale, no serverless, no RI) |
| SQL DB vCore | 2018 | Low — primary model |
| Azure Cache for Redis (OSS Redis) | 2014 | **Medium** — Redis Labs license changes (2024) pushed Microsoft to add Redis Enterprise tiers; future direction is Azure Managed Redis |
| Azure Managed Redis (preview, new) | 2025 | Too new to recommend — but worth tracking |
| Blob Storage Hot/Cool/Archive | 2016/2017/2017 | Low — industry standard tiering |
| Log Analytics / App Insights (workspace-based) | 2022 (merger) | Low — classic AI deprecated April 2025 |
| Classic Application Insights | 2015 | **DEPRECATED** — migrate to workspace-based |
| Azure Monitor alert rules | 2018 | Low — v2 alerts fully replaced classic in 2019 |

**Key stability red-flag**: If you're still using **classic Application Insights**, migrate to **workspace-based** before more features get withdrawn.

---

## 5. Optimization / Performance

### App Service performance per dollar (East US)

| SKU | vCPU | RAM | $/month | $/vCPU/month | Comments |
|-----|------|-----|---------|---------------|----------|
| B1 | 1 | 1.75 GB | $12.41 | $12.41 | Cheapest; no auto-scale, no slots |
| S1 | 1 | 1.75 GB | $69.35 | $69.35 | Same hardware as B1, 5.6× price — you're paying for features (slots, autoscale, VNet) |
| P1v3 | 2 | 8 GB | $113.15 | $56.58 | **Best $/vCPU in production** |
| P2v3 | 4 | 16 GB | $226.30 | $56.58 | Same rate per vCPU as P1v3 |
| P3v3 | 8 | 32 GB | $452.60 | $56.58 | Linear scaling |

> **Insight**: P1v3 is the cost-per-vCPU sweet spot. S1 exists primarily for slots+autoscale on small workloads — if you need >1 vCPU or zone redundancy, **jump to P1v3**.

### SQL DB performance per dollar

| SKU | DTU | $/mo | $/DTU |
|-----|-----|------|-------|
| Basic | 5 | $4.90 | $0.98 |
| S0 | 10 | $14.72 | $1.47 |
| S1 | 20 | $29.45 | $1.47 |
| S2 | 50 | $73.65 | $1.47 |
| S3 | 100 | $147.26 | $1.47 |
| P1 | 125 | $456.56 | $3.65 |

> **Insight**: DTU $/unit is **flat** across Standard tier (S0–S3) at ~$1.47. Premium tier is **2.5× more expensive per DTU** but offers I/O-heavy workloads (higher IOPS per DTU, in-memory OLTP). Most apps can stay Standard.

### Redis performance per dollar

| SKU | Memory | $/mo | $/GB/mo |
|-----|--------|------|---------|
| Basic C0 | 0.25 GB | $16.06 | $64.24 |
| Basic C1 | 1 GB | $40.15 | $40.15 |
| Basic C2 | 2.5 GB | $65.70 | $26.28 |
| Standard C1 | 1 GB | $100.74 | $100.74 |
| Standard C2 | 2.5 GB | $164.25 | $65.70 |

> **Insight**: Small caches (≤ 1 GB) are expensive per GB. If you truly need caching, scaling to C2+ gives better $/GB.

---

## 6. Compatibility

### App Service Linux Runtime support (all tiers B1+)

- Python 3.8 – 3.12 (3.13 preview), .NET, Node.js, PHP, Java, Ruby, Go, custom containers
- Docker Hub + Azure Container Registry (ACR) integration
- All tiers support container deployment, so **tier choice is about features, not runtime compatibility**.

### SQL DB DTU compatibility

- All DTU tiers support the same T-SQL surface
- ⚠️ **Missing features vs vCore (may affect architecture decisions):**
  - ❌ No Hyperscale (elastic storage up to 100 TB)
  - ❌ No Serverless (auto-pause for sporadic workloads)
  - ❌ No Reserved Instance pricing
  - ❌ No In-Memory OLTP (except P1+)
  - ❌ No Columnstore (except P1+)

### Redis compatibility

- Basic + Standard run **Redis OSS 6.0** (optional 4.0 for compat)
- No RedisJSON, RediSearch, RedisTimeSeries on Basic/Standard (only on Enterprise/Managed Redis)

### Storage compatibility

- Hot LRS is maximally compatible (default for most services, e.g., AKS volumes, Functions, App Service deployments)
- ZRS not available in all regions (East US ✅, West US 2 ✅)

---

## 7. Maintenance / Operational Burden

| Service | Update Model | Operator Action Required |
|---------|--------------|--------------------------|
| App Service | Automatic host OS patches (Linux); platform updates are transparent | Periodic language runtime version bumps (every ~18 months) |
| SQL DB | Fully managed — Microsoft patches engine | Monitor compat level; upgrade major compat when ready |
| Redis | Managed; Microsoft schedules updates | **Applies to Basic/Standard only in maintenance windows** — plan for brief downtime notifications |
| Storage | Fully managed | None |
| Key Vault | Fully managed | None |
| App Insights | Fully managed | Workspace retention policy review |
| Azure Monitor alerts | Fully managed | Periodic tuning to reduce noise |

---

## 8. Cost Optimization Levers Summary

| Lever | Savings Potential | Complexity |
|-------|-------------------|------------|
| **Move Standard App Service workloads to West US 2** | ~16% | Trivial (regional decision at deploy time) |
| **Use Azure SQL Free Offer for dev/test** | ~$30/mo per dev DB | Trivial |
| **Stay within 5 GB/month Log Analytics free tier** | $11.50/mo saved (per 5 GB) | Sampling / filtering |
| **Use Basic Redis for non-critical caches** | ~60% vs Standard | Accept no SLA |
| **Switch DTU→vCore General Purpose + 1-yr RI** | ~45% on compute | Migration project (hours) |
| **3-Year App Service RI on Premium v3** | ~55% | Commitment risk |
| **Use Blob Cool tier for infrequently accessed data** | ~27% vs Hot ($0.0152 vs $0.0208) | Lifecycle management policies |
| **Reserve bandwidth for aggressive use of free 100 GB + Internet routing preference** | ~10% egress | Config-only change |
| **Scale S1→P1v3 for better $/vCPU if >1 core needed** | 18% savings per vCPU | Tier change (near-zero downtime) |

---

## 9. Decision Framework

```
Need deployment slots?  ─── NO  ──► B-tier (cheapest)
      │
      YES
      │
Need autoscale to >10 instances?  ─── NO  ──► S-tier
      │
      YES or need private endpoints / zone redundancy
      │
      ──► P1v3+
      │
Committed 1yr+?  ─── YES ──► Premium v3 RI (-35% to -55%)
      │
      NO
      │
      ──► Pay-as-you-go
```

```
SQL DB choice:
  Dev/test only, OK with pause ──► Azure SQL Free Offer ($0)
  Tiny load, <5 DTU            ──► Basic DTU ($4.90/mo)
  Predictable small load       ──► Standard DTU S0-S3 ($15-$147)
  Need RI savings / Hyperscale / Serverless ──► vCore model (not DTU)
  High OLTP / large            ──► Premium or Business Critical vCore
```
