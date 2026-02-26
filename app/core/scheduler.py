"""Background job scheduler for data synchronization."""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import get_settings
from app.core.sync.compliance import sync_compliance
from app.core.sync.costs import sync_costs
from app.core.sync.identity import sync_identity
from app.core.sync.resources import sync_resources

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

    logger.info("Scheduler initialized with sync jobs")
    return scheduler


def get_scheduler() -> AsyncIOScheduler | None:
    """Get the scheduler instance."""
    return scheduler


async def trigger_manual_sync(sync_type: str) -> bool:
    """Trigger a manual sync job."""
    sync_functions = {
        "costs": sync_costs,
        "compliance": sync_compliance,
        "resources": sync_resources,
        "identity": sync_identity,
    }

    if sync_type not in sync_functions:
        return False

    await sync_functions[sync_type]()
    return True
