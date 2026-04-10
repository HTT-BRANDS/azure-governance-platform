# Circuit Breaker Auto-Recovery Behavior

**Sources**:
- Martin Fowler, "Circuit Breaker" (Tier 2 — recognized expert): https://martinfowler.com/bliki/CircuitBreaker.html
- Project source code: `app/core/circuit_breaker.py` (Primary source — actual implementation)
- Michael Nygard, "Release It!" — original pattern description (Tier 1 — primary source)

## Canonical Circuit Breaker Pattern (Martin Fowler)

### State Machine

```
                 fail [threshold reached]
    ┌─────────┐ ────────────────────────→ ┌──────────┐
    │ CLOSED  │                           │   OPEN   │
    └─────────┘ ←──────────── success ─── └──────────┘
         ↑                                     │
         │ success                             │ reset timeout elapsed
         │                                     ↓
         └────────── success ──────────── ┌───────────┐
                                          │ HALF_OPEN │
              ┌── fail ──────────────────→└───────────┘
              │                                │
              └────────────────────────────────┘
```

### From Martin Fowler's Article (2014)

> "This simple circuit breaker avoids making the protected call when the circuit is open,
> but would need an **external intervention** to reset it when things are well again. This is
> a reasonable approach with electrical circuit breakers in buildings, but for software
> circuit breakers we can have the breaker itself detect if the underlying calls are
> working again."

> "We can implement this **self-resetting behavior** by trying the protected call again
> after a suitable interval, and resetting the breaker should it succeed."

> "There is now a third state present - **half open** - meaning the circuit is ready to make
> a real call as trial to see if the problem is fixed."

> "Asked to call in the half-open state results in a **trial call**, which will either
> **reset the breaker if successful** or **restart the timeout if not**."

### Lazy vs Timer-Based Transition

Martin Fowler's implementation (and most implementations including ours) use a
**lazy/passive transition** — the state is computed when a call is attempted:

```ruby
# Martin Fowler's Ruby implementation
def state
  case
  when (@failure_count >= @failure_threshold) &&
       (Time.now - @last_failure_time) > @reset_timeout
    :half_open    # Transition happens on next call attempt
  when (@failure_count >= @failure_threshold)
    :open
  else
    :closed
  end
end
```

This means:
1. The circuit does NOT transition via a background timer
2. The transition happens **on the next call attempt** after the timeout elapses
3. If no calls are attempted, the circuit stays logically OPEN (but this is harmless)

## Our Implementation Analysis

### Source: `app/core/circuit_breaker.py`

Our implementation follows the canonical pattern exactly:

```python
def can_execute(self) -> bool:
    with self._lock:
        if self._state == CircuitState.CLOSED:
            return True
        elif self._state == CircuitState.OPEN:
            if self._should_attempt_reset():  # Check if timeout elapsed
                self._state = CircuitState.HALF_OPEN
                self._success_count = 0
                return True  # Allow one trial call
            return False
        elif self._state == CircuitState.HALF_OPEN:
            return True
        return True

def _should_attempt_reset(self) -> bool:
    if self._last_failure_time is None:
        return False
    elapsed = time.monotonic() - self._last_failure_time
    return elapsed >= self.config.recovery_timeout
```

### State Transitions in Our Implementation

| From | To | Trigger | Behavior |
|------|----|---------|----------|
| CLOSED | OPEN | `failures >= failure_threshold` | Blocks all calls |
| OPEN | HALF_OPEN | `can_execute()` called AND `recovery_timeout` elapsed | Allows one trial call |
| HALF_OPEN | CLOSED | `success_count >= success_threshold` | Full recovery |
| HALF_OPEN | OPEN | Any failure | Re-blocks all calls, restarts timeout |
| CLOSED | CLOSED | Any success | Resets failure count |

### Auto-Recovery: YES, It's Automatic

**The circuit breaker DOES auto-recover.** Specifically:

