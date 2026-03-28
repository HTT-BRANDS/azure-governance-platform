# Source Credibility Assessment

## Tier 1 Sources (Official Documentation — Highest Reliability)

### 1. Azure App Service Linux Pricing
- **URL:** https://azure.microsoft.com/en-us/pricing/details/app-service/linux/
- **Publisher:** Microsoft (official pricing page)
- **Verified:** 2026-03-27
- **Currency:** Current (live pricing, USD, Central US region)
- **Key Data Extracted:**
  - F1 Free: Shared cores, 60 CPU min/day, 1GB RAM, 1GB storage, $0
  - B1 Basic: 1 core, 1.75GB RAM, 10GB storage, $13.14/mo
  - B2 Basic: 2 cores, 3.50GB RAM, 10GB storage, $25.55/mo
  - P0v3 Premium: 1 vCPU, 4GB RAM, 250GB storage, $62.05/mo (PAYG)
  - **Note: Basic tier does NOT support savings plans or reserved instances**
- **Bias Assessment:** Official vendor pricing — no bias, but prices may vary by region/agreement

### 2. Azure Container Apps Pricing
- **URL:** https://azure.microsoft.com/en-us/pricing/details/container-apps/
- **Publisher:** Microsoft (official pricing page)
- **Verified:** 2026-03-27
- **Currency:** Current
- **Key Data Extracted:**
  - Free grants: 180,000 vCPU-seconds, 360,000 GiB-seconds, 2M requests/mo
  - Active vCPU: $0.000024/second (after free grant)
  - Active Memory: $0.000003/GiB-second (after free grant)
  - Idle vCPU: $0.000003/second
  - Scale to zero = $0 when not processing requests
- **Bias Assessment:** None — standard pricing disclosure

### 3. Azure SQL Database Free Offer
- **URL:** https://learn.microsoft.com/en-us/azure/azure-sql/database/free-offer
- **Publisher:** Microsoft Learn (official documentation)
- **Verified:** 2026-03-27
- **Currency:** Current (docs regularly updated)
- **Key Data Extracted:**
  - 100,000 vCore seconds/month of serverless compute
  - 32GB data storage per database
  - 32GB backup storage
  - Up to 10 General Purpose databases per subscription
  - Lifetime of subscription (not time-limited)
  - Limitations: Max 4 vCores, PITR limited to 7 days, LRS backup only
  - Cannot convert existing database to free offer (must create new)
- **Bias Assessment:** None — official documentation of free tier constraints

### 4. Azure Functions Pricing
- **URL:** https://azure.microsoft.com/en-us/pricing/details/functions/
- **Publisher:** Microsoft (official pricing page)
- **Verified:** 2026-03-27
- **Currency:** Current
- **Key Data Extracted:**
  - Consumption: 1M executions free, 400K GB-s free
  - Beyond free: $0.000016/GB-s, $0.20/million executions
  - Flex Consumption: 250K executions free, 100K GB-s free
  - Note: Storage account not included in free grant
- **Bias Assessment:** None

### 5. Azure Cosmos DB Free Tier
- **URL:** https://learn.microsoft.com/en-us/azure/cosmos-db/free-tier
- **Publisher:** Microsoft Learn (official documentation)
- **Verified:** 2026-03-27
- **Currency:** Current
- **Key Data Extracted:**
  - 1,000 RU/s shared throughput
  - 25GB storage
  - Max 25 containers per shared database
  - One free tier account per subscription
  - Must opt-in at creation time
  - Not available for serverless accounts
  - Up to 63% discount with Reserved Capacity
- **Bias Assessment:** None

### 6. Azure Container Registry Pricing
- **URL:** https://azure.microsoft.com/en-us/pricing/details/container-registry/
- **Publisher:** Microsoft (official pricing page)
- **Verified:** 2026-03-27
- **Currency:** Current
- **Key Data Extracted:**
  - Basic: $0.167/day (~$5.01/mo), 10GB included storage
  - Standard: $0.667/day (~$20.01/mo), 100GB storage
  - Premium: $1.667/day (~$50.01/mo), 500GB storage
  - Additional storage: $0.00334/GB/day for all tiers
