"""Azure SQL monitoring and Query Store integration.

Tracks Query Store metrics, DTU/CPU usage, connection pool stats,
and integrates with Application Insights for comprehensive monitoring.

Features:
- Query Store top/slow query tracking
- DTU and CPU usage monitoring
- Connection pool statistics
- Application Insights integration
- Automated alerts for performance thresholds

References:
- https://docs.microsoft.com/en-us/sql/relational-databases/performance/monitoring-performance-by-using-the-query-store
- https://docs.microsoft.com/en-us/azure/azure-sql/database/monitoring-with-dmvs
"""

import logging
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_pool_stats

logger = logging.getLogger(__name__)

settings = get_settings()


@dataclass
class QueryStoreMetrics:
    """Query Store performance metrics for a single query."""

    query_id: int
    query_text: str
    avg_duration_ms: float
    total_duration_ms: float
    execution_count: int
    avg_cpu_time_ms: float
    avg_logical_io_reads: int
    avg_logical_io_writes: int
    last_execution_time: datetime
    plan_id: int


@dataclass
class DTUMetrics:
    """Azure SQL DTU/vCore utilization metrics."""

    avg_cpu_percent: float
    avg_data_io_percent: float
    avg_log_write_percent: float
    avg_memory_usage_percent: float
    xtp_storage_percent: float | None  # In-Memory OLTP
    dtu_limit: int | None  # For DTU-based tiers
    vcores: int | None  # For vCore-based tiers
    timestamp: datetime


@dataclass
class ConnectionPoolMetrics:
    """Connection pool utilization metrics."""

    pool_size: int
    checked_in: int
    checked_out: int
    overflow: int
    utilization_percent: float
    wait_count: int | None  # If pool exhaustion occurred
    timestamp: datetime


