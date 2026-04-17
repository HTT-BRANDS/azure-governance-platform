# Project-Specific Recommendations — Azure Governance Platform

**Project context**: This is an **Azure Governance Platform** (Python/FastAPI; SQLAlchemy → Azure SQL; containers deployed to App Service for Linux; observability via App Insights/Log Analytics; secrets in Key Vault). Prior research (`research/azure-pricing-west-us-2/`, `research/azure-hosting-alternatives/`, `research/architecture-audit-2026/`) indicates the stack currently uses **App Service B1 or S1 (Linux)**, **Azure SQL S0 (10 DTU)**, **Key Vault Standard**, and **Log Analytics with workspace-based App Insights**.

Recommendations below are ranked by expected ROI and fit with this specific codebase.

---

## 🔝 Tier 1 — High-impact, Low-risk (do these first)

### R1. If you don't need >1 GB RAM and don't need staging slots → stick with **B1** ($12.41/mo)
- Current architecture appears to use sporadic governance scans + periodic API calls; B1 is adequate for <100 req/s steady-state.
- **Savings vs S1: $56.94/mo** per environment. For 3 envs (dev/staging/prod) that's **$170/mo saved**.
- ⚠️ Only do this if you accept: manual scale only, no deployment slots, no VNet integration below B2.

### R2. If you need deployment slots → the **cheapest slot-capable tier is S1**
- S1 East US: $69.35/mo vs S1 West US 2: $58.40/mo → **if slots are your driver, deploy to West US 2** for a 15.8% saving.
- For this project, the **WIGGUM_ROADMAP.md** mentions a blue/green deployment goal — slots make that trivial. Standard tier gives you 5 slots at no extra charge.

### R3. Keep Azure SQL on **S0 DTU** ($14.72/mo) until you actually need vCore features
- Governance platform workloads are metadata-heavy but low-RPS. S0's 10 DTU is sufficient based on `research/architecture-audit-2026/raw-findings/azure-sql-s0-limits.json`.
- ⚠️ **Do NOT over-optimize by going to S1 DTU ($29.45)** unless DTU saturation >80% sustained.
- **If you need RI savings**: migrate to **vCore General Purpose 1 vCore**. Monthly math:
  - vCore GP 1 vCore PAYG: ~$132.50/mo + storage $0.115/GB/mo (first 5 GB included)
  - vCore GP 1 vCore + 1-yr RI: **$72.25/mo** + storage
  - **Crossover**: If you're paying >$29.45/mo DTU and your workload doesn't fit in S0, go vCore + RI.

### R4. Use **Azure SQL Free Offer** for dev/test databases
- Dev/test DB can run at $0 within the 100K vCore-sec/month allotment. Auto-pauses when idle.
- **Savings**: $14.72/mo × 2 envs = **$29.44/mo** if you currently have S0 for dev/staging.
- Caveat: 32 GB storage limit; schema + test data for a governance platform should fit.

### R5. Watch the **5 GB/month Log Analytics free tier** aggressively
- Current `App Insights` configuration ingestion rate unknown. Set up a daily cap or sampling (e.g., `adaptiveSampling = true` and `maxTelemetryItemsPerSecond = 5`).
- Each 1 GB over free = **$2.30/mo**. Easy to accidentally ingest 10+ GB/day on a chatty app with verbose request logging.
- Create an Azure Monitor alert on `Data Ingestion > 4 GB/day` so you're warned before overage.
- For compliance/audit logs you must keep, route them to **Basic Logs ($0.50/GB)** or **Auxiliary Logs ($0.05/GB)** instead of Analytics tier.

### R6. Keep Key Vault **Standard**; cost is effectively $0
- At typical governance workload ops rates (10-50K/mo), total Key Vault cost will be **< $0.15/mo**.
- **Avoid Premium/HSM unless you have a regulatory mandate** (FIPS 140-2 Level 3). HSM Pool starts at $2,336/month.

---

## 🔁 Tier 2 — Medium-impact, moderate risk

### R7. **Reserve App Service compute only if you've been on the same SKU for ≥6 months and plan to stay**
- If you're on **P1v3** steadily: 1-yr RI saves **$39.40/mo** ($472.80/year). Strong ROI after 7 months.
- If you're on **S1 or lower**: **no RI available** for Standard/Basic — don't bother.
- Keep shared scope on reservations (account-wide) so any matching SKU in any RG consumes it.

### R8. Redis: prefer **Basic C0 for dev, Standard C1 for prod**; avoid Basic in production
- Basic C0 ($16.06/mo) is fine for local dev — no SLA acceptable.
- **Basic in production** is a footgun: single node, any VM event = total cache loss + downtime.
- Standard C1 ($100.74/mo) buys you the 99.9% SLA. Don't "save" $60/mo by running Basic for user-facing production.
- If your governance platform caches are ephemeral (e.g., Azure API response caching), consider skipping Redis entirely and using in-process caching — or Azure App Configuration's feature flag caching ($1.20/day Standard).

### R9. **Choose your region once, stick with it** — avoid cross-region egress
- If data egress between App Service and SQL spans regions: $0.02/GB adds up.
- For a governance platform pulling Azure Resource Graph data (can be multi-region queries), egress from queried regions back to **East US / West US 2** is billed. Budget for ~$5-$10/mo if your tenants span globally.
- **Recommendation**: Deploy this governance platform in the **same region as the majority of managed tenant subscriptions** — likely East US for most enterprise customers.

