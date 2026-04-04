"""Tests for app/api/services/sync_service.py — sync operations.

Covers:
- trigger_sync: creates SyncJob with correct fields
- get_sync_status: returns SyncStatus
- get_sync_results: returns empty list, passes date filters

Phase B.11 of the test coverage sprint.
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from app.api.services.sync_service import SyncService
from app.schemas.sync import SyncJob, SyncStatus

# ---------------------------------------------------------------------------
# trigger_sync
# ---------------------------------------------------------------------------


class TestTriggerSync:
    @pytest.mark.asyncio
    async def test_returns_sync_job(self):
        svc = SyncService(MagicMock())

        job = await svc.trigger_sync("tid-1")

        assert isinstance(job, SyncJob)
        assert job.tenant_id == "tid-1"
        assert job.sync_type == "full"
        assert job.status == "pending"

    @pytest.mark.asyncio
    async def test_custom_sync_type(self):
        svc = SyncService(MagicMock())

        job = await svc.trigger_sync("tid-1", sync_type="incremental")

        assert job.sync_type == "incremental"

    @pytest.mark.asyncio
    async def test_generates_unique_job_ids(self):
        svc = SyncService(MagicMock())

        job1 = await svc.trigger_sync("tid-1")
        job2 = await svc.trigger_sync("tid-1")

        assert job1.job_id != job2.job_id

    @pytest.mark.asyncio
    async def test_sets_created_at(self):
        svc = SyncService(MagicMock())

        before = datetime.now(UTC)
        job = await svc.trigger_sync("tid-1")
        after = datetime.now(UTC)

        assert before <= job.created_at <= after

    @pytest.mark.asyncio
    async def test_started_at_is_none(self):
        svc = SyncService(MagicMock())

        job = await svc.trigger_sync("tid-1")

        assert job.started_at is None
        assert job.completed_at is None


# ---------------------------------------------------------------------------
# get_sync_status
# ---------------------------------------------------------------------------


class TestGetSyncStatus:
    @pytest.mark.asyncio
    async def test_returns_status(self):
        svc = SyncService(MagicMock())

        status = await svc.get_sync_status("job-123")

        assert isinstance(status, SyncStatus)
        assert status.job_id == "job-123"
        assert status.status == "running"

    @pytest.mark.asyncio
    async def test_has_progress_info(self):
        svc = SyncService(MagicMock())

        status = await svc.get_sync_status("job-456")

        assert 0 <= status.progress_percent <= 100
        assert isinstance(status.current_step, str)


# ---------------------------------------------------------------------------
# get_sync_results
# ---------------------------------------------------------------------------


class TestGetSyncResults:
    @pytest.mark.asyncio
    async def test_returns_list(self):
        svc = SyncService(MagicMock())

        results = await svc.get_sync_results("tid-1")

        assert isinstance(results, list)
        assert results == []

    @pytest.mark.asyncio
    async def test_accepts_date_filters(self):
        svc = SyncService(MagicMock())

        results = await svc.get_sync_results(
            "tid-1",
            start_date="2024-01-01",
            end_date="2024-06-01",
        )

        assert isinstance(results, list)
