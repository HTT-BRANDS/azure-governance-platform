"""Background job scheduler for data synchronization."""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from app.core.config import get_settings
from app.core.sync.compliance import sync_compliance
from app.core.sync.costs import sync_costs
from app.core.sync.dmarc import sync_dmarc_dkim
from app.core.sync.identity import sync_identity
from app.core.sync.resources import sync_resources
from app.core.sync.riverside import sync_riverside
from app.services.riverside_sync import (
    sync_all_tenants,
    sync_tenant_mfa,
    sync_tenant_devices,
    sync_requirement_status,
    sync_maturity_scores,
)

logger = logging.getLogger(__name__)
settings = get_settings()

# Global scheduler instance
scheduler: AsyncIOScheduler | None = None


def init_scheduler() -> AsyncIOScheduler:
    """Initialize and configure the background scheduler."""
    global scheduler

    scheduler = AsyncIOScheduler()

    # Cost sync job
    scheduler.add_job(
        sync_costs,
        trigger=IntervalTrigger(hours=settings.cost_sync_interval_hours),
        id="sync_costs",
        name="Sync Cost Data",
        replace_existing=True,
    )

    # Compliance sync job
    scheduler.add_job(
        sync_compliance,
        trigger=IntervalTrigger(hours=settings.compliance_sync_interval_hours),
        id="sync_compliance",
        name="Sync Compliance Data",
        replace_existing=True,
    )

    # Resource sync job
    scheduler.add_job(
        sync_resources,
        trigger=IntervalTrigger(hours=settings.resource_sync_interval_hours),
        id="sync_resources",
        name="Sync Resource Inventory",
        replace_existing=True,
    )

    # Identity sync job
    scheduler.add_job(
        sync_identity,
        trigger=IntervalTrigger(hours=settings.identity_sync_interval_hours),
        id="sync_identity",
        name="Sync Identity Data",
        replace_existing=True,
    )

    # Riverside compliance sync job (every 4 hours)
    scheduler.add_job(
        sync_riverside,
        trigger=IntervalTrigger(hours=4),
        id="sync_riverside",
        name="Sync Riverside Compliance Data",
        replace_existing=True,
    )

    # DMARC/DKIM sync job (daily at 2 AM)
    scheduler.add_job(
        sync_dmarc_dkim,
        trigger=CronTrigger(hour=2, minute=0),
        id="sync_dmarc",
        name="Sync DMARC/DKIM Data",
        replace_existing=True,
    )

    # Riverside MFA sync job (hourly - refresh MFA data every hour)
    scheduler.add_job(
        hourly_mfa_sync,
        trigger=CronTrigger(minute=0),  # Every hour at minute 0
        id="riverside_hourly_mfa_sync",
        name="Riverside Hourly MFA Sync",
        replace_existing=True,
    )

    # Riverside full compliance sync job (daily at 1 AM)
    scheduler.add_job(
        daily_full_sync,
        trigger=CronTrigger(hour=1, minute=0),
        id="riverside_daily_full_sync",
        name="Riverside Daily Full Compliance Sync",
        replace_existing=True,
    )

    # Riverside threat data sync job (weekly on Sunday at 3 AM)
    scheduler.add_job(
        weekly_threat_sync,
        trigger=CronTrigger(day_of_week="sun", hour=3, minute=0),
        id="riverside_weekly_threat_sync",
        name="Riverside Weekly Threat Data Sync",
        replace_existing=True,
    )

    # Riverside monthly report sync job (1st of month at 4 AM)
    scheduler.add_job(
        monthly_report_sync,
        trigger=CronTrigger(day=1, hour=4, minute=0),
        id="riverside_monthly_report_sync",
        name="Riverside Monthly Report Sync",
        replace_existing=True,
    )

    logger.info("Scheduler initialized with sync jobs")
    return scheduler


def get_scheduler() -> AsyncIOScheduler | None:
    """Get the scheduler instance."""
    return scheduler


# Riverside scheduled sync wrapper functions

async def hourly_mfa_sync():
    """Hourly MFA data refresh for all tenants.
    
    Refreshes MFA enrollment data across all active tenants.
    Runs every hour to provide near real-time MFA coverage visibility.
    """
    logger.info("Starting hourly MFA sync job")
    try:
        result = await sync_all_tenants(
            skip_failed=True,
            include_mfa=True,
            include_devices=False,
            include_requirements=False,
            include_maturity=False,
        )
        logger.info(f"Hourly MFA sync completed: {result.get('tenants_processed', 0)} tenants processed")
    except Exception as e:
        logger.error(f"Hourly MFA sync failed: {e}")


async def daily_full_sync():
    """Daily full compliance sync for all tenants.
    
    Performs comprehensive compliance data synchronization including:
    - MFA enrollment data
    - Device compliance status
    - Requirement status updates
    - Maturity score calculations
    
    Runs daily at 1:00 AM to ensure fresh daily compliance data.
    """
    logger.info("Starting daily full compliance sync job")
    try:
        result = await sync_all_tenants(
            skip_failed=True,
            include_mfa=True,
            include_devices=True,
            include_requirements=True,
            include_maturity=True,
        )
        logger.info(
            f"Daily full sync completed: {result.get('tenants_processed', 0)} tenants, "
            f"{result.get('tenants_failed', 0)} failed"
        )
    except Exception as e:
        logger.error(f"Daily full sync failed: {e}")


async def weekly_threat_sync():
    """Weekly threat data synchronization.
    
    Performs deep device compliance and threat detection data sync:
    - Device compliance status
    - EDR coverage verification
    - Encryption status audit
    - Security posture assessment
    
    Runs weekly on Sundays at 3:00 AM for comprehensive weekly review.
    """
    logger.info("Starting weekly threat data sync job")
    try:
        result = await sync_all_tenants(
            skip_failed=True,
            include_mfa=False,
            include_devices=True,
            include_requirements=True,
            include_maturity=False,
        )
        logger.info(
            f"Weekly threat sync completed: {result.get('tenants_processed', 0)} tenants processed"
        )
    except Exception as e:
        logger.error(f"Weekly threat sync failed: {e}")


async def monthly_report_sync():
    """Monthly report generation sync.
    
    Generates comprehensive monthly compliance reports including:
    - Full maturity score calculations
    - Requirement status summaries
    - Compliance trend analysis
    - Executive summary data preparation
    
    Runs monthly on the 1st at 4:00 AM to generate month-end reports.
    """
    logger.info("Starting monthly report sync job")
    try:
        result = await sync_all_tenants(
            skip_failed=True,
            include_mfa=True,
            include_devices=True,
            include_requirements=True,
            include_maturity=True,
        )
        logger.info(
            f"Monthly report sync completed: {result.get('tenants_processed', 0)} tenants, "
            f"status: {result.get('status', 'unknown')}"
        )
    except Exception as e:
        logger.error(f"Monthly report sync failed: {e}")


async def trigger_manual_sync(sync_type: str) -> bool:
    """Trigger a manual sync job."""
    sync_functions = {
        "costs": sync_costs,
        "compliance": sync_compliance,
        "resources": sync_resources,
        "identity": sync_identity,
        "riverside": sync_riverside,
        "dmarc": sync_dmarc_dkim,
        "hourly_mfa": hourly_mfa_sync,
        "daily_full": daily_full_sync,
        "weekly_threat": weekly_threat_sync,
        "monthly_report": monthly_report_sync,
    }

    if sync_type not in sync_functions:
        return False

    await sync_functions[sync_type]()
    return True
