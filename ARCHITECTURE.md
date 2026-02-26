# Azure Multi-Tenant Governance Platform - Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        AZURE GOVERNANCE PLATFORM                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  Tenant A   │  │  Tenant B   │  │  Tenant C   │  │  Tenant D   │        │
│  │  (Azure)    │  │  (Azure)    │  │  (Azure)    │  │  (Azure)    │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
│         │                │                │                │                │
│         └────────────────┴────────────────┴────────────────┘                │
│                                   │                                          │
│                    ┌──────────────▼──────────────┐                          │
│                    │      Azure Lighthouse       │                          │
│                    │   (Cross-Tenant Delegation) │                          │
│                    └──────────────┬──────────────┘                          │
│                                   │                                          │
│  ┌────────────────────────────────▼────────────────────────────────────┐    │
│  │                     GOVERNANCE PLATFORM                              │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │                    FastAPI Backend                          │    │    │
│  │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │    │    │
│  │  │  │   Cost   │ │Compliance│ │ Resource │ │   Identity   │   │    │    │
│  │  │  │ Service  │ │ Service  │ │ Service  │ │   Service    │   │    │    │
│  │  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └──────┬───────┘   │    │    │
│  │  │       └────────────┴────────────┴──────────────┘           │    │    │
│  │  │                           │                                 │    │    │
│  │  │                    ┌──────▼──────┐                         │    │    │
│  │  │                    │   SQLite    │                         │    │    │
│  │  │                    │  Database   │                         │    │    │
│  │  │                    └─────────────┘                         │    │    │
│  │  └─────────────────────────────────────────────────────────────┘    │    │
│  │                                                                      │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │                HTMX + Tailwind Frontend                     │    │    │
│  │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │    │    │
│  │  │  │   Cost   │ │Compliance│ │ Resource │ │   Identity   │   │    │    │
│  │  │  │Dashboard │ │Dashboard │ │ Explorer │ │   Viewer     │   │    │    │
│  │  │  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │    │    │
│  │  └─────────────────────────────────────────────────────────────┘    │    │
│  └──────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

| Layer | Technology | Rationale |
|-------|------------|----------|
| Backend | Python 3.11 + FastAPI | Fast, async, low resource |
| Frontend | HTMX + Tailwind CSS | No build step, lightweight |
| Database | SQLite | Zero cost, simple, portable |
| Charts | Chart.js | Client-side, no server load |
| Auth | Azure AD / Entra ID | Native SSO integration |
| APIs | Azure SDK + httpx | Official + async HTTP |
| Caching | SQLite + in-memory | Reduce API calls |
| Tasks | APScheduler | Background data sync |
| Hosting | Azure App Service (B1) | $13/mo, adequate scale |

---

## Component Architecture

### Backend Structure

```
app/
├── main.py                 # FastAPI app entry
├── core/
│   ├── config.py           # Settings & env vars
│   ├── security.py         # Auth middleware
│   ├── database.py         # SQLite connection
│   └── scheduler.py        # Background jobs
├── api/
│   ├── routes/
│   │   ├── dashboard.py    # Main dashboard
│   │   ├── costs.py        # Cost endpoints
│   │   ├── compliance.py   # Compliance endpoints
│   │   ├── resources.py    # Resource endpoints
│   │   └── identity.py     # Identity endpoints
│   └── services/
│       ├── azure_client.py # Azure SDK wrapper
│       ├── graph_client.py # MS Graph wrapper
│       ├── cost_service.py # Cost logic
│       ├── compliance_svc.py# Compliance logic
│       ├── resource_svc.py # Resource logic
│       └── identity_svc.py # Identity logic
├── models/
│   ├── tenant.py           # Tenant model
│   ├── cost.py             # Cost models
│   ├── compliance.py       # Compliance models
│   ├── resource.py         # Resource models
│   └── identity.py         # Identity models
├── schemas/
│   ├── cost.py             # Cost Pydantic schemas
│   ├── compliance.py       # Compliance schemas
│   ├── resource.py         # Resource schemas
│   └── identity.py         # Identity schemas
└── templates/
    ├── base.html           # Base template
    ├── components/         # Reusable HTMX partials
    └── pages/              # Full page templates
```

---

## Data Flow

### Sync Flow (Background)