class AzureSQLMonitor:
    """Azure SQL performance monitoring with Query Store integration."""

    def __init__(self, db: Session):
        self.db = db
        self._query_store_enabled: bool | None = None

    def is_query_store_enabled(self) -> bool:
        """Check if Query Store is enabled for the current database."""
        if self._query_store_enabled is not None:
            return self._query_store_enabled

        if not settings.azure_sql_enable_query_store:
            self._query_store_enabled = False
            return False

        try:
            # Query Store is only available on Azure SQL (not SQLite)
            if settings.database_url.startswith("sqlite"):
                self._query_store_enabled = False
                return False

            result = self.db.execute(
                text("""
                    SELECT actual_state_desc
                    FROM sys.database_query_store_options
                """)
            ).scalar()

            self._query_store_enabled = result == "READ_WRITE"
            return self._query_store_enabled
        except Exception as e:
            logger.warning(f"Could not check Query Store status: {e}")
            self._query_store_enabled = False
            return False

    def get_top_queries_by_duration(
        self,
        top_n: int = 10,
        time_window_hours: int = 24,
    ) -> list[QueryStoreMetrics]:
        """Get top N queries by average duration from Query Store.

        Args:
            top_n: Number of queries to return
            time_window_hours: Lookback window for query history

        Returns:
            List of QueryStoreMetrics for slowest queries
        """
        if not self.is_query_store_enabled():
            logger.debug("Query Store not enabled, skipping top queries analysis")
            return []

        try:
            # Query Store query for top duration queries
            query = text("""
                SELECT TOP (:top_n)
                    q.query_id,
                    t.query_sql_text,
                    AVG(rs.avg_duration / 1000.0) as avg_duration_ms,
                    SUM(rs.avg_duration * rs.count_executions / 1000.0) as total_duration_ms,
                    SUM(rs.count_executions) as execution_count,
                    AVG(rs.avg_cpu_time / 1000.0) as avg_cpu_time_ms,
                    AVG(rs.avg_logical_io_reads) as avg_logical_io_reads,
                    AVG(rs.avg_logical_io_writes) as avg_logical_io_writes,
                    MAX(rs.last_execution_time) as last_execution_time,
                    rs.plan_id
                FROM sys.query_store_query q
                JOIN sys.query_store_query_text t ON q.query_text_id = t.query_text_id
                JOIN sys.query_store_plan p ON q.query_id = p.query_id
                JOIN sys.query_store_runtime_stats rs ON p.plan_id = rs.plan_id
                WHERE rs.last_execution_time >= DATEADD(HOUR, -:hours, GETUTCDATE())
                GROUP BY q.query_id, t.query_sql_text, rs.plan_id
                ORDER BY avg_duration_ms DESC
            """)

            results = self.db.execute(
                query,
                {"top_n": top_n, "hours": time_window_hours},
            )

            return [
                QueryStoreMetrics(
                    query_id=row.query_id,
                    query_text=row.query_sql_text[:500],  # Truncate for logging
                    avg_duration_ms=float(row.avg_duration_ms),
                    total_duration_ms=float(row.total_duration_ms),
                    execution_count=int(row.execution_count),
                    avg_cpu_time_ms=float(row.avg_cpu_time_ms),
                    avg_logical_io_reads=int(row.avg_logical_io_reads or 0),
                    avg_logical_io_writes=int(row.avg_logical_io_writes or 0),
                    last_execution_time=row.last_execution_time,
                    plan_id=row.plan_id,
                )
                for row in results
            ]
        except Exception as e:
            logger.error(f"Failed to get top queries from Query Store: {e}")
            return []

    def get_slow_queries(
        self,
        threshold_ms: float | None = None,
        time_window_hours: int = 24,
    ) -> list[QueryStoreMetrics]:
        """Get queries exceeding duration threshold.

        Args:
            threshold_ms: Duration threshold in milliseconds
            time_window_hours: Lookback window for query history

        Returns:
            List of slow queries
        """
        threshold = threshold_ms or settings.slow_query_threshold_ms
        all_queries = self.get_top_queries_by_duration(
            top_n=100,  # Get more to filter
            time_window_hours=time_window_hours,
        )
        return [q for q in all_queries if q.avg_duration_ms > threshold]

    def get_n1_query_candidates(self, time_window_hours: int = 24) -> list[dict[str, Any]]:
        """Identify potential N+1 query patterns.

        Looks for queries that:
        - Have high execution counts with low individual duration
        - Similar query patterns with different IDs (parameter sniffing issues)

        Returns:
            List of potential N+1 query patterns
        """
        if not self.is_query_store_enabled():
            return []

        try:
            query = text("""
                SELECT
                    q.query_id,
                    t.query_sql_text,
                    SUM(rs.count_executions) as execution_count,
                    AVG(rs.avg_duration / 1000.0) as avg_duration_ms,
                    COUNT(DISTINCT p.plan_id) as plan_count
                FROM sys.query_store_query q
                JOIN sys.query_store_query_text t ON q.query_text_id = t.query_text_id
                JOIN sys.query_store_plan p ON q.query_id = p.query_id
                JOIN sys.query_store_runtime_stats rs ON p.plan_id = rs.plan_id
                WHERE rs.last_execution_time >= DATEADD(HOUR, -:hours, GETUTCDATE())
                    AND rs.count_executions > 100
                    AND rs.avg_duration < 50000  -- Less than 50ms avg
                GROUP BY q.query_id, t.query_sql_text
                HAVING SUM(rs.count_executions) > 500
                ORDER BY execution_count DESC
            """)

            results = self.db.execute(query, {"hours": time_window_hours})

            candidates = []
            for row in results:
                # Check for query patterns that might be N+1
                sql = row.query_sql_text.upper()
                is_n1_candidate = any(
                    pattern in sql for pattern in ["WHERE ID =", "WHERE ID IN", "SELECT TOP 1"]
                )

                if is_n1_candidate and row.execution_count > 1000:
                    candidates.append(
                        {
                            "query_id": row.query_id,
                            "query_preview": row.query_sql_text[:200],
                            "execution_count": row.execution_count,
                            "avg_duration_ms": float(row.avg_duration_ms),
                            "plan_count": row.plan_count,
                            "suspected_pattern": "N+1 loop candidate",
                        }
                    )

            return candidates
        except Exception as e:
            logger.error(f"Failed to identify N+1 patterns: {e}")
            return []

    def get_dtu_metrics(self) -> DTUMetrics | None:
        """Get current DTU/vCore utilization from Azure SQL.

        Uses sys.dm_db_resource_stats for resource utilization.

        Returns:
            DTUMetrics with current utilization or None if not available
        """
        if settings.database_url.startswith("sqlite"):
            return None

        try:
            # Get latest resource stats
            query = text("""
                SELECT TOP 1
                    avg_cpu_percent,
                    avg_data_io_percent,
                    avg_log_write_percent,
                    avg_memory_usage_percent,
                    xtp_storage_percent,
                    dtu_limit,
                    (SELECT COUNT(*) FROM sys.dm_os_schedulers WHERE status = 'VISIBLE ONLINE') as vcores
                FROM sys.dm_db_resource_stats
                ORDER BY end_time DESC
            """)

            result = self.db.execute(query).fetchone()
            if not result:
                return None

            return DTUMetrics(
                avg_cpu_percent=float(result.avg_cpu_percent),
                avg_data_io_percent=float(result.avg_data_io_percent),
                avg_log_write_percent=float(result.avg_log_write_percent),
                avg_memory_usage_percent=float(result.avg_memory_usage_percent),
                xtp_storage_percent=float(result.xtp_storage_percent)
                if result.xtp_storage_percent
                else None,
                dtu_limit=int(result.dtu_limit) if result.dtu_limit else None,
                vcores=int(result.vcores) if result.vcores else None,
                timestamp=datetime.now(UTC),
            )
        except Exception as e:
            logger.warning(f"Could not retrieve DTU metrics: {e}")
            return None

    def get_connection_stats(self) -> dict[str, Any]:
        """Get Azure SQL connection statistics.

        Returns:
            Dict with connection counts and status
        """
        if settings.database_url.startswith("sqlite"):
            return {"note": "SQLite - no connection stats available"}

        try:
            query = text("""
                SELECT
                    COUNT(*) as total_connections,
                    SUM(CASE WHEN status = 'sleeping' THEN 1 ELSE 0 END) as idle_connections,
                    SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) as active_connections,
                    SUM(CASE WHEN is_user_process = 0 THEN 1 ELSE 0 END) as system_connections
                FROM sys.dm_exec_sessions
                WHERE is_user_process = 1 OR last_request_start_time > DATEADD(MINUTE, -5, GETDATE())
            """)

            result = self.db.execute(query).fetchone()

            # Also get blocking info
            blocking_query = text("""
                SELECT COUNT(*) as blocking_count
                FROM sys.dm_exec_requests
                WHERE blocking_session_id > 0
            """)
            blocking = self.db.execute(blocking_query).scalar()

            return {
                "total_sessions": result.total_connections if result else 0,
                "idle_sessions": result.idle_connections if result else 0,
                "active_sessions": result.active_connections if result else 0,
                "blocking_sessions": blocking or 0,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        except Exception as e:
            logger.warning(f"Could not retrieve connection stats: {e}")
            return {"error": str(e)}

    def get_pool_metrics(self) -> ConnectionPoolMetrics:
        """Get SQLAlchemy connection pool metrics combined with Azure SQL stats."""
        pool_stats = get_pool_stats()

        return ConnectionPoolMetrics(
            pool_size=pool_stats.get("size", 0),
            checked_in=pool_stats.get("checked_in", 0),
            checked_out=pool_stats.get("checked_out", 0),
            overflow=pool_stats.get("overflow", 0),
            utilization_percent=pool_stats.get("utilization_percent", 0.0),
            wait_count=None,  # Would need custom pool implementation
            timestamp=datetime.now(UTC),
        )

    def get_missing_indexes(self) -> list[dict[str, Any]]:
        """Get missing index recommendations from Query Store.

        Returns:
            List of missing index recommendations
        """
        if not self.is_query_store_enabled():
            return []

        try:
            query = text("""
                SELECT TOP 20
                    mig.index_handle,
                    OBJECT_NAME(mid.object_id) as table_name,
                    mid.equality_columns,
                    mid.inequality_columns,
                    mid.included_columns,
                    migs.user_seeks,
                    migs.user_scans,
                    migs.avg_total_user_cost,
                    migs.avg_user_impact,
                    (migs.user_seeks + migs.user_scans) * migs.avg_total_user_cost * migs.avg_user_impact / 100.0 as improvement_measure
                FROM sys.dm_db_missing_index_groups mig
                INNER JOIN sys.dm_db_missing_index_group_stats migs ON mig.index_group_handle = migs.index_group_handle
                INNER JOIN sys.dm_db_missing_index_details mid ON mig.index_handle = mid.index_handle
                WHERE mid.database_id = DB_ID()
                ORDER BY improvement_measure DESC
            """)

            results = self.db.execute(query)

            return [
                {
                    "table": row.table_name,
                    "equality_columns": row.equality_columns,
                    "inequality_columns": row.inequality_columns,
                    "included_columns": row.included_columns,
                    "user_seeks": row.user_seeks,
                    "user_scans": row.user_scans,
                    "avg_cost": float(row.avg_total_user_cost),
                    "improvement_percent": float(row.avg_user_impact),
                    "improvement_measure": float(row.improvement_measure),
                }
                for row in results
            ]
        except Exception as e:
            logger.warning(f"Could not retrieve missing indexes: {e}")
            return []

    def get_full_report(self) -> dict[str, Any]:
        """Get comprehensive Azure SQL monitoring report."""
        start_time = time.time()

        report = {
            "timestamp": datetime.now(UTC).isoformat(),
            "query_store_enabled": self.is_query_store_enabled(),
            "dtu_metrics": None,
            "pool_metrics": None,
            "connection_stats": None,
            "top_slow_queries": [],
            "n1_candidates": [],
            "missing_indexes": [],
            "recommendations": [],
        }

        # Collect all metrics
        try:
            report["dtu_metrics"] = self.get_dtu_metrics()
        except Exception as e:
            logger.warning(f"DTU metrics failed: {e}")

        try:
            report["pool_metrics"] = self.get_pool_metrics()
        except Exception as e:
            logger.warning(f"Pool metrics failed: {e}")

        try:
            report["connection_stats"] = self.get_connection_stats()
        except Exception as e:
            logger.warning(f"Connection stats failed: {e}")

        try:
            report["top_slow_queries"] = [
                {
                    "query_id": q.query_id,
                    "avg_duration_ms": q.avg_duration_ms,
                    "execution_count": q.execution_count,
                    "query_preview": q.query_text[:100],
                }
                for q in self.get_top_queries_by_duration(top_n=5)
            ]
        except Exception as e:
            logger.warning(f"Top queries failed: {e}")

        try:
            report["n1_candidates"] = self.get_n1_query_candidates()[:5]
        except Exception as e:
            logger.warning(f"N+1 detection failed: {e}")

        try:
            report["missing_indexes"] = self.get_missing_indexes()[:10]
        except Exception as e:
            logger.warning(f"Missing indexes failed: {e}")

        # Generate recommendations
        report["recommendations"] = self._generate_recommendations(report)

        report["generation_time_ms"] = (time.time() - start_time) * 1000

        return report

    def _generate_recommendations(self, report: dict[str, Any]) -> list[str]:
        """Generate optimization recommendations based on metrics."""
        recommendations = []

        # DTU recommendations
        dtu = report.get("dtu_metrics")
        if dtu:
            if dtu.avg_cpu_percent > 80:
                recommendations.append(
                    f"HIGH CPU: {dtu.avg_cpu_percent:.1f}% - Consider scaling up or optimizing top queries"
                )
            if dtu.avg_data_io_percent > 80:
                recommendations.append(
                    f"HIGH IO: {dtu.avg_data_io_percent:.1f}% - Consider adding indexes or scaling storage"
                )
            if dtu.avg_memory_usage_percent > 90:
                recommendations.append(
                    f"HIGH MEMORY: {dtu.avg_memory_usage_percent:.1f}% - Consider scaling compute tier"
                )

        # Pool recommendations
        pool = report.get("pool_metrics")
        if pool and pool.utilization_percent > 80:
            recommendations.append(
                f"HIGH POOL UTILIZATION: {pool.utilization_percent:.1f}% - "
                f"Consider increasing pool_size (currently {pool.pool_size})"
            )

        # Query recommendations
        slow_queries = report.get("top_slow_queries", [])
        if slow_queries:
            avg_slow = sum(q["avg_duration_ms"] for q in slow_queries) / len(slow_queries)
            if avg_slow > 1000:
                recommendations.append(
                    f"SLOW QUERIES: {len(slow_queries)} queries avg {avg_slow:.0f}ms - "
                    "Review Query Store for optimization opportunities"
                )

        # N+1 recommendations
        n1 = report.get("n1_candidates", [])
        if n1:
            recommendations.append(
                f"N+1 PATTERN DETECTED: {len(n1)} candidates - "
                "Consider eager loading with joinedload()"
            )

        # Missing index recommendations
        indexes = report.get("missing_indexes", [])
        if len(indexes) > 5:
            recommendations.append(
                f"MISSING INDEXES: {len(indexes)} recommendations available - "
                "Run analyze_azure_sql_queries.py for details"
            )

        return recommendations


def track_sql_dependency(
    name: str,
    data: str,
    duration_ms: float,
    success: bool,
    properties: dict[str, Any] | None = None,
) -> None:
    """Track SQL operation in Application Insights.

    Args:
        name: Operation name
        data: Query or operation details
        duration_ms: Duration in milliseconds
        success: Whether operation succeeded
        properties: Additional custom properties
    """
    if not settings.app_insights_enabled:
        return

    try:
        from app.core.app_insights import track_dependency

        track_dependency(
            name=name,
            data=data[:100],  # Truncate for safety
            duration=duration_ms,
            success=success,
            dependency_type="SQL",
            properties=properties or {},
        )
    except Exception as e:
        logger.debug(f"Failed to track SQL dependency: {e}")


def log_query_store_metrics(
    db: Session,
    operation_name: str = "query_analysis",
) -> None:
    """Log Query Store metrics to Application Insights.

    This is designed to be called periodically (e.g., from a scheduled job)
    to track database performance trends.
    """
    if not settings.app_insights_enabled:
        return

    monitor = AzureSQLMonitor(db)

    try:
        dtu = monitor.get_dtu_metrics()
        if dtu:
            from app.core.app_insights import track_metric

            track_metric("sql_cpu_percent", dtu.avg_cpu_percent)
            track_metric("sql_data_io_percent", dtu.avg_data_io_percent)
            track_metric("sql_log_write_percent", dtu.avg_log_write_percent)
            track_metric("sql_memory_percent", dtu.avg_memory_usage_percent)

        pool = monitor.get_pool_metrics()
        if pool:
            track_metric("sql_pool_utilization", pool.utilization_percent)
            track_metric("sql_pool_checked_out", pool.checked_out)

    except Exception as e:
        logger.warning(f"Failed to log Query Store metrics: {e}")