1. After the `recovery_timeout` elapses (300s = 5 min for most sync breakers)
2. The **next call** to `can_execute()` transitions to HALF_OPEN
3. The trial call is attempted
4. If `success_threshold` (2) consecutive successes → CLOSED (fully recovered)
5. If any failure → back to OPEN, timeout restarts

**No manual reset is required** for normal recovery.

### When Manual Reset IS Needed

The `CircuitBreakerRegistry.reset()` method exists for cases where:
- The underlying issue is known to be fixed and you want immediate recovery
- A deployment/restart should reset all breakers
- The breaker is OPEN but the sync job isn't being called (no trigger to attempt recovery)

### Configuration for Each Breaker

| Breaker | Failure Threshold | Recovery Timeout | Success Threshold | Expected Exceptions |
|---------|-------------------|-----------------|-------------------|-------------------|
| `cost_sync` | 5 | 300s (5 min) | 2 | HttpResponseError, ConnectionError, TimeoutError |
| `compliance_sync` | 5 | 300s (5 min) | 2 | HttpResponseError, ConnectionError, TimeoutError |
| `resource_sync` | 5 | 300s (5 min) | 2 | HttpResponseError, ConnectionError, TimeoutError |
| `identity_sync` | 3 | 180s (3 min) | 2 | HttpResponseError, ConnectionError, TimeoutError |
| `graph_api` | 5 | 300s (5 min) | 2 | HttpResponseError, ConnectionError, TimeoutError |
| `riverside_sync` | 5 | 300s (5 min) | 2 | HttpResponseError, ConnectionError, TimeoutError |
| `dmarc_sync` | 3 | 300s (5 min) | 2 | HttpResponseError, ConnectionError, TimeoutError |
| `budget_sync` | 5 | 300s (5 min) | 2 | HttpResponseError, ConnectionError, TimeoutError |

### Important: What Trips the Breaker

The `expected_exception` list is `(HttpResponseError, ConnectionError, TimeoutError)`.

This means:
- **`DataError`** (SQLAlchemy) → Does NOT trip the breaker ✅ (correct — DB schema issues shouldn't block Azure API calls)
- **`IntegrityError`** (SQLAlchemy) → Does NOT trip the breaker ✅ (correct)
- **`PendingRollbackError`** → Does NOT trip the breaker ✅ (correct)
- **HTTP 429/503** from Azure → DOES trip the breaker ✅ (correct)
- **Network timeout** → DOES trip the breaker ✅ (correct)

### Interaction with Scheduler

The `@circuit_breaker(COMPLIANCE_SYNC_BREAKER)` decorator wraps the **entire** `sync_compliance()` function. This means:

1. If the function catches errors internally (as it currently does for HttpResponseError), those don't trip the breaker
2. Only **uncaught** exceptions that propagate out of `sync_compliance()` are evaluated
3. The current code catches most Azure errors internally → breaker rarely trips
4. A `DataError` crash WOULD propagate out but wouldn't trip the breaker (not in expected_exception)
5. After fixing DataError (with truncation + SAVEPOINT), the breaker behavior is unchanged

### Recovery Timeline Example

```
T+0:00  sync_compliance() fails with uncaught HttpResponseError
T+0:00  COMPLIANCE_SYNC_BREAKER: failure_count = 1
...
T+0:20  (4 more failures across retries)
T+0:20  COMPLIANCE_SYNC_BREAKER: failure_count = 5 → STATE: OPEN
T+0:20  All subsequent calls immediately raise CircuitBreakerError

T+5:20  recovery_timeout (300s) elapses
T+5:20  Next scheduled call triggers can_execute()
T+5:20  COMPLIANCE_SYNC_BREAKER: STATE → HALF_OPEN
T+5:20  Trial call to sync_compliance() begins

        If success:
T+5:20    success_count = 1
T+9:20    Next scheduled call, another success → success_count = 2
T+9:20    success_threshold reached → STATE: CLOSED (fully recovered)

        If failure:
T+5:20    STATE → OPEN again, timeout restarts from T+5:20
```
