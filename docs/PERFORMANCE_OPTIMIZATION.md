# Performance Optimization Features

This document describes the performance optimization features implemented in the Azure Governance Platform.

## Overview

The following performance optimizations have been implemented:

1. **Redis Caching** - Multi-layer caching with Redis or in-memory fallback
2. **Query Optimization** - Database indexes and connection pooling
3. **Bulk Operations** - Efficient batch processing for large datasets
4. **Background Job Optimization** - Chunked processing and parallel sync
5. **Performance Monitoring** - Metrics collection and dashboard

---

## 1. Redis Caching (`app/core/cache.py`)

### Features
- **Dual backend support**: Redis for production, in-memory dict for development
- **Automatic fallback**: Falls back to memory cache if Redis unavailable
- **TTL management**: Different TTLs per data type
- **Tenant isolation**: Cache keys include tenant ID for multi-tenancy
- **Cache decorators**: Simple `@cached()` decorator for expensive operations
- **Metrics**: Built-in hit/miss tracking

### Configuration
```python
# Environment variables
CACHE_ENABLED=true                    # Toggle caching
REDIS_URL=redis://localhost:6379      # Redis connection
CACHE_TTL_COST_SUMMARY=3600           # 1 hour
CACHE_TTL_COMPLIANCE_SUMMARY=1800     # 30 minutes
CACHE_TTL_RESOURCE_INVENTORY=900      # 15 minutes
CACHE_TTL_IDENTITY_SUMMARY=3600       # 1 hour
CACHE_TTL_RIVERSIDE_SUMMARY=900       # 15 minutes
```

### Usage
```python
from app.core.cache import cached, invalidate_on_sync_completion

class CostService:
    @cached("cost_summary")
    async def get_cost_summary(self, period_days: int = 30):
        # Expensive aggregation logic
        return summary

    async def acknowledge_anomaly(self, anomaly_id: int, user: str):
        # ... update logic ...
        await invalidate_on_sync_completion(tenant_id)
```

### Cache Invalidation
- Automatic invalidation on sync completion
- Manual invalidation via `invalidate_on_sync_completion(tenant_id)`
- Pattern-based deletion for bulk invalidation

---

## 2. Database Optimizations (`app/core/database.py`)

### Features
- **Connection pooling**: Configurable pool size for PostgreSQL/MySQL
- **Slow query logging**: Automatic detection of queries exceeding threshold
- **Database indexes**: Optimized indexes for common query patterns
- **Query timing**: Built-in query performance tracking
- **Batch operations**: Efficient chunked processing for large datasets

### Configuration
```python
# Environment variables
DB_POOL_SIZE=5                        # Connection pool size
DB_MAX_OVERFLOW=10                    # Max overflow connections
DB_POOL_TIMEOUT=30                    # Connection timeout (seconds)
SLOW_QUERY_THRESHOLD_MS=500.0         # Slow query threshold
ENABLE_QUERY_LOGGING=false            # Enable query logging
```

### Database Indexes Created
- Cost snapshots by date, tenant, service
- Cost anomalies by acknowledgment status
- Resources by tenant, type, orphaned status
- Idle resources by review status
- Compliance snapshots by tenant and date
- Policy states by compliance state
- Identity snapshots by tenant
- Sync jobs by status and tenant

### Helper Functions
```python
from app.core.database import (
    batch_query,           # Iterate in chunks
    bulk_insert_chunks,    # Efficient bulk inserts
    eager_load_options,    # Prevent N+1 queries
    query_with_timing,     # Track query performance
    get_db_stats,          # Database statistics
)
```

---

## 3. Bulk Operations (`app/api/services/bulk_service.py`)

### Features
- **Bulk tagging**: Tag multiple resources by ID or filter criteria
- **Bulk acknowledgment**: Acknowledge multiple anomalies at once
- **Bulk dismissal**: Dismiss multiple recommendations
- **Batch sync**: Chunked inserts for large sync jobs

### API Endpoints

```
POST /bulk/tags/apply              # Apply tags to resources
POST /bulk/tags/remove             # Remove tags from resources
POST /bulk/anomalies/acknowledge   # Acknowledge cost anomalies
POST /bulk/recommendations/dismiss # Dismiss recommendations
POST /bulk/idle-resources/review   # Review idle resources
```

### Example Usage
```python
# Bulk tag operation
operation = BulkTagOperation(
    resource_ids=["id1", "id2"],
    tags={"Environment": "Production"},
    required_tags=["Environment"]
)

# Or use filters
operation = BulkTagOperation(
    resource_filter=ResourceFilterCriteria(
        tenant_ids=["tenant1"],
        resource_types=["Microsoft.Compute/virtualMachines"]
    ),
    tags={"Owner": "team@example.com"}
)
```

---

## 4. Background Job Optimization

### Features
- **Chunked processing**: Process resources in configurable chunks (default 1000)
- **Batch inserts**: Reduce transaction overhead with bulk operations
- **Progress tracking**: Monitor sync job performance
- **Parallel sync**: Asyncio support for concurrent tenant processing

