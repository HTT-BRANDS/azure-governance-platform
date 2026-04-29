"""Compatibility exports for the resumable backfill service.

The implementation is split into focused modules:
- ``backfill_core``: shared processor and batch-insert primitives
- ``backfill_processors``: cost, identity, compliance, and resource fetchers
- ``backfill_engine``: job lifecycle and resumable orchestration

Keep this module as the stable public import path for downstream callers.
"""

from app.services.backfill_core import (
    BackfillProcessor,
    BatchInserter,
    _log_http_error,
    _run_async,
)
from app.services.backfill_engine import BackfillService, ResumableBackfillService
from app.services.backfill_processors import (
    ComplianceDataProcessor,
    CostDataProcessor,
    IdentityDataProcessor,
    ResourcesDataProcessor,
    azure_client_manager,
)

__all__ = [
    "BackfillProcessor",
    "BackfillService",
    "BatchInserter",
    "ComplianceDataProcessor",
    "CostDataProcessor",
    "IdentityDataProcessor",
    "ResourcesDataProcessor",
    "ResumableBackfillService",
    "_log_http_error",
    "_run_async",
    "azure_client_manager",
]
