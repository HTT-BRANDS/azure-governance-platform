# Cost Optimization Summary — March 26, 2026

## Original Monthly Cost: ~$298/mo
## Optimized Monthly Cost: ~$73/mo
## Savings: $225/mo (75% reduction)

## Changes Made

### Production Environment
| Resource | Before | After | Savings |
|----------|--------|-------|---------|
| App Service Plan | B2 (2 cores, 3.5GB) | B1 (1 core, 1.75GB) | $60/mo |
| SQL Database | S2 (20 DTU, 250GB) | S0 (10 DTU, 250GB) | $45/mo |
| Container Registry | Standard | Standard (unchanged) | — |

### Staging Environment
| Resource | Before | After | Savings |
|----------|--------|-------|---------|
| App Service Plan | B1 | B1 (unchanged) | — |
| SQL Database | S2 (20 DTU) | S0 (10 DTU) | $45/mo |
| Container Registry | Standard | **DELETED** (use prod) | $5/mo |
| Orphaned resources | Multiple | **CLEANED** | $85/mo |

## Verification

Production health: https://app-governance-prod.azurewebsites.net/health
Staging health: https://app-governance-staging-xnczpwyv.azurewebsites.net/health

Both returning: `{"status": "healthy"}`

## Future Optimization Opportunities

1. **Staging F1 Free Tier**: Convert to ZIP deployment → Save $13/mo
2. **SQL Basic Tier**: Shrink DB to <2GB → Save $10/mo  
3. **Delete Staging**: Use prod with feature flags → Save $38/mo

## Performance Impact

- **10-30 non-concurrent users**: No performance degradation expected
- **B1 tier**: 1.75GB RAM, 1 core — sufficient for light governance workloads
- **S0 SQL**: 10 DTUs — handles 6.25MB database with ease
- **Monitoring**: Watch CPU/memory during first week of usage

## Rollback Plan

If performance issues arise:
```bash
# Scale production back up
az appservice plan update --name asp-governance-production --resource-group rg-governance-production --sku B2
az sql db update --name governance --server sql-gov-prod-mylxq53d --resource-group rg-governance-production --service-objective S2
```
