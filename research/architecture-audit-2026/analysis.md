# Multi-Dimensional Analysis

## Topic 1: python-jose JWT Library Security Status

### Current State
- **Latest version**: python-jose 3.5.0 (released May 28, 2025)
- **GitHub**: 88 open issues, 15 open PRs — multiple unaddressed security issues
- **Dependency**: `python-rsa` library is **retired** (issue #392)
- **Project usage**: `from jose import jwt` in `app/core/auth.py` for both token creation (HS256) and Azure AD validation (RS256)

### Known CVEs (All Unpatched in python-jose)

| CVE | Severity | Type | Description | Affected Versions |
|-----|----------|------|-------------|-------------------|
| **CVE-2024-33663** | HIGH | Algorithm Confusion | OpenSSH ECDSA key algorithm confusion allows signature forgery. CWE-327: Use of Broken Cryptographic Algorithm. | ≤ 3.3.0 |
| **CVE-2024-33664** | MEDIUM | Denial of Service | JWE "JWT bomb" — crafted token with high compression ratio causes resource exhaustion. | ≤ 3.3.0 |
| **CVE-2024-23342** | HIGH | Timing Attack (transitive) | Minerva timing attack in `ecdsa` dependency. No patched version of `ecdsa` exists. Allows ECDSA signature forgery via timing side-channel. | ≤ 0.18.0 (ecdsa) |

### Open Security Issues (GitHub, March 2026)
- **#399**: Minerva timing attack vulnerability in python-ecdsa usage (2 weeks old)
- **#398**: DER key algorithm confusion, empty HMAC key, and timing side-channels (3 weeks old)
- **#390**: CVE-2024-23342 report — no assignee, no milestone, no fix planned (since Oct 2025)
- **#392**: Python-RSA dependency library is **retired** — no longer maintained

### Security Analysis
- **Direct risk to project**: The project uses HS256 for internal tokens and RS256 for Azure AD tokens. CVE-2024-33663 (ECDSA confusion) may not directly apply to HS256/RS256, but the library's security posture is fundamentally compromised.
- **Transitive risk**: The `ecdsa` and `python-rsa` dependencies are unmaintained/retired.
- **Supply chain risk**: 88 unresolved issues with security reports sitting unactioned for 5+ months signals abandoned maintenance.

### Recommended Replacements

| Library | Version | Last Release | Maintainer | Best For |
|---------|---------|-------------|------------|----------|
| **PyJWT** | 2.12.1 | Mar 13, 2026 | Auth0/Okta (Jpadilla) | JWT-only use cases. Simplest migration path. 99% codecov. |
| **joserfc** | 1.6.3 | Feb 25, 2026 | Hsiaoming Yang (Authlib author) | Full JOSE stack (JWS, JWE, JWK, JWA, JWT). Most comprehensive. |

### Migration Complexity
- **PyJWT**: Low. API is similar. `jwt.encode()`/`jwt.decode()` work nearly identically. Need to change `from jose import jwt` → `import jwt`. Algorithm parameter syntax differs slightly.
- **joserfc**: Medium. Different API paradigm (`joserfc.jwt.encode(header, claims, key)`) but more RFC-compliant.

---

## Topic 2: Azure SQL Connection Pooling for FastAPI/SQLAlchemy

### Current Project Configuration (from `app/core/config.py` and `database.py`)
```python
pool_size = 5          # DB_POOL_SIZE
max_overflow = 10      # DB_MAX_OVERFLOW  
pool_timeout = 30      # DB_POOL_TIMEOUT
pool_pre_ping = True   # Verify connections before use
pool_recycle = 3600    # Recycle connections after 1 hour
```

### Azure SQL S0 Tier Limits (Verified from Microsoft Docs)

| Resource | S0 Limit |
|----------|----------|
| Max DTUs | 10 |
| Max concurrent workers | 60 |
| Max concurrent logins | 60 |
| **Max concurrent external connections** | **6** |
| Max concurrent sessions | 600 |
| Max storage | 250 GB |

### ⚠️ Critical Issue: Connection Exhaustion Risk

The project configures `pool_size=5 + max_overflow=10 = 15 potential connections`, but **Azure SQL S0 allows only 6 concurrent external connections**. This means:

1. Under load, SQLAlchemy may attempt to open up to 15 connections
2. Azure SQL will reject connections beyond 6, causing `Error 10928` (resource limit reached)
3. The `max_overflow=10` is dangerously high for S0 tier

### Recommended Configuration for S0 on B1 App Service

```python
# Conservative settings for Azure SQL S0 + single-worker B1
pool_size = 3           # Stay well under 6 external connection limit
max_overflow = 2        # Allow 5 total max (3+2), leaving 1 for admin/monitoring
pool_timeout = 30       # Acceptable for B1
pool_pre_ping = True    # CRITICAL: detect dropped Azure SQL connections
pool_recycle = 1800     # 30 minutes (Azure SQL idle timeout is ~30 min)
pool_reset_on_return = "rollback"  # Clean state for recycled connections
```

### Additional Recommendations
- **pool_recycle**: Reduce from 3600s to 1800s — Azure SQL aggressively closes idle connections (default ~30 min idle timeout)
- **pool_pre_ping**: Already enabled ✅ — essential for Azure SQL which drops idle connections
- **Connection string**: Add `Connection Timeout=30;` and `Command Timeout=30;` to pyodbc connection string
- **Health check**: Implement a periodic `SELECT 1` health check endpoint that validates pool health

---

## Topic 3: In-Memory Token Blacklist Security Risks

### Current Implementation Analysis (`app/core/token_blacklist.py`)
The project implements a **Redis-preferred, in-memory-fallback** pattern:
```python
class TokenBlacklist:
    def __init__(self):
        self._memory_fallback: set[str] = set()
        self._redis = None
        self._init_redis()  # Try Redis, fallback to memory
```

### Failure Modes in Production (Without Redis)

| Scenario | Impact | Likelihood on Azure B1 |
|----------|--------|----------------------|
| **App Service restart** (platform-initiated) | All blacklisted tokens become valid again. Logged-out users regain access. | High — happens during updates, scaling, health check failures |
| **Deployment/redeploy** | Blacklist cleared. Any revoked tokens work again until they naturally expire. | Certain — every deployment |
| **Process crash** | Complete blacklist loss | Medium |
| **Memory pressure** | Set grows unbounded (no TTL in memory mode) until OOM | Low on B1 (1.75 GB RAM) but possible with long token lifetimes |
| **Worker recycling** | Azure App Service recycles workers periodically (default every 29 hours) | Certain |

### Security Implications
1. **Logout is not honored**: User logs out → token added to blacklist → App Service restarts → blacklisted token works again
2. **Token revocation is unreliable**: Admin revokes compromised token → restart clears revocation → attacker can reuse token
3. **No memory TTL**: In-memory set has no automatic cleanup (unlike Redis with SETEX TTL). Tokens accumulate until process restart.
4. **False sense of security**: The blacklist "works" in development but silently fails in production

### Risk Assessment
- With current JWT expiry of **30 minutes** (access tokens), the window of vulnerability is limited but real
- With **7-day refresh tokens**, a blacklist failure means revoked refresh tokens remain valid for up to 7 days
- Azure App Service B1 typically restarts: during deployments, during platform updates (monthly), during health check failures, and on periodic worker recycling

---

## Topic 4: APScheduler in Single-Process Production

### Current Implementation Analysis
The project runs **two APScheduler instances** in the same process:
1. `app/core/scheduler.py` — General sync scheduler (costs, compliance, resources, identity, DMARC)
2. `app/core/riverside_scheduler.py` — Riverside-specific scheduler (MFA, threats, reports)

Both use `AsyncIOScheduler` with **default memory job store** (no persistence).

### Risks on Azure App Service B1

| Risk | Description | Impact |
|------|-------------|--------|
| **All jobs lost on restart** | Memory job store means zero persistence. Restart = all scheduled jobs must be re-registered at startup. | Jobs registered with `replace_existing=True` handle this correctly, but any **state** (last run time, next run time) is lost. |
| **Missed jobs not recovered** | Without a persistent job store, the scheduler cannot detect misfired jobs after restart. The `misfire_grace_time` parameter only works if the scheduler is running when the misfire is detected. | If the daily 1 AM sync is due during a restart window, it silently doesn't run. No audit trail. |
| **No duplicate protection** | If multiple workers/instances are started (even transiently during deployment), each starts its own scheduler. Both will execute the same jobs. | Duplicate API calls to Azure, duplicate data syncs, potential data corruption. |
| **Azure App Service restart behavior** | B1 tier restarts: platform updates, deployment slots, health check failures, "Always On" ping failures, and periodic recycling (~29 hours by default). | Jobs can be interrupted mid-execution with no cleanup or retry. |
| **Blocking the event loop** | APScheduler `AsyncIOScheduler` runs in the same asyncio event loop as FastAPI. A long-running sync job can block request handling. | API latency spikes during sync jobs. |

### APScheduler Documentation Warning
> "Sometimes the scheduler may be unable to execute a scheduled job at the time it was scheduled to run. The most common case is when a job is scheduled in a **persistent job store** and the scheduler is shut down and restarted after the job was supposed to execute."

The project uses the **non-persistent (memory) store**, meaning misfired jobs are **silently lost** rather than detected and re-executed.

### Alternatives

| Solution | Complexity | Azure-Native | Persistence |
|----------|-----------|--------------|-------------|
| APScheduler + SQLAlchemyJobStore | Low | No | Yes (DB) |
| Azure Functions Timer Triggers | Medium | Yes | Yes (Azure) |
| Azure Logic Apps | Medium | Yes | Yes (Azure) |
| Celery + Redis/Azure Service Bus | High | Partial | Yes |

---

## Topic 5: Azure SQL Public Network Access

### Current Infrastructure Configuration (`infrastructure/modules/sql-server.bicep`)
```bicep
properties: {
    publicNetworkAccess: 'Enabled'          // ⚠️ SECURITY ISSUE
    restrictOutboundNetworkAccess: 'Disabled'
    minimalTlsVersion: '1.2'               // ✅ Good
}

// Firewall rule — allows ANY Azure service
resource allowAzureServices ... {
    startIpAddress: '0.0.0.0'              // ⚠️ OVERLY PERMISSIVE
    endIpAddress: '0.0.0.0'
}
```

### Security Assessment

| Setting | Current | Recommended | Risk Level |
|---------|---------|-------------|------------|
| `publicNetworkAccess` | `Enabled` | `Disabled` | **HIGH** |
| Firewall: AllowAllAzureIps | `0.0.0.0-0.0.0.0` | Remove (use Private Endpoints) | **HIGH** |
| `minimalTlsVersion` | `1.2` | `1.2` (correct) | ✅ OK |
| Private Endpoints | Not configured | Should be configured | **HIGH** |
| VNet Integration | Optional (`enableVNetIntegration=false`) | Required for production | **HIGH** |

### Microsoft's Official Guidance (March 2026)
1. **Azure Security Benchmark v3**: Recommends disabling public network access for all PaaS data services
2. **Microsoft Defender for Cloud**: Flags `publicNetworkAccess: 'Enabled'` as a security finding
3. **Private Link documentation**: Explicitly warns that adding a private endpoint does NOT automatically block public access — you must explicitly set "Deny public network access"

### The `AllowAllAzureIps` Anti-Pattern
The `0.0.0.0` to `0.0.0.0` firewall rule allows **any Azure service in any subscription** to connect. This includes:
- Other customers' Azure resources
- Compromised Azure VMs anywhere in Azure
- Azure services in any region globally

This is **not** limited to the project's own subscription or resource group.

---

## Topic 6: Bicep IaC Secret Output Leakage

### Current Vulnerability (`infrastructure/modules/sql-server.bicep`)
```bicep
output connectionString string = 'Server=tcp:${sqlServer.properties.fullyQualifiedDomainName},1433;Database=${databaseName};User ID=${adminUsername};Password=${adminPassword};Encrypt=true;...'
```

### Where This Secret Is Exposed
1. **Azure deployment history**: The output value is stored in plaintext in the resource group's deployment history (visible in Azure Portal → Resource Group → Deployments)
2. **ARM deployment API**: Queryable via `GET /providers/Microsoft.Resources/deployments/{name}?api-version=2023-07-01`
3. **CLI output**: `az deployment sub show` displays the connection string in terminal
4. **CI/CD logs**: If the deployment step captures output, the password appears in pipeline logs
5. **deploy-output.json**: The project's own output file (committed to repo or generated locally)

### Bicep Linter Already Flags This
The project's `infrastructure/deploy-output.json` contains these warnings:
```
Warning outputs-should-not-contain-secrets: Outputs should not contain secrets. 
Found possible secret: secure value 'adminUsername'
Warning outputs-should-not-contain-secrets: Outputs should not contain secrets. 
Found possible secret: secure value 'adminPassword'
```

### Remediation Options
1. **Remove the output entirely** — connection string should be constructed at deployment time and stored in Key Vault
2. **Use `@secure()` decorator** (Bicep ≥0.35.1) — prevents logging but still passes through ARM:
   ```bicep
   @secure()
   output connectionString string = '...'
   ```
3. **Best practice**: Output only the server FQDN and database name. Store credentials in Key Vault. Construct connection string in application configuration.

---

## Topic 7: FastAPI Rate Limiting Without Redis

### Current Implementation Analysis (`app/core/rate_limit.py`)

```python
class RateLimiter:
    def __init__(self):
        self._redis = None
        self._memory_cache: dict[str, tuple[int, float]] = {}  # (count, reset_time)
        # ...
    
    async def is_allowed(self, request, config):
        try:
            if self._redis:
                return await self._check_redis_limit(key, config)
            else:
                return self._check_memory_limit(key, config)
        except Exception as e:
            # Fail open - allow request if rate limiting fails
            return True, {}   # ⚠️ FAIL-OPEN
```

### Vulnerabilities Without Redis

| Attack Vector | Impact | Difficulty |
|--------------|--------|------------|
| **Restart cycling** | Attacker waits for/triggers App Service restart, rate limits reset | Easy |
| **Deployment window** | During deployment, new process starts with empty rate limit cache | Trivial |
| **Distributed attack** | Multiple IPs attack from different sources — memory cache is per-process | Medium |
| **Memory exhaustion** | Flood with unique IPs to grow `_memory_cache` dict unboundedly | Medium |
| **Fail-open on error** | Any exception in rate limit check allows the request through | Depends |

### Rate Limit Configuration Analysis

| Endpoint Type | Limit | Window | Adequate? |
|--------------|-------|--------|-----------|
| Login | 5 req | 300s (5 min) | ✅ Good limit, but ineffective without persistence |
| Auth | 10 req | 60s | ✅ Good limit, but ineffective without persistence |
| Sync | 5 req | 60s | ✅ Good limit, but ineffective without persistence |
| Bulk | 3 req | 60s | ✅ Good limit, but ineffective without persistence |
| Default | 100 req | 60s | ⚠️ Generous for B1 tier |

### Key Concern: Login Brute Force
The login endpoint has a 5-request-per-5-minute limit. Without Redis:
- An attacker can brute-force 5 passwords, wait for App Service restart (or trigger one), and try 5 more
- The `fail-open` design means any error bypasses rate limiting entirely
- With `X-Forwarded-For` spoofing (if not validated at load balancer), attackers can rotate identifiers

### Cleanup Concern
```python
# Clean old entries periodically
if len(self._memory_cache) > 10000:
    self._memory_cache = {k: v for k, v in self._memory_cache.items() if v[1] > now}
```
This cleanup only triggers at 10,000 entries and performs a full dict comprehension (O(n)), which can cause latency spikes.
