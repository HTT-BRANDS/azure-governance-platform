# Source Credibility Assessment

## Topic 1: python-jose Security Status

| Source | URL | Tier | Currency | Notes |
|--------|-----|------|----------|-------|
| NVD — CVE-2024-33663 | https://nvd.nist.gov/vuln/detail/CVE-2024-33663 | **Tier 1** | Published 04/25/2024, Modified 09/02/2025 | Official US Government vulnerability database. Algorithm confusion with ECDSA keys. CWE-327. |
| NVD — CVE-2024-33664 | https://nvd.nist.gov/vuln/detail/CVE-2024-33664 | **Tier 1** | Published 04/25/2024, Modified 09/02/2025 | Official. DoS via JWE "JWT bomb" high compression ratio. |
| NVD — CVE-2024-23342 | https://nvd.nist.gov/vuln/detail/CVE-2024-23342 | **Tier 1** | Published 01/22/2024, Modified 08/26/2025 | Official. Minerva timing attack in `ecdsa` dependency (transitive). |
| PyPI — python-jose | https://pypi.org/project/python-jose/ | **Tier 1** | v3.5.0, Released May 28, 2025 | Primary source. Package metadata and release history. |
| GitHub — python-jose issues | https://github.com/mpdavis/python-jose/issues | **Tier 2** | Viewed March 2026 | 88 open issues including #398, #399 (security), #390 (CVE-2024-23342), #392 (retired dependency). |
| PyPI — joserfc | https://pypi.org/project/joserfc/ | **Tier 1** | v1.6.3, Released Feb 25, 2026 | Primary source. Actively maintained replacement. |
| PyPI — PyJWT | https://pypi.org/project/PyJWT/ | **Tier 1** | v2.12.1, Released Mar 13, 2026 | Primary source. Backed by Auth0/Okta. 99% codecov. |

## Topic 2: Azure SQL Connection Pooling

| Source | URL | Tier | Currency | Notes |
|--------|-----|------|----------|-------|
| Azure SQL DTU resource limits | https://learn.microsoft.com/en-us/azure/azure-sql/database/resource-limits-dtu-single-databases | **Tier 1** | Current (Azure docs) | Official Microsoft documentation. S0 tier: 60 workers, 6 external connections. |
| SQLAlchemy connection pooling docs | https://docs.sqlalchemy.org/en/20/core/pooling.html | **Tier 1** | SQLAlchemy 2.0 | Official library documentation. |

## Topic 3: In-Memory Token Blacklist

| Source | URL | Tier | Currency | Notes |
|--------|-----|------|----------|-------|
| Project source code | app/core/token_blacklist.py | **Tier 1** | Current | Primary source — actual implementation shows Redis-with-fallback pattern. |
| OWASP JWT Security Cheat Sheet | https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html | **Tier 1** | 2025 | Industry standard security guidance. |

## Topic 4: APScheduler in Production

| Source | URL | Tier | Currency | Notes |
|--------|-----|------|----------|-------|
| APScheduler User Guide | https://apscheduler.readthedocs.io/en/3.x/userguide.html | **Tier 1** | v3.11.2 | Official documentation. Covers missed job executions, coalescing, job stores. |
| Project source code | app/core/scheduler.py, app/core/riverside_scheduler.py | **Tier 1** | Current | Uses AsyncIOScheduler with default (memory) job store. |

## Topic 5: Azure SQL Public Network Access

| Source | URL | Tier | Currency | Notes |
|--------|-----|------|----------|-------|
| Azure SQL Connectivity Settings | https://learn.microsoft.com/en-us/azure/azure-sql/database/connectivity-settings | **Tier 1** | Current (Azure docs) | Official. Documents public access, deny access, TLS settings. |
| Azure Private Link for SQL | https://learn.microsoft.com/en-us/azure/azure-sql/database/private-endpoint-overview | **Tier 1** | Current (Azure docs) | Official. Warns that public access is NOT auto-disabled with private endpoints. |
| Microsoft Defender for Cloud | Azure Security Benchmark v3 | **Tier 1** | 2025 | Recommends disabling public network access for all PaaS services. |

## Topic 6: Bicep Secret Output Leakage

| Source | URL | Tier | Currency | Notes |
|--------|-----|------|----------|-------|
| Bicep Outputs Documentation | https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/outputs | **Tier 1** | Current | Official. Documents `@secure()` decorator for outputs (Bicep ≥0.35.1). |
| Bicep Linter — outputs-should-not-contain-secrets | https://aka.ms/bicep/linter-diagnostics#outputs-should-not-contain-secrets | **Tier 1** | Current | Official lint rule. Already firing on project's sql-server.bicep. |
| Project deploy output | infrastructure/deploy-output.json | **Tier 1** | Current | Shows the linter warnings flagging adminUsername and adminPassword in output. |

## Topic 7: FastAPI Rate Limiting Without Redis

| Source | URL | Tier | Currency | Notes |
|--------|-----|------|----------|-------|
| Project source code | app/core/rate_limit.py | **Tier 1** | Current | Shows Redis-with-fallback to in-memory dict. Fail-open on errors. |
| OWASP Rate Limiting Guidance | https://owasp.org/www-community/controls/Blocking_Brute_Force_Attacks | **Tier 1** | Current | Industry standard. Recommends persistent rate limit storage. |
