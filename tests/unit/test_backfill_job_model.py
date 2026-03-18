"""Unit tests for BackfillJob SQLAlchemy model.

Tests column definitions, defaults, properties, and status transitions
in app/models/backfill_job.py.

Traces: CO-001, CM-001, RM-001, IG-001 (backfill for all modules)
"""

from datetime import datetime
from enum import StrEnum
from unittest.mock import MagicMock

from app.models.backfill_job import BackfillJob, BackfillStatus

# ---------------------------------------------------------------------------
# BackfillStatus enum
# ---------------------------------------------------------------------------


class TestBackfillStatus:
    """Tests for BackfillStatus StrEnum."""

    def test_is_str_enum(self):
        assert issubclass(BackfillStatus, StrEnum)

    def test_member_count(self):
        assert len(BackfillStatus) == 6

    def test_values(self):
        assert BackfillStatus.PENDING == "pending"
        assert BackfillStatus.RUNNING == "running"
        assert BackfillStatus.PAUSED == "paused"
        assert BackfillStatus.COMPLETED == "completed"
        assert BackfillStatus.FAILED == "failed"
        assert BackfillStatus.CANCELLED == "cancelled"


# ---------------------------------------------------------------------------
# BackfillJob Model — Schema Tests
# ---------------------------------------------------------------------------


class TestBackfillJobModel:
    """Tests for BackfillJob SQLAlchemy model schema."""

    def test_tablename(self):
        assert BackfillJob.__tablename__ == "backfill_jobs"

    def test_has_expected_columns(self):
        col_names = {c.name for c in BackfillJob.__table__.columns}
        expected = {
            "id",
            "job_type",
            "tenant_id",
            "status",
            "start_date",
            "end_date",
            "current_date",
            "progress_percent",
            "records_processed",
            "records_inserted",
            "records_failed",
            "last_error",
            "error_count",
            "created_at",
            "started_at",
            "completed_at",
            "paused_at",
            "cancelled_at",
        }
        assert expected.issubset(col_names)

    def test_primary_key(self):
        pk_cols = [c.name for c in BackfillJob.__table__.primary_key.columns]
        assert pk_cols == ["id"]

    def test_nullable_columns(self):
        cols = {c.name: c.nullable for c in BackfillJob.__table__.columns}
        # Required fields
        assert cols["job_type"] is False
        assert cols["status"] is False
        assert cols["start_date"] is False
        assert cols["end_date"] is False
        # Optional fields
        assert cols["tenant_id"] is True
        assert cols["current_date"] is True
        assert cols["last_error"] is True

    def test_column_count(self):
        """Should have 18 columns."""
        assert len(BackfillJob.__table__.columns) == 18


# ---------------------------------------------------------------------------
# Properties — using MagicMock to avoid SQLAlchemy instrumentation
# ---------------------------------------------------------------------------


def _mock_job(status: str = "pending", **kwargs) -> MagicMock:
    """Create a mock BackfillJob with property access."""
    job = MagicMock(spec=BackfillJob)
    job.id = "test-001"
    job.job_type = "costs"
    job.tenant_id = "t-001"
    job.status = status
    job.started_at = kwargs.get("started_at")
    job.completed_at = kwargs.get("completed_at")
    job.paused_at = kwargs.get("paused_at")
    job.cancelled_at = kwargs.get("cancelled_at")

    # Wire up real property implementations
    job.is_pending = BackfillJob.is_pending.fget(job)
    job.is_running = BackfillJob.is_running.fget(job)
    job.is_paused = BackfillJob.is_paused.fget(job)
    job.is_completed = BackfillJob.is_completed.fget(job)
    job.is_failed = BackfillJob.is_failed.fget(job)
    job.is_cancelled = BackfillJob.is_cancelled.fget(job)
    job.is_terminal = BackfillJob.is_terminal.fget(job)
    job.can_resume = BackfillJob.can_resume.fget(job)
    job.can_cancel = BackfillJob.can_cancel.fget(job)
    job.duration_seconds = BackfillJob.duration_seconds.fget(job)

    return job


