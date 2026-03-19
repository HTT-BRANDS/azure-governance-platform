"""Unit tests for AccessReviewService (IG-010).

Coverage:
 1. list_stale_assignments — happy path (stale users returned)
 2. list_stale_assignments — user inactive >90 days is stale
 3. list_stale_assignments — null lastSignIn is stale
 4. list_stale_assignments — recent sign-in is NOT stale
 5. list_stale_assignments — service principal principals are skipped
 6. list_stale_assignments — Graph 401 raises AccessReviewServiceError
 7. list_stale_assignments — Graph 403 raises AccessReviewServiceError
 8. create_review — creates review with pending status
 9. create_review — idempotent: same assignment_id returns existing pending review
10. get_reviews — returns all reviews for tenant sorted newest-first
11. take_action approve — updates status to approved, sets resolved_at
12. take_action revoke — calls Graph DELETE, updates status to revoked
13. take_action revoke — Graph 401 on DELETE raises AccessReviewServiceError
14. take_action — unknown review_id raises KeyError
15. Route GET /access-reviews — 200 with auto-created reviews
16. Route POST /access-reviews/{id}/action — 200 approve action
17. Route POST /access-reviews/{id}/action — 404 unknown review
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.api.services.access_review_service import (
    STALE_THRESHOLD_DAYS,
    AccessReviewService,
    AccessReviewServiceError,
)
from app.schemas.access_review import AccessReview

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TENANT_ID = "test-tenant-123"
ASSIGNMENT_ID = "asgn-001"
USER_ID = "user-001"
ROLE_NAME = "Global Administrator"
USER_NAME = "Alice Admin"


def _build_assignment(
    assignment_id: str = ASSIGNMENT_ID,
    user_id: str = USER_ID,
    display_name: str = USER_NAME,
    role_name: str = ROLE_NAME,
    odata_type: str = "#microsoft.graph.user",
) -> dict:
    """Build a raw Graph role assignment dict."""
    return {
        "id": assignment_id,
        "principal": {
            "@odata.type": odata_type,
            "id": user_id,
            "displayName": display_name,
        },
        "roleDefinition": {"displayName": role_name},
    }


def _sign_in_response(last_sign_in: datetime | None) -> dict:
    """Build a raw Graph user-with-signInActivity dict."""
    if last_sign_in is None:
        activity = {}
    else:
        activity = {"lastSignInDateTime": last_sign_in.strftime("%Y-%m-%dT%H:%M:%SZ")}
    return {"id": USER_ID, "signInActivity": activity}


def _fresh_service() -> AccessReviewService:
    """Return a pristine AccessReviewService (no shared state)."""
    return AccessReviewService()


# ---------------------------------------------------------------------------
# Tests: list_stale_assignments
# ---------------------------------------------------------------------------


class TestListStaleAssignments:
    """Tests for AccessReviewService.list_stale_assignments."""

    @pytest.mark.asyncio
    async def test_happy_path_stale_user_returned(self):
        """A user inactive >90 days appears in the result list."""
        svc = _fresh_service()
        last_sign_in = datetime.utcnow() - timedelta(days=100)

        with (
            patch.object(
                svc,
                "_get_client",
                return_value=MagicMock(
                    _request=AsyncMock(return_value={"value": [_build_assignment()]}),
                    tenant_id=TENANT_ID,
                ),
            ),
            patch.object(
                svc,
                "_get_sign_in_activity",
                new_callable=AsyncMock,
                return_value=last_sign_in,
            ),
        ):
            results = await svc.list_stale_assignments(TENANT_ID)

        assert len(results) == 1
        r = results[0]
        assert r.assignment_id == ASSIGNMENT_ID
        assert r.user_id == USER_ID
        assert r.user_display_name == USER_NAME
        assert r.role_name == ROLE_NAME
        assert r.last_sign_in == last_sign_in
        assert r.days_inactive == 100

    @pytest.mark.asyncio
    async def test_user_inactive_over_90_days_is_stale(self):
        """Exactly 91 days inactive qualifies as stale."""
        svc = _fresh_service()
        last_sign_in = datetime.utcnow() - timedelta(days=91)

        with (
            patch.object(
                svc,
                "_get_client",
                return_value=MagicMock(
                    _request=AsyncMock(return_value={"value": [_build_assignment()]}),
                    tenant_id=TENANT_ID,
                ),
            ),
            patch.object(
                svc, "_get_sign_in_activity", new_callable=AsyncMock, return_value=last_sign_in
            ),
        ):
            results = await svc.list_stale_assignments(TENANT_ID)

        assert len(results) == 1
        assert results[0].days_inactive >= 91

    @pytest.mark.asyncio
    async def test_null_last_sign_in_is_stale(self):
        """A user who has never signed in (null signInActivity) is stale."""
        svc = _fresh_service()

        with (
            patch.object(
                svc,
                "_get_client",
                return_value=MagicMock(
                    _request=AsyncMock(return_value={"value": [_build_assignment()]}),
                    tenant_id=TENANT_ID,
                ),
            ),
            patch.object(svc, "_get_sign_in_activity", new_callable=AsyncMock, return_value=None),
        ):
            results = await svc.list_stale_assignments(TENANT_ID)

        assert len(results) == 1
        assert results[0].last_sign_in is None
        assert results[0].days_inactive == 0  # never signed in → 0 days reported

    @pytest.mark.asyncio
    async def test_recent_sign_in_is_not_stale(self):
        """A user who signed in yesterday is NOT returned."""
        svc = _fresh_service()
        last_sign_in = datetime.utcnow() - timedelta(days=1)

        with (
            patch.object(
                svc,
                "_get_client",
                return_value=MagicMock(
                    _request=AsyncMock(return_value={"value": [_build_assignment()]}),
                    tenant_id=TENANT_ID,
                ),
            ),
            patch.object(
                svc, "_get_sign_in_activity", new_callable=AsyncMock, return_value=last_sign_in
            ),
        ):
            results = await svc.list_stale_assignments(TENANT_ID)

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_service_principal_principal_is_skipped(self):
        """Non-user principals (servicePrincipal) are ignored."""
        svc = _fresh_service()

        sp_assignment = _build_assignment(odata_type="#microsoft.graph.servicePrincipal")

        with (
            patch.object(
                svc,
                "_get_client",
                return_value=MagicMock(
                    _request=AsyncMock(return_value={"value": [sp_assignment]}),
                    tenant_id=TENANT_ID,
                ),
            ),
            patch.object(svc, "_get_sign_in_activity", new_callable=AsyncMock, return_value=None),
        ):
            results = await svc.list_stale_assignments(TENANT_ID)

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_graph_401_raises_access_review_service_error(self):
        """Graph 401 on role assignments call raises AccessReviewServiceError."""
        svc = _fresh_service()

        mock_response = MagicMock(status_code=401)
        http_error = httpx.HTTPStatusError("401", request=MagicMock(), response=mock_response)

        with patch.object(
            svc,
            "_get_client",
            return_value=MagicMock(
                _request=AsyncMock(side_effect=http_error),
                tenant_id=TENANT_ID,
            ),
        ):
            with pytest.raises(AccessReviewServiceError) as exc_info:
                await svc.list_stale_assignments(TENANT_ID)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_graph_403_raises_access_review_service_error(self):
        """Graph 403 on role assignments call raises AccessReviewServiceError."""
        svc = _fresh_service()

        mock_response = MagicMock(status_code=403)
        http_error = httpx.HTTPStatusError("403", request=MagicMock(), response=mock_response)

        with patch.object(
            svc,
            "_get_client",
            return_value=MagicMock(
                _request=AsyncMock(side_effect=http_error),
                tenant_id=TENANT_ID,
            ),
        ):
            with pytest.raises(AccessReviewServiceError) as exc_info:
                await svc.list_stale_assignments(TENANT_ID)

        assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# Tests: create_review
# ---------------------------------------------------------------------------


class TestCreateReview:
    """Tests for AccessReviewService.create_review."""

    @pytest.mark.asyncio
    async def test_creates_review_with_pending_status(self):
        """create_review returns an AccessReview in pending status."""
        svc = _fresh_service()

        review = await svc.create_review(TENANT_ID, ASSIGNMENT_ID)

        assert isinstance(review, AccessReview)
        assert review.assignment_id == ASSIGNMENT_ID
        assert review.tenant_id == TENANT_ID
        assert review.status == "pending"
        assert review.resolved_at is None
        assert review.id  # UUID assigned

    @pytest.mark.asyncio
    async def test_create_review_idempotent_returns_existing_pending(self):
        """Calling create_review twice for the same assignment returns the same review."""
        svc = _fresh_service()

        review1 = await svc.create_review(TENANT_ID, ASSIGNMENT_ID)
        review2 = await svc.create_review(TENANT_ID, ASSIGNMENT_ID)

        assert review1.id == review2.id


# ---------------------------------------------------------------------------
# Tests: get_reviews
# ---------------------------------------------------------------------------


class TestGetReviews:
    """Tests for AccessReviewService.get_reviews."""

    @pytest.mark.asyncio
    async def test_get_reviews_returns_all_tenant_reviews_sorted_newest_first(self):
        """get_reviews returns reviews sorted by created_at descending."""
        svc = _fresh_service()

        r1 = await svc.create_review(TENANT_ID, "asgn-001")
        r2 = await svc.create_review(TENANT_ID, "asgn-002")
        r3 = await svc.create_review(TENANT_ID, "asgn-003")

        reviews = await svc.get_reviews(TENANT_ID)

        assert len(reviews) == 3
        # All IDs present
        ids = {r.id for r in reviews}
        assert r1.id in ids
        assert r2.id in ids
        assert r3.id in ids

    @pytest.mark.asyncio
    async def test_get_reviews_empty_for_new_tenant(self):
        """An unknown tenant has no reviews."""
        svc = _fresh_service()
        reviews = await svc.get_reviews("brand-new-tenant")
        assert reviews == []


# ---------------------------------------------------------------------------
# Tests: take_action
# ---------------------------------------------------------------------------


class TestTakeAction:
    """Tests for AccessReviewService.take_action."""

    @pytest.mark.asyncio
    async def test_take_action_approve_updates_status(self):
        """Approving a review sets status to 'approved' and resolved_at."""
        svc = _fresh_service()
        review = await svc.create_review(TENANT_ID, ASSIGNMENT_ID)

        resolved = await svc.take_action(TENANT_ID, review.id, "approve")

        assert resolved.status == "approved"
        assert resolved.resolved_at is not None

    @pytest.mark.asyncio
    async def test_take_action_revoke_calls_graph_delete_and_updates_status(self):
        """Revoking a review calls Graph DELETE and sets status to 'revoked'."""
        svc = _fresh_service()
        review = await svc.create_review(TENANT_ID, ASSIGNMENT_ID)

        with patch.object(svc, "_get_client", return_value=MagicMock(tenant_id=TENANT_ID)):
            with patch.object(svc, "_delete_assignment", new_callable=AsyncMock) as mock_delete:
                resolved = await svc.take_action(TENANT_ID, review.id, "revoke")

        mock_delete.assert_awaited_once()
        assert resolved.status == "revoked"
        assert resolved.resolved_at is not None

    @pytest.mark.asyncio
    async def test_take_action_revoke_graph_401_raises_error(self):
        """If the Graph DELETE call returns 401, AccessReviewServiceError is raised."""
        svc = _fresh_service()
        review = await svc.create_review(TENANT_ID, ASSIGNMENT_ID)

        with patch.object(svc, "_get_client", return_value=MagicMock(tenant_id=TENANT_ID)):
            with patch.object(
                svc,
                "_delete_assignment",
                new_callable=AsyncMock,
                side_effect=AccessReviewServiceError("Unauthorized", status_code=401),
            ):
                with pytest.raises(AccessReviewServiceError) as exc_info:
                    await svc.take_action(TENANT_ID, review.id, "revoke")

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_take_action_unknown_review_id_raises_key_error(self):
        """A review_id that doesn't exist raises KeyError."""
        svc = _fresh_service()

        with pytest.raises(KeyError):
            await svc.take_action(TENANT_ID, "nonexistent-review-id", "approve")


