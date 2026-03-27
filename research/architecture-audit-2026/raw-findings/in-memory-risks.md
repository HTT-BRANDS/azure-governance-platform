# In-Memory State Risks: Token Blacklist, Rate Limiter, APScheduler

## Common Failure Mode: Azure App Service B1 Restart Scenarios

Azure App Service B1 restarts the application process in these scenarios:

| Trigger | Frequency | Predictable? |
|---------|-----------|-------------|
| Code deployment | Every deploy | Yes |
| Platform update | Monthly (sometimes more) | Partially (notification) |
| "Always On" ping failure | When app becomes unresponsive | No |
| Worker recycling | Default: every 29 hours | Configurable but still periodic |
| Configuration change | When app settings modified | Yes |
| Manual restart | Admin action | Yes |
| Scaling event | When tier changes | Yes |
| Health check failure | When health endpoint fails | No |
| Memory pressure / OOM | When app exceeds memory limit | No |

**Minimum expected restarts**: ~2-4 per week (deployments + platform updates + recycling)

---

## Token Blacklist (app/core/token_blacklist.py)

### Architecture
```
Redis available? → Use Redis (persistent, shared, TTL-based)
       ↓ No
Use in-memory set → Lost on every restart
```

### Impact Without Redis
1. **Logout bypass**: User logs out → token blacklisted → restart → token valid again
2. **Revocation bypass**: Admin revokes compromised token → restart → attacker can reuse
3. **No TTL cleanup**: In-memory `set()` has no automatic expiration — grows until restart
4. **Refresh token risk**: 7-day refresh tokens remain exploitable for up to 7 days after revocation if restart occurs

### Specific Code Issue
```python
self._memory_fallback: set[str] = set()  # Full tokens stored in memory
```
- Stores full JWT strings (not hashes) — memory inefficient
- No periodic cleanup of expired tokens
- No size limit — could grow to thousands of entries

---

## Rate Limiter (app/core/rate_limit.py)

### Architecture
```
Redis available? → Use Redis (persistent, shared, atomic operations)
       ↓ No
Use in-memory dict → Lost on every restart
```

### Impact Without Redis
1. **Brute force reset**: Login rate limit (5/5min) resets on every restart
2. **Continuous bypass**: Attacker can time attacks around known restart windows
3. **Fail-open design**: `except Exception: return True, {}` — any error allows the request
4. **No cross-instance sharing**: If multiple workers/instances exist, each has independent limits
5. **Memory growth**: Dict grows up to 10,000 entries before cleanup triggers

### Specific Code Issues
```python
# Fail-open — allows request if anything goes wrong
except Exception as e:
    logger.error(f"Rate limit check failed: {e}")
    return True, {}  # ⚠️ ALLOWS REQUEST
```

```python
# Cleanup only at 10k entries, O(n) operation
if len(self._memory_cache) > 10000:
    self._memory_cache = {k: v for k, v in self._memory_cache.items() if v[1] > now}
```

---

## APScheduler (app/core/scheduler.py, app/core/riverside_scheduler.py)

### Architecture
```
AsyncIOScheduler with default (memory) job store
  → 11 scheduled jobs in same process as FastAPI
  → All state lost on restart
  → No missed-job detection
```

### Registered Jobs
| Job | Schedule | Impact if Missed |
|-----|----------|-----------------|
| sync_costs | Every 24h | Stale cost data for tenants |
| sync_compliance | Every 4h | Compliance scores outdated |
| sync_resources | Every 1h | Resource inventory gaps |
| sync_identity | Every 24h | Identity data stale |
| sync_riverside | Every 4h | Riverside compliance gaps |
| sync_dmarc | Daily at 2 AM | DMARC/DKIM data stale |
| hourly_mfa_sync | Every hour | MFA coverage data outdated |
| daily_full_sync | Daily at 1 AM | Full sync missed |
| weekly_threat_sync | Sundays 3 AM | Threat data stale for a week |
| monthly_report_sync | 1st at 4 AM | Monthly report data missing |

### Specific Risks
1. **No persistence**: `AsyncIOScheduler()` uses `MemoryJobStore` by default
2. **No misfire recovery**: Without persistent store, scheduler can't detect missed runs
3. **No duplicate protection**: During deployment overlap, two processes may run the same jobs
4. **Event loop blocking**: Long sync jobs (especially full tenant sync) block FastAPI request handling
5. **No audit trail**: No record of whether scheduled jobs actually ran

### APScheduler Documentation Quote
> "Sometimes the scheduler may be unable to execute a scheduled job at the time it was 
> scheduled to run. The most common case is when a job is scheduled in a **persistent job 
> store** and the scheduler is shut down and restarted after the job was supposed to execute."

The project uses the **non-persistent** store, so misfires are **silently lost** rather than detected.
