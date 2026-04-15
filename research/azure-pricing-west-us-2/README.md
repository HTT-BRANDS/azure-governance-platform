# Azure Pricing Research — West US 2 Region

**Research Date**: April 15, 2026  
**Region**: West US 2  
**Currency**: USD  
**Primary Source**: Azure Retail Prices REST API (`prices.azure.com/api/retail/prices`)  
**Cross-verified**: Azure pricing web pages, Microsoft Learn documentation

---

## Executive Summary

| # | Service / SKU | Monthly Cost | Unit Basis |
|---|--------------|-------------|------------|
| 1 | **App Service B1 Basic (Linux)** | **$12.41** | $0.017/hr × 730 hrs |
| 2 | **App Service S1 Standard (Linux)** | **$58.40** | $0.080/hr × 730 hrs |
| 3 | **App Service P1v3 Premium v3 (Linux)** | **$113.15** | $0.155/hr × 730 hrs |
| 4 | **Azure SQL Database S0 (10 DTU)** | **$14.72** | $0.4839/day × 30.42 days |
| 5 | **Azure SQL Database Free tier** | **$0.00** | Free (32 MB, 5 DTU) |
| 6 | **Azure Container Registry Basic** | **$5.00** | $0.1666/day × 30 days |
| 7 | **Azure Container Registry Standard** | **$20.00** | $0.6666/day × 30 days |
| 8 | **Key Vault Standard (operations)** | **$0.03 / 10K ops** | Per-transaction pricing |
| 9 | **Application Insights (ingestion)** | **$2.30 / GB** | Workspace-based = Log Analytics pricing |
| 10 | **Log Analytics (PerGB2018)** | **$2.30 / GB** | First 5 GB/month free per billing account |
| 11 | **GitHub Enterprise Cloud** | **$21.00 / user** | Per user/month |

### 🎯 Key Finding: Deployment Slots

> **The cheapest App Service tier that supports deployment (staging) slots is Standard S1 at $58.40/month.**
>
> - Free and Basic tiers: **NO** deployment slots
> - Standard tier: Up to **5** deployment slots
> - Premium v3 tier: Up to **20** deployment slots
> - Isolated tier: Up to **20** deployment slots
>
> There is **no extra charge** for deployment slots themselves — the slot runs on the same App Service Plan resources.
>
> **Source**: [Microsoft Learn — Set up staging environments in Azure App Service](https://learn.microsoft.com/en-us/azure/app-service/deploy-staging-slots)

---

## Detailed Pricing Notes

### App Service Plans (Linux, 1 instance)

Azure bills App Service hourly. Standard monthly estimate uses **730 hours** (365 × 24 / 12).

| Tier | Hourly Rate | Monthly (730h) | Cores | RAM | Storage | Deployment Slots |
|------|------------|----------------|-------|-----|---------|-----------------|
| B1 Basic | $0.017 | $12.41 | 1 | 1.75 GB | 10 GB | ❌ None |
| S1 Standard | $0.080 | $58.40 | 1 | 1.75 GB | 50 GB | ✅ Up to 5 |
| P1v3 Premium v3 | $0.155 | $113.15 | 2 | 8 GB | 250 GB | ✅ Up to 20 |

**Reserved Instance savings for P1v3:**
- 1-Year RI: $885.00/year = **$73.75/month** (35% savings)
- 3-Year RI: $1,839.00/3yr = **$51.08/month** (55% savings)

### Azure SQL Database (DTU Model)

| Tier | DTUs | Storage | Daily Rate | Monthly |
|------|------|---------|-----------|---------|
| Free | 5 | 32 MB | $0.00 | **$0.00** |
| Standard S0 | 10 | 250 GB included | $0.4839 | **~$14.72** |

- The Free tier has no SLA and is limited to 1 database per server
- S0 includes 250 GB storage; overages billed at $0.17/GB/month

### Azure Container Registry

| Tier | Daily Rate | Monthly | Included Storage | Webhooks |
|------|-----------|---------|-----------------|----------|
| Basic | $0.1666 | **$5.00** | 10 GB | 2 |
| Standard | $0.6666 | **$20.00** | 100 GB | 10 |

- Overage storage: $0.10/GB/month (both tiers)
- ACR Tasks vCPU: first 6,000 seconds free, then $0.0001/second

### Key Vault Standard

| Operation Type | Price |
|---------------|-------|
| Secrets operations | **$0.03 per 10,000 transactions** |
| Advanced key operations (RSA-HSM) | **$0.15 per 10,000 transactions** |
| Certificate renewal request | $3.00 per renewal |
| Secret renewal | $1.00 per renewal |
| Automated key rotation | $1.00 per rotation |

- No monthly base fee — pure per-transaction pricing
- Typical small app (~10K ops/month): **< $0.03/month**

### Observability (Azure Monitor / Log Analytics)

| Service | Ingestion Cost | Free Allowance |
|---------|---------------|----------------|
| Log Analytics (PerGB2018 / Pay-As-You-Go) | **$2.30 per GB** | 5 GB/month per billing account |
| Application Insights (workspace-based) | **$2.30 per GB** | Uses same Log Analytics allowance |
| Basic Logs ingestion | $0.50 per GB | — |
| Data retention (beyond 31/90 days) | $0.10 per GB/month | 31 days free (Analytics), 90 days (App Insights) |

- Workspace-based Application Insights uses the **same** Log Analytics pricing ($2.30/GB)
- Commitment tiers available for high volume (100+ GB/day = $1.96/GB, 15% savings)

### GitHub Enterprise Cloud

| Plan | Price | Key Features |
|------|-------|-------------|
| Free | $0/user/month | Public repos, basic CI/CD |
| Team | $4/user/month | Private repos, 3,000 CI minutes |
| **Enterprise Cloud** | **$21/user/month** | SAML SSO, advanced audit, GHAS available |

- Enterprise Cloud price confirmed on github.com/pricing (April 2026)
- GitHub Advanced Security is additional cost on top of Enterprise
