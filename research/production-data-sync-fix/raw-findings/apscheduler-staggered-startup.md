# APScheduler Staggered Startup Pattern

**Sources**: APScheduler 3.x Official Documentation (Tier 1)
- https://apscheduler.readthedocs.io/en/3.x/userguide.html#missed-job-executions-and-coalescing
- https://apscheduler.readthedocs.io/en/3.x/userguide.html#limiting-the-number-of-concurrently-executing-instances-of-a-job
- https://apscheduler.readthedocs.io/en/3.x/modules/executors/pool.html
- https://apscheduler.readthedocs.io/en/3.x/modules/schedulers/base.html#apscheduler.schedulers.base.BaseScheduler.add_job

## The Thundering Herd Problem

When all sync jobs use `next_run_time=datetime.now(UTC)` to fire immediately on startup,
they all compete simultaneously for:

1. **Executor thread pool** — APScheduler's `ThreadPoolExecutor` defaults to `max_workers=10`.
   With 6+ sync jobs (costs, compliance, resources, identity, riverside, dmarc), they consume
   6 of 10 threads instantly.

2. **Azure API rate limits** — Azure Management API allows ~12,000 read requests/hour per
   subscription. Six sync jobs each making dozens of API calls simultaneously can trigger
   HTTP 429 (Too Many Requests) throttling.

3. **Database connection pool** — All jobs writing simultaneously contend for the connection
   pool (configured in `app/core/azure_sql_pool.py`). On Azure SQL S0 with 60 max concurrent
   workers, this is rarely a bottleneck, but unnecessary contention degrades performance.

4. **Application startup** — If sync jobs fire before the app is fully initialized (routes
   registered, health checks passing), they may fail and trip circuit breakers before the
   app is even ready to serve traffic.

## APScheduler Documented Behavior

### Executor Thread Pool (Default: 10)

From the official executor pool docs:

> `ThreadPoolExecutor(max_workers=10, pool_kwargs=None)`
>
> An executor that runs jobs in a concurrent.futures thread pool.

With 10 default threads and 6+ sync jobs firing simultaneously, the pool isn't exhausted,
but the sync jobs dominate available threads, potentially delaying any other scheduled work.

### Concurrent Instance Limiting

From the user guide:

> By default, only **one instance of each job** is allowed to be run at the same time. This
> means that if the job is about to be run but the previous run hasn't finished yet, then
> the latest run is considered a misfire.

This prevents the same job from running twice simultaneously, but doesn't prevent
different jobs from running concurrently.

### Missed Executions and Coalescing

From the user guide:

> If the execution of a job is delayed due to no threads or processes being available in
> the pool, the executor may skip it due to it being run too late (compared to its
> originally designated run time). If this is likely to happen in your application, you
> may want to either increase the number of threads/processes in the executor, or adjust
> the `misfire_grace_time` setting to a higher value.

If the thread pool is saturated by all jobs firing simultaneously, some jobs may be
skipped entirely if `misfire_grace_time` is too short.

## Recommended Staggered Startup Pattern

### Pattern: Offset `next_run_time` by Incremental Delays

```python
from datetime import datetime, timedelta, UTC

def init_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    sync_fns = _get_sync_functions()
    now = datetime.now(UTC)

    # Stagger startup: each job starts 2 minutes after the previous one
    staggered_jobs = [
        ("costs",      sync_fns["costs"],      settings.cost_sync_interval_hours,      0),
        ("compliance", sync_fns["compliance"],  settings.compliance_sync_interval_hours, 2),
        ("resources",  sync_fns["resources"],   settings.resource_sync_interval_hours,   4),
        ("identity",   sync_fns["identity"],    settings.identity_sync_interval_hours,   6),
        ("riverside",  sync_fns["riverside"],   4,                                       8),
    ]

    for job_id, func, interval_hours, delay_minutes in staggered_jobs:
        scheduler.add_job(
            func,
            trigger=IntervalTrigger(hours=interval_hours),
            id=f"sync_{job_id}",
            name=f"Sync {job_id.title()} Data",
            replace_existing=True,
            next_run_time=now + timedelta(minutes=delay_minutes),
            misfire_grace_time=300,  # 5 minutes grace for delayed execution
        )

    return scheduler
```

### Why 2-Minute Intervals?

- **API rate limit headroom**: Each sync job typically makes 10-50 API calls per
  subscription. With 2-minute spacing, the previous job has time to complete most
  of its API calls before the next starts.
- **Database write batching**: Each sync job commits in batches. Spacing prevents
  write contention on the same tables.
- **Error isolation**: If one job fails and trips its circuit breaker, subsequent
  jobs still start normally (they use separate circuit breakers).
- **Observable startup**: Log messages are spaced out, making it easy to monitor
  which sync completed successfully.

### Alternative: Startup Delay

Another pattern is to delay ALL sync jobs until the app is fully healthy:

```python
# Wait 30 seconds after startup for app initialization
startup_delay = timedelta(seconds=30)
now = datetime.now(UTC) + startup_delay

# Then stagger from there
scheduler.add_job(..., next_run_time=now)
scheduler.add_job(..., next_run_time=now + timedelta(minutes=2))
```

This ensures health checks pass before sync jobs begin.

## Impact on Circuit Breakers

With staggered startup:
- Each circuit breaker is tested independently
- If Azure APIs are down at startup, the first job trips its breaker
- Subsequent jobs still attempt (different breakers), providing signal about
  which Azure service is impacted
- 5-minute recovery timeout means breakers reopen naturally before the next
  interval-based run

## Current Project State

The current `app/core/scheduler.py` uses `IntervalTrigger` without `next_run_time`,
meaning jobs don't fire until the first interval elapses (e.g., 4 hours after startup).
Adding `next_run_time` with staggering is the recommended improvement.
