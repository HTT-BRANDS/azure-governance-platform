"""Unit tests for CO-010: Chargeback / Showback Reporting.

Tests cover:
- ChargebackService.get_chargeback_report() — DB integration via real SQLite session
- ChargebackService.export_chargeback_csv() — CSV correctness
- ChargebackService.export_chargeback_json() — JSON correctness
- GET /api/v1/costs/chargeback — route-level tests via TestClient
"""

import csv
import io
import json
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.services.chargeback_service import (
    ChargebackReport,
    ChargebackService,
    TenantChargebackEntry,
)
from app.models.cost import CostSnapshot
from app.models.tenant import Tenant

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TODAY = date.today()
_START = _TODAY - timedelta(days=30)
_END = _TODAY


def _make_tenant(db, tenant_id: str, name: str) -> Tenant:
    """Insert and return a Tenant row."""
    tenant = Tenant(
        id=tenant_id,
        tenant_id=tenant_id,
        name=name,
        is_active=True,
    )
    db.add(tenant)
    return tenant


def _make_snapshot(
    db,
    *,
    tenant_id: str,
    subscription_id: str = "sub-001",
    snap_date: date | None = None,
    total_cost: float = 100.0,
    service_name: str | None = None,
    meter_category: str | None = None,
    resource_group: str | None = "rg-prod",
) -> CostSnapshot:
    """Insert and return a CostSnapshot row."""
    snap = CostSnapshot(
        tenant_id=tenant_id,
        subscription_id=subscription_id,
        date=snap_date or _TODAY - timedelta(days=1),
        total_cost=total_cost,
        service_name=service_name,
        meter_category=meter_category,
        resource_group=resource_group,
    )
    db.add(snap)
    return snap


def _build_report(
    *,
    tenants: list[TenantChargebackEntry] | None = None,
    total_cost: float = 1000.0,
) -> ChargebackReport:
    """Build a synthetic ChargebackReport for export tests."""

    if tenants is None:
        tenants = [
            TenantChargebackEntry(
                tenant_id="t-1",
                tenant_name="Tenant Alpha",
                total_cost=600.0,
                percentage_of_total=60.0,
                breakdown={"compute": 400.0, "storage": 200.0},
                cost_per_resource=150.0,
                resource_count=4,
            ),
            TenantChargebackEntry(
                tenant_id="t-2",
                tenant_name="Tenant Beta",
                total_cost=400.0,
                percentage_of_total=40.0,
                breakdown={"network": 250.0, "other": 150.0},
                cost_per_resource=200.0,
                resource_count=2,
            ),
        ]
    return ChargebackReport(
        period_start=_START,
        period_end=_END,
        generated_at=__import__("datetime").datetime(2024, 6, 1, 12, 0, 0),
        tenants=tenants,
        total_cost=total_cost,
        currency="USD",
    )


# ===========================================================================
# 1. get_chargeback_report — all tenants (no filter)
# ===========================================================================


def test_get_chargeback_report_all_tenants(db_session):
    """Reports include all tenants when no tenant_ids filter is supplied."""
    _make_tenant(db_session, "t-aaa", "Alpha Corp")
    _make_tenant(db_session, "t-bbb", "Beta Inc")
    _make_snapshot(db_session, tenant_id="t-aaa", total_cost=500.0)
    _make_snapshot(db_session, tenant_id="t-bbb", total_cost=300.0)
    db_session.commit()

    import asyncio

    service = ChargebackService(db_session)
    report = asyncio.get_event_loop().run_until_complete(
        service.get_chargeback_report(
            tenant_ids=None,
            start_date=_START,
            end_date=_END,
        )
    )

    tenant_ids_in_report = {e.tenant_id for e in report.tenants}
    assert "t-aaa" in tenant_ids_in_report
    assert "t-bbb" in tenant_ids_in_report
    assert len(report.tenants) == 2
    assert report.total_cost == pytest.approx(800.0, abs=0.01)
    assert report.currency == "USD"


# ===========================================================================
# 2. get_chargeback_report — specific tenant filter
# ===========================================================================


def test_get_chargeback_report_specific_tenant_filter(db_session):
    """Reports include only the requested tenants when tenant_ids is provided."""
    _make_tenant(db_session, "t-x", "X Corp")
    _make_tenant(db_session, "t-y", "Y Corp")
    _make_snapshot(db_session, tenant_id="t-x", total_cost=1000.0)
    _make_snapshot(db_session, tenant_id="t-y", total_cost=2000.0)
    db_session.commit()

    import asyncio

    service = ChargebackService(db_session)
    report = asyncio.get_event_loop().run_until_complete(
        service.get_chargeback_report(
            tenant_ids=["t-x"],
            start_date=_START,
            end_date=_END,
        )
    )

    assert len(report.tenants) == 1
    assert report.tenants[0].tenant_id == "t-x"
    assert report.tenants[0].tenant_name == "X Corp"
    assert report.total_cost == pytest.approx(1000.0, abs=0.01)