```
┌────────────┐     ┌────────────┐     ┌────────────┐     ┌────────────┐
│ Scheduler  │────▶│  Service   │────▶│ Azure APIs │────▶│  SQLite    │
│ (APSched)  │     │  Layer     │     │ (ARM/Graph)│     │  Cache     │
└────────────┘     └────────────┘     └────────────┘     └────────────┘
      │                                                         │
      │              Every 1-24 hours (configurable)            │
      └─────────────────────────────────────────────────────────┘
```

### Request Flow (User)

```
┌────────────┐     ┌────────────┐     ┌────────────┐     ┌────────────┐
│   User     │────▶│   HTMX     │────▶│  FastAPI   │────▶│  SQLite    │
│  Browser   │     │  Request   │     │  Endpoint  │     │  (Cached)  │
└────────────┘     └────────────┘     └────────────┘     └────────────┘
      ▲                                      │
      │            HTML Fragment             │
      └──────────────────────────────────────┘
```

---

## Database Schema

### Core Tables

```sql
-- Tenant configuration
tenants (
    id TEXT PRIMARY KEY,
    name TEXT,
    tenant_id TEXT,        -- Azure tenant GUID
    client_id TEXT,        -- App registration
    client_secret_ref TEXT,-- Key Vault reference
    is_active BOOLEAN,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)

-- Subscriptions per tenant
subscriptions (
    id TEXT PRIMARY KEY,
    tenant_id TEXT FK,
    subscription_id TEXT,
    display_name TEXT,
    state TEXT,
    synced_at TIMESTAMP
)

-- Daily cost snapshots
cost_snapshots (
    id INTEGER PRIMARY KEY,
    tenant_id TEXT FK,
    subscription_id TEXT,
    date DATE,
    total_cost REAL,
    currency TEXT,
    resource_group TEXT,
    service_name TEXT,
    synced_at TIMESTAMP
)

-- Compliance states
compliance_snapshots (
    id INTEGER PRIMARY KEY,
    tenant_id TEXT FK,
    subscription_id TEXT,
    policy_name TEXT,
    compliance_state TEXT,
    non_compliant_count INTEGER,
    synced_at TIMESTAMP
)

-- Resource inventory
resources (
    id TEXT PRIMARY KEY,
    tenant_id TEXT FK,
    subscription_id TEXT,
    resource_group TEXT,
    resource_type TEXT,
    name TEXT,
    location TEXT,
    tags TEXT,            -- JSON blob
    synced_at TIMESTAMP
)

-- Identity snapshots
identity_snapshots (
    id INTEGER PRIMARY KEY,
    tenant_id TEXT FK,
    snapshot_date DATE,
    total_users INTEGER,
    guest_users INTEGER,
    mfa_enabled INTEGER,
    privileged_users INTEGER,
    stale_accounts INTEGER,
    synced_at TIMESTAMP
)

-- Sync job tracking
sync_jobs (
    id INTEGER PRIMARY KEY,
    job_type TEXT,
    tenant_id TEXT,
    status TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT
)
```

---

## Authentication Architecture

### Option A: Azure Lighthouse (Recommended)

```
┌─────────────────────────────────────────────────────────────┐
│                    Managing Tenant                           │
│  ┌─────────────────────────────────────────────────────┐    │
│  │           Governance Platform                        │    │
│  │           (Single App Registration)                  │    │
│  └───────────────────────┬─────────────────────────────┘    │
└──────────────────────────┼──────────────────────────────────┘
                           │
          Azure Lighthouse Delegation
                           │
    ┌──────────────────────┼──────────────────────┐
    ▼                      ▼                      ▼
┌────────┐           ┌────────┐            ┌────────┐
│Tenant B│           │Tenant C│            │Tenant D│
│(Reader)│           │(Reader)│            │(Reader)│
└────────┘           └────────┘            └────────┘
```

### Option B: Per-Tenant App Registrations

```
┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐
│  Tenant A  │  │  Tenant B  │  │  Tenant C  │  │  Tenant D  │
│  App Reg   │  │  App Reg   │  │  App Reg   │  │  App Reg   │
│  + SP      │  │  + SP      │  │  + SP      │  │  + SP      │
└─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘
      │               │               │               │
      └───────────────┴───────────────┴───────────────┘
                              │
                    ┌─────────▼─────────┐
                    │   Governance      │
                    │   Platform        │
                    │   (Stores creds)  │
                    └───────────────────┘
```

---

## API Design

### REST Endpoints

