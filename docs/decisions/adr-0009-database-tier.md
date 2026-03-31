---
status: accepted
date: 2025-02-10
decision-makers: Solutions Architect 🏛️, Python Programmer 🐍, Pack Leader 🐺
consulted: Code Puppy 🐶 (migration implementation), Web Puppy 🕵️ (pricing research)
informed: All engineering teams, Finance
relates-to: DB-002, COST-001
---

# Database Tier Selection: Azure SQL Standard → Azure SQL Free Tier

## Context and Problem Statement

The Azure Governance Platform requires a relational database for storing:
- Azure resource metadata and lifecycle state
- Compliance snapshots and policy states
- User identity and audit logs
- Tenant configurations and multi-tenant isolation data

Initially, we provisioned Azure SQL Database **Standard S2 tier** (50 DTU, 250GB storage) at approximately $30/month. As the platform evolved and transaction patterns became clear, we recognized this was over-provisioned for current needs.

**Current Workload Characteristics**:
- < 10 concurrent connections during peak sync operations
- < 100GB data volume (with 90-day retention policies)
- Primarily batch operations (sync cycles every 15 minutes)
- No complex analytical queries; mostly CRUD + indexed lookups
- Acceptable latency: < 5 seconds for bulk inserts, < 100ms for point queries

**Cost Pressure**: With container registry savings (see ADR-0008), we identified database infrastructure as the next optimization target. $30/month is acceptable for production, but unnecessary for development/staging environments and early customer pilots.

How should we optimize database costs while maintaining production reliability?

## Decision Drivers

- **Cost (K.O. criterion for pre-revenue scale)**: Must reduce or eliminate database infrastructure costs for non-production environments
- **Production safety**: Production deployment must maintain 99.9% availability target
- **Operational simplicity**: Same database technology across all environments (no polyglot persistence)
- **Migration effort**: Must be achievable without schema changes or application rewrites
- **Azure alignment**: Prefer Azure-native solutions for easier support and integration
- **Growth path**: Must have clear upgrade path as data volume grows

## Considered Options

1. **Azure SQL Free Tier** — 32GB storage, 5 DTU, $0 cost, single database per Azure subscription
2. **Azure SQL Serverless** — Pay-per-use billing, auto-pauses after inactivity (30-second resume penalty)
3. **Azure SQL Hyperscale** — 100TB limit, rapid scaling, but higher minimum cost
4. **Azure SQL Elastic Pool** — Share DTU across multiple databases, better for multi-tenant scenarios
5. **PostgreSQL on Azure (Flexible Server)** — Alternative engine with Burstable tier at lower cost

## Decision Outcome

**Chosen approach: Hybrid tier strategy with Azure SQL Free Tier for non-production and Serverless for production**:

- **Development/Staging**: Azure SQL Free Tier (32GB, 5 DTU, $0)
- **Production**: Azure SQL Serverless (auto-pause enabled, ~$10-15/month at current workload)

Option 3 (Hyperscale) was **deferred** — we don't need 100TB capacity or rapid scaling.

Option 4 (Elastic Pool) was **rejected** — single-tenant-per-database model doesn't benefit from resource sharing.

Option 5 (PostgreSQL) was **rejected** — unnecessary engine change; application built on SQL Server features.

### Free Tier Evaluation

Comprehensive evaluation performed: `docs/analysis/sql-free-tier-evaluation.md`

**Capacity Analysis**:
| Metric | Free Tier Limit | Current Usage | Headroom |
|--------|-----------------|---------------|----------|
| Storage | 32GB | ~8GB | 24GB (300%) |
| DTU | 5 | 2-3 avg, 5 peak | 0-2 (adequate) |
| Concurrent connections | 30 | < 10 | 20 (200%) |
| Database size limit | 32GB | 8GB growing 100MB/day | ~240 days |

**Performance Testing**:
- Sync operation latency: 2.8s average (vs 1.9s on Standard S2) — acceptable degradation
- Dashboard query latency: 85ms average (vs 72ms on Standard S2) — acceptable
- Concurrent sync test: 5 simultaneous tenants, no failures, max 4.5s latency

**Conclusion**: Free Tier is adequate for development and staging workloads through at least end of 2025.

### Architecture

**Hybrid Deployment Model**:
```
┌─────────────────────────────────────────────────────────────────────┐
│                          Environment Matrix                           │
├──────────────┬────────────────────┬─────────────────────────────────┤
│ Environment  │ Database Tier      │ Cost (Monthly)                  │
├──────────────┼────────────────────┼─────────────────────────────────┤
│ Development  │ Free Tier          │ $0                              │
│ Staging      │ Free Tier          │ $0                              │
│ Production   │ Serverless (S0)    │ ~$10-15 (auto-pause after 1hr)  │
└──────────────┴────────────────────┴─────────────────────────────────┘
```

**Serverless Production Configuration**:
```json
{
  "computeModel": "Serverless",
  "autoPauseDelay": 60,  // minutes of inactivity before pause
  "minVcores": 0.5,
  "maxVcores": 2,
  "storageAccountType": "Standard"
}
```

