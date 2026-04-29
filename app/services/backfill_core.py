"""Core primitives for resumable historical backfill jobs."""

import asyncio
import concurrent.futures
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import TypeVar

from azure.core.exceptions import HttpResponseError
from sqlalchemy.orm import Session

from app.core.database import bulk_insert_chunks

logger = logging.getLogger(__name__)

T = TypeVar("T")


def _run_async(coro):
    """Run an async coroutine synchronously for backfill compatibility."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result(timeout=300)
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


def _log_http_error(context: str, sub_id: str, error: HttpResponseError) -> None:
    """Log Azure HTTP errors with appropriate context."""
    if error.status_code == 403:
        logger.warning(f"{context}: access denied for subscription {sub_id}")
    else:
        logger.warning(
            f"{context}: HTTP {error.status_code} for subscription {sub_id}: {error.message}"
        )


class BatchInserter:
    """Optimized batch insert for SQLite (500 records)."""

    def __init__(self, db: Session, model_class: type[T], batch_size: int = 500) -> None:
        """Initialize batch inserter.

        Args:
            db: Database session
            model_class: SQLAlchemy model class to insert
            batch_size: Number of records per batch (default 500 for SQLite)
        """
        self.db = db
        self.model_class = model_class
        self.batch_size = batch_size
        self._buffer: list[dict] = []
        self._total_inserted = 0

    def add(self, record: dict) -> None:
        """Add a record to the batch buffer.

        Args:
            record: Dictionary of column values
        """
        self._buffer.append(record)
        if len(self._buffer) >= self.batch_size:
            self.flush()

    def add_many(self, records: list[dict]) -> None:
        """Add multiple records to the batch buffer.

        Args:
            records: List of record dictionaries
        """
        for record in records:
            self.add(record)

    def flush(self) -> int:
        """Insert current batch and clear buffer.

        Returns:
            Number of records inserted
        """
        if not self._buffer:
            return 0

        try:
            count = bulk_insert_chunks(
                self.db,
                self.model_class,
                self._buffer,
                batch_size=self.batch_size,
            )
            self._total_inserted += count
            inserted = len(self._buffer)
            self._buffer.clear()
            return inserted
        except Exception as e:
            logger.error(f"Batch insert failed: {e}")
            raise

    def commit(self) -> int:
        """Final commit - flush remaining records.

        Returns:
            Total number of records inserted
        """
        self.flush()
        return self._total_inserted

    @property
    def buffer_size(self) -> int:
        """Current number of records in buffer."""
        return len(self._buffer)

    @property
    def total_inserted(self) -> int:
        """Total number of records inserted so far."""
        return self._total_inserted


class BackfillProcessor(ABC):
    """Abstract base class for data type processors."""

    def __init__(self, db: Session, tenant_id: str) -> None:
        """Initialize processor.

        Args:
            db: Database session
            tenant_id: Tenant ID to process
        """
        self.db = db
        self.tenant_id = tenant_id

    @abstractmethod
    def fetch_data(self, date: datetime) -> list[dict]:
        """Fetch data for a specific date.

        Args:
            date: Date to fetch data for

        Returns:
            List of record dictionaries
        """
        pass

    @abstractmethod
    def get_model_class(self) -> type:
        """Get the SQLAlchemy model class for this processor."""
        pass

    def process_day(
        self,
        date: datetime,
        batch_inserter: BatchInserter,
    ) -> tuple[int, int]:
        """Process a single day of data.

        Args:
            date: Date to process
            batch_inserter: Batch inserter for records

        Returns:
            Tuple of (records fetched, records inserted)
        """
        try:
            records = self.fetch_data(date)
            fetched = len(records)

            if records:
                batch_inserter.add_many(records)

            return fetched, fetched
        except Exception as e:
            logger.error(f"Failed to process {date.date()}: {e}")
            raise
