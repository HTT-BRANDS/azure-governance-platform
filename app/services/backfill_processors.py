"""Domain-specific data processors for historical backfill."""

import json
import logging
from datetime import UTC, datetime, timedelta

from azure.core.exceptions import HttpResponseError

from app.api.services.azure_client import azure_client_manager
from app.models.compliance import ComplianceSnapshot
from app.models.cost import CostSnapshot
from app.models.identity import IdentitySnapshot
from app.models.resource import Resource
from app.services.backfill_core import BackfillProcessor, _log_http_error, _run_async

logger = logging.getLogger(__name__)


class CostDataProcessor(BackfillProcessor):
    """Processor for cost data backfill."""

    def get_model_class(self) -> type:
        """Return CostSnapshot model class."""
        return CostSnapshot

    def fetch_data(self, date: datetime) -> list[dict]:
        """Fetch cost data for a specific date via Azure Cost Management API.

        Queries subscriptions and retrieves actual cost data using the
        Azure Cost Management query API, grouped by resource group and
        service name. Skips zero-cost entries to save storage.
        """
        from azure.mgmt.costmanagement.models import (
            QueryAggregation,
            QueryDataset,
            QueryDefinition,
            QueryGrouping,
            QueryTimePeriod,
        )

        try:
            subs = _run_async(azure_client_manager.list_subscriptions(self.tenant_id))
        except Exception as e:
            logger.warning(f"Cost backfill: failed listing subs for {self.tenant_id}: {e}")
            return []

        from_date = date.strftime("%Y-%m-%d")
        to_date = (date + timedelta(days=1)).strftime("%Y-%m-%d")
        records = []

        for sub in subs:
            sub_id = sub["subscription_id"]
            if sub.get("state") != "Enabled":
                continue
            try:
                cost_client = azure_client_manager.get_cost_client(
                    self.tenant_id,
                    sub_id,
                )
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
                            "totalCost": QueryAggregation(
                                name="Cost",
                                function="Sum",
                            ),
                        },
                        grouping=[
                            QueryGrouping(
                                type="Dimension",
                                name="ResourceGroupName",
                            ),
                            QueryGrouping(
                                type="Dimension",
                                name="ServiceName",
                            ),
                        ],
                    ),
                )
                result = cost_client.query.usage(
                    scope=f"/subscriptions/{sub_id}",
                    parameters=query,
                )
                if not (result.properties and result.properties.rows):
                    continue
                for row in result.properties.rows:
                    if len(row) < 3:
                        continue
                    cost_value = float(row[0]) if row[0] else 0.0
                    if cost_value == 0.0:
                        continue
                    records.append(
                        {
                            "tenant_id": self.tenant_id,
                            "subscription_id": sub_id,
                            "date": date.date(),
                            "total_cost": cost_value,
                            "currency": str(row[2]) if row[2] else "USD",
                            "resource_group": (str(row[3]) if len(row) > 3 and row[3] else None),
                            "service_name": (str(row[4]) if len(row) > 4 and row[4] else None),
                            "meter_category": None,
                            "synced_at": datetime.now(UTC),
                        }
                    )
            except HttpResponseError as e:
                _log_http_error("Cost backfill", sub_id, e)
            except Exception as e:
                logger.warning(f"Cost backfill: error for sub {sub_id}: {e}")

        logger.info(f"Cost backfill: {len(records)} records for {date.date()}")
        return records