### Configuration
```python
# Environment variables
BULK_BATCH_SIZE=1000                  # Records per batch insert
SYNC_CHUNK_SIZE=1000                  # Records per processing chunk
ENABLE_PARALLEL_SYNC=true             # Enable parallel tenant sync
MAX_PARALLEL_TENANTS=5                # Max concurrent tenants
```

---

## 5. Performance Monitoring (`app/core/monitoring.py`)

### Features
- **Cache metrics**: Hit rate, average get time, error count
- **Sync job metrics**: Records per second, duration, error tracking
- **Query metrics**: Query duration, slow query detection
- **Performance dashboard**: Unified view of all metrics

### API Endpoints

```
GET /monitoring/performance    # Comprehensive performance metrics
GET /monitoring/cache          # Cache statistics
GET /monitoring/sync-jobs      # Sync job performance history
GET /monitoring/queries        # Query performance metrics
POST /monitoring/reset         # Reset metrics (use with caution)
GET /monitoring/health         # Quick health check
```

### Example Response
```json
{
  "cache": {
    "backend": "memory",
    "hits": 150,
    "misses": 10,
    "hit_rate_percent": 93.75,
    "avg_get_time_ms": 0.05
  },
  "sync_jobs": {
    "total_jobs": 25,
    "avg_records_per_second": 450.5,
    "avg_duration_seconds": 12.3,
    "total_records_processed": 50000
  },
  "queries": {
    "total_queries": 500,
    "avg_duration_ms": 45.2,
    "slow_queries": 3
  }
}
```

### Usage in Code
```python
from app.core.monitoring import track_sync_job, track_query

@track_sync_job("resources", tenant_id="abc123")
async def sync_resources():
    # ... sync logic ...
    return {"processed": 1000, "inserted": 800, "updated": 200}

# Or use context manager
with track_query("get_cost_summary"):
    results = db.query(CostSnapshot).all()
```

---

## Services with Caching

The following services have been updated with caching:

| Service | Cached Methods | TTL |
|---------|----------------|-----|
| CostService | get_cost_summary, get_costs_by_tenant, get_cost_trends, get_anomaly_trends, get_anomalies_by_service, get_cost_forecast | 1 hour |
| ComplianceService | get_compliance_summary, get_scores_by_tenant, get_compliance_trends | 30 min |
| ResourceService | get_resource_inventory, get_orphaned_resources, get_tagging_compliance, get_idle_resources_summary | 15 min |
| IdentityService | get_identity_summary, get_privileged_accounts, get_identity_trends | 1 hour |
| RiversideService | get_riverside_summary, get_mfa_status, get_maturity_scores, get_gaps | 15 min |

---

## Environment Variables Reference

### Cache Settings
- `CACHE_ENABLED` - Enable/disable caching (default: true)
- `REDIS_URL` - Redis connection string
- `CACHE_TTL_COST_SUMMARY` - TTL for cost data (default: 3600s)
- `CACHE_TTL_COMPLIANCE_SUMMARY` - TTL for compliance data (default: 1800s)
- `CACHE_TTL_RESOURCE_INVENTORY` - TTL for resource data (default: 900s)
- `CACHE_TTL_IDENTITY_SUMMARY` - TTL for identity data (default: 3600s)
- `CACHE_TTL_RIVERSIDE_SUMMARY` - TTL for Riverside data (default: 900s)

### Database Settings
- `DB_POOL_SIZE` - Connection pool size (default: 5)
- `DB_MAX_OVERFLOW` - Max overflow connections (default: 10)
- `DB_POOL_TIMEOUT` - Pool timeout in seconds (default: 30)
- `SLOW_QUERY_THRESHOLD_MS` - Slow query threshold (default: 500ms)
- `ENABLE_QUERY_LOGGING` - Enable query logging (default: false)

### Performance Settings
- `BULK_BATCH_SIZE` - Batch insert size (default: 1000)
- `SYNC_CHUNK_SIZE` - Sync chunk size (default: 1000)
- `ENABLE_PARALLEL_SYNC` - Enable parallel sync (default: true)
- `MAX_PARALLEL_TENANTS` - Max concurrent tenants (default: 5)

---

## Performance Best Practices

1. **Use cached methods** for expensive aggregations
2. **Invalidate cache** after data mutations
3. **Use bulk operations** for batch updates
4. **Monitor slow queries** and add indexes as needed
5. **Track sync job metrics** to identify bottlenecks
6. **Use chunked processing** for large datasets
7. **Enable query logging** in debug mode

---

## Testing Performance

Use the monitoring endpoints to verify performance improvements:

```bash
# Check cache performance
curl http://localhost:8000/monitoring/cache

# Check overall performance
curl http://localhost:8000/monitoring/performance

# Check sync job history
curl http://localhost:8000/monitoring/sync-jobs

# Check slow queries
curl "http://localhost:8000/monitoring/queries?slow_only=true"
```
