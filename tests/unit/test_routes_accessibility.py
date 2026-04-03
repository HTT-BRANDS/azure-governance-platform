"""Unit tests for accessibility API routes.

Tests all accessibility endpoints with FastAPI TestClient:
- GET /api/v1/accessibility/touch-targets
- GET /api/v1/accessibility/wcag-checklist
"""


# ============================================================================
# GET /api/v1/accessibility/touch-targets Tests
# ============================================================================


class TestTouchTargetsEndpoint:
    """Tests for GET /api/v1/accessibility/touch-targets endpoint."""

    def test_get_touch_targets_returns_200(self, client):
        """Touch targets endpoint returns 200 OK."""
        response = client.get("/api/v1/accessibility/touch-targets")
        assert response.status_code == 200

    def test_get_touch_targets_report_shape(self, client):
        """Touch targets response matches TouchTargetReport schema."""
        response = client.get("/api/v1/accessibility/touch-targets")
        data = response.json()

        assert "compliant" in data
        assert "total_elements" in data
        assert "violations" in data
        assert "score" in data

        assert isinstance(data["compliant"], bool)
        assert isinstance(data["total_elements"], int)
        assert isinstance(data["violations"], list)
        assert isinstance(data["score"], int | float)

    def test_get_touch_targets_score_in_valid_range(self, client):
        """Touch targets score is between 0 and 100."""
        response = client.get("/api/v1/accessibility/touch-targets")
        data = response.json()

        assert 0 <= data["score"] <= 100

    def test_get_touch_targets_compliant_when_no_violations(self, client):
        """Report shows compliant=True when violations list is empty."""
        response = client.get("/api/v1/accessibility/touch-targets")
        data = response.json()

        if len(data["violations"]) == 0:
            assert data["compliant"] is True


# ============================================================================
# GET /api/v1/accessibility/wcag-checklist Tests
# ============================================================================


class TestWcagChecklistEndpoint:
    """Tests for GET /api/v1/accessibility/wcag-checklist endpoint."""

    def test_get_wcag_checklist_returns_200(self, client):
        """WCAG checklist endpoint returns 200 OK."""
        response = client.get("/api/v1/accessibility/wcag-checklist")
        assert response.status_code == 200

    def test_get_wcag_checklist_structure(self, client):
        """WCAG checklist response has expected top-level fields."""
        response = client.get("/api/v1/accessibility/wcag-checklist")
        data = response.json()

        assert "version" in data
        assert "last_updated" in data
        assert "categories" in data
        assert isinstance(data["categories"], list)
        assert len(data["categories"]) > 0

    def test_get_wcag_checklist_category_shape(self, client):
        """Each WCAG checklist category has required fields."""
        response = client.get("/api/v1/accessibility/wcag-checklist")
        categories = response.json()["categories"]

        for category in categories:
            assert "id" in category
            assert "name" in category
            assert "criteria" in category
            assert "tests" in category
            assert isinstance(category["criteria"], list)
            assert isinstance(category["tests"], list)
            assert len(category["tests"]) > 0

    def test_get_wcag_checklist_contains_expected_categories(self, client):
        """WCAG checklist includes key accessibility categories."""
        response = client.get("/api/v1/accessibility/wcag-checklist")
        categories = response.json()["categories"]

        category_ids = [c["id"] for c in categories]
        assert "keyboard" in category_ids
        assert "screen-reader" in category_ids
        assert "contrast" in category_ids
        assert "touch-targets" in category_ids

    def test_get_wcag_checklist_version_is_wcag_22(self, client):
        """WCAG checklist reports WCAG 2.2 AA version."""
        response = client.get("/api/v1/accessibility/wcag-checklist")
        data = response.json()

        assert "2.2" in data["version"]