class IdentityDataProcessor(BackfillProcessor):
    """Processor for identity data backfill."""

    def get_model_class(self) -> type:
        """Return IdentitySnapshot model class."""
        return IdentitySnapshot

    def fetch_data(self, date: datetime) -> list[dict]:
        """Fetch identity snapshot data via Microsoft Graph API.

        Identity snapshots are monthly aggregates. Only generates records
        on first-of-month dates. Fetches user counts, guest users,
        privileged users, and MFA status from Graph API.
        """
        if date.day != 1:
            return []

        from app.api.services.graph_client import GraphClient

        try:
            graph_client = GraphClient(self.tenant_id)
            users = _run_async(graph_client.get_users())
            guest_users = _run_async(graph_client.get_guest_users())
            directory_roles = _run_async(graph_client.get_directory_roles())
            service_principals = _run_async(graph_client.get_service_principals())

            # MFA status (may fail with insufficient permissions)
            mfa_enabled_count = 0
            mfa_disabled_count = len(users)
            try:
                mfa_response = _run_async(graph_client.get_mfa_status())
                mfa_users = mfa_response.get("value", [])
                mfa_enabled_count = sum(1 for u in mfa_users if u.get("isMfaRegistered", False))
                mfa_disabled_count = len(mfa_users) - mfa_enabled_count
            except Exception as e:
                logger.warning(f"Identity backfill: could not fetch MFA status: {e}")

            # Calculate active/stale users
            now = datetime.now(UTC)
            stale_30d = now - timedelta(days=30)
            stale_90d = now - timedelta(days=90)
            active_count = 0
            stale_30d_count = 0
            stale_90d_count = 0

            for user in users:
                sign_in = user.get("signInActivity", {})
                last_str = sign_in.get("lastSignInDateTime")
                if last_str:
                    try:
                        last_dt = datetime.fromisoformat(last_str.replace("Z", "+00:00")).replace(
                            tzinfo=None
                        )
                        if last_dt >= stale_30d:
                            active_count += 1
                        if last_dt < stale_90d:
                            stale_90d_count += 1
                            stale_30d_count += 1
                        elif last_dt < stale_30d:
                            stale_30d_count += 1
                    except (ValueError, AttributeError):
                        stale_30d_count += 1
                        stale_90d_count += 1
                else:
                    stale_30d_count += 1
                    stale_90d_count += 1

            # Count privileged users from directory roles
            privileged_count = 0
            for role in directory_roles:
                for member in role.get("members", []):
                    if "#microsoft.graph.user" in member.get("@odata.type", ""):
                        privileged_count += 1

            records = [
                {
                    "tenant_id": self.tenant_id,
                    "snapshot_date": date.date(),
                    "total_users": len(users),
                    "active_users": active_count,
                    "guest_users": len(guest_users),
                    "mfa_enabled_users": mfa_enabled_count,
                    "mfa_disabled_users": mfa_disabled_count,
                    "privileged_users": privileged_count,
                    "stale_accounts_30d": stale_30d_count,
                    "stale_accounts_90d": stale_90d_count,
                    "service_principals": len(service_principals),
                    "synced_at": datetime.now(UTC),
                }
            ]
            logger.info(f"Identity backfill: {len(users)} users for {date.date()}")
            return records

        except Exception as e:
            logger.warning(f"Identity backfill: failed for {self.tenant_id}: {e}")
            return []


class ComplianceDataProcessor(BackfillProcessor):
    """Processor for compliance data backfill."""

    def get_model_class(self) -> type:
        """Return ComplianceSnapshot model class."""
        return ComplianceSnapshot

    def fetch_data(self, date: datetime) -> list[dict]:
        """Fetch compliance data via Azure Policy Insights API.

        Queries subscriptions and retrieves compliance states, counting
        compliant, non-compliant, and exempt resources per subscription.
        """
        try:
            subs = _run_async(azure_client_manager.list_subscriptions(self.tenant_id))
        except Exception as e:
            logger.warning(f"Compliance backfill: failed listing subs for {self.tenant_id}: {e}")
            return []

        records = []
        for sub in subs:
            sub_id = sub["subscription_id"]
            if sub.get("state") != "Enabled":
                continue
            try:
                policy_client = azure_client_manager.get_policy_client(
                    self.tenant_id,
                    sub_id,
                )
                compliant = 0
                non_compliant = 0
                exempt = 0

                policy_states = policy_client.policy_states.list_query_results_for_subscription(
                    policy_states_resource="latest",
                    subscription_id=sub_id,
                )
                for state in policy_states:
                    cs = state.compliance_state.value if state.compliance_state else "Unknown"
                    if cs == "Compliant":
                        compliant += 1
                    elif cs == "NonCompliant":
                        non_compliant += 1
                    elif cs == "Exempt":
                        exempt += 1

                total = compliant + non_compliant + exempt
                pct = (compliant / total * 100) if total > 0 else 0.0

                records.append(
                    {
                        "tenant_id": self.tenant_id,
                        "subscription_id": sub_id,
                        "snapshot_date": date,
                        "overall_compliance_percent": pct,
                        "secure_score": None,
                        "compliant_resources": compliant,
                        "non_compliant_resources": non_compliant,
                        "exempt_resources": exempt,
                        "synced_at": datetime.now(UTC),
                    }
                )
            except HttpResponseError as e:
                _log_http_error("Compliance backfill", sub_id, e)
            except Exception as e:
                logger.warning(f"Compliance backfill: error for sub {sub_id}: {e}")

        logger.info(f"Compliance backfill: {len(records)} records for {date.date()}")
        return records


