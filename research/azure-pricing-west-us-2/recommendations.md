# Recommendations for azure-governance-platform

**Context**: This project is a Python-based Azure governance platform using Docker, Azure SQL, and Azure App Service.

---

## Cost Optimization Scenarios

### Scenario A: Development / Staging Environment (Minimum Viable)
| Service | SKU | Monthly Cost |
|---------|-----|-------------|
| App Service | B1 Basic Linux | $12.41 |
| SQL Database | Free tier | $0.00 |
| Container Registry | Basic | $5.00 |
| Key Vault | Standard (~1K ops) | ~$0.01 |
| App Insights + Log Analytics | ~1 GB/month | $0.00 (within free 5GB) |
| **Total** | | **~$17.42/month** |

⚠️ **No deployment slots** — B1 does not support staging slots.

### Scenario B: Production (Minimum with Staging Slots)
| Service | SKU | Monthly Cost |
|---------|-----|-------------|
| App Service | **S1 Standard Linux** | $58.40 |
| SQL Database | S0 (10 DTU) | $14.72 |
| Container Registry | Basic | $5.00 |
| Key Vault | Standard (~10K ops) | ~$0.03 |
| App Insights + Log Analytics | ~5 GB/month | $0.00 (within free tier) |
| **Total** | | **~$78.15/month** |

✅ **Supports deployment slots** (up to 5) for zero-downtime deployments.

### Scenario C: Production (Recommended)
| Service | SKU | Monthly Cost |
|---------|-----|-------------|
| App Service | **P1v3 Premium v3 Linux** | $113.15 |
| SQL Database | S0 (10 DTU) | $14.72 |
| Container Registry | Standard | $20.00 |
| Key Vault | Standard (~50K ops) | ~$0.15 |
| App Insights + Log Analytics | ~10 GB/month | $11.50 |
| GitHub Enterprise Cloud (5 users) | Enterprise | $105.00 |
| **Total** | | **~$264.52/month** |

✅ Up to 20 deployment slots, VNet integration, more CPU/RAM, geo-replication ready.

### Scenario D: Production with Reserved Instances
Same as Scenario C but with P1v3 1-Year RI:
| Service | Change | Savings |
|---------|--------|---------|
| App Service P1v3 | $113.15 → $73.75/mo (1yr RI) | **-$39.40/month** |
| App Service P1v3 | $113.15 → $51.08/mo (3yr RI) | **-$62.07/month** |

---

## Key Recommendations

### 1. Deployment Slots Strategy
**Use S1 Standard ($58.40/month) minimum for production** — it's the cheapest tier with staging slots. The jump from B1 ($12.41) to S1 ($58.40) is $45.99/month but buys you:
- Zero-downtime deployments via slot swapping
- Up to 5 deployment slots
- Auto-scale support
- 50 GB storage (vs 10 GB on Basic)

### 2. Observability Cost Control
- Application Insights and Log Analytics **share the same 5 GB/month free allowance**
- Implement **sampling** in Application Insights to reduce ingestion volume
- Use **Basic Logs** ($0.50/GB) instead of Analytics Logs ($2.30/GB) for verbose logs that don't need full query capability
- Set **daily caps** to prevent runaway costs

### 3. Container Registry
- **Basic ($5/month)** is sufficient for most single-app deployments (10 GB storage)
- Upgrade to **Standard ($20/month)** only if you need geo-replication, more webhooks, or >10 GB of images

### 4. SQL Database Free Tier Limitations
- 32 MB storage limit
- 5 DTU only
- No SLA
- 1 free database per subscription
- **Suitable only for dev/test**, never production

### 5. Key Vault Cost
- Key Vault is essentially free for typical app usage
- At $0.03/10K transactions, even 100K ops/month costs only $0.30
- No monthly base fee — pure consumption