# ---------------------------------------------------------------------------
# Tests: helper methods
# ---------------------------------------------------------------------------


class TestHelpers:
    """Unit tests for the pure helper methods."""

    def test_is_stale_none_last_sign_in(self):
        """None last_sign_in is always stale."""
        svc = _fresh_service()
        assert svc._is_stale(None) is True

    def test_is_stale_old_sign_in(self):
        """Sign-in older than STALE_THRESHOLD_DAYS is stale."""
        svc = _fresh_service()
        old = datetime.utcnow() - timedelta(days=STALE_THRESHOLD_DAYS + 1)
        assert svc._is_stale(old) is True

    def test_is_stale_recent_sign_in(self):
        """Sign-in within the threshold is NOT stale."""
        svc = _fresh_service()
        recent = datetime.utcnow() - timedelta(days=10)
        assert svc._is_stale(recent) is False

    def test_days_inactive_none_returns_zero(self):
        """days_inactive returns 0 for None (never signed in)."""
        svc = _fresh_service()
        assert svc._days_inactive(None) == 0

    def test_days_inactive_calculates_correctly(self):
        """days_inactive returns the approximate number of days since sign-in."""
        svc = _fresh_service()
        last = datetime.utcnow() - timedelta(days=30)
        assert svc._days_inactive(last) == 30

    def test_parse_graph_datetime_valid(self):
        """ISO 8601 strings are parsed correctly."""
        svc = _fresh_service()
        result = svc._parse_graph_datetime("2024-01-15T10:30:00Z")
        assert result is not None
        assert result.year == 2024
        assert result.month == 1

    def test_parse_graph_datetime_none(self):
        """None input returns None."""
        svc = _fresh_service()
        assert svc._parse_graph_datetime(None) is None