class TestBackfillJobProperties:
    """Tests for BackfillJob computed properties."""

    def test_is_pending(self):
        job = _mock_job("pending")
        assert job.is_pending is True
        assert job.is_running is False

    def test_is_running(self):
        job = _mock_job("running")
        assert job.is_running is True
        assert job.is_pending is False

    def test_is_paused(self):
        job = _mock_job("paused")
        assert job.is_paused is True

    def test_is_completed(self):
        job = _mock_job("completed")
        assert job.is_completed is True

    def test_is_failed(self):
        job = _mock_job("failed")
        assert job.is_failed is True

    def test_is_cancelled(self):
        job = _mock_job("cancelled")
        assert job.is_cancelled is True

    def test_is_terminal_completed(self):
        assert _mock_job("completed").is_terminal is True

    def test_is_terminal_failed(self):
        assert _mock_job("failed").is_terminal is True

    def test_is_terminal_cancelled(self):
        assert _mock_job("cancelled").is_terminal is True

    def test_is_not_terminal_running(self):
        assert _mock_job("running").is_terminal is False

    def test_can_resume_paused(self):
        assert _mock_job("paused").can_resume is True

    def test_can_resume_failed(self):
        assert _mock_job("failed").can_resume is True

    def test_cannot_resume_completed(self):
        assert _mock_job("completed").can_resume is False

    def test_can_cancel_pending(self):
        assert _mock_job("pending").can_cancel is True

    def test_can_cancel_running(self):
        assert _mock_job("running").can_cancel is True

    def test_can_cancel_paused(self):
        assert _mock_job("paused").can_cancel is True

    def test_cannot_cancel_completed(self):
        assert _mock_job("completed").can_cancel is False

    def test_duration_seconds_with_times(self):
        job = _mock_job(
            "completed",
            started_at=datetime(2024, 1, 1, 0, 0, 0),
            completed_at=datetime(2024, 1, 1, 1, 30, 0),
        )
        assert job.duration_seconds == 5400.0

    def test_duration_seconds_none_when_not_completed(self):
        job = _mock_job("running")
        assert job.duration_seconds is None


# ---------------------------------------------------------------------------
# __repr__
# ---------------------------------------------------------------------------


class TestBackfillJobRepr:
    """Tests for BackfillJob __repr__."""

    def test_repr_format(self):
        job = MagicMock(spec=BackfillJob)
        job.id = "test-001"
        job.job_type = "costs"
        job.status = "running"
        r = BackfillJob.__repr__(job)
        assert "BackfillJob" in r
        assert "test-001" in r
        assert "costs" in r
        assert "running" in r


# ---------------------------------------------------------------------------
# update_status
# ---------------------------------------------------------------------------


class TestBackfillJobUpdateStatus:
    """Tests for BackfillJob.update_status method."""

    def _make_mock_job(self) -> MagicMock:
        job = MagicMock(spec=BackfillJob)
        job.status = "pending"
        job.started_at = None
        job.completed_at = None
        job.paused_at = None
        job.cancelled_at = None
        return job

    def test_update_to_running_sets_started_at(self):
        job = self._make_mock_job()
        BackfillJob.update_status(job, BackfillStatus.RUNNING)
        assert job.status == "running"
        assert job.started_at is not None

    def test_update_to_running_preserves_started_at(self):
        job = self._make_mock_job()
        original_time = datetime(2024, 1, 1)
        job.started_at = original_time
        BackfillJob.update_status(job, BackfillStatus.RUNNING)
        assert job.started_at == original_time

    def test_update_to_completed_sets_completed_at(self):
        job = self._make_mock_job()
        BackfillJob.update_status(job, BackfillStatus.COMPLETED)
        assert job.status == "completed"
        assert job.completed_at is not None

    def test_update_to_paused_sets_paused_at(self):
        job = self._make_mock_job()
        BackfillJob.update_status(job, BackfillStatus.PAUSED)
        assert job.status == "paused"
        assert job.paused_at is not None

    def test_update_to_cancelled_sets_cancelled_at(self):
        job = self._make_mock_job()
        BackfillJob.update_status(job, BackfillStatus.CANCELLED)
        assert job.status == "cancelled"
        assert job.cancelled_at is not None
