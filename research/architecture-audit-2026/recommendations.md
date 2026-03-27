# Project-Specific Recommendations

## Priority 1: CRITICAL — Immediate Action Required

### 1.1 Migrate from python-jose to PyJWT

**Why**: 3 unpatched CVEs (CVE-2024-33663, CVE-2024-33664, CVE-2024-23342), retired dependencies, 88 open issues with security reports unactioned for 5+ months.

**Recommended replacement**: `PyJWT 2.12.1` (simplest migration for this project)

**Migration steps for `app/core/auth.py`**:

```python
# BEFORE (python-jose)
from jose import JWTError, jwt

token = jwt.encode(payload, secret, algorithm="HS256")
decoded = jwt.decode(token, secret, algorithms=["HS256"], audience="...", issuer="...")

# AFTER (PyJWT)
import jwt
from jwt.exceptions import InvalidTokenError  # replaces JWTError

token = jwt.encode(payload, secret, algorithm="HS256")
decoded = jwt.decode(token, secret, algorithms=["HS256"], audience="...", issuer="...")
```

**Key differences to handle**:
- `JWTError` → `jwt.exceptions.InvalidTokenError`
- `jwt.get_unverified_header()` → `jwt.get_unverified_header()` (same API ✅)
- `jwt.get_unverified_claims()` → `jwt.decode(token, options={"verify_signature": False})`
- Azure AD JWKS validation: PyJWT has `jwt.PyJWKClient` for JWKS fetching (simplifies the custom `_get_jwks` code)

**Dependency change** in `pyproject.toml`:
```toml
# Remove: "python-jose[cryptography]>=3.3.0"
# Add:    "PyJWT[crypto]>=2.12.0"
```

**Estimated effort**: 4-8 hours (auth.py + token_blacklist.py + tests)

---

### 1.2 Remove Connection String from Bicep Outputs

**Why**: `infrastructure/modules/sql-server.bicep` outputs a connection string containing the admin password. This is stored in Azure deployment history, visible in the portal, queryable via API, and captured in CI/CD logs.

**Current vulnerable code**:
```bicep
output connectionString string = 'Server=tcp:${sqlServer.properties.fullyQualifiedDomainName},1433;Database=${databaseName};User ID=${adminUsername};Password=${adminPassword};...'
```

**Fix — Option A (Recommended): Remove output, use Key Vault**:
```bicep
// Remove the connectionString output entirely

// Instead, store in Key Vault during deployment:
resource kvSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'sql-connection-string'
  properties: {
    value: 'Server=tcp:${sqlServer.properties.fullyQualifiedDomainName},1433;Database=${databaseName};User ID=${adminUsername};Password=${adminPassword};Encrypt=true;TrustServerCertificate=false;Connection Timeout=30;'
  }
}

// Output only non-sensitive values:
output serverId string = sqlServer.id
output serverName string = sqlServer.name
output serverFqdn string = sqlServer.properties.fullyQualifiedDomainName
output databaseName string = sqlDatabase.name
```

**Fix — Option B (Minimum): Use @secure() decorator**:
```bicep
@secure()
output connectionString string = '...'
```
Note: This prevents logging but the value still passes through ARM. Option A is strongly preferred.

**Also required**: Rotate the SQL admin password since it may already be exposed in deployment history.

**Estimated effort**: 2-4 hours

---

## Priority 2: HIGH — Address Before Next Release

### 2.1 Disable Azure SQL Public Network Access

**Why**: `publicNetworkAccess: 'Enabled'` with `AllowAllAzureIps (0.0.0.0)` allows any Azure service in any subscription globally to attempt connections.

**Implementation plan**:

1. **Enable VNet integration** for App Service (set `enableVNetIntegration = true` in main.bicep)
2. **Create Private Endpoint** for Azure SQL in the VNet:
   ```bicep
   resource sqlPrivateEndpoint 'Microsoft.Network/privateEndpoints@2023-05-01' = {
     name: 'pe-${sqlServerName}'
     location: location
     properties: {
       subnet: { id: vnet.outputs.privateEndpointSubnetId }
       privateLinkServiceConnections: [{
         name: 'sql-connection'
         properties: {
           privateLinkServiceId: sqlServer.id
           groupIds: ['sqlServer']
         }
       }]
     }
   }
   ```
3. **Disable public access**:
   ```bicep
   properties: {
     publicNetworkAccess: 'Disabled'  // Changed from 'Enabled'
   }
   ```
4. **Remove the AllowAllAzureIps firewall rule** entirely
5. **Configure Private DNS Zone** for `privatelink.database.windows.net`

**Cost impact**: Private Endpoints are free. VNet integration requires at least B1 plan (already in use). The private DNS zone costs ~$0.50/month.