# ===========================================================================
# 3. get_chargeback_report — empty date range (no data)
# ===========================================================================


def test_get_chargeback_report_empty_date_range(db_session):
    """Report has zero tenants when no snapshots exist in the requested window."""
    _make_tenant(db_session, "t-empty", "Empty Tenant")
    # Snapshot is outside the requested window
    far_past = date(2020, 1, 1)
    _make_snapshot(db_session, tenant_id="t-empty", snap_date=far_past, total_cost=999.0)
    db_session.commit()

    import asyncio

    service = ChargebackService(db_session)
    report = asyncio.get_event_loop().run_until_complete(
        service.get_chargeback_report(
            tenant_ids=None,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )
    )

    assert report.tenants == []
    assert report.total_cost == 0.0


# ===========================================================================
# 4. export_chargeback_csv — valid CSV with headers
# ===========================================================================


def test_export_chargeback_csv_valid_headers():
    """CSV output starts with the expected header row."""
    service = ChargebackService(db=MagicMock())
    report = _build_report()
    csv_str = service.export_chargeback_csv(report)

    reader = csv.DictReader(io.StringIO(csv_str))
    headers = reader.fieldnames or []

    assert "tenant_id" in headers
    assert "tenant_name" in headers
    assert "total_cost" in headers
    assert "percentage_of_total" in headers
    assert "resource_count" in headers
    assert "cost_per_resource" in headers


# ===========================================================================
# 5. export_chargeback_csv — correct column count
# ===========================================================================


def test_export_chargeback_csv_correct_column_count():
    """Column count equals base columns (6) plus unique breakdown categories."""
    service = ChargebackService(db=MagicMock())
    report = _build_report()
    csv_str = service.export_chargeback_csv(report)

    reader = csv.DictReader(io.StringIO(csv_str))
    headers = reader.fieldnames or []

    # Base: tenant_id, tenant_name, total_cost, percentage_of_total,
    #       resource_count, cost_per_resource  →  6
    # Breakdown: compute, storage (t-1) + network, other (t-2)  →  4 unique cats
    base_count = 6
    unique_categories = {"compute", "storage", "network", "other"}
    assert len(headers) == base_count + len(unique_categories)


# ===========================================================================
# 6. export_chargeback_csv — handles single tenant
# ===========================================================================


def test_export_chargeback_csv_single_tenant():
    """CSV with a single tenant produces exactly one data row plus header."""
    single_entry = [
        TenantChargebackEntry(
            tenant_id="t-solo",
            tenant_name="Solo Tenant",
            total_cost=999.99,
            percentage_of_total=100.0,
            breakdown={"compute": 999.99},
            cost_per_resource=333.33,
            resource_count=3,
        )
    ]
    service = ChargebackService(db=MagicMock())
    report = _build_report(tenants=single_entry, total_cost=999.99)
    csv_str = service.export_chargeback_csv(report)

    rows = list(csv.DictReader(io.StringIO(csv_str)))
    assert len(rows) == 1
    assert rows[0]["tenant_id"] == "t-solo"
    assert rows[0]["tenant_name"] == "Solo Tenant"
    assert float(rows[0]["total_cost"]) == pytest.approx(999.99, abs=0.01)
    assert float(rows[0]["compute"]) == pytest.approx(999.99, abs=0.01)


# ===========================================================================
# 7. export_chargeback_json — produces valid JSON
# ===========================================================================


def test_export_chargeback_json_valid():
    """JSON export can be parsed and contains expected top-level keys."""
    service = ChargebackService(db=MagicMock())
    report = _build_report()
    json_str = service.export_chargeback_json(report)

    # Must parse without error
    data = json.loads(json_str)

    assert "period_start" in data
    assert "period_end" in data
    assert "generated_at" in data
    assert "tenants" in data
    assert "total_cost" in data
    assert "currency" in data
    assert isinstance(data["tenants"], list)
    assert len(data["tenants"]) == 2


# ===========================================================================
# 8. percentage_of_total sums to ~100% across all tenants
# ===========================================================================


def test_percentage_of_total_sums_to_100(db_session):
    """The sum of all tenant percentage_of_total values rounds to 100."""
    _make_tenant(db_session, "t-p1", "P1")
    _make_tenant(db_session, "t-p2", "P2")
    _make_tenant(db_session, "t-p3", "P3")
    _make_snapshot(db_session, tenant_id="t-p1", total_cost=300.0)
    _make_snapshot(db_session, tenant_id="t-p2", total_cost=500.0)
    _make_snapshot(db_session, tenant_id="t-p3", total_cost=200.0)
    db_session.commit()

    import asyncio

    service = ChargebackService(db_session)
    report = asyncio.get_event_loop().run_until_complete(
        service.get_chargeback_report(
            tenant_ids=None,
            start_date=_START,
            end_date=_END,
        )
    )

    total_pct = sum(e.percentage_of_total for e in report.tenants)
    assert total_pct == pytest.approx(100.0, abs=0.01)


