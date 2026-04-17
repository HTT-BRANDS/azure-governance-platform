# Azure Pricing Comprehensive Research — East US & West US 2

**Research Date**: April 17, 2026
**Agent**: web-puppy-abcd82
**Regions Covered**: East US (`eastus`), West US 2 (`westus2`)
**OS**: Linux
**Pricing Model**: Pay-As-You-Go (no commitment), USD
**Primary Source (Tier 1)**: Azure Retail Prices REST API — `https://prices.azure.com/api/retail/prices`
**Cross-verified**: azure.microsoft.com/en-us/pricing/details/* pages
**Monthly Basis**: 730 hours/month (365.25 days × 24 ÷ 12)

> **⚠️ Important finding about Azure pricing pages:** The HTML pricing pages at `azure.microsoft.com/en-us/pricing/details/*` render their USD values via JavaScript at runtime — the raw HTML contains placeholder `$-` strings. The **Azure Retail Prices REST API is the authoritative source** and is what populates those pages. All numbers in this report are pulled directly from that API (the source of truth Azure itself uses).

---

## 🎯 Executive Summary — Answers to Every Question

### 1. App Service Plans (Linux) — Monthly @ 730 hrs

| SKU | vCPU / RAM | $/hour (East US) | $/month East US | $/hour (West US 2) | $/month West US 2 | Deployment Slots | Autoscale |
|-----|-----------|------------------|-----------------|--------------------|-------------------|------------------|-----------|
| **B1** | 1 / 1.75 GB | $0.017 | **$12.41** | $0.017 | **$12.41** | ❌ None | ❌ No |
| **B2** | 2 / 3.5 GB | $0.034 | **$24.82** | $0.034 | **$24.82** | ❌ None | ❌ No |
| **B3** | 4 / 7 GB | $0.067 | **$48.91** | $0.067 | **$48.91** | ❌ None | ❌ No |
| **S1** | 1 / 1.75 GB | $0.095 | **$69.35** | $0.080 | **$58.40** | ✅ 5 | ✅ Up to 10 instances |
| **S2** | 2 / 3.5 GB | $0.190 | **$138.70** | $0.160 | **$116.80** | ✅ 5 | ✅ Up to 10 instances |
| **S3** | 4 / 7 GB | $0.380 | **$277.40** | $0.320 | **$233.60** | ✅ 5 | ✅ Up to 10 instances |
| **P0v3** | 1 / 4 GB | $0.0775 | **$56.58** | $0.0775 | **$56.58** | ✅ 10 | ✅ Up to 30 instances |
| **P1v3** | 2 / 8 GB | $0.155 | **$113.15** | $0.155 | **$113.15** | ✅ 10 | ✅ Up to 30 instances |
| **P2v3** | 4 / 16 GB | $0.310 | **$226.30** | $0.310 | **$226.30** | ✅ 10 | ✅ Up to 30 instances |
| **P3v3** | 8 / 32 GB | $0.620 | **$452.60** | $0.620 | **$452.60** | ✅ 10 | ✅ Up to 30 instances |
| F1 (Free) | shared | $0 | **$0** | $0 | **$0** | ❌ | ❌ |

**🔑 Key facts about slots & autoscale (per Microsoft Learn):**
- **Free/Basic**: NO deployment slots, NO autoscale (manual scale only on Basic)
- **Standard**: 5 slots, autoscale to 10 instances
- **Premium v2**: 5 slots (increased in newer tiers), autoscale to 30 instances
- **Premium v3**: **10 slots** (production + 9 staging), autoscale to 30 instances
- **Isolated v2**: 20 slots, autoscale to 100 instances

> ⚠️ **Regional note**: Only **Standard** tier (S1/S2/S3) has different pricing between East US and West US 2 — Basic and Premium v3 are identical in both regions. East US is ~18% more expensive for Standard tier.

**Sources**:
- Pricing: https://azure.microsoft.com/en-us/pricing/details/app-service/linux/
- Slots/autoscale limits: https://learn.microsoft.com/en-us/azure/app-service/overview-hosting-plans
- Deployment slots doc: https://learn.microsoft.com/en-us/azure/app-service/deploy-staging-slots

---

### 2. Azure SQL Database (DTU Model) — Monthly @ 30.4375 days

Prices identical in East US and West US 2 (DTU model is not region-differentiated for these tiers).

| Tier / SKU | DTUs | Included Storage | Daily Rate | Monthly Cost |
|-----------|------|------------------|-----------|--------------|
| **Free** (Azure SQL Free Offer) | 100k vCore-seconds/month on GP serverless + 32 GB | — | $0.00 | **$0.00** |
| **Basic** | 5 DTU | 2 GB max | $0.161 | **$4.90/mo** |
| **S0 Standard** | 10 DTU | 250 GB included | $0.4839 | **$14.72/mo** |
| **S1 Standard** | 20 DTU | 250 GB included | $0.9677 | **$29.45/mo** |
| **S2 Standard** | 50 DTU | 250 GB included | $2.42 | **$73.65/mo** |
| **S3 Standard** | 100 DTU | 250 GB included | $4.8387 | **$147.26/mo** |
| **P1 Premium** | 125 DTU | 500 GB included | $15.00 | **$456.56/mo** |
| **P2 Premium** | 250 DTU | 500 GB included | $30.00 | **$913.13/mo** |

**Free tier (Azure SQL Database Free offer — launched late 2023):**
- **100,000 vCore-seconds/month** of General Purpose serverless compute (~28 hours/month of 1 vCore continuously; auto-pauses)
- **32 GB of data storage**
- **32 GB of backup storage** (LRS)
- Limit: **1 free database per subscription**
- After exhausting free allotment: DB pauses (or you can opt to continue with pay-as-you-go)
- ⚠️ The "Basic edition Free tier" (32 MB, 5 DTU) referenced in older docs is deprecated; Azure SQL Free Offer is the current free path.

**Storage overage (all DTU tiers)**: $0.17/GB/month beyond included amount.

> 🔑 **DTU reservations: NOT AVAILABLE.** Reserved Instances for SQL DB apply only to the **vCore model**, not DTU. If you want RI savings, migrate from DTU → vCore General Purpose.

**Sources**:
- DTU pricing: https://azure.microsoft.com/en-us/pricing/details/azure-sql-database/single/
- Free tier: https://learn.microsoft.com/en-us/azure/azure-sql/database/free-offer
- DTU vs vCore: https://learn.microsoft.com/en-us/azure/azure-sql/database/service-tiers-dtu

---

### 3. Azure Cache for Redis (Monthly @ 730 hrs)

Prices identical in East US and West US 2.

| Tier | SKU | Memory | $/hour | $/month |
|------|-----|--------|--------|---------|
| **Basic** | **C0** | 250 MB (shared) | $0.022 | **$16.06** |
| **Basic** | **C1** | 1 GB | $0.055 | **$40.15** |
| **Basic** | **C2** | 2.5 GB | $0.090 | **$65.70** |
| **Standard** | **C0** | 250 MB (shared) | $0.055 | **$40.15** |
| **Standard** | **C1** | 1 GB | $0.138 | **$100.74** |
| **Standard** | **C2** | 2.5 GB | $0.225 | **$164.25** |
| Standard C3 | — | 6 GB | $0.450 | $328.50 |
| Standard C4 | — | 13 GB | $0.525 | $383.25 |

**Key differences Basic vs Standard:**
- **Basic**: Single node, **no SLA**, no replication — dev/test only
- **Standard**: Two-node (primary/replica), **99.9% SLA**, automatic failover — production-ready
- Standard is ~2× Basic price for the same cache size

**Sources**:
- https://azure.microsoft.com/en-us/pricing/details/cache/
- API meter: `Azure Redis Cache Basic` / `Azure Redis Cache Standard`

---

### 4. Azure Storage (East US; West US 2 is identical for Standard tiers)

#### Blob Storage — Hot Tier, Data Stored (per GB/month)

| Volume tier | Hot LRS | Hot GRS | Hot RA-GRS | Hot ZRS |
|-------------|---------|---------|------------|---------|
| First 50 TB/month | **$0.0208** | **$0.0458** | $0.0574 | $0.026 |
| Next 450 TB/month | $0.019968 | $0.043968 | — | — |
| Over 500 TB/month | $0.019136 | $0.042136 | — | — |

- **Blob Hot LRS (small workload, <50 TB): $0.0208 per GB/month** — $20.80 per TB
- **Blob Hot GRS (small workload): $0.0458 per GB/month** — $45.80 per TB (2.2× LRS)

#### Blob Operations (Hot LRS)

| Operation | Price |
|-----------|-------|
| Write operations (PutBlob, PutBlock, etc.) | $0.05 per 10,000 |
| List + Create Container | $0.05 per 10,000 |
| Read operations | $0.004 per 10,000 |
| All other operations | $0.004 per 10,000 |

#### Queue Storage (Standard, per 10,000 operations)

| Operation class | LRS | GRS | ZRS |
|-----------------|-----|-----|-----|
| **Class 1 Operations** (PutMessage, GetMessage, etc.) | **$0.004** | $0.008 | $0.004 |
| **Class 2 Operations** (ClearMessages, DeleteMessage, etc.) | **$0.0004** | $0.008 | $0.004 |
| Queue data stored | **$0.045/GB/mo (LRS)** | $0.0598/GB/mo | — |

> 🎯 **Per your question "per 10K operations": Standard LRS = $0.004 / 10K ops (~$0.40 per million)**

#### Standard LRS vs GRS (Storage pricing comparison)

| Redundancy | Copies | Scope | Hot Blob $/GB/mo | vs. LRS |
|-----------|--------|-------|-------------------|---------|
| **LRS** (Locally Redundant) | 3 copies | 1 datacenter | $0.0208 | baseline |
| **ZRS** (Zone Redundant) | 3 copies | 3 AZs in region | $0.026 | +25% |
| **GRS** (Geo Redundant) | 6 copies | Primary + paired region | $0.0458 | +120% |
| **RA-GRS** (Read-Access GRS) | 6 copies + read secondary | Primary + paired region | $0.0574 | +176% |

#### Azure Files — Hot Tier (File Share)

| SKU | Data Stored ($/GB/month) | Write Ops ($/10K) | Read Ops ($/10K) |
|-----|--------------------------|---------------------|---------------------|
| **Standard LRS (transaction optimized)** | **$0.06** | $0.015 | $0.0015 |
| **Standard GRS** | **$0.10** | $0.03 | $0.0015 |
| **Files v2 Hot LRS** | same $0.06 (data stored via Standard LRS meter) + $0.0297/GB metadata | $0.065 | $0.0052 |
| **Files v2 Cool LRS** | $0.015-$0.0152 | $0.13 | $0.013 + $0.01/GB retrieval |

> **File share "Hot" standard LRS: $0.06 per GB/month**
> For a 100 GB share: 100 × $0.06 = **$6.00/month** + minimal operations.

**Sources**:
- Blob: https://azure.microsoft.com/en-us/pricing/details/storage/blobs/
- Queue: https://azure.microsoft.com/en-us/pricing/details/storage/queues/
- Files: https://azure.microsoft.com/en-us/pricing/details/storage/files/

---

### 5. Application Insights / Log Analytics (East US, same in West US 2)

| Feature | Cost | Notes |
|---------|------|-------|
| **Log Analytics / App Insights Free Tier** | **5 GB/billing account/month** | Workspace-level free allowance; applies to both Log Analytics and workspace-based App Insights |
| **Analytics Logs (Pay-As-You-Go, PerGB2018)** | **$2.30 per GB** ingested | Standard ingestion tier |
| **Basic Logs** | **$0.50 per GB** ingested | For high-volume debug logs (reduced query features) |
| **Auxiliary Logs** | **$0.05 per GB** ingested | Very low-cost archival (limited query) |
| **Data Retention — interactive (default 31 days)** | **Free for first 31 days** (90 days for Sentinel/App Insights workspaces), then **$0.10 per GB/month** | — |
| **Long-term retention / Archive** | $0.026 per GB/month (archive tier, up to 12 years) | Cheapest for compliance |
| **Search Jobs** | $0.005 per GB scanned | Re-query archived data |
| **Log Data Export** | $0.10 per GB | Export to storage/event hub |

**Commitment tiers (discount for predictable volume):**
- 100 GB/day commitment: $196/day = **~$1.96/GB** (~15% savings)
- 200 GB/day: **$1.90/GB** (~17%)
- 500 GB/day: **$1.81/GB** (~21%)
- 1 000 GB/day: **$1.70/GB** (~26%)
- 2 000 GB/day: **$1.64/GB** (~29%)
- 5 000 GB/day: **$1.58/GB** (~31%)

> **Application Insights specifically**: Since April 2024 *all* new App Insights resources are **workspace-based** and priced under Log Analytics ($2.30/GB). The legacy "Classic" App Insights (Basic tier @ $2.30/GB + $10/month multi-step web tests) is deprecated.

**Sources**:
- https://azure.microsoft.com/en-us/pricing/details/monitor/
- https://learn.microsoft.com/en-us/azure/azure-monitor/logs/cost-logs

---

### 6. Azure Key Vault — Standard tier (no regional differentiation)

| Operation Type | Price |
|---------------|-------|
| **Secret & key operations (software-protected)** | **$0.03 per 10,000 transactions** |
| Advanced key operations (RSA-HSM 2048+) | $0.15 per 10,000 |
| Certificate renewal request | $3.00 per renewal |
| Secret renewal | $1.00 per renewal |
| Automated key rotation | $1.00 per rotation |
| Monthly base fee | **$0.00** — pure per-transaction |

- Managed HSM pool (Standard B1): $3.20/hour = $2,336/month (enterprise HSM only)
- Dedicated HSM: $4.85/hour = $3,540/month

> **For a typical small app (~10K ops/month): < $0.03/month on Standard Key Vault.** Key Vault cost is effectively noise for most workloads.

**Source**: https://azure.microsoft.com/en-us/pricing/details/key-vault/

---

### 7. Network / Egress Bandwidth

| Destination / Volume | Price |
|----------------------|-------|
| Data transfer IN (ingress) | **Always FREE** |
| Data transfer within same Availability Zone | **FREE** |
| **First 100 GB/month Internet egress (any region)** | **FREE** |
| Egress Zone 1 (North America/Europe) — Next 10 TB/mo | **$0.087 per GB** (Microsoft Global Network) |
| Egress Zone 1 — Next 40 TB (10–50 TB band) | $0.083/GB |
| Egress Zone 1 — Next 100 TB (50–150 TB band) | $0.070/GB |
| Egress Zone 1 — Over 150 TB | $0.050/GB |
| Routing Preference: Internet (transit ISP) — Next 10 TB | $0.080/GB (~10% cheaper; higher latency) |
| Inter-region, N. America ↔ N. America | $0.02/GB |
| Inter-region, N. America ↔ other continent | $0.05/GB |
| Inter-AZ data transfer (in/out, within region) | $0.01/GB each way |

**Zone 1 = US (all regions including East US & West US 2), Canada, Europe, UK, Switzerland, Israel, UAE.**

> **Rule of thumb for East US / West US 2**: If your app egresses <100 GB/month → **$0**.
> At 1 TB/month → **(1,000 − 100) × $0.087 = $78.30/month**.

**Source**: https://azure.microsoft.com/en-us/pricing/details/bandwidth/ (verified via browser 2026-04-17)

---

### 8. App Service Deployment Slots — Cost implications

| Question | Answer |
|----------|--------|
| Are staging slots included free on S1? | **✅ Yes — no separate fee for the slot itself** |
| Does a slot cost extra compute? | **❌ No extra App Service Plan charge** — slots share the compute of the parent App Service Plan |
| Do slots consume plan resources? | **✅ Yes** — each running slot instance uses CPU/RAM of the plan. Traffic to slots counts toward the plan's limits. |
| Max slots on S1/S2/S3? | **5 slots** (1 production + up to 4 deployment slots) |
| Max slots on P1v3/P2v3/P3v3? | **10 slots** (1 production + 9 deployment slots) — increased from 20 for legacy Premium, **10 is current Premium v3 limit** per Microsoft Learn |
| Max slots on Isolated v2? | **20 slots** |

**Cost implication example**:
- S1 with 1 production + 1 staging slot = still just **$69.35/month** (East US). Both slots run on same compute.
- ⚠️ BUT: If you scale out to 2 instances to handle swap-load, that's **$138.70/month** (you pay per instance across all slots).
- ⚠️ Database connections, outbound bandwidth, Application Insights ingestion from the slot all add up normally.
- Best practice: Keep slot instance count = 0 or 1, and use the slot only around deploy windows if strict cost-sensitive.

**Source**: https://learn.microsoft.com/en-us/azure/app-service/deploy-staging-slots

---

### 9. Azure Monitor — Alerts & Action Groups

#### Alert Rules Pricing (East US)

| Alert Type | Frequency | Price |
|------------|-----------|-------|
| **Metric alert** — Resource monitored | **15 min** | **$0.05 / time-series / month** (first time-series per rule free) |
| Metric alert — Resource monitored | 10 min | $0.10 / time-series / month |
| Metric alert — Resource monitored | 5 min | $0.15 / time-series / month |
| Metric alert — Resource monitored | 1 min | $1.50 / time-series / month |
| **Metric alert — Dynamic Thresholds** (additional) | any | **+$0.10 / time-series / month** |
| **Log alert** — System log | **15 min** | **$0.50 / rule / month** |
| Log alert — System log | 10 min | **$1.00 / rule / month** |
| Log alert — System log | 5 min | $1.50 / rule / month |
| Log alert — System log | 1 min | $7.50 / rule / month |
| Activity log alerts | any | **FREE** (unlimited) |
| Prometheus metric alerts | any | FREE (only charged for underlying Prometheus query) |

#### Action Groups (Notifications)

| Channel | Included Free | Overage Price |
|---------|---------------|----------------|
| **Email** | 1,000 emails/month | $2 per 100,000 emails (~$0.00002/email) |
| **Push (Azure Mobile app)** | 1,000/month | $2 per 100,000 (~$0.00002/push) |
| **Webhook** | 100,000/month | $0.60 per 1,000,000 ($6e-06/webhook) |
| **Secure Webhook (Entra-authed)** | 1/month free | $6 per 1,000,000 ($6e-05/webhook) |
| **ITSM Connector** | — | $0.005 per event |
| **SMS — US (+1)** | 100 free/month | **$0.00645 per SMS** |
| SMS — India (+91) | 100 free/month | $0.0042 per SMS |
| SMS — UK (+44) | 100 free/month | ~$0.09 per SMS |
| SMS — varies by country | — | See Azure Monitor pricing page |
| **Voice call — US (+1)** | 10 free/month | varies (included in US typically free) |

> **Most small apps have $0–$2/month alert spend**: a handful of metric alerts (first time-series free), 1 log alert at 15-min ($0.50), under 1K email notifications (free).

**Sources**:
- https://azure.microsoft.com/en-us/pricing/details/monitor/
- API: `serviceName eq 'Azure Monitor'`

---

### 10. Reserved Instance Savings (East US, verified via API)

#### App Service Premium v3 — Linux (1-year & 3-year RI)

| SKU | PAYG Monthly | 1-Yr RI Monthly | 1-Yr Savings | 3-Yr RI Monthly | 3-Yr Savings |
|-----|--------------|-----------------|--------------|-----------------|--------------|
| P0v3 | $56.58 | $443/yr = **$36.92** | **~35%** | $920/3yr = **$25.56** | **~55%** |
| **P1v3** | **$113.15** | $885/yr = **$73.75** | **~35%** | $1,839/3yr = **$51.08** | **~55%** |
| **P2v3** | **$226.30** | $1,770/yr = **$147.50** | **~35%** | $3,678/3yr = **$102.17** | **~55%** |
| **P3v3** | **$452.60** | $3,530/yr = **$294.17** | **~35%** | $7,332/3yr = **$203.67** | **~55%** |
| P1mv3 (mem-optimized) | $135.78 | $1,059/yr = $88.25 | 35% | $2,200/3yr = $61.11 | 55% |

> **App Service RI headline: ~35% off for 1-year, ~55% off for 3-year.** Only Premium v3 and Premium v4 SKUs are reservable; Basic and Standard tiers are **not** reservable.

#### Azure SQL Database — vCore Gen5 General Purpose (compute only; storage billed separately)

| Term | Per vCore / year | Monthly equiv | Savings vs PAYG (~$0.1815/hr) |
|------|-------------------|---------------|-------------------------------|
| PAYG | — | **~$132.50 / vCore / mo** | baseline |
| **1-Year RI** | **$867 / vCore** | **$72.25 / vCore / mo** | **~45%** |
| **3-Year RI** | **$1,800 / vCore (3yr)** = $600/yr | **$50.00 / vCore / mo** | **~62%** |

Also available:
- SQL GP **Zone Redundant**: 1-yr $520/vCore; 3-yr $1,080 (lower because ZR is only for bigger SKUs)
- SQL Business Critical Gen5: 1-yr $1,733/vCore = ~**$144/mo** (~45% savings vs $262/mo PAYG); 3-yr $3,600 = $100/mo (~62%)
- SQL **Hyperscale**: 1-yr $1,040/vCore = $86.67/mo; 3-yr $2,160 = $60/mo

> 🔑 **SQL DB RI critical caveat**: Reservations apply **only to the vCore compute model**, not the DTU model (Basic/S0-S12/P1-P15). If you use DTU SKUs and want RI savings, you must migrate to vCore General Purpose first.

**Sources**:
- App Service RI: https://azure.microsoft.com/en-us/pricing/details/app-service/linux/ (scroll to "Savings options")
- SQL RI: https://azure.microsoft.com/en-us/pricing/details/azure-sql-database/single/ (Reserved capacity section)
- Reservations doc: https://learn.microsoft.com/en-us/azure/cost-management-billing/reservations/

---

## 📊 Regional Comparison: East US vs West US 2

| Service | East US | West US 2 | Diff | Recommendation |
|---------|---------|-----------|------|----------------|
| App Service B1/B2/B3 | same | same | 0% | Either region |
| **App Service S1** | **$69.35/mo** | **$58.40/mo** | -15.8% in WUS2 | **West US 2** if cost-sensitive Standard tier |
| **App Service S2/S3** | $138.70/$277.40 | $116.80/$233.60 | -15.8% | **West US 2** |
| App Service P1v3/P2v3/P3v3 | same | same | 0% | Either (latency-based) |
| SQL DB DTU (all SKUs) | same | same | 0% | Either |
| Azure Cache for Redis | same | same | 0% | Either |
| Blob Storage (Hot LRS) | same | same | 0% | Either |
| Egress bandwidth | same (Zone 1) | same (Zone 1) | 0% | Either |
| Key Vault | same | same | 0% | Either |

**🎯 Bottom line**: The only meaningful cost difference between East US and West US 2 is the **Standard App Service tier (~16% cheaper in West US 2)**. For all other services in scope, pricing is identical. Choose region based on latency to users, compliance (data residency), and availability-zone requirements.

---

## 🧭 Navigation
- **[analysis.md](./analysis.md)** — Multi-dimensional analysis (cost, security, compatibility, etc.)
- **[recommendations.md](./recommendations.md)** — Project-specific recommendations for this Azure Governance Platform
- **[sources.md](./sources.md)** — Source URLs with credibility assessments
- **[raw-findings/](./raw-findings/)** — Raw API responses and supporting data