**⚠️ Warning**: This change requires the App Service to have VNet integration configured BEFORE disabling public access, or the app will lose database connectivity.

**Estimated effort**: 8-16 hours (including testing and validation)

---

### 2.2 Deploy Redis for Token Blacklist and Rate Limiting

**Why**: Without Redis, both the token blacklist and rate limiter use in-memory storage that is lost on every restart, deployment, or worker recycle.

**Recommended**: Azure Cache for Redis Basic C0 tier
- **Cost**: ~$16/month (Basic C0, 250 MB)
- **Latency**: <1ms within same region
- **Persistence**: Survives app restarts

**Implementation**:
1. Add Azure Cache for Redis to Bicep infrastructure
2. Set `REDIS_URL` environment variable on App Service
3. Both `TokenBlacklist` and `RateLimiter` already support Redis — they'll auto-detect it

**Alternative (budget option)**: Use Azure SQL as the backing store for the token blacklist:
```python
# Simple SQL-backed blacklist table
class BlacklistedToken(Base):
    __tablename__ = "blacklisted_tokens"
    token_hash = Column(String(64), primary_key=True)  # SHA-256 hash, not full token
    expires_at = Column(DateTime, index=True)
```
This avoids adding Redis but adds DB load. Use a periodic cleanup job to delete expired entries.

**Estimated effort**: 4-8 hours (Redis) or 8-16 hours (SQL-backed)

---

### 2.3 Externalize APScheduler Job Store

**Why**: All 11 scheduled jobs use in-memory storage. Process restart loses all state. Missed jobs are silently dropped.

**Recommended: SQLAlchemy Job Store** (uses existing database):
```python
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

scheduler = AsyncIOScheduler(
    jobstores={
        'default': SQLAlchemyJobStore(url=settings.database_url)
    },
    job_defaults={
        'coalesce': True,           # Roll missed executions into one
        'max_instances': 1,         # Prevent duplicate execution
        'misfire_grace_time': 3600  # 1 hour grace period for misfires
    }
)
```

**Additional safeguards**:
- Add `coalesce=True` to all job definitions to prevent burst re-execution after restart
- Add `max_instances=1` to prevent duplicate execution during deployment overlap
- Set `misfire_grace_time` appropriately per job type
- Consider adding a database-backed lock to prevent duplicate scheduler instances

**Alternative**: Migrate critical jobs (daily sync, MFA checks) to Azure Functions Timer Triggers for cloud-native scheduling with built-in persistence and monitoring.

**Estimated effort**: 4-8 hours (SQLAlchemy job store) or 16-24 hours (Azure Functions migration)

---

## Priority 3: MEDIUM — Plan for Remediation

### 3.1 Right-Size Connection Pool for S0 Tier

**Why**: Current `pool_size=5 + max_overflow=10 = 15` exceeds S0's 6 external connection limit.

**Recommended configuration**:
```python
# In app/core/config.py
database_pool_size: int = Field(default=3, alias="DB_POOL_SIZE")      # Was 5
database_max_overflow: int = Field(default=2, alias="DB_MAX_OVERFLOW") # Was 10
database_pool_timeout: int = Field(default=30, alias="DB_POOL_TIMEOUT")

# In app/core/database.py
_engine_args.update({
    "pool_size": settings.database_pool_size,        # 3
    "max_overflow": settings.database_max_overflow,   # 2 (total max: 5)
    "pool_timeout": settings.database_pool_timeout,   # 30
    "pool_pre_ping": True,                            # Already set ✅
    "pool_recycle": 1800,                             # Was 3600, reduce to 30 min
    "pool_reset_on_return": "rollback",               # Add: clean state
})
```

**Monitoring**: Add a health check endpoint that reports pool status:
```python
@router.get("/health/db-pool")
async def db_pool_health():
    pool = _get_engine().pool
    return {
        "pool_size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "azure_sql_max_external": 6,
    }
```

**Estimated effort**: 2-4 hours

---

## Implementation Roadmap

| Phase | Items | Timeline | Risk Reduction |
|-------|-------|----------|----------------|
| **Phase 1** (Week 1) | 1.1 Migrate python-jose, 1.2 Fix Bicep outputs | 2-3 days | Eliminates 3 CVEs + credential exposure |
| **Phase 2** (Week 2) | 2.2 Deploy Redis, 3.1 Right-size pool | 2-3 days | Reliable token revocation + rate limiting |
| **Phase 3** (Week 3) | 2.1 Private Endpoints, 2.3 Job store | 3-5 days | Network isolation + reliable scheduling |
| **Phase 4** (Week 4) | Validation, penetration testing, documentation | 2-3 days | Verification |

### Total Estimated Effort: 30-55 hours across 4 weeks
