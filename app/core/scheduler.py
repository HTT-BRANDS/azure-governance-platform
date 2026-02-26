"""Background job scheduler for data synchronization."""

import logging
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from azure.core.exceptions import HttpResponseError
from azure.mgmt.costmanagement.models import (
    QueryAggregation,
    QueryDataset,
    QueryDefinition,
    QueryGrouping,
    QueryTimePeriod,
)

from app.api.services.azure_client import azure_client_manager
from app.core.config import get_settings
from app.core.database import get_db_context
from app.models.cost import CostSnapshot
from app.models.tenant import Tenant

logger = logging.getLogger(__name__)
settings = get_settings()

# Global scheduler instance
scheduler: AsyncIOScheduler | None = None


async def sync_costs():
    """Sync cost data from all tenants.

    Fetches the last 30 days of cost data from Azure Cost Management API
    for all active tenants and their subscriptions, storing results in
    the CostSnapshot model grouped by resource group and service name.
    """
    logger.info(f"Starting cost sync at {datetime.utcnow()}")

    # Define time period (last 30 days)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    from_date = start_date.strftime("%Y-%m-%d")
    to_date = end_date.strftime("%Y-%m-%d")

    total_synced = 0
    total_errors = 0

    try:
        with get_db_context() as db:
            # Get all active tenants
            tenants = db.query(Tenant).filter(Tenant.is_active).all()
            logger.info(f"Found {len(tenants)} active tenants to sync")

            for tenant in tenants:
                logger.info(f"Syncing costs for tenant: {tenant.name} ({tenant.tenant_id})")

                try:
                    # Get subscriptions for this tenant
                    subscriptions = await azure_client_manager.list_subscriptions(tenant.tenant_id)
                    logger.info(f"Found {len(subscriptions)} subscriptions for tenant {tenant.name}")

                    for sub in subscriptions:
                        sub_id = sub["subscription_id"]
                        sub_name = sub["display_name"]

                        # Skip non-enabled subscriptions
                        if sub["state"] != "Enabled":
                            logger.info(f"Skipping subscription {sub_name} (state: {sub['state']})")
                            continue

                        try:
                            logger.info(f"Querying costs for subscription: {sub_name} ({sub_id[:8]}...)")

                            # Get cost client for this subscription
                            cost_client = azure_client_manager.get_cost_client(
                                tenant.tenant_id,
                                sub_id
                            )

                            # Build query definition with grouping by ResourceGroup and ServiceName
                            query = QueryDefinition(
                                type="ActualCost",
                                timeframe="Custom",
                                time_period=QueryTimePeriod(
                                    from_property=from_date,
                                    to=to_date,
                                ),
                                dataset=QueryDataset(
                                    granularity="Daily",
                                    aggregation={
                                        "totalCost": QueryAggregation(name="Cost", function="Sum")
                                    },
                                    grouping=[
                                        QueryGrouping(type="Dimension", name="ResourceGroupName"),
                                        QueryGrouping(type="Dimension", name="ServiceName"),
                                    ],
                                ),
                            )

                            # Execute query
                            result = cost_client.query.usage(
                                scope=f"/subscriptions/{sub_id}",
                                parameters=query,
                            )

                            # Process results
                            if result.properties and result.properties.rows:
                                rows_processed = 0

                                # Column indices (based on query grouping and aggregation)
                                # Typical order: Cost, UsageDate, Currency, ResourceGroupName, ServiceName
                                for row in result.properties.rows:
                                    try:
                                        if len(row) < 3:
                                            continue

                                        # Extract values from row
                                        cost_value = float(row[0]) if row[0] else 0.0
                                        usage_date = datetime.strptime(str(row[1]), "%Y%m%d").date()
                                        currency = str(row[2]) if len(row) > 2 and row[2] else "USD"
                                        resource_group = str(row[3]) if len(row) > 3 and row[3] else None
                                        service_name = str(row[4]) if len(row) > 4 and row[4] else None

                                        # Skip zero-cost entries to save space
                                        if cost_value == 0.0:
                                            continue

                                        # Create or update cost snapshot
                                        snapshot = CostSnapshot(
                                            tenant_id=tenant.id,
                                            subscription_id=sub_id,
                                            date=usage_date,
                                            total_cost=cost_value,
                                            currency=currency,
                                            resource_group=resource_group,
                                            service_name=service_name,
                                            synced_at=datetime.utcnow(),
                                        )

                                        db.add(snapshot)
                                        rows_processed += 1

                                    except (ValueError, TypeError, IndexError) as e:
                                        logger.warning(f"Error processing cost row: {e}")
                                        continue

                                # Commit all snapshots for this subscription
                                db.commit()
                                total_synced += rows_processed
                                logger.info(
                                    f"Successfully synced {rows_processed} cost records "
                                    f"for subscription {sub_name}"
                                )
                            else:
                                logger.info(f"No cost data found for subscription {sub_name}")

                        except HttpResponseError as e:
                            total_errors += 1
                            if e.status_code == 403:
                                logger.error(
                                    f"Access denied to cost data for subscription {sub_name}. "
                                    f"Missing Cost Management Reader role?"
                                )
                            else:
                                logger.error(
                                    f"HTTP error querying costs for subscription {sub_name}: "
                                    f"{e.status_code} - {e.message}"
                                )
                        except Exception as e:
                            total_errors += 1
                            logger.error(
                                f"Error syncing costs for subscription {sub_name}: {e}",
                                exc_info=True
                            )

                except Exception as e:
                    total_errors += 1
                    logger.error(
                        f"Error processing tenant {tenant.name}: {e}",
                        exc_info=True
                    )

        logger.info(
            f"Cost sync completed: {total_synced} records synced, "
            f"{total_errors} errors encountered"
        )

    except Exception as e:
        logger.error(f"Fatal error during cost sync: {e}", exc_info=True)
        raise


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