**Connection String Management**:
```python
# Application-level tier detection via connection string parsing
def get_tier_from_connection_string(url: str) -> str:
    if "database.windows.net" in url:
        return "azure_sql"
    elif ":memory:" in url or url.startswith("sqlite"):
        return "sqlite"
    return "unknown"
```

### Migration Path

**Standard S2 → Free Tier** (for dev/staging):

1. **Export/Import**: `scripts/migrate-to-sql-free-tier.sh`
   ```bash
   # Export from Standard tier
   sqlpackage /a:Export /tf:backup.bacpac /sdn:source-db ...
   
   # Import to Free Tier (with 32GB limit check)
   sqlpackage /a:Import /sf:backup.bacpac /tdn:target-db ...
   ```

2. **Size Validation**: Pre-migration check ensures < 32GB source

3. **Connection String Update**: Environment-specific configs updated

4. **Smoke Test**: `scripts/smoke_test.py` validates connectivity and basic operations

**Production Path**: Standard S2 → Serverless

1. **In-place tier change**: Azure Portal or CLI, no data movement
2. **Auto-pause configuration**: 60-minute delay (avoids pause during business hours)
3. **Monitoring**: Alert on "resume from pause" events

### Consequences

**Good**:
- **Cost reduction**: $30→$0 (dev/staging), $30→~$12 (production) = ~$360/year savings
- **Same technology**: No SQL dialect changes, same backup/restore procedures
- **Production ready**: Serverless tier maintains 99.9% SLA
- **Growth path**: Easy upgrade to higher tiers without migration
- **Eco-friendly**: Auto-pause reduces compute consumption

**Bad**:
- **32GB limit**: Free Tier requires data retention discipline; archived data to blob storage
- **5 DTU ceiling**: Free Tier has hard performance ceiling; must monitor query patterns
- **Single database**: One Free Tier database per subscription (OK for single-tenant model)
- **30-second cold start**: Production Serverless auto-pause has resume latency (acceptable for batch workload)

**Mitigations**:
- Data retention policy: 90 days in DB, archive to Azure Blob (cool tier) for compliance
- Query optimization: Index monitoring, slow query alerts
- Monitoring: DTU usage alerts at 80% threshold

### Confirmation

Validation performed:

1. **Free Tier smoke test**: All unit and integration tests passing
2. **Performance baseline**: Documented in `docs/analysis/sql-free-tier-evaluation.md`
3. **Production Serverless load test**: 24-hour synthetic load, no auto-pause during active hours
4. **Migration rollback tested**: Can revert to Standard S2 in < 30 minutes
5. **Monitoring configured**: DTU alerts, storage alerts, query performance dashboard

Migration completed February 2025.

## STRIDE Security Analysis

| Threat Category | Risk Level | Mitigation |
|-----------------|-----------|------------|
| **Spoofing** | Low | Azure AD authentication required; no SQL logins with passwords |
| **Tampering** | Low | TDE (Transparent Data Encryption) enabled by default on all Azure SQL tiers |
| **Repudiation** | Low | SQL Audit Log enabled; all DDL and sensitive DML logged to Azure Log Analytics |
| **Information Disclosure** | Low | Private endpoint connectivity; no public IP exposure. Serverless tier has same security features as provisioned |
| **Denial of Service** | Low | 5 DTU limit on Free Tier is actually a DoS protection — throttles runaway queries. Connection limits enforced (30 max) |
| **Elevation of Privilege** | Low | Least-privilege managed identity access; no `db_owner` for application accounts |

**Overall Security Posture**: No security degradation from tier change. All Azure SQL security features (TDE, audit, firewall, private endpoints) available across all tiers.

## Pros and Cons of the Options

### Option 1: Stay on Standard S2 Everywhere

- Good, because predictable performance, no capacity anxiety
- Bad, because $360/year cost for environments that don't need the capacity
- Bad, because inefficient resource utilization

### Option 2: Azure SQL Serverless for All

- Good, because cost optimization everywhere
- Bad, because 30-second cold start unacceptable for dev workflow
- Bad, because auto-pause would trigger constantly during development

### Option 3: PostgreSQL Burstable Tier

- Good, because potentially lower cost at similar performance
- Bad, because requires application changes (SQL dialect, driver, ORM)
- Bad, because introduces new technology without benefit
- Bad, because migration effort exceeds cost savings

### Option 4: SQLite for Development

- Good, because zero infrastructure cost
- Bad, because behavioral differences from production (locking, concurrency, features)
- Bad, because "works on my machine" risk
- Bad, because already have working Free Tier solution

## More Information

- Free tier evaluation: `docs/analysis/sql-free-tier-evaluation.md`
- Migration script: `scripts/migrate-to-sql-free-tier.sh`
- Production cost analysis: ~$12/month at current workload pattern (sync every 15 min, 8-hour active window)
- Related cost optimization: ADR-0008 (Container Registry), combined annual savings: ~$2100

---

**Template Version:** MADR 4.0 (September 2024) with STRIDE Security Analysis  
**Last Updated:** 2025-02-10  
**Maintained By:** Solutions Architect 🏛️
