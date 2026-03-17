"""Unit tests for tenant data synchronization utilities.

Tests the sync coordination logic in app/core/sync/tenant_sync.py.

Traces: RM-003 — Tenant data sync triggering and scheduler integration.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.core.sync.tenant_sync import sync_tenant_data


class TestSyncTenantData:
    """Tests for sync_tenant_data function."""

    @pytest.mark.asyncio
    async def test_queues_sync_job_when_scheduler_available(self):
        """Should queue a sync job when the scheduler is available."""
        mock_scheduler = MagicMock()

        with patch("app.core.scheduler.get_scheduler", return_value=mock_scheduler):
            await sync_tenant_data("tenant-123")

        mock_scheduler.add_job.assert_called_once()
        call_kwargs = mock_scheduler.add_job.call_args
        assert call_kwargs[1]["id"] == "sync-tenant-tenant-123"
        assert call_kwargs[1]["trigger"] == "date"
        assert call_kwargs[1]["replace_existing"] is True

    @pytest.mark.asyncio
    async def test_no_error_when_scheduler_none(self):
        """Should not raise when scheduler is None."""
        with patch("app.core.scheduler.get_scheduler", return_value=None):
            # Should not raise
            await sync_tenant_data("tenant-456")

    @pytest.mark.asyncio
    async def test_job_id_includes_tenant_id(self):
        """Job ID should contain the tenant ID for uniqueness."""
        mock_scheduler = MagicMock()

        with patch("app.core.scheduler.get_scheduler", return_value=mock_scheduler):
            await sync_tenant_data("abc-def")

        job_id = mock_scheduler.add_job.call_args[1]["id"]
        assert "abc-def" in job_id

    @pytest.mark.asyncio
    async def test_replace_existing_true(self):
        """Should replace existing job to avoid duplicates."""
        mock_scheduler = MagicMock()

        with patch("app.core.scheduler.get_scheduler", return_value=mock_scheduler):
            await sync_tenant_data("t-1")

        assert mock_scheduler.add_job.call_args[1]["replace_existing"] is True
