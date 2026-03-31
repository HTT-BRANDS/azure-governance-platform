"""Azure SQL connection pool management and retry logic.

Provides cloud-native Azure SQL optimizations:
- Exponential backoff retry for transient faults
- Pool statistics and monitoring
- Azure Functions serverless support
- Failover detection and handling

References:
- https://docs.microsoft.com/en-us/azure/azure-sql/database/troubleshoot-common-connectivity-issues
- https://docs.microsoft.com/en-us/azure/azure-sql/database/quota-increase-request
"""

import logging
import random
import time
from collections.abc import Callable
from functools import wraps
from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool, QueuePool

from app.core.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# Azure SQL transient fault codes that warrant retry
AZURE_SQL_TRANSIENT_ERRORS = frozenset(
    {
        # Connection errors
        "08S01",  # Communication link failure
        "08001",  # Unable to connect
        "08002",  # Connection in use
        "08003",  # Connection does not exist
        "08004",  # Server rejected connection
        "08007",  # Connection failure during transaction
        # Deadlock and resource errors
        "40001",  # Deadlock victim
        "40020",  # Deadlock
        "40143",  # Service is too busy
        "40197",  # Service encountered an error
        "40501",  # Service is busy
        # Throttling errors
        "40613",  # Database is not currently available (failover)
        "49918",  # Cannot process request (insufficient resources)
        "49919",  # Cannot process create or update request
        "49920",  # Too many operations in progress
    }
)


def is_azure_sql() -> bool:
    """Check if connected to Azure SQL."""
    return (
        "database.windows.net" in settings.database_url or "mssql" in settings.database_url
    ) and not settings.database_url.startswith("sqlite")


def get_azure_sql_engine_args(base_args: dict[str, Any]) -> dict[str, Any]:
    """Get engine arguments optimized for Azure SQL.

    Args:
        base_args: Base engine arguments to extend

    Returns:
        Engine arguments with Azure SQL optimizations
    """
    if not is_azure_sql():
        return base_args

    # Azure Functions: Use NullPool to avoid connection issues in serverless
    if settings.is_azure_functions or settings.azure_sql_use_null_pool:
        base_args["poolclass"] = NullPool
        logger.info("Using NullPool for Azure Functions/serverless environment")
        return base_args

    # Standard Azure SQL: Use QueuePool with optimized settings
    base_args.update(
        {
            "poolclass": QueuePool,
            "pool_size": settings.azure_sql_pool_size,
            "max_overflow": settings.azure_sql_max_overflow,
            "pool_timeout": settings.azure_sql_pool_timeout,
            "pool_pre_ping": settings.azure_sql_pool_pre_ping,
            "pool_recycle": settings.azure_sql_pool_recycle,
        }
    )

    return base_args


def is_transient_error(error: Exception) -> bool:
    """Check if an exception is a transient Azure SQL fault.

    Args:
        error: The exception to check

    Returns:
        True if the error is transient and should be retried
    """
    error_str = str(error).upper()

    # Check SQL error codes
    is_transient = any(
        code in error_str or code in str(getattr(error, "args", []))
        for code in AZURE_SQL_TRANSIENT_ERRORS
    )

    # Also check for common Azure SQL error patterns
    if not is_transient:
        is_transient = any(
            pattern in error_str
            for pattern in [
                "TRANSIENT ERROR",
                "SERVICE IS BUSY",
                "DEADLOCK",
                "TIMEOUT",
                "COMMUNICATION LINK FAILURE",
                "DATABASE IS NOT CURRENTLY AVAILABLE",
            ]
        )

    return is_transient


