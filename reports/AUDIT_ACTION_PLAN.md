# Code Quality Audit - Action Plan

**Priority fixes with code examples**

---

## 🔴 HIGH PRIORITY FIXES

### 1. Fix N+1 Query Patterns

**File:** `app/api/services/resource_service.py` (lines 55-60)

**Current (Inefficient):**
```python
# N+1: Queries all tenants for every call
tenants = {t.id: t.name for t in self.db.query(Tenant).all()}

# Then iterates through resources and looks up tenant
for r in resources:
    tenant_name = tenants.get(r.tenant_id, "Unknown")  # Memory lookup OK
```

**Better (With Caching):**
```python
from functools import lru_cache
from app.core.cache import cache_manager

# Add to cache manager or use lru_cache
@lru_cache(maxsize=1)
def get_tenant_name_map(db: Session) -> dict[str, str]:
    """Cached tenant lookup - refreshes every 5 minutes."""
    return {t.id: t.name for t in db.query(Tenant).all()}

# In service method:
tenants = get_tenant_name_map(self.db)
```

**Files to Fix:**
- [ ] `app/api/services/resource_service.py` (5 instances)
- [ ] `app/api/services/cost_service.py` (1 instance)
- [ ] `app/api/services/identity_service.py` (2 instances)
- [ ] `app/api/services/recommendation_service.py` (1 instance)
- [ ] `app/api/services/budget_service.py` (1 instance)

---

### 2. Convert Synchronous HTTP to Async

**File:** `app/core/metrics.py`

**Current:**
```python
import requests

response = requests.get(url, headers=headers)
```

**Fixed:**
```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.get(url, headers=headers)
```

---

### 3. Split Large Files

**Target:** `app/preflight/azure_checks.py` (1,866 lines)

**Proposed Structure:**
```
app/preflight/azure/
├── __init__.py          # Re-exports main check functions
├── base.py              # Base Azure check classes
├── compute_checks.py    # VM, VMSS checks (~300 lines)
├── storage_checks.py    # Storage account checks (~250 lines)
├── network_checks.py    # VNet, NSG checks (~300 lines)
├── identity_checks.py   # AAD, RBAC checks (~350 lines)
├── security_checks.py   # Security center, policy (~250 lines)
└── monitoring_checks.py # Alerts, diagnostics (~200 lines)
```

**Migration Strategy:**
1. Create new directory structure
2. Move related classes/functions to appropriate modules
3. Update imports in calling code
4. Add re-exports to `__init__.py` for backward compatibility
5. Run tests to verify

**Files to Split:**
- [ ] `app/preflight/azure_checks.py` → `app/preflight/azure/` (1,866 → ~300 each)
- [ ] `app/preflight/riverside_checks.py` → `app/preflight/riverside/` (1,431 → ~300 each)
- [ ] `app/api/services/graph_client.py` → `app/api/services/graph/` (1,208 → ~400 each)

---

## 🟡 MEDIUM PRIORITY FIXES

### 4. Add Type Hints to Public APIs

**Priority Functions (most used):**

```python
# app/api/services/resource_service.py
def get_resource_summary(
    self, 
    tenant_id: str | None = None,
    resource_type: str | None = None,
    limit: int = 1000
) -> ResourceSummaryResponse:  # Add return type
    ...
```

**Quick Win Script:**
```bash
# Find functions missing return types
 grep -rn "^def [a-z_]*(" app/api/services/*.py | grep -v "->" | head -30
```

---

### 5. Complete Route Test Coverage

**Missing Route Tests:**
```
app/api/routes/          tests/unit/
├── audit_logs.py   →    ❌ Missing
├── compliance_frameworks.py → ❌ Missing  
├── compliance_rules.py → ❌ Missing
├── exports.py      →    ❌ Missing
├── pages.py        →    ❌ Missing
├── preflight.py    →    ✅ test_routes_preflight.py
├── privacy.py      →    ❌ Missing
├── quotas.py       →    ❌ Missing
├── recommendations.py → ✅ test_routes_recommendations.py
├── sync.py         →    ✅ test_routes_sync.py
├── tenants.py      →    ✅ test_routes_tenants.py
├── threats.py      →    ❌ Missing
└── (15 more)...
```