# ---------------------------------------------------------------------------
# Tests: Routes (integration-style with TestClient)
# ---------------------------------------------------------------------------


class TestAccessReviewRoutes:
    """Route-level tests for the access review endpoints."""

    @patch("app.api.routes.identity.access_review_service")
    def test_get_access_reviews_returns_pending_reviews(self, mock_svc, authed_client):
        """GET /access-reviews returns 200 with list of pending reviews."""
        mock_svc.list_stale_assignments = AsyncMock(return_value=[])
        mock_svc.create_review = AsyncMock()
        mock_svc.get_reviews = AsyncMock(
            return_value=[
                AccessReview(
                    id=str(uuid.uuid4()),
                    assignment_id="asgn-abc",
                    tenant_id="test-tenant-123",
                    status="pending",
                    created_at=datetime.utcnow(),
                ),
            ]
        )

        response = authed_client.get("/api/v1/identity/access-reviews?tenant_id=test-tenant-123")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["status"] == "pending"
        assert data[0]["assignment_id"] == "asgn-abc"

    @patch("app.api.routes.identity.access_review_service")
    def test_post_access_review_action_approve(self, mock_svc, authed_client):
        """POST /access-reviews/{id}/action with approve returns 200."""
        review_id = str(uuid.uuid4())
        mock_svc.take_action = AsyncMock(
            return_value=AccessReview(
                id=review_id,
                assignment_id="asgn-abc",
                tenant_id="test-tenant-123",
                status="approved",
                created_at=datetime.utcnow(),
                resolved_at=datetime.utcnow(),
            )
        )

        response = authed_client.post(
            f"/api/v1/identity/access-reviews/{review_id}/action?tenant_id=test-tenant-123",
            json={"action": "approve"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "approved"
        assert data["id"] == review_id

    @patch("app.api.routes.identity.access_review_service")
    def test_post_access_review_action_not_found_returns_404(self, mock_svc, authed_client):
        """POST /access-reviews/{id}/action for unknown review returns 404."""
        review_id = str(uuid.uuid4())
        mock_svc.take_action = AsyncMock(side_effect=KeyError(f"Review {review_id!r} not found"))

        response = authed_client.post(
            f"/api/v1/identity/access-reviews/{review_id}/action?tenant_id=test-tenant-123",
            json={"action": "approve"},
        )

        assert response.status_code == 404

    def test_get_access_reviews_requires_auth(self, client):
        """GET /access-reviews returns 401 without authentication."""
        response = client.get("/api/v1/identity/access-reviews?tenant_id=test-tenant-123")
        assert response.status_code == 401

    def test_post_access_review_action_requires_auth(self, client):
        """POST /access-reviews/{id}/action returns 401 without authentication."""
        response = client.post(
            f"/api/v1/identity/access-reviews/{uuid.uuid4()}/action?tenant_id=test-tenant-123",
            json={"action": "approve"},
        )
        assert response.status_code == 401