```
GET  /api/v1/tenants                    # List all tenants
GET  /api/v1/tenants/{id}/subscriptions # Subscriptions per tenant

GET  /api/v1/costs/summary              # Aggregated costs
GET  /api/v1/costs/by-tenant            # Costs per tenant
GET  /api/v1/costs/by-service           # Costs by service type
GET  /api/v1/costs/trends               # Cost trending
GET  /api/v1/costs/anomalies            # Cost anomalies

GET  /api/v1/compliance/scores          # Compliance scores
GET  /api/v1/compliance/policies        # Policy status
GET  /api/v1/compliance/non-compliant   # Non-compliant resources

GET  /api/v1/resources                  # Resource inventory
GET  /api/v1/resources/orphaned         # Orphaned resources
GET  /api/v1/resources/tagging          # Tagging compliance

GET  /api/v1/identity/summary           # Identity overview
GET  /api/v1/identity/privileged        # Privileged accounts
GET  /api/v1/identity/guests            # Guest accounts
GET  /api/v1/identity/stale             # Stale accounts

POST /api/v1/sync/{type}                # Trigger manual sync
GET  /api/v1/sync/status                # Sync job status
```

### HTMX Partials

```
GET  /partials/cost-summary-card        # Cost summary widget
GET  /partials/cost-chart               # Cost trend chart
GET  /partials/compliance-gauge         # Compliance score gauge
GET  /partials/resource-table           # Resource list table
GET  /partials/identity-stats           # Identity statistics
GET  /partials/alerts-panel             # Active alerts
```

---

## Deployment Architecture

### Minimal Cost Option (< $50/mo)

```
┌─────────────────────────────────────────────────────────────┐
│              Azure App Service (B1 - $13/mo)                │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  FastAPI + HTMX + SQLite (single instance)            │  │
│  │  - APScheduler runs in-process                        │  │
│  │  - SQLite file in persistent storage                  │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              +
┌─────────────────────────────────────────────────────────────┐
│              Azure Key Vault ($0.03/10k operations)         │
│  - Store tenant credentials securely                        │
└─────────────────────────────────────────────────────────────┘

Total: ~$15-20/month
```

### Production Option (< $100/mo)

```
┌─────────────────────────────────────────────────────────────┐
│              Azure Container Apps ($30-50/mo)               │
│  ┌─────────────────────┐  ┌─────────────────────┐          │
│  │   Web Container     │  │  Worker Container   │          │
│  │   (FastAPI)         │  │  (Sync Jobs)        │          │
│  └─────────────────────┘  └─────────────────────┘          │
└─────────────────────────────────────────────────────────────┘
                              +
┌─────────────────────────────────────────────────────────────┐
│              Azure SQL (Serverless - $5-30/mo)              │
│  - Auto-pause when idle (cost savings)                      │
└─────────────────────────────────────────────────────────────┘
                              +
┌─────────────────────────────────────────────────────────────┐
│              Azure Key Vault + App Insights                 │
└─────────────────────────────────────────────────────────────┘

Total: ~$50-100/month
```

---

## Security Considerations

### Credential Management

```python
# Never store credentials in code or SQLite
# Use Azure Key Vault references

class TenantCredentials:
    tenant_id: str
    client_id: str
    client_secret_ref: str  # Key Vault secret URI
```

### Network Security

- Enable Azure AD authentication on App Service
- Use managed identity for Key Vault access
- Restrict outbound to Azure APIs only
- Enable HTTPS-only

### Data Protection

- SQLite encryption at rest (via App Service)
- No PII stored beyond Azure AD identifiers
- Audit logging for all data access
- Regular credential rotation

---

## Scalability Path

### Phase 1: MVP (4 tenants, <50 users)
- SQLite database
- Single App Service instance
- In-process scheduler
- ~$20/month

### Phase 2: Growth (10 tenants, <200 users)
- Migrate to Azure SQL Serverless
- Add Redis caching
- Container Apps with auto-scale
- ~$100/month

### Phase 3: Enterprise (25+ tenants, 500+ users)
- Azure SQL Elastic Pool
- Azure Functions for sync jobs
- API Management gateway
- ~$500/month

---

## Monitoring & Alerting

### Built-in Alerts

| Alert | Condition | Channel |
|-------|-----------|--------|
| Cost Spike | >20% daily increase | Teams |
| Compliance Drop | Score drops >5% | Teams |
| Stale Sync | No sync in 24h | Teams |
| API Errors | >10 errors/hour | Teams |
| Idle Resources | Cost >$100/mo | Weekly |

### Health Endpoints

```
GET /health          # Basic health check
GET /health/detailed # DB + API connectivity
GET /metrics         # Prometheus-compatible
```
