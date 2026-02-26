"""Background job scheduler for data synchronization."""

import logging
from datetime import datetime
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Global scheduler instance
scheduler: Optional[AsyncIOScheduler] = None


async def sync_costs():
    """Sync cost data from all tenants."""
    logger.info(f"Starting cost sync at {datetime.utcnow()}")
    # TODO: Implement actual sync logic
    # from app.api.services.cost_service import CostService
    # await CostService.sync_all_tenants()
    logger.info("Cost sync completed")


async def sync_compliance():
    """Sync compliance data from all tenants."""
    logger.info(f"Starting compliance sync at {datetime.utcnow()}")
    # TODO: Implement actual sync logic
    logger.info("Compliance sync completed")


async def sync_resources():
    """Sync resource inventory from all tenants."""
    logger.info(f"Starting resource sync at {datetime.utcnow()}")
    # TODO: Implement actual sync logic
    logger.info("Resource sync completed")


async def sync_identity():
    """Sync identity data from all tenants."""
    logger.info(f"Starting identity sync at {datetime.utcnow()}")
    # TODO: Implement actual sync logic
    logger.info("Identity sync completed")


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


def get_scheduler() -> Optional[AsyncIOScheduler]:
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
