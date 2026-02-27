# API Completeness Documentation

This document describes all the enhanced and new API endpoints added for API completeness.

## Overview

The API has been significantly expanded to provide:
- Complete CRUD operations for anomalies, recommendations, and idle resources
- Comprehensive filtering and pagination across all endpoints
- CSV export functionality for reporting
- Enhanced status and health monitoring
- Trends and forecasting capabilities

---

## Cost Anomalies API

Base path: `/api/v1/costs`

### Enhanced Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/anomalies` | List anomalies with filtering (acknowledged, tenant_ids, pagination) |
| POST | `/anomalies/{id}/acknowledge` | Acknowledge single anomaly |

### New Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/anomalies/trends` | Anomaly trends over time (grouped by month) |
| GET | `/anomalies/by-service` | Anomalies grouped by Azure service |
| GET | `/anomalies/top` | Top N anomalies by impact score |
| POST | `/anomalies/bulk-acknowledge` | Acknowledge multiple anomalies at once |
| GET | `/trends/forecast` | Cost forecast using linear projection |

### Query Parameters

#### GET /anomalies
- `acknowledged` (bool, optional): Filter by acknowledged status
- `tenant_ids` (list[str], optional): Filter by tenant IDs
- `limit` (int, default=50): Pagination limit (1-200)
- `offset` (int, default=0): Pagination offset
- `sort_by` (str, default="detected_at"): Sort field
- `sort_order` (str, default="desc"): Sort direction (asc/desc)

#### GET /anomalies/trends
- `months` (int, default=6): Number of months to analyze (1-24)

#### GET /anomalies/by-service
- `limit` (int, default=20): Maximum services to return (1-50)

#### GET /anomalies/top
- `n` (int, default=10): Number of top anomalies (1-50)
- `acknowledged` (bool, optional): Filter by acknowledged status

#### GET /trends/forecast
- `days` (int, default=30): Forecast days (7-90)

---

## Recommendations API

Base path: `/api/v1/recommendations`

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List all recommendations with filtering |
| GET | `/by-category` | Recommendations grouped by category |
| GET | `/by-tenant` | Recommendations grouped by tenant |
| GET | `/savings-potential` | Total potential savings summary |
| GET | `/summary` | Summary statistics by category |
| POST | `/{id}/dismiss` | Dismiss a recommendation |

### Query Parameters

#### GET /
- `category` (enum, optional): Filter by category (cost_optimization, security, performance, reliability)
- `tenant_ids` (list[str], optional): Filter by tenant IDs
- `impact` (str, optional): Filter by impact (Low, Medium, High, Critical)
- `dismissed` (bool, default=False): Include dismissed recommendations
- `limit` (int, default=100): Pagination limit (1-500)
- `offset` (int, default=0): Pagination offset
- `sort_by` (str, default="created_at"): Sort field
- `sort_order` (str, default="desc"): Sort direction (asc/desc)

### Categories

- **cost_optimization**: Cost saving opportunities
- **security**: Security improvements
- **performance**: Performance enhancements
- **reliability**: Reliability improvements

---

## Idle Resources API

Base path: `/api/v1/resources`

### New Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/idle` | List idle resources |
| GET | `/idle/summary` | Summary statistics for idle resources |
| POST | `/idle/{id}/tag` | Mark resource as reviewed |

### Query Parameters

#### GET /idle
- `tenant_ids` (list[str], optional): Filter by tenant IDs
- `idle_type` (str, optional): Filter by idle type (e.g., low_cpu, no_connections)
- `is_reviewed` (bool, optional): Filter by review status
- `limit` (int, default=100): Pagination limit (1-500)
- `offset` (int, default=0): Pagination offset
- `sort_by` (str, default="estimated_monthly_savings"): Sort field
- `sort_order` (str, default="desc"): Sort direction (asc/desc)

---

## Export API

