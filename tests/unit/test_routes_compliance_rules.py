"""Unit tests for compliance rules CRUD routes (CM-002).

Tests all custom compliance rule endpoints with FastAPI TestClient:
- POST   /api/v1/compliance/rules        (create)
- GET    /api/v1/compliance/rules        (list)
- GET    /api/v1/compliance/rules/:id    (get by ID)
- PUT    /api/v1/compliance/rules/:id    (update)
- DELETE /api/v1/compliance/rules/:id    (delete)
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

_BASE = "/api/v1/compliance/rules"
_TENANT = "test-tenant-123"
_RULE_ID = "rule-abc-123"
_NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)


def _make_rule(**overrides) -> MagicMock:
    """Build a mock CustomComplianceRule with sensible defaults."""
    defaults = {
        "id": _RULE_ID,
        "tenant_id": _TENANT,
        "name": "Require encryption",
        "description": "All storage must use encryption",
        "category": "resource_property",
        "severity": "high",
        "rule_schema": {"type": "object", "properties": {"encrypted": {"const": True}}},
        "is_enabled": True,
        "created_by": "test@example.com",
        "created_at": _NOW,
        "updated_at": _NOW,
        "last_evaluated_at": None,
    }
    defaults.update(overrides)
    rule = MagicMock()
    for k, v in defaults.items():
        setattr(rule, k, v)
    rule.to_dict.return_value = defaults
    return rule


def _valid_create_body(**overrides) -> dict:
    """Return a valid POST body for rule creation."""
    body = {
        "tenant_id": _TENANT,
        "name": "Require encryption",
        "description": "All storage must use encryption",
        "category": "resource_property",
        "severity": "high",
        "rule_schema": {"type": "object", "properties": {"encrypted": {"const": True}}},
    }
    body.update(overrides)
    return body


# ============================================================================
# POST /api/v1/compliance/rules  (create)
# ============================================================================


class TestCreateRule:
    """Tests for POST /api/v1/compliance/rules."""

    @patch("app.api.routes.compliance_rules.CustomRuleService")
    def test_create_rule_success(self, mock_svc_cls, authed_client):
        """Successful creation returns 201 with rule data."""
        rule = _make_rule()
        mock_svc = MagicMock()
        mock_svc.create.return_value = (rule, [])
        mock_svc_cls.return_value = mock_svc

        response = authed_client.post(_BASE, json=_valid_create_body())

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == _RULE_ID
        assert data["name"] == "Require encryption"
        assert data["category"] == "resource_property"
        mock_svc.create.assert_called_once()

    @patch("app.api.routes.compliance_rules.CustomRuleService")
    def test_create_rule_validation_errors(self, mock_svc_cls, authed_client):
        """Service validation errors return 422."""
        mock_svc = MagicMock()
        mock_svc.create.return_value = (
            None,
            ["severity must be one of ['critical', 'high', 'low', 'medium']"],
        )
        mock_svc_cls.return_value = mock_svc

        response = authed_client.post(_BASE, json=_valid_create_body(severity="invalid"))

        assert response.status_code == 422
        assert "severity" in response.json()["detail"][0]

    def test_create_rule_missing_required_fields(self, authed_client):
        """Missing required fields return 422 from Pydantic validation."""
        # Omit 'name' which is required
        body = {"tenant_id": _TENANT, "category": "resource_property", "rule_schema": {}}
        response = authed_client.post(_BASE, json=body)
        assert response.status_code == 422

    def test_create_rule_requires_auth(self, client):
        """Unauthenticated request returns 401."""
        response = client.post(_BASE, json=_valid_create_body())
        assert response.status_code == 401


# ============================================================================
# GET /api/v1/compliance/rules  (list)
# ============================================================================


class TestListRules:
    """Tests for GET /api/v1/compliance/rules."""

    @patch("app.api.routes.compliance_rules.CustomRuleService")
    def test_list_rules_success(self, mock_svc_cls, authed_client):
        """Listing rules returns structured response with count."""
        rules = [_make_rule(id="r1"), _make_rule(id="r2")]
        mock_svc = MagicMock()
        mock_svc.list_rules.return_value = rules
        mock_svc_cls.return_value = mock_svc

        response = authed_client.get(f"{_BASE}?tenant_id={_TENANT}")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert data["tenant_id"] == _TENANT
        assert len(data["rules"]) == 2

    @patch("app.api.routes.compliance_rules.CustomRuleService")
    def test_list_rules_empty(self, mock_svc_cls, authed_client):
        """Empty tenant returns zero rules."""
        mock_svc = MagicMock()
        mock_svc.list_rules.return_value = []
        mock_svc_cls.return_value = mock_svc

        response = authed_client.get(f"{_BASE}?tenant_id={_TENANT}")

        assert response.status_code == 200
        assert response.json()["count"] == 0
        assert response.json()["rules"] == []

    def test_list_rules_requires_tenant_id(self, authed_client):
        """Missing tenant_id query param returns 422."""
        response = authed_client.get(_BASE)
        assert response.status_code == 422

    def test_list_rules_requires_auth(self, client):
        """Unauthenticated request returns 401."""
        response = client.get(f"{_BASE}?tenant_id={_TENANT}")
        assert response.status_code == 401


# ============================================================================
# GET /api/v1/compliance/rules/:id  (get by ID)
# ============================================================================


class TestGetRule:
    """Tests for GET /api/v1/compliance/rules/{rule_id}."""

    @patch("app.api.routes.compliance_rules.CustomRuleService")
    def test_get_rule_success(self, mock_svc_cls, authed_client):
        """Getting a rule by ID returns the rule data."""
        rule = _make_rule()
        mock_svc = MagicMock()
        mock_svc.get.return_value = rule
        mock_svc_cls.return_value = mock_svc

        response = authed_client.get(f"{_BASE}/{_RULE_ID}?tenant_id={_TENANT}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == _RULE_ID
        assert data["name"] == "Require encryption"
        mock_svc.get.assert_called_once_with(_RULE_ID, _TENANT)

    @patch("app.api.routes.compliance_rules.CustomRuleService")
    def test_get_rule_not_found(self, mock_svc_cls, authed_client):
        """Non-existent rule returns 404."""
        mock_svc = MagicMock()
        mock_svc.get.return_value = None
        mock_svc_cls.return_value = mock_svc

        response = authed_client.get(f"{_BASE}/nonexistent?tenant_id={_TENANT}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_rule_requires_auth(self, client):
        """Unauthenticated request returns 401."""
        response = client.get(f"{_BASE}/{_RULE_ID}?tenant_id={_TENANT}")
        assert response.status_code == 401


# ============================================================================
# PUT /api/v1/compliance/rules/:id  (update)
# ============================================================================


class TestUpdateRule:
    """Tests for PUT /api/v1/compliance/rules/{rule_id}."""

    @patch("app.api.routes.compliance_rules.CustomRuleService")
    def test_update_rule_success(self, mock_svc_cls, authed_client):
        """Successful update returns updated rule data."""
        updated = _make_rule(name="Updated name", severity="critical")
        mock_svc = MagicMock()
        mock_svc.update.return_value = (updated, [])
        mock_svc_cls.return_value = mock_svc

        body = {"name": "Updated name", "severity": "critical"}
        response = authed_client.put(f"{_BASE}/{_RULE_ID}?tenant_id={_TENANT}", json=body)

        assert response.status_code == 200
        mock_svc.update.assert_called_once()

    @patch("app.api.routes.compliance_rules.CustomRuleService")
    def test_update_rule_not_found(self, mock_svc_cls, authed_client):
        """Updating a non-existent rule returns 404."""
        mock_svc = MagicMock()
        mock_svc.update.return_value = (None, ["Rule not found or access denied"])
        mock_svc_cls.return_value = mock_svc

        body = {"name": "New name"}
        response = authed_client.put(f"{_BASE}/nonexistent?tenant_id={_TENANT}", json=body)

        assert response.status_code == 404

    @patch("app.api.routes.compliance_rules.CustomRuleService")
    def test_update_rule_validation_error(self, mock_svc_cls, authed_client):
        """Validation errors from service return 422."""
        mock_svc = MagicMock()
        mock_svc.update.return_value = (
            None,
            ["severity must be one of ['critical', 'high', 'low', 'medium']"],
        )
        mock_svc_cls.return_value = mock_svc

        body = {"severity": "invalid"}
        response = authed_client.put(f"{_BASE}/{_RULE_ID}?tenant_id={_TENANT}", json=body)

        assert response.status_code == 422
        assert "severity" in response.json()["detail"][0]

    def test_update_rule_requires_auth(self, client):
        """Unauthenticated request returns 401."""
        response = client.put(f"{_BASE}/{_RULE_ID}?tenant_id={_TENANT}", json={"name": "x"})
        assert response.status_code == 401


# ============================================================================
# DELETE /api/v1/compliance/rules/:id  (delete)
# ============================================================================


class TestDeleteRule:
    """Tests for DELETE /api/v1/compliance/rules/{rule_id}."""

    @patch("app.api.routes.compliance_rules.CustomRuleService")
    def test_delete_rule_success(self, mock_svc_cls, authed_client):
        """Successful deletion returns 204 with no content."""
        mock_svc = MagicMock()
        mock_svc.delete.return_value = True
        mock_svc_cls.return_value = mock_svc

        response = authed_client.delete(f"{_BASE}/{_RULE_ID}?tenant_id={_TENANT}")

        assert response.status_code == 204
        assert response.content == b""
        mock_svc.delete.assert_called_once_with(_RULE_ID, _TENANT)

    @patch("app.api.routes.compliance_rules.CustomRuleService")
    def test_delete_rule_not_found(self, mock_svc_cls, authed_client):
        """Deleting a non-existent rule returns 404."""
        mock_svc = MagicMock()
        mock_svc.delete.return_value = False
        mock_svc_cls.return_value = mock_svc

        response = authed_client.delete(f"{_BASE}/nonexistent?tenant_id={_TENANT}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_delete_rule_requires_auth(self, client):
        """Unauthenticated request returns 401."""
        response = client.delete(f"{_BASE}/{_RULE_ID}?tenant_id={_TENANT}")
        assert response.status_code == 401