### R10. Use **GRS for audit/compliance data, LRS for everything else**
- Governance audit trails → **Blob Hot GRS** ($0.0458/GB/mo) — protects against regional disaster (compliance requirement).
- Application working data / caches → **Blob Hot LRS** ($0.0208/GB/mo) — 55% cheaper.
- At 100 GB audit storage: $4.58/mo GRS vs $2.08/mo LRS = $2.50 saved → keep compliance data on GRS regardless.

---

## ⚠️ Tier 3 — Do NOT do these (anti-patterns)

### R11. Don't migrate to Premium v3 for "the slots" if S1 is enough
- Premium v3 gives 10 slots vs Standard's 5 — but most apps use 1–2 slots. P1v3 costs **$43.80/mo more than S1** for a slot count you won't use.
- Only go P1v3 if you also need: private endpoints, zone redundancy, higher CPU/RAM, or autoscale >10 instances.

### R12. Don't buy reservations for DTU SQL tiers
- **SQL DB DTU is not reservable.** If a sales rep suggests otherwise, they may mean migrating to vCore first.

### R13. Don't pay for multi-step web tests unless you need them
- Classic App Insights web tests = $10/test/month.
- Replace with GitHub Actions scheduled HTTP probes (free in public repos, or included in GitHub Enterprise Cloud $21/user/mo if already committed).

### R14. Don't use Blob Archive tier for active audit logs
- Archive tier is $0.00299/GB/mo (cheap!) but has **15-hour standard rehydration** and $0.02/GB retrieval + $5/10K read ops.
- For governance compliance where auditors may query records unpredictably, use **Cool ($0.0152/GB)** instead — 10 ms retrieval, reasonable operations pricing.

---

## 💰 Recommended Monthly Budget (this specific project)

Assuming small-to-mid production workload:

| Component | SKU | East US | West US 2 |
|-----------|-----|---------|-----------|
| App Service (prod) | **S1 Linux** | $69.35 | $58.40 |
| App Service (staging) | slot on prod plan | $0.00 | $0.00 |
| App Service (dev) | **B1 Linux** | $12.41 | $12.41 |
| SQL DB (prod) | **S0 DTU** + 250 GB included | $14.72 | $14.72 |
| SQL DB (dev) | Azure SQL Free Offer | $0.00 | $0.00 |
| Redis Cache | Optional Basic C0 for dev, skip for prod initially | $0–$16 | $0–$16 |
| Key Vault Standard | 2 vaults × ~20K ops | $0.12 | $0.12 |
| Log Analytics + App Insights | ≤ 5 GB/mo (free) | $0.00 | $0.00 |
| Storage | 100 GB Hot LRS blob + minor queue ops | $3.00 | $3.00 |
| Storage — audit logs | 50 GB Hot GRS | $2.29 | $2.29 |
| Alerts (3 metric, 2 log @ 15min) | Azure Monitor | ~$1.10 | ~$1.10 |
| Egress | <100 GB/month | $0.00 | $0.00 |
| **TOTAL** | |  **~$103.00/month** | **~$92.05/month** |

> **West US 2 saves ~$11/month** for this configuration; that's **~$132/year**. Not huge, but meaningful if you run dozens of similar environments for multi-tenant governance deployments.

---

## 🚦 Action Items (Prioritized)

1. **[High] Verify App Insights ingestion rate** is under 5 GB/month; if not, enable adaptive sampling.
2. **[High] Tag all resources** with `cost-center`, `env`, `owner` for cost allocation queries.
3. **[Med] Switch dev SQL DB to Azure SQL Free Offer** — save $14.72/mo/env.
4. **[Med] Decide region strategy** — if >80% of tenants are East US, stay in East US; if flexibility exists, West US 2 saves on S-tier.
5. **[Med] If staying on S1+ ≥ 12 months**, evaluate Premium v3 migration + 1-year RI (35% off).
6. **[Low] Move audit log storage to GRS Hot Blob**; regular operational data stays on LRS.
7. **[Low] Create cost anomaly alert** in Cost Management at 120% of baseline.

---

## 📎 Dependencies on Other Research

- **`research/azure-hosting-alternatives/`** — evaluates Container Apps as an alternative to App Service (different pricing model, potential cost savings for bursty workloads).
- **`research/azure-native-governance-deep-dive/`** — documents Azure Cost Management / Advisor capabilities this platform should surface.
- **`research/architecture-audit-2026/raw-findings/azure-sql-s0-limits.json`** — confirms S0 DTU is adequate for current load.
- **`research/tech-stack-alternatives/`** — scheduling options (APScheduler in-process vs Azure Functions) affect whether App Service vs Functions is cheaper.

---

## 🔍 Open Questions for Follow-up Research

1. Does your governance platform need **zone redundancy** (SLA 99.99% vs 99.95%)? If yes, Premium v3 + ZR SQL GP is required, bumping baseline by ~$300/mo.
2. Have you measured actual Log Analytics ingestion? If >15 GB/day sustained, a **commitment tier (100 GB/day @ $196/day)** becomes cheaper than PAYG.
3. Is there a plan to offer this as a SaaS? Multi-tenant pricing should use Azure Lighthouse + per-tenant cost attribution (free), not one subscription per tenant.
4. Does the product roadmap include customer-hosted deployments (bring-your-own-Azure)? If so, the customer pays these costs directly; our AZ choice only affects our demo/trial environments.