def with_azure_sql_retry(
    max_attempts: int | None = None,
    base_delay: float | None = None,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
) -> Callable:
    """Decorator for Azure SQL transient fault retry logic.

    Implements exponential backoff with jitter for Azure SQL transient faults.

    Args:
        max_attempts: Max retry attempts (default: AZURE_SQL_CONNECTION_RETRY_ATTEMPTS)
        base_delay: Initial delay in seconds (default: AZURE_SQL_CONNECTION_RETRY_DELAY)
        max_delay: Maximum delay between retries
        exponential_base: Base for exponential backoff calculation
        jitter: Add random jitter to prevent thundering herd

    Example:
        @with_azure_sql_retry(max_attempts=5)
        def get_expensive_data(db: Session):
            return db.query(Model).all()
    """
    attempts = max_attempts or settings.azure_sql_connection_retry_attempts
    delay = base_delay or settings.azure_sql_connection_retry_delay

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    if not is_transient_error(e) or attempt == attempts - 1:
                        raise

                    # Calculate backoff with exponential increase
                    current_delay = min(delay * (exponential_base**attempt), max_delay)

                    if jitter:
                        # Add 0-25% jitter
                        current_delay *= 1 + random.random() * 0.25

                    logger.warning(
                        f"Azure SQL transient error on attempt {attempt + 1}/{attempts}: {e}. "
                        f"Retrying in {current_delay:.2f}s..."
                    )
                    time.sleep(current_delay)

            raise last_exception

        return wrapper

    return decorator


def get_pool_stats(engine_instance: Any | None = None) -> dict[str, Any]:
    """Get connection pool statistics for Azure SQL monitoring.

    Returns pool metrics including:
    - Pool size and overflow
    - Checked-in and checked-out connections
    - For Azure SQL: helps identify connection exhaustion

    Args:
        engine_instance: SQLAlchemy engine instance (optional)

    Returns:
        Dict with pool statistics or empty dict if using NullPool
    """
    if engine_instance is None:
        return {"error": "Engine not initialized"}

    pool = engine_instance.pool

    # NullPool doesn't track these metrics
    if isinstance(pool, NullPool):
        return {
            "pool_type": "NullPool",
            "note": "Serverless mode - no connection pooling",
        }

    return {
        "pool_type": "QueuePool",
        "size": pool.size(),  # Current pool size
        "checked_in": pool.checkedin(),  # Available connections
        "checked_out": pool.checkedout(),  # In-use connections
        "overflow": pool.overflow(),  # Overflow connections
        "max_overflow": settings.azure_sql_max_overflow,
        "pool_size": settings.azure_sql_pool_size,
        "utilization_percent": ((pool.checkedout() / (pool.size() or 1)) * 100),
    }


def reset_pool(engine_instance: Any) -> None:
    """Reset the connection pool (useful after Azure SQL failover).

    This disposes of all connections and recreates the pool,
    ensuring fresh connections after a geo-failover event.

    Args:
        engine_instance: SQLAlchemy engine instance
    """
    if engine_instance is not None:
        logger.info("Resetting Azure SQL connection pool after potential failover")
        engine_instance.dispose()


class AzureSQLRetryContext:
    """Context manager for database sessions with Azure SQL retry logic.

    Use this for operations that might hit transient Azure SQL faults.

    Example:
        with AzureSQLRetryContext() as db:
            return db.query(Model).all()
    """

    def __init__(
        self,
        session_factory: Callable[[], Session],
        max_attempts: int | None = None,
        base_delay: float | None = None,
    ):
        self.session_factory = session_factory
        self.max_attempts = max_attempts or settings.azure_sql_connection_retry_attempts
        self.base_delay = base_delay or settings.azure_sql_connection_retry_delay
        self.db: Session | None = None
        self.last_exception: Exception | None = None

    def __enter__(self) -> Session:
        for attempt in range(self.max_attempts):
            self.db = self.session_factory()
            try:
                return self.db
            except Exception as e:
                if self.db:
                    self.db.rollback()
                    self.db.close()

                self.last_exception = e

                if not is_transient_error(e) or attempt == self.max_attempts - 1:
                    raise

                current_delay = min(self.base_delay * (2.0**attempt), 60.0)
                logger.warning(
                    f"Azure SQL transient error on session attempt {attempt + 1}/{self.max_attempts}: {e}. "
                    f"Retrying in {current_delay:.2f}s..."
                )
                time.sleep(current_delay)

        if self.last_exception:
            raise self.last_exception

        raise RuntimeError("Failed to create database session")

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.db:
            if exc_type:
                self.db.rollback()
            else:
                self.db.commit()
            self.db.close()
