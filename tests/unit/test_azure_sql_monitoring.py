"""Tests for app/core/azure_sql_monitoring.py.

Covers:
- Dataclass creation (QueryStoreMetrics, DTUMetrics, ConnectionPoolMetrics)
- AzureSQLMonitor: query store checks, top queries, slow queries,
  N+1 detection, DTU metrics, connection stats, pool metrics,
  missing indexes, full report, recommendations
- track_sql_dependency helper
- log_query_store_metrics helper

Phase B.2 of the test coverage sprint.
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from app.core.azure_sql_monitoring import (
    AzureSQLMonitor,
    ConnectionPoolMetrics,
    DTUMetrics,
    QueryStoreMetrics,
)

# ---------------------------------------------------------------------------
# Dataclass construction
# ---------------------------------------------------------------------------


class TestQueryStoreMetrics:
    def test_creation(self):
        m = QueryStoreMetrics(
            query_id=1,
            query_text="SELECT * FROM tenants",
            avg_duration_ms=12.5,
            total_duration_ms=125.0,
            execution_count=10,
            avg_cpu_time_ms=3.2,
            avg_logical_io_reads=100,
            avg_logical_io_writes=5,
            last_execution_time=datetime(2025, 1, 1),
            plan_id=42,
        )
        assert m.query_id == 1
        assert m.avg_duration_ms == 12.5
        assert m.execution_count == 10


class TestDTUMetrics:
    def test_creation(self):
        m = DTUMetrics(
            avg_cpu_percent=45.0,
            avg_data_io_percent=20.0,
            avg_log_write_percent=10.0,
            avg_memory_usage_percent=60.0,
            xtp_storage_percent=None,
            dtu_limit=100,
            vcores=None,
            timestamp=datetime(2025, 1, 1),
        )
        assert m.avg_cpu_percent == 45.0
        assert m.dtu_limit == 100
        assert m.xtp_storage_percent is None


class TestConnectionPoolMetrics:
    def test_creation(self):
        m = ConnectionPoolMetrics(
            pool_size=10,
            checked_in=7,
            checked_out=3,
            overflow=0,
            utilization_percent=30.0,
            wait_count=None,
            timestamp=datetime(2025, 1, 1),
        )
        assert m.pool_size == 10
        assert m.utilization_percent == 30.0


# ---------------------------------------------------------------------------
# AzureSQLMonitor — is_query_store_enabled
# ---------------------------------------------------------------------------


class TestIsQueryStoreEnabled:
    """Various scenarios for Query Store detection."""

    @patch("app.core.azure_sql_monitoring.settings")
    def test_disabled_by_setting(self, mock_settings):
        mock_settings.azure_sql_enable_query_store = False
        monitor = AzureSQLMonitor(MagicMock())
        assert monitor.is_query_store_enabled() is False

    @patch("app.core.azure_sql_monitoring.settings")
    def test_sqlite_returns_false(self, mock_settings):
        mock_settings.azure_sql_enable_query_store = True
        mock_settings.database_url = "sqlite:///test.db"
        monitor = AzureSQLMonitor(MagicMock())
        assert monitor.is_query_store_enabled() is False

    @patch("app.core.azure_sql_monitoring.settings")
    def test_read_write_returns_true(self, mock_settings):
        mock_settings.azure_sql_enable_query_store = True
        mock_settings.database_url = "mssql+pyodbc://server/db"
        db = MagicMock()
        db.execute.return_value.scalar.return_value = "READ_WRITE"
        monitor = AzureSQLMonitor(db)
        assert monitor.is_query_store_enabled() is True

    @patch("app.core.azure_sql_monitoring.settings")
    def test_read_only_returns_false(self, mock_settings):
        mock_settings.azure_sql_enable_query_store = True
        mock_settings.database_url = "mssql+pyodbc://server/db"
        db = MagicMock()
        db.execute.return_value.scalar.return_value = "READ_ONLY"
        monitor = AzureSQLMonitor(db)
        assert monitor.is_query_store_enabled() is False

    @patch("app.core.azure_sql_monitoring.settings")
    def test_exception_returns_false(self, mock_settings):
        mock_settings.azure_sql_enable_query_store = True
        mock_settings.database_url = "mssql+pyodbc://server/db"
        db = MagicMock()
        db.execute.side_effect = Exception("connection lost")
        monitor = AzureSQLMonitor(db)
        assert monitor.is_query_store_enabled() is False

    @patch("app.core.azure_sql_monitoring.settings")
    def test_caches_result(self, mock_settings):
        mock_settings.azure_sql_enable_query_store = True
        mock_settings.database_url = "mssql+pyodbc://server/db"
        db = MagicMock()
        db.execute.return_value.scalar.return_value = "READ_WRITE"
        monitor = AzureSQLMonitor(db)
        monitor.is_query_store_enabled()
        monitor.is_query_store_enabled()
        # Only one DB call — cached after first
        assert db.execute.call_count == 1


# ---------------------------------------------------------------------------
# AzureSQLMonitor — get_top_queries_by_duration
# ---------------------------------------------------------------------------


class TestGetTopQueriesByDuration:
    @patch("app.core.azure_sql_monitoring.settings")
    def test_returns_empty_when_qs_disabled(self, mock_settings):
        mock_settings.azure_sql_enable_query_store = False
        monitor = AzureSQLMonitor(MagicMock())
        assert monitor.get_top_queries_by_duration() == []

    @patch("app.core.azure_sql_monitoring.settings")
    def test_returns_empty_on_exception(self, mock_settings):
        mock_settings.azure_sql_enable_query_store = True
        mock_settings.database_url = "mssql+pyodbc://server/db"
        db = MagicMock()
        # First call: is_query_store_enabled check
        db.execute.return_value.scalar.return_value = "READ_WRITE"
        monitor = AzureSQLMonitor(db)
        monitor.is_query_store_enabled()
        # Second call: the actual query throws
        db.execute.side_effect = Exception("query failed")
        assert monitor.get_top_queries_by_duration() == []


# ---------------------------------------------------------------------------
# AzureSQLMonitor — get_slow_queries
# ---------------------------------------------------------------------------


class TestGetSlowQueries:
    @patch("app.core.azure_sql_monitoring.settings")
    def test_filters_by_threshold(self, mock_settings):
        mock_settings.azure_sql_enable_query_store = False
        mock_settings.slow_query_threshold_ms = 100
        monitor = AzureSQLMonitor(MagicMock())
        # QS disabled, so get_top_queries_by_duration returns []
        assert monitor.get_slow_queries(threshold_ms=50) == []

    @patch.object(AzureSQLMonitor, "get_top_queries_by_duration")
    @patch("app.core.azure_sql_monitoring.settings")
    def test_filters_above_threshold(self, mock_settings, mock_top):
        mock_settings.slow_query_threshold_ms = 100
        fast = MagicMock()
        fast.avg_duration_ms = 50.0
        slow = MagicMock()
        slow.avg_duration_ms = 200.0
        mock_top.return_value = [fast, slow]

        monitor = AzureSQLMonitor(MagicMock())
        result = monitor.get_slow_queries(threshold_ms=100)
        assert len(result) == 1
        assert result[0].avg_duration_ms == 200.0


# ---------------------------------------------------------------------------
# AzureSQLMonitor — get_n1_query_candidates
# ---------------------------------------------------------------------------


class TestGetN1QueryCandidates:
    @patch("app.core.azure_sql_monitoring.settings")
    def test_returns_empty_when_qs_disabled(self, mock_settings):
        mock_settings.azure_sql_enable_query_store = False
        monitor = AzureSQLMonitor(MagicMock())
        assert monitor.get_n1_query_candidates() == []


# ---------------------------------------------------------------------------
# AzureSQLMonitor — get_dtu_metrics
# ---------------------------------------------------------------------------


class TestGetDTUMetrics:
    @patch("app.core.azure_sql_monitoring.settings")
    def test_sqlite_returns_none(self, mock_settings):
        mock_settings.database_url = "sqlite:///test.db"
        monitor = AzureSQLMonitor(MagicMock())
        assert monitor.get_dtu_metrics() is None

    @patch("app.core.azure_sql_monitoring.settings")
    def test_exception_returns_none(self, mock_settings):
        mock_settings.database_url = "mssql+pyodbc://server/db"
        db = MagicMock()
        db.execute.side_effect = Exception("boom")
        monitor = AzureSQLMonitor(db)
        assert monitor.get_dtu_metrics() is None

    @patch("app.core.azure_sql_monitoring.settings")
    def test_no_result_returns_none(self, mock_settings):
        mock_settings.database_url = "mssql+pyodbc://server/db"
        db = MagicMock()
        db.execute.return_value.fetchone.return_value = None
        monitor = AzureSQLMonitor(db)
        assert monitor.get_dtu_metrics() is None


# ---------------------------------------------------------------------------
# AzureSQLMonitor — get_connection_stats
# ---------------------------------------------------------------------------


class TestGetConnectionStats:
    @patch("app.core.azure_sql_monitoring.settings")
    def test_sqlite_returns_note(self, mock_settings):
        mock_settings.database_url = "sqlite:///test.db"
        monitor = AzureSQLMonitor(MagicMock())
        result = monitor.get_connection_stats()
        assert "note" in result
        assert "SQLite" in result["note"]

    @patch("app.core.azure_sql_monitoring.settings")
    def test_exception_returns_error(self, mock_settings):
        mock_settings.database_url = "mssql+pyodbc://server/db"
        db = MagicMock()
        db.execute.side_effect = Exception("access denied")
        monitor = AzureSQLMonitor(db)
        result = monitor.get_connection_stats()
        assert "error" in result


# ---------------------------------------------------------------------------
# AzureSQLMonitor — get_pool_metrics
# ---------------------------------------------------------------------------


class TestGetPoolMetrics:
    @patch("app.core.azure_sql_monitoring.get_pool_stats")
    def test_returns_connection_pool_metrics(self, mock_pool):
        mock_pool.return_value = {
            "size": 5,
            "checked_in": 3,
            "checked_out": 2,
            "overflow": 0,
            "utilization_percent": 40.0,
        }
        monitor = AzureSQLMonitor(MagicMock())
        result = monitor.get_pool_metrics()
        assert isinstance(result, ConnectionPoolMetrics)
        assert result.pool_size == 5
        assert result.checked_out == 2
        assert result.utilization_percent == 40.0

    @patch("app.core.azure_sql_monitoring.get_pool_stats")
    def test_handles_empty_pool_stats(self, mock_pool):
        mock_pool.return_value = {}
        monitor = AzureSQLMonitor(MagicMock())
        result = monitor.get_pool_metrics()
        assert result.pool_size == 0
        assert result.checked_in == 0


# ---------------------------------------------------------------------------
# AzureSQLMonitor — get_missing_indexes
# ---------------------------------------------------------------------------


class TestGetMissingIndexes:
    @patch("app.core.azure_sql_monitoring.settings")
    def test_returns_empty_when_qs_disabled(self, mock_settings):
        mock_settings.azure_sql_enable_query_store = False
        monitor = AzureSQLMonitor(MagicMock())
        assert monitor.get_missing_indexes() == []


# ---------------------------------------------------------------------------
# AzureSQLMonitor — _generate_recommendations
# ---------------------------------------------------------------------------


class TestGenerateRecommendations:
    def test_high_cpu_recommendation(self):
        monitor = AzureSQLMonitor(MagicMock())
        dtu = MagicMock()
        dtu.avg_cpu_percent = 95.0
        dtu.avg_data_io_percent = 10.0
        dtu.avg_memory_usage_percent = 20.0
        report = {
            "dtu_metrics": dtu,
            "pool_metrics": None,
            "top_slow_queries": [],
            "n1_candidates": [],
            "missing_indexes": [],
        }
        recs = monitor._generate_recommendations(report)
        assert any("HIGH CPU" in r for r in recs)

    def test_high_io_recommendation(self):
        monitor = AzureSQLMonitor(MagicMock())
        dtu = MagicMock()
        dtu.avg_cpu_percent = 10.0
        dtu.avg_data_io_percent = 90.0
        dtu.avg_memory_usage_percent = 20.0
        report = {
            "dtu_metrics": dtu,
            "pool_metrics": None,
            "top_slow_queries": [],
            "n1_candidates": [],
            "missing_indexes": [],
        }
        recs = monitor._generate_recommendations(report)
        assert any("HIGH IO" in r for r in recs)

    def test_high_memory_recommendation(self):
        monitor = AzureSQLMonitor(MagicMock())
        dtu = MagicMock()
        dtu.avg_cpu_percent = 10.0
        dtu.avg_data_io_percent = 10.0
        dtu.avg_memory_usage_percent = 95.0
        report = {
            "dtu_metrics": dtu,
            "pool_metrics": None,
            "top_slow_queries": [],
            "n1_candidates": [],
            "missing_indexes": [],
        }
        recs = monitor._generate_recommendations(report)
        assert any("HIGH MEMORY" in r for r in recs)

    def test_high_pool_utilization(self):
        monitor = AzureSQLMonitor(MagicMock())
        pool = MagicMock()
        pool.utilization_percent = 85.0
        pool.pool_size = 10
        report = {
            "dtu_metrics": None,
            "pool_metrics": pool,
            "top_slow_queries": [],
            "n1_candidates": [],
            "missing_indexes": [],
        }
        recs = monitor._generate_recommendations(report)
        assert any("HIGH POOL" in r for r in recs)

    def test_slow_queries_recommendation(self):
        monitor = AzureSQLMonitor(MagicMock())
        report = {
            "dtu_metrics": None,
            "pool_metrics": None,
            "top_slow_queries": [
                {"avg_duration_ms": 2000},
                {"avg_duration_ms": 1500},
            ],
            "n1_candidates": [],
            "missing_indexes": [],
        }
        recs = monitor._generate_recommendations(report)
        assert any("SLOW QUERIES" in r for r in recs)

    def test_n1_candidates_recommendation(self):
        monitor = AzureSQLMonitor(MagicMock())
        report = {
            "dtu_metrics": None,
            "pool_metrics": None,
            "top_slow_queries": [],
            "n1_candidates": [{"query_id": 1}],
            "missing_indexes": [],
        }
        recs = monitor._generate_recommendations(report)
        assert any("N+1" in r for r in recs)

    def test_missing_indexes_recommendation(self):
        monitor = AzureSQLMonitor(MagicMock())
        report = {
            "dtu_metrics": None,
            "pool_metrics": None,
            "top_slow_queries": [],
            "n1_candidates": [],
            "missing_indexes": [{"table": f"t{i}"} for i in range(8)],
        }
        recs = monitor._generate_recommendations(report)
        assert any("MISSING INDEXES" in r for r in recs)

    def test_no_recommendations_when_healthy(self):
        monitor = AzureSQLMonitor(MagicMock())
        dtu = MagicMock()
        dtu.avg_cpu_percent = 20.0
        dtu.avg_data_io_percent = 15.0
        dtu.avg_memory_usage_percent = 30.0
        pool = MagicMock()
        pool.utilization_percent = 25.0
        report = {
            "dtu_metrics": dtu,
            "pool_metrics": pool,
            "top_slow_queries": [],
            "n1_candidates": [],
            "missing_indexes": [],
        }
        recs = monitor._generate_recommendations(report)
        assert recs == []


# ---------------------------------------------------------------------------
# AzureSQLMonitor — get_full_report
# ---------------------------------------------------------------------------


class TestGetFullReport:
    @patch("app.core.azure_sql_monitoring.settings")
    def test_full_report_structure(self, mock_settings):
        mock_settings.azure_sql_enable_query_store = False
        mock_settings.database_url = "sqlite:///test.db"
        db = MagicMock()
        monitor = AzureSQLMonitor(db)

        with patch.object(monitor, "get_pool_metrics") as mock_pool:
            mock_pool.return_value = ConnectionPoolMetrics(
                pool_size=5,
                checked_in=3,
                checked_out=2,
                overflow=0,
                utilization_percent=40.0,
                wait_count=None,
                timestamp=datetime.now(UTC),
            )
            report = monitor.get_full_report()

        assert "timestamp" in report
        assert "query_store_enabled" in report
        assert report["query_store_enabled"] is False
        assert "generation_time_ms" in report
        assert "recommendations" in report
        assert isinstance(report["recommendations"], list)


# ---------------------------------------------------------------------------
# track_sql_dependency
# ---------------------------------------------------------------------------


class TestTrackSqlDependency:
    @patch("app.core.azure_sql_monitoring.settings")
    def test_noop_when_insights_disabled(self, mock_settings):
        mock_settings.app_insights_enabled = False
        from app.core.azure_sql_monitoring import track_sql_dependency

        # Should not raise
        track_sql_dependency("test", "SELECT 1", 10.0, True)

    @patch("app.core.azure_sql_monitoring.settings")
    def test_handles_import_error_gracefully(self, mock_settings):
        mock_settings.app_insights_enabled = True
        from app.core.azure_sql_monitoring import track_sql_dependency

        with patch(
            "app.core.azure_sql_monitoring.settings.app_insights_enabled",
            new=True,
        ):
            # If app_insights module fails to import, just logs debug
            track_sql_dependency("test", "SELECT 1", 10.0, True)


# ---------------------------------------------------------------------------
# log_query_store_metrics
# ---------------------------------------------------------------------------


class TestLogQueryStoreMetrics:
    @patch("app.core.azure_sql_monitoring.settings")
    def test_noop_when_insights_disabled(self, mock_settings):
        mock_settings.app_insights_enabled = False
        from app.core.azure_sql_monitoring import log_query_store_metrics

        log_query_store_metrics(MagicMock())  # Should not raise
