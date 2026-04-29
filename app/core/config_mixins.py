"""Settings mixins for app.core.config.

These are BaseModel mixins so Settings can inherit grouped fields without making
one config module exceed the Phase 1.5 file-size target.
"""

import os

from pydantic import BaseModel, Field, field_validator


class RuntimeSettingsMixin(BaseModel):
    database_pool_size: int = Field(default=3, alias="DB_POOL_SIZE")
    database_max_overflow: int = Field(default=2, alias="DB_MAX_OVERFLOW")
    database_pool_timeout: int = Field(default=30, alias="DB_POOL_TIMEOUT")
    slow_query_threshold_ms: float = Field(default=500.0, alias="SLOW_QUERY_THRESHOLD_MS")
    enable_query_logging: bool = Field(default=False, alias="ENABLE_QUERY_LOGGING")

    azure_sql_pool_size: int = Field(
        default=5,
        alias="AZURE_SQL_POOL_SIZE",
        description="Number of connections to keep in pool. 5-10 is optimal for most Azure SQL workloads",
    )
    azure_sql_max_overflow: int = Field(
        default=10,
        alias="AZURE_SQL_MAX_OVERFLOW",
        description="Extra connections beyond pool_size when needed",
    )
    azure_sql_pool_timeout: int = Field(
        default=30,
        alias="AZURE_SQL_POOL_TIMEOUT",
        description="Seconds to wait for connection from pool",
    )
    azure_sql_pool_pre_ping: bool = Field(
        default=True,
        alias="AZURE_SQL_POOL_PRE_PING",
        description="Verify connections before use (critical for Azure SQL)",
    )
    azure_sql_pool_recycle: int = Field(
        default=1800,
        alias="AZURE_SQL_POOL_RECYCLE",
        description="Seconds before recycling connections (Azure SQL timeout is ~30 min)",
    )
    azure_sql_use_null_pool: bool = Field(
        default=False,
        alias="AZURE_SQL_USE_NULL_POOL",
        description="Use NullPool for serverless scenarios (Azure Functions)",
    )

    azure_sql_connection_retry_attempts: int = Field(
        default=5,
        alias="AZURE_SQL_CONNECTION_RETRY_ATTEMPTS",
        description="Max retry attempts for transient Azure SQL faults",
    )
    azure_sql_connection_retry_delay: float = Field(
        default=1.0,
        alias="AZURE_SQL_CONNECTION_RETRY_DELAY",
        description="Initial retry delay in seconds (uses exponential backoff)",
    )

    azure_sql_enable_query_store: bool = Field(
        default=True,
        alias="AZURE_SQL_ENABLE_QUERY_STORE",
        description="Enable Query Store for performance monitoring",
    )
    azure_sql_query_store_max_size_mb: int = Field(
        default=100,
        alias="AZURE_SQL_QUERY_STORE_MAX_SIZE_MB",
        description="Max storage for Query Store data",
    )
    azure_sql_query_store_retention_days: int = Field(
        default=30,
        alias="AZURE_SQL_QUERY_STORE_RETENTION_DAYS",
        description="Days to retain Query Store data",
    )

    is_azure_functions: bool = Field(
        default=False,
        alias="AZURE_FUNCTIONS_ENVIRONMENT",
        description="True when running in Azure Functions",
    )

    @field_validator("is_azure_functions", mode="before")
    @classmethod
    def detect_azure_functions(cls, v: bool | None) -> bool:
        """Auto-detect Azure Functions environment."""
        if v:
            return True
        return any(
            [
                os.getenv("FUNCTIONS_WORKER_RUNTIME") is not None,
                os.getenv("FUNCTIONS_EXTENSION_VERSION") is not None,
                os.getenv("AZURE_FUNCTIONS_ENVIRONMENT") is not None,
            ]
        )

    bulk_batch_size: int = Field(default=1000, alias="BULK_BATCH_SIZE")
    sync_chunk_size: int = Field(default=1000, alias="SYNC_CHUNK_SIZE")
    enable_parallel_sync: bool = Field(default=True, alias="ENABLE_PARALLEL_SYNC")
    max_parallel_tenants: int = Field(default=5, alias="MAX_PARALLEL_TENANTS")

    enable_tracing: bool = Field(default=False, alias="ENABLE_TRACING")
    otel_exporter_endpoint: str | None = Field(default=None, alias="OTEL_EXPORTER_ENDPOINT")
    otel_exporter_headers: str | None = Field(default=None, alias="OTEL_EXPORTER_HEADERS")
