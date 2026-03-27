# Architecture Audit Research — March 2026

## Executive Summary

This research covers 7 critical topics for a production architecture audit of the Azure Governance Platform. **All 7 topics reveal actionable security or reliability concerns** that should be addressed before the next production release.

### 🔴 Critical Findings (Immediate Action Required)

| # | Topic | Severity | Finding |
|---|-------|----------|---------|
| 1 | python-jose JWT library | **CRITICAL** | 3 unpatched CVEs, including signature forgery (CVE-2024-33663). Migrate to `PyJWT` or `joserfc` immediately. |
| 6 | Bicep secret output leakage | **CRITICAL** | `sql-server.bicep` outputs connection string with plaintext password. Exposed in deployment history. Bicep linter already flags this. |
| 5 | Azure SQL public network access | **HIGH** | `publicNetworkAccess: 'Enabled'` with `AllowAllAzureIps` firewall rule. Should use Private Endpoints + disable public access. |

### 🟠 High Findings (Address Before Next Release)

| # | Topic | Severity | Finding |
|---|-------|----------|---------|
| 3 | In-memory token blacklist | **HIGH** | Without Redis, blacklisted tokens survive only until process restart. Any App Service restart/redeploy clears the blacklist. |
| 4 | APScheduler in single process | **HIGH** | All job state lost on restart. No persistence, no missed-job recovery, no duplicate protection. Critical sync jobs (MFA, compliance) can silently fail. |
| 7 | In-memory rate limiting | **HIGH** | Without Redis, rate limits reset on every restart. Attackers can bypass by waiting for redeployment or restart cycling. |

### 🟡 Medium Findings (Plan for Remediation)

| # | Topic | Severity | Finding |
|---|-------|----------|---------|
| 2 | Azure SQL connection pooling | **MEDIUM** | `pool_size=5 + max_overflow=10 = 15` may exceed S0 tier's 6 external connection limit. Pool recycle at 3600s is good but needs `pool_pre_ping` validation. |

### Key Recommendations Priority Order

1. **Migrate from python-jose** → `PyJWT 2.12.1` (simplest) or `joserfc 1.6.3` (most comprehensive)
2. **Remove connection string from Bicep outputs** — use Key Vault reference instead
3. **Disable Azure SQL public network access** — implement Private Endpoints with VNet integration
4. **Deploy Redis** for token blacklist + rate limiting (or use Azure Cache for Redis Basic tier)
5. **Externalize APScheduler job store** to database or migrate to Azure-native scheduling
6. **Right-size connection pool** for S0 tier constraints (max 6 external connections)

---

*Research conducted: March 27, 2026*
*Researcher: web-puppy-7ad7a7*
*Project: azure-governance-platform v1.6.3*