# ===========================================================================
# Route tests — GET /api/v1/costs/chargeback
# ===========================================================================


class TestChargebackRoute:
    """Route-level tests for GET /api/v1/costs/chargeback."""

    # -----------------------------------------------------------------------
    # 9. Returns 200 JSON by default
    # -----------------------------------------------------------------------

    @patch("app.api.routes.costs.ChargebackService")
    def test_returns_200_json_by_default(self, mock_service_cls, authed_client):
        """GET /costs/chargeback returns 200 and JSON by default."""
        from datetime import datetime

        mock_svc = MagicMock()
        mock_svc.get_chargeback_report = AsyncMock(
            return_value=ChargebackReport(
                period_start=_START,
                period_end=_END,
                generated_at=datetime.utcnow(),
                tenants=[],
                total_cost=0.0,
                currency="USD",
            )
        )
        mock_service_cls.return_value = mock_svc

        response = authed_client.get(
            f"/api/v1/costs/chargeback?start_date={_START}&end_date={_END}"
        )

        assert response.status_code == 200
        data = response.json()
        assert "tenants" in data
        assert "total_cost" in data
        assert data["currency"] == "USD"

    # -----------------------------------------------------------------------
    # 10. Returns CSV content-type when format=csv
    # -----------------------------------------------------------------------

    @patch("app.api.routes.costs.ChargebackService")
    def test_returns_csv_content_type(self, mock_service_cls, authed_client):
        """GET /costs/chargeback?format=csv returns text/csv with Content-Disposition."""
        from datetime import datetime

        mock_report = ChargebackReport(
            period_start=_START,
            period_end=_END,
            generated_at=datetime.utcnow(),
            tenants=[
                TenantChargebackEntry(
                    tenant_id="t-csv",
                    tenant_name="CSV Tenant",
                    total_cost=500.0,
                    percentage_of_total=100.0,
                    breakdown={"compute": 500.0},
                    cost_per_resource=500.0,
                    resource_count=1,
                )
            ],
            total_cost=500.0,
            currency="USD",
        )
        mock_svc = MagicMock()
        mock_svc.get_chargeback_report = AsyncMock(return_value=mock_report)
        mock_svc.export_chargeback_csv = MagicMock(
            return_value="tenant_id,tenant_name,total_cost\nt-csv,CSV Tenant,500.0\n"
        )
        mock_service_cls.return_value = mock_svc

        response = authed_client.get(
            f"/api/v1/costs/chargeback?start_date={_START}&end_date={_END}&format=csv"
        )

        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
        assert "attachment" in response.headers["content-disposition"]
        assert f"chargeback-{_START}-{_END}.csv" in response.headers["content-disposition"]

    # -----------------------------------------------------------------------
    # 11. tenant_ids filter is passed through to service
    # -----------------------------------------------------------------------

    @patch("app.api.routes.costs.ChargebackService")
    def test_tenant_ids_filter_passed_to_service(self, mock_service_cls, authed_client):
        """GET /costs/chargeback with tenant_ids= passes the filter to the service."""
        from datetime import datetime

        mock_svc = MagicMock()
        mock_svc.get_chargeback_report = AsyncMock(
            return_value=ChargebackReport(
                period_start=_START,
                period_end=_END,
                generated_at=datetime.utcnow(),
                tenants=[],
                total_cost=0.0,
                currency="USD",
            )
        )
        mock_service_cls.return_value = mock_svc

        response = authed_client.get(
            f"/api/v1/costs/chargeback"
            f"?start_date={_START}&end_date={_END}"
            f"&tenant_ids=test-tenant-123"
        )

        assert response.status_code == 200
        mock_svc.get_chargeback_report.assert_called_once()
        call_kwargs = mock_svc.get_chargeback_report.call_args.kwargs
        # The mock_authz fixture returns ["test-tenant-123"] for filter_tenant_ids
        assert call_kwargs["tenant_ids"] is not None

    # -----------------------------------------------------------------------
    # 12. Auth required — unauthenticated returns 401
    # -----------------------------------------------------------------------

    def test_requires_authentication(self, client):
        """Unauthenticated request to /costs/chargeback returns 401."""
        response = client.get(f"/api/v1/costs/chargeback?start_date={_START}&end_date={_END}")
        assert response.status_code == 401

    # -----------------------------------------------------------------------
    # 13. Date range validation — end_date before start_date → 422
    # -----------------------------------------------------------------------

    def test_date_range_validation_end_before_start(self, authed_client):
        """end_date before start_date returns 422 Unprocessable Entity."""
        bad_start = _END
        bad_end = _START  # end is before start
        response = authed_client.get(
            f"/api/v1/costs/chargeback?start_date={bad_start}&end_date={bad_end}"
        )
        assert response.status_code == 422