Base path: `/api/v1/exports`

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/costs` | Export cost data to CSV |
| GET | `/resources` | Export resource inventory to CSV |
| GET | `/compliance` | Export compliance report to CSV |

### Query Parameters

#### GET /costs
- `start_date` (date, optional): Start date (defaults to 30 days ago)
- `end_date` (date, optional): End date (defaults to today)
- `tenant_ids` (list[str], optional): Filter by tenant IDs

#### GET /resources
- `tenant_ids` (list[str], optional): Filter by tenant IDs
- `resource_type` (str, optional): Filter by resource type
- `include_orphaned` (bool, default=True): Include orphaned resources

#### GET /compliance
- `tenant_ids` (list[str], optional): Filter by tenant IDs
- `include_non_compliant` (bool, default=True): Include non-compliant policies

---

## Trends API

### Cost Trends
Base path: `/api/v1/costs`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/trends/forecast` | Cost forecasting (7-90 days) |

### Compliance Trends
Base path: `/api/v1/compliance`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/trends` | Compliance score trends over time |

### Identity Trends
Base path: `/api/v1/identity`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/trends` | Identity metrics trends (MFA adoption, etc.) |

### Query Parameters

#### GET /compliance/trends
- `tenant_ids` (list[str], optional): Filter by tenant IDs
- `days` (int, default=30): Days of history (7-365)

#### GET /identity/trends
- `tenant_ids` (list[str], optional): Filter by tenant IDs
- `days` (int, default=30): Days of history (7-365)

---

## Status API

Base path: `/api/v1/status`

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Detailed system status |
| GET | `/sync` | Sync job status summary |

### Enhanced Health Check
Base path: `/health`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Basic health check |
| GET | `/detailed` | Detailed health with component status |

---

## Enhanced Filter Support

All list endpoints now support consistent filtering:

### Common Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `tenant_ids` | list[str] | Filter by specific tenants |
| `start_date` | date | Start date for date range |
| `end_date` | date | End date for date range |
| `limit` | int | Maximum results (varies by endpoint) |
| `offset` | int | Pagination offset |
| `sort_by` | str | Field to sort by |
| `sort_order` | str | Sort direction (asc/desc) |

### Endpoints with Enhanced Filtering

- `/api/v1/costs/summary` - tenant_ids, start_date, end_date
- `/api/v1/costs/by-tenant` - tenant_ids
- `/api/v1/costs/trends` - tenant_ids, start_date, end_date
- `/api/v1/costs/anomalies` - acknowledged, tenant_ids, pagination
- `/api/v1/resources` - tenant_ids, resource_type, pagination
- `/api/v1/resources/orphaned` - tenant_ids, pagination
- `/api/v1/resources/idle` - tenant_ids, idle_type, is_reviewed, pagination
- `/api/v1/resources/tagging` - tenant_ids
- `/api/v1/compliance/summary` - tenant_ids
- `/api/v1/compliance/scores` - tenant_ids, pagination
- `/api/v1/compliance/non-compliant` - tenant_ids, severity, pagination
- `/api/v1/identity/privileged` - tenant_ids, risk_level, mfa_enabled, pagination
- `/api/v1/identity/guests` - tenant_ids, stale_only, pagination
- `/api/v1/identity/stale` - tenant_ids, pagination

---

## Response Schemas

### BulkAcknowledgeResponse
```json
{
  "success": true,
  "acknowledged_count": 5,
  "failed_ids": [],
  "acknowledged_at": "2024-01-15T10:30:00Z"
}
```

### SavingsPotential
```json
{
  "total_potential_savings_monthly": 12500.00,
  "total_potential_savings_annual": 150000.00,
  "by_category": {
    "cost_optimization": 10000.00,
    "security": 1500.00,
    "performance": 1000.00
  },
  "by_tenant": {
    "Tenant A": 5000.00,
    "Tenant B": 7500.00
  }
}
```

### IdleResourceSummary
```json
{
  "total_count": 45,
  "total_potential_savings_monthly": 8500.00,
  "total_potential_savings_annual": 102000.00,
  "by_type": {
    "low_cpu": 20,
    "no_connections": 15,
    "unattached_disk": 10
  },
  "by_tenant": {
    "Tenant A": 25,
    "Tenant B": 20
  }
}
```

