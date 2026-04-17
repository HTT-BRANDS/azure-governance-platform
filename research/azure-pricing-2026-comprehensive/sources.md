# Sources & Credibility Assessment

All pricing data in this report was obtained from **Tier 1** sources: Azure's own Retail Prices REST API and official Microsoft pricing/documentation pages. Cross-verification was performed where possible.

## Primary Source (Tier 1 — Official Azure)

### Azure Retail Prices REST API
- **Endpoint**: `https://prices.azure.com/api/retail/prices`
- **Documentation**: https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices
- **Authority**: Official Microsoft API. This is the **exact same data source** that powers the `azure.microsoft.com/pricing/details/*` pages at runtime.
- **Currency indicator**: Each record has an `effectiveStartDate`; most retrieved records are current (2024–2026 effective dates).
- **Credibility**: ★★★★★ (Tier 1). Primary source, no intermediary interpretation.
- **Filters used in this research**:
  - `serviceName eq 'Azure App Service' and armRegionName eq 'eastus'/'westus2' and priceType eq 'Consumption'`
  - `serviceName eq 'SQL Database' and armRegionName eq 'eastus' and priceType eq 'Consumption'`
  - `serviceName eq 'Redis Cache' and armRegionName eq 'eastus'`
  - `serviceName eq 'Storage' and armRegionName eq 'eastus'`
  - `serviceName eq 'Key Vault' and armRegionName eq 'eastus'`
  - `serviceName eq 'Log Analytics' and armRegionName eq 'eastus'`
  - `serviceName eq 'Application Insights' and armRegionName eq 'eastus'`
  - `serviceName eq 'Azure Monitor' and armRegionName eq 'eastus'`
  - `serviceName eq 'Bandwidth'`
  - `priceType eq 'Reservation' and armRegionName eq 'eastus' and serviceName eq 'Azure App Service'/'SQL Database'`

## Cross-Reference Pricing Pages (Tier 1 — Official Azure Web)

> **Caveat:** Azure pricing web pages use JavaScript to render prices at runtime; the raw HTML contains `$-` placeholder strings. The page calls the Retail Prices API for live values. Using the API directly is more reliable than scraping the HTML.

| Page | URL | Used For |
|------|-----|----------|
| App Service (Linux) | https://azure.microsoft.com/en-us/pricing/details/app-service/linux/ | B1/B2/B3, S1/S2/S3, P*v3 hourly rates, RI %s |
| Azure SQL Database Single | https://azure.microsoft.com/en-us/pricing/details/azure-sql-database/single/ | DTU model Basic/S/P tiers, storage included |
| Azure SQL Database Free Offer | https://learn.microsoft.com/en-us/azure/azure-sql/database/free-offer | Free tier limits (100K vCore-sec, 32 GB) |
| Azure Cache for Redis | https://azure.microsoft.com/en-us/pricing/details/cache/ | Basic C0-C6, Standard C0-C6 |
| Blob Storage | https://azure.microsoft.com/en-us/pricing/details/storage/blobs/ | Hot/Cool/Archive, LRS/GRS/ZRS/RA-GRS |
| Queue Storage | https://azure.microsoft.com/en-us/pricing/details/storage/queues/ | Per-10K operations pricing |
| Azure Files | https://azure.microsoft.com/en-us/pricing/details/storage/files/ | Standard hot ($0.06/GB/mo LRS) |
| Azure Monitor | https://azure.microsoft.com/en-us/pricing/details/monitor/ | Log Analytics $2.30/GB, alerts, action groups |
| Key Vault | https://azure.microsoft.com/en-us/pricing/details/key-vault/ | Standard $0.03/10K ops |
| Bandwidth | https://azure.microsoft.com/en-us/pricing/details/bandwidth/ | 100 GB free, Zone 1 $0.087/GB |
| Reservations | https://azure.microsoft.com/en-us/pricing/reserved-vm-instances/ | RI concept and eligibility |

**Credibility**: ★★★★★ (Tier 1) — Official Microsoft, current as of research date.