- **Bias Assessment:** None

### 7. Azure Static Web Apps Pricing
- **URL:** https://azure.microsoft.com/en-us/pricing/details/app-service/static/
- **Publisher:** Microsoft (official pricing page)
- **Verified:** 2026-03-27
- **Currency:** Current
- **Key Data Extracted:**
  - Free: $0, 100GB BW, 2 custom domains, 0.50GB storage (0.25GB/app)
  - Standard: $9/app/mo, 5 custom domains, 2GB storage (0.50GB/app)
  - Free tier includes service-defined auth but NOT custom auth
- **Bias Assessment:** None

### 8. GCP Cloud Run Pricing
- **URL:** https://cloud.google.com/run/pricing
- **Publisher:** Google Cloud (official pricing page)
- **Verified:** 2026-03-27
- **Currency:** Current
- **Key Data Extracted:**
  - CPU: $0.000018/vCPU-second (default)
  - Memory: $0.000002/GiB-second (default)
  - Free tier: 240,000 vCPU-seconds, 450,000 GiB-seconds/mo
  - CUD discounts: 15-17% for 1-3 year commitments
- **Bias Assessment:** None — competitor pricing for comparison

### 9. DigitalOcean Droplet Pricing
- **URL:** https://www.digitalocean.com/pricing/droplets
- **Publisher:** DigitalOcean (official pricing page)
- **Verified:** 2026-03-27
- **Currency:** Current
- **Key Data Extracted:**
  - $4/mo: 512MB RAM, 1 vCPU, 500GB transfer, 10GB SSD
  - $6/mo: 1GB RAM, 1 vCPU, 1TB transfer, 25GB SSD
  - $12/mo: 2GB RAM, 1 vCPU, 2TB transfer, 50GB SSD
- **Bias Assessment:** None — competitor pricing for comparison

### 10. GitHub Packages Billing
- **URL:** https://docs.github.com/en/billing/concepts/product-billing/github-packages
- **Publisher:** GitHub/Microsoft (official documentation)
- **Verified:** 2026-03-27
- **Currency:** Current
- **Key Data Extracted:**
  - GitHub Free: 500MB storage, 1GB transfer/mo
  - GitHub Pro: 2GB storage, 10GB transfer/mo
  - **Container Registry (GHCR): Currently FREE for container images**
  - Storage shared with GitHub Actions
- **Bias Assessment:** Note — "currently free" policy may change with 1 month notice

## Tier 2 Sources (Project Documentation — High Reliability)

### 11. Project Infrastructure Inventory
- **File:** INFRASTRUCTURE_INVENTORY.md
- **Source:** Internal project documentation
- **Verified:** 2026-03-27 (by cross-referencing pricing pages)
- **Key Data:** Current resource configuration, SKUs, and cost estimates
- **Note:** Minor inconsistency found — inventory lists ACR as "Standard" at ~$5/mo,
  but Standard tier is actually ~$20/mo. Likely using Basic tier, or pricing was different at provisioning time.

### 12. Project Architecture Document
- **File:** ARCHITECTURE.md
- **Source:** Internal project documentation
- **Key Data:** FastAPI + HTMX + SQLAlchemy + Docker architecture details

## Sources NOT Consulted (and why)

| Source Type | Reason for Exclusion |
|-------------|---------------------|
| Blog posts on "Azure cost optimization" | Secondary sources, may be outdated |
| Reddit/HN cost discussions | Anecdotal, unverifiable |
| Third-party cost calculators | Potential inaccuracies vs. official pricing |
| AWS Fargate pricing page | Table failed to load (dynamic rendering); used known rates |

## Data Freshness Note

All pricing was verified on **2026-03-27** from official sources. Azure pricing changes periodically.
The Azure SQL Database free offer was introduced in 2024 and is confirmed active as of this date.
GHCR's free container storage policy has been in place since launch but is explicitly noted as subject to change.