class ResourcesDataProcessor(BackfillProcessor):
    """Processor for resources data backfill."""

    def get_model_class(self) -> type:
        """Return Resource model class."""
        return Resource

    def fetch_data(self, date: datetime) -> list[dict]:
        """Fetch resource inventory via Azure Resource Manager API.

        Queries subscriptions and retrieves the full resource inventory,
        parsing resource IDs for resource group, type, and name.
        Detects orphaned resources via provisioning state and tags.
        """
        try:
            subs = _run_async(azure_client_manager.list_subscriptions(self.tenant_id))
        except Exception as e:
            logger.warning(f"Resources backfill: failed listing subs for {self.tenant_id}: {e}")
            return []

        records = []
        for sub in subs:
            sub_id = sub["subscription_id"]
            if sub.get("state") != "Enabled":
                continue
            try:
                resource_client = azure_client_manager.get_resource_client(
                    self.tenant_id,
                    sub_id,
                )
                resources = resource_client.resources.list(
                    expand="provisioningState,createdTime,changedTime",
                )
                for resource in resources:
                    resource_id = resource.id or ""
                    resource_group = ""
                    resource_type = ""

                    # Parse resource group from resource ID
                    id_parts = resource_id.split("/")
                    for i, part in enumerate(id_parts):
                        if part.lower() == "resourcegroups" and i + 1 < len(id_parts):
                            resource_group = id_parts[i + 1]
                            break

                    # Parse resource type (provider/type)
                    if "/providers/" in resource_id:
                        prov = resource_id.split("/providers/")[-1]
                        prov_parts = prov.split("/")
                        if len(prov_parts) >= 2:
                            resource_type = f"{prov_parts[0]}/{prov_parts[1]}"

                    tags_json = json.dumps(resource.tags) if resource.tags else None

                    # Detect orphaned resources
                    is_orphaned = 0
                    prov_state = resource.provisioning_state or ""
                    if prov_state.lower() in ("failed", "canceled"):
                        is_orphaned = 1
                    elif resource.tags:
                        tag_str = json.dumps(resource.tags).lower()
                        if any(ind in tag_str for ind in ["orphaned", "orphan", "untracked"]):
                            is_orphaned = 1

                    sku_str = None
                    if resource.sku:
                        sku_str = (
                            resource.sku.name
                            if hasattr(resource.sku, "name")
                            else str(resource.sku)
                        )

                    records.append(
                        {
                            "id": resource_id,
                            "tenant_id": self.tenant_id,
                            "subscription_id": sub_id,
                            "resource_group": resource_group,
                            "resource_type": resource_type,
                            "name": resource.name or "",
                            "location": resource.location or "",
                            "provisioning_state": prov_state,
                            "sku": sku_str,
                            "kind": getattr(resource, "kind", None),
                            "tags_json": tags_json,
                            "is_orphaned": is_orphaned,
                            "estimated_monthly_cost": None,
                            "synced_at": datetime.now(UTC),
                        }
                    )
            except HttpResponseError as e:
                _log_http_error("Resources backfill", sub_id, e)
            except Exception as e:
                logger.warning(f"Resources backfill: error for sub {sub_id}: {e}")

        logger.info(f"Resources backfill: {len(records)} records for {date.date()}")
        return records