## Microsoft Learn Documentation (Tier 1 — Primary Technical Docs)

| Document | URL | Used For |
|----------|-----|----------|
| App Service hosting plans overview | https://learn.microsoft.com/en-us/azure/app-service/overview-hosting-plans | Tier feature matrix (slots, autoscale limits) |
| Deployment slots | https://learn.microsoft.com/en-us/azure/app-service/deploy-staging-slots | Standard = 5 slots, Premium v3 = 10 slots, no extra charge |
| App Service quotas | https://learn.microsoft.com/en-us/azure/app-service/overview-hosting-plans#how-much-does-my-app-service-plan-cost | Autoscale instance limits |
| SQL DB DTU vs vCore | https://learn.microsoft.com/en-us/azure/azure-sql/database/service-tiers-dtu | DTU tier definitions, storage inclusions |
| SQL DB Reservations | https://learn.microsoft.com/en-us/azure/azure-sql/database/reserved-capacity-overview | RI applies only to vCore model |
| Log Analytics pricing details | https://learn.microsoft.com/en-us/azure/azure-monitor/logs/cost-logs | $2.30/GB, 5 GB/month free, commitment tiers |
| App Insights workspace-based | https://learn.microsoft.com/en-us/azure/azure-monitor/app/create-workspace-resource | All new AI resources use Log Analytics pricing |
| Alert rule pricing | https://learn.microsoft.com/en-us/azure/azure-monitor/alerts/alerts-types | Metric, log, activity log alert types |

**Credibility**: ★★★★★ (Tier 1) — Official Microsoft, maintained by product teams.

## Verification Method

1. **Queried Azure Retail Prices API** for each service × region × `priceType=Consumption` (and `priceType=Reservation` for RI data).
2. **Cross-referenced** results against azure.microsoft.com pricing pages via headless browser (Playwright).
3. **Confirmed feature limits** (slot counts, autoscale caps, free tier limits) via Microsoft Learn documentation.
4. **Sampled multiple meter names** to distinguish between overlapping SKUs (e.g., "Cache" vs "Cache Instance" meters for Redis).

## Data Currency

- API records retrieved: **April 17, 2026**
- Most records have `effectiveStartDate` in 2024 or 2025 (prices remain stable)
- SQL DB Free Offer was launched in 2023; still current
- Blob Storage tiered pricing (50 TB / 450 TB / 500+ TB bands) introduced 2018; unchanged
- Bandwidth: Microsoft introduced 100 GB/month free egress in July 2024; confirmed still active on 2026-04-17

## Potential Biases & Limitations

| Bias/Limitation | Mitigation |
|-----------------|------------|
| Azure pricing page has marketing framing ("save X%") | Used raw API numbers, computed savings independently |
| Some SKUs have multiple meters (e.g., Redis `C0 Cache` vs `C0 Cache Instance`) | Matched meter names against Azure docs; `Cache Instance` meters are for clustered Standard (C0 on AZ-enabled regions) |
| Reserved Instance math assumes 730 hr/mo | Explicitly documented this assumption; actual billing is by exact hours |
| DTU vs vCore pricing comparison | Avoided direct comparison — noted DTU is not reservable; vCore is |
| US SMS pricing retrieved, but country-by-country SMS pricing varies widely | Only documented US (+1), India (+91), UK (+44) as representative |
| Free tier details change more often than consumption prices | Verified Log Analytics 5 GB free and 100 GB bandwidth free on 2026-04-17 |

## Not Used (Lower Tiers Avoided)

- ❌ Third-party cost calculators (azureprice.net, infracost.io) — potentially stale
- ❌ Community blog posts about pricing — often outdated within weeks
- ❌ Stack Overflow answers about pricing — frequently reference deprecated SKUs
- ❌ AI-scraped aggregators — no way to verify currency

All pricing figures can be independently verified by running the same API queries:

```bash
curl "https://prices.azure.com/api/retail/prices?\$filter=serviceName%20eq%20'Azure%20App%20Service'%20and%20armRegionName%20eq%20'eastus'%20and%20priceType%20eq%20'Consumption'"
```