**Template for New Route Test:**
```python
# tests/unit/test_routes_audit_logs.py
import pytest
from fastapi.testclient import TestClient

class TestAuditLogRoutes:
    """Test suite for audit log API routes."""
    
    def test_get_audit_logs_requires_auth(self, client: TestClient):
        response = client.get("/api/v1/audit-logs")
        assert response.status_code == 401
    
    def test_get_audit_logs_success(
        self, 
        authenticated_client: TestClient,
        mock_audit_logs
    ):
        response = authenticated_client.get("/api/v1/audit-logs")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
```

---

### 6. Refine Error Handling

**Current (Too Broad):**
```python
# app/core/auth.py:99
except Exception as e:
    logger.error(f"Failed to fetch Azure AD JWKS: {e}")
```

**Fixed:**
```python
import httpx

except httpx.TimeoutException as e:
    logger.error(f"Azure AD JWKS request timed out: {e}")
    raise AuthenticationError("Identity provider unavailable") from e
except httpx.HTTPStatusError as e:
    logger.error(f"Azure AD returned error: {e.response.status_code}")
    raise AuthenticationError("Identity provider error") from e
except Exception as e:
    logger.exception("Unexpected error fetching Azure AD JWKS")
    raise AuthenticationError("Authentication service error") from e
```

**Files with Broad Exception Handling:**
- [ ] `app/core/auth.py` (2 instances)
- [ ] `app/core/token_blacklist.py` (5 instances)
- [ ] `app/core/metrics.py` (4 instances)
- [ ] `app/core/database.py` (4 instances)
- [ ] `app/core/config.py` (3 instances)

---

### 7. Add Bulk Operations

**Current (Inefficient for large datasets):**
```python
for item in items:
    db.add(Model(**item))
db.commit()  # N round trips
```

**Fixed (Bulk Insert):**
```python
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

# Single round trip
stmt = sqlite_insert(MyModel).values(items)
db.execute(stmt)
db.commit()

# Or with SQLAlchemy ORM bulk
from sqlalchemy.orm import Session

db.bulk_insert_mappings(MyModel, items)
db.commit()
```

---

## 🟢 LOW PRIORITY FIXES

### 8. Increase Eager Loading

**Current (Lazy Loading):**
```python
budget = db.query(Budget).filter(Budget.id == budget_id).first()
# Later access triggers additional query:
alerts = budget.alerts  # N+1!
```

**Fixed (Eager Loading):**
```python
from sqlalchemy.orm import selectinload

budget = (
    db.query(Budget)
    .options(selectinload(Budget.alerts))
    .filter(Budget.id == budget_id)
    .first()
)
# Now alerts are pre-loaded - no additional query
```

---

## Implementation Timeline

| Week | Focus | Effort |
|------|-------|--------|
| Week 1 | Fix N+1 patterns + HTTP async | 2 days |
| Week 2 | Split large files (azure_checks, riverside_checks) | 2 days |
| Week 3 | Add route tests + Type hints | 2 days |
| Week 4 | Error handling refinement + Bulk ops | 1 day |

**Total Estimated Effort: 7 developer days**

---

## Success Metrics

After implementing fixes:
- [ ] 0 N+1 query patterns detected
- [ ] 0 synchronous I/O in async contexts
- [ ] 100% of route files have tests
- [ ] 80%+ function type coverage
- [ ] 0 files >600 lines
- [ ] <5 broad `except Exception` per 1000 lines

---

## Testing Strategy

For each fix:
1. Add test case demonstrating the issue (if not already present)
2. Implement the fix
3. Verify test passes
4. Run full test suite: `pytest -xvs`
5. Run performance smoke test: `pytest tests/smoke/`
6. Check for regressions with `git diff --stat`

---

*Action plan generated by Richard 🐕 - Ready to help you implement these fixes!*
