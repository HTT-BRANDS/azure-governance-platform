"""Riverside preflight check: RiversideSchedulerCheck.

Split from the monolithic app/preflight/riverside_checks.py
(issue 6oj7, 2026-04-22).
"""

import time

from app.preflight.base import BasePreflightCheck
from app.preflight.models import CheckCategory, CheckResult, CheckStatus
from app.preflight.riverside_checks._common import SeverityLevel


class RiversideSchedulerCheck(BasePreflightCheck):
    """Check Riverside scheduler job registration.

    Validates that the Riverside sync job is properly registered
    in the background scheduler and configured with appropriate intervals.
    """

    def __init__(self):
        super().__init__(
            check_id="riverside_scheduler",
            name="Riverside Scheduler Job Registration",
            category=CheckCategory.RIVERSIDE,
            description="Verify Riverside sync job is registered in scheduler",
            timeout_seconds=10.0,
        )

    async def _execute_check(self, tenant_id: str | None = None) -> CheckResult:
        """Execute scheduler job registration check."""
        start_time = time.perf_counter()

        try:
            from app.core.scheduler import get_scheduler

            scheduler = get_scheduler()

            if not scheduler:
                duration_ms = (time.perf_counter() - start_time) * 1000
                return CheckResult(
                    check_id=self.check_id,
                    name=self.name,
                    category=self.category,
                    status=CheckStatus.WARNING,
                    message="Scheduler not initialized",
                    details={
                        "scheduler_initialized": False,
                        "severity": SeverityLevel.WARNING,
                    },
                    duration_ms=duration_ms,
                    recommendations=[
                        "Call init_scheduler() during application startup",
                        "Verify scheduler configuration in core/config.py",
                    ],
                    tenant_id=tenant_id,
                )

            # Look for Riverside sync job
            riverside_job = None
            job_details = {}

            for job in scheduler.get_jobs():
                job_id = job.id if hasattr(job, "id") else str(job)
                if "riverside" in job_id.lower() or "riverside" in str(job.name).lower():
                    riverside_job = job
                    job_details = {
                        "id": job_id,
                        "name": getattr(job, "name", "Unknown"),
                        "trigger": str(job.trigger) if hasattr(job, "trigger") else "Unknown",
                        "next_run_time": str(job.next_run_time)
                        if hasattr(job, "next_run_time")
                        else None,
                    }
                    break

            duration_ms = (time.perf_counter() - start_time) * 1000

            if not riverside_job:
                return CheckResult(
                    check_id=self.check_id,
                    name=self.name,
                    category=self.category,
                    status=CheckStatus.FAIL,
                    message="Riverside sync job not found in scheduler",
                    details={
                        "scheduler_running": scheduler.running,
                        "total_jobs": len(scheduler.get_jobs()),
                        "available_jobs": [
                            job.id if hasattr(job, "id") else str(job)
                            for job in scheduler.get_jobs()
                        ],
                        "severity": SeverityLevel.CRITICAL,
                    },
                    duration_ms=duration_ms,
                    recommendations=[
                        "Add Riverside sync job in init_scheduler() in core/scheduler.py",
                        "Verify the job function exists: app.core.sync.riverside.sync_riverside",
                        "Check job interval configuration (recommended: 4 hours)",
                    ],
                    tenant_id=tenant_id,
                )

            # Check if scheduler is running
            is_running = scheduler.running if hasattr(scheduler, "running") else False

            if not is_running:
                return CheckResult(
                    check_id=self.check_id,
                    name=self.name,
                    category=self.category,
                    status=CheckStatus.WARNING,
                    message="Riverside job registered but scheduler is not running",
                    details={
                        "job_details": job_details,
                        "scheduler_running": False,
                        "severity": SeverityLevel.WARNING,
                    },
                    duration_ms=duration_ms,
                    recommendations=[
                        "Call scheduler.start() during application startup",
                        "Check for scheduler initialization errors in logs",
                    ],
                    tenant_id=tenant_id,
                )

            return CheckResult(
                check_id=self.check_id,
                name=self.name,
                category=self.category,
                status=CheckStatus.PASS,
                message="Riverside sync job registered and scheduler running",
                details={
                    "job_details": job_details,
                    "scheduler_running": True,
                    "total_jobs": len(scheduler.get_jobs()),
                    "severity": SeverityLevel.INFO,
                },
                duration_ms=duration_ms,
                tenant_id=tenant_id,
            )

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            return CheckResult(
                check_id=self.check_id,
                name=self.name,
                category=self.category,
                status=CheckStatus.FAIL,
                message=f"Scheduler check failed: {str(e)}",
                details={
                    "error_type": type(e).__name__,
                    "severity": SeverityLevel.CRITICAL,
                },
                duration_ms=duration_ms,
                recommendations=[
                    "Verify APScheduler is installed: pip install apscheduler",
                    "Check scheduler initialization in core/scheduler.py",
                    "Review application logs for import errors",
                ],
                tenant_id=tenant_id,
            )


async def check_riverside_scheduler(tenant_id: str | None = None) -> CheckResult:
    """Check Riverside scheduler job registration.

    Args:
        tenant_id: Optional tenant ID for tenant-specific checks

    Returns:
        CheckResult with scheduler status
    """
    check = RiversideSchedulerCheck()
    return await check.run(tenant_id=tenant_id)