### SystemStatus
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2024-01-15T10:30:00Z",
  "components": {
    "database": {"status": "healthy", "message": "Connected"},
    "scheduler": {"status": "running", "message": "Active"},
    "azure": {"status": "configured", "message": "Azure credentials configured"}
  },
  "sync_jobs": {
    "costs": {
      "last_run": "2024-01-15T09:00:00Z",
      "success_rate": 98.5,
      "total_runs": 100
    }
  },
  "alerts": {
    "total_active": 2,
    "by_severity": {"warning": 2}
  }
}
```

---

## Usage Examples

### Get Top Cost Anomalies
```bash
curl "http://localhost:8000/api/v1/costs/anomalies/top?n=5&acknowledged=false"
```

### Bulk Acknowledge Anomalies
```bash
curl -X POST "http://localhost:8000/api/v1/costs/anomalies/bulk-acknowledge" \
  -H "X-User-Id: admin@example.com" \
  -H "Content-Type: application/json" \
  -d '{"anomaly_ids": [1, 2, 3]}'
```

### Get Recommendations by Category
```bash
curl "http://localhost:8000/api/v1/recommendations/by-category"
```

### Dismiss Recommendation
```bash
curl -X POST "http://localhost:8000/api/v1/recommendations/42/dismiss" \
  -H "X-User-Id: admin@example.com" \
  -H "Content-Type: application/json" \
  -d '{"reason": "Not applicable to production environment"}'
```

### Export Resources to CSV
```bash
curl "http://localhost:8000/api/v1/exports/resources?tenant_ids=tenant-1" \
  -o resources_export.csv
```

### Get Idle Resources
```bash
curl "http://localhost:8000/api/v1/resources/idle?sort_by=estimated_monthly_savings&limit=10"
```

### Tag Idle Resource as Reviewed
```bash
curl -X POST "http://localhost:8000/api/v1/resources/idle/123/tag" \
  -H "X-User-Id: admin@example.com" \
  -H "Content-Type: application/json" \
  -d '{"notes": "Verified - VM needed for DR"}'
```

### Get System Status
```bash
curl "http://localhost:8000/api/v1/status"
```

### Get Compliance Trends
```bash
curl "http://localhost:8000/api/v1/compliance/trends?days=90"
```

---

## Implementation Details

### New Files Created

1. **Models:**
   - `app/models/recommendation.py` - Recommendation model
   - Updated `app/models/resource.py` - Added IdleResource model

2. **Schemas:**
   - `app/schemas/recommendation.py` - Recommendation schemas
   - Updated `app/schemas/cost.py` - Added anomaly-related schemas
   - Updated `app/schemas/resource.py` - Added idle resource schemas

3. **Services:**
   - `app/api/services/recommendation_service.py` - Recommendation service
   - Updated `app/api/services/cost_service.py` - Added anomaly methods
   - Updated `app/api/services/resource_service.py` - Added idle resource methods
   - Updated `app/api/services/compliance_service.py` - Added trends method
   - Updated `app/api/services/identity_service.py` - Added trends method

4. **Routes:**
   - `app/api/routes/recommendations.py` - Recommendations API
   - `app/api/routes/exports.py` - Export API
   - Updated `app/api/routes/costs.py` - Enhanced anomaly endpoints
   - Updated `app/api/routes/resources.py` - Added idle resource endpoints
   - Updated `app/api/routes/compliance.py` - Added trends endpoint
   - Updated `app/api/routes/identity.py` - Added trends endpoint

5. **Main Application:**
   - Updated `app/main.py` - Added status endpoints and new routers
   - Updated `app/api/routes/__init__.py` - Exported new routers
   - Updated `app/schemas/__init__.py` - Exported new schemas
   - Updated `app/api/services/__init__.py` - Exported new service
   - Updated `app/models/__init__.py` - Exported new models

6. **Tests:**
   - `tests/test_api_completeness.py` - Unit tests for new endpoints
