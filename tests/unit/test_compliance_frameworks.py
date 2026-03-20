"""Unit tests for compliance frameworks service and routes — CM-003.

Covers:
- YAML loading and validation
- ComplianceFrameworksService methods
- GET /api/v1/compliance/frameworks route
- GET /api/v1/compliance/frameworks/{id} route
- GET /api/v1/compliance/frameworks/{id}/controls/{ctrl} route
- Authentication enforcement
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_REAL_YAML_PATH = Path("config/compliance_frameworks.yaml")


def _make_service(yaml_path: Path | None = None):
    """Return a ComplianceFrameworksService loaded from the real (or a custom) YAML."""
    from app.api.services.compliance_frameworks_service import ComplianceFrameworksService

    return ComplianceFrameworksService(yaml_path=yaml_path or _REAL_YAML_PATH)


def _mock_service() -> MagicMock:
    """Return a MagicMock that quacks like ComplianceFrameworksService."""
    from app.api.services.compliance_frameworks_service import ComplianceFrameworksService

    mock = MagicMock(spec=ComplianceFrameworksService)
    mock.get_all_frameworks.return_value = [
        {
            "id": "SOC2_2017",
            "name": "SOC 2 Trust Services Criteria",
            "version": "2017 (Revised Points of Focus 2022)",
            "authority": "AICPA",
            "control_count": 36,
        },
        {
            "id": "NIST_CSF_2.0",
            "name": "NIST Cybersecurity Framework",
            "version": "2.0",
            "authority": "NIST",
            "control_count": 106,
        },
    ]
    mock.get_framework.side_effect = lambda fw_id: (
        {
            "id": fw_id,
            "name": "SOC 2 Trust Services Criteria",
            "version": "2017",
            "authority": "AICPA",
            "controls": {"CC6.1": {"name": "Logical Access Security Software"}},
            "control_count": 1,
        }
        if fw_id == "SOC2_2017"
        else (_ for _ in ()).throw(KeyError(f"Framework '{fw_id}' not found"))
    )
    mock.get_control.return_value = {
        "id": "CC6.1",
        "framework_id": "SOC2_2017",
        "name": "Logical Access Security Software",
        "series": "CC6",
    }
    return mock


# ---------------------------------------------------------------------------
# 1. YAML loading
# ---------------------------------------------------------------------------


class TestYamlLoading:
    """Tests that the YAML file loads correctly with the expected structure."""

    def test_yaml_loads_successfully(self):
        """config/compliance_frameworks.yaml loads without errors."""
        svc = _make_service()
        assert svc is not None

    def test_yaml_has_frameworks_root_key(self):
        """Loaded YAML has a 'frameworks' root key."""
        svc = _make_service()
        # _frameworks is populated from YAML
        assert len(svc._frameworks) > 0

    def test_yaml_size_guard_raises_for_oversized_file(self, tmp_path):
        """ValueError is raised when YAML exceeds 512 KB."""
        from app.api.services.compliance_frameworks_service import _load_frameworks_yaml

        # Create a large but syntactically valid YAML file
        big_yaml = tmp_path / "big.yaml"
        # Write > 512_000 bytes of valid YAML
        lines = ["frameworks:\n", "  FOO:\n", "    controls:\n"]
        # ~513 KB of filler
        for i in range(15000):
            lines.append(f"      KEY_{i:05d}:\n        name: 'Control {i}'\n")  # pragma: allowlist secret
        big_yaml.write_text("".join(lines))

        with pytest.raises(ValueError, match="512KB"):
            _load_frameworks_yaml(big_yaml)

    def test_yaml_missing_file_raises_file_not_found(self, tmp_path):
        """FileNotFoundError is raised for a non-existent path."""
        from app.api.services.compliance_frameworks_service import _load_frameworks_yaml

        with pytest.raises(FileNotFoundError):
            _load_frameworks_yaml(tmp_path / "does_not_exist.yaml")

    def test_yaml_invalid_root_type_raises_value_error(self, tmp_path):
        """ValueError is raised when the YAML root is not a mapping."""
        from app.api.services.compliance_frameworks_service import _load_frameworks_yaml

        bad_yaml = tmp_path / "bad.yaml"
        bad_yaml.write_text("- just\n- a\n- list\n")

        with pytest.raises(ValueError, match="mapping"):
            _load_frameworks_yaml(bad_yaml)


# ---------------------------------------------------------------------------
# 2. get_all_frameworks()
# ---------------------------------------------------------------------------


class TestGetAllFrameworks:
    """Tests for ComplianceFrameworksService.get_all_frameworks()."""

    def test_returns_both_frameworks(self):
        """get_all_frameworks() returns at least SOC2_2017 and NIST_CSF_2.0."""
        svc = _make_service()
        frameworks = svc.get_all_frameworks()
        ids = {fw["id"] for fw in frameworks}
        assert "SOC2_2017" in ids
        assert "NIST_CSF_2.0" in ids

    def test_each_summary_has_required_keys(self):
        """Each framework summary contains id, name, version, authority, control_count."""
        svc = _make_service()
        for fw in svc.get_all_frameworks():
            assert "id" in fw
            assert "name" in fw
            assert "version" in fw
            assert "authority" in fw
            assert "control_count" in fw

    def test_control_counts_are_positive(self):
        """Each framework has at least one control."""
        svc = _make_service()
        for fw in svc.get_all_frameworks():
            assert fw["control_count"] > 0, f"{fw['id']} has no controls"

    def test_soc2_has_at_least_20_controls(self):
        """SOC2_2017 has the expected minimum number of controls (≥20)."""
        svc = _make_service()
        soc2 = next(fw for fw in svc.get_all_frameworks() if fw["id"] == "SOC2_2017")
        assert soc2["control_count"] >= 20

    def test_nist_has_at_least_25_controls(self):
        """NIST_CSF_2.0 has the expected minimum number of controls (≥25)."""
        svc = _make_service()
        nist = next(fw for fw in svc.get_all_frameworks() if fw["id"] == "NIST_CSF_2.0")
        assert nist["control_count"] >= 25


# ---------------------------------------------------------------------------
# 3. get_framework()
# ---------------------------------------------------------------------------


class TestGetFramework:
    """Tests for ComplianceFrameworksService.get_framework()."""

    def test_returns_soc2_with_controls(self):
        """get_framework('SOC2_2017') returns the framework with controls."""
        svc = _make_service()
        fw = svc.get_framework("SOC2_2017")
        assert fw["id"] == "SOC2_2017"
        assert "controls" in fw
        assert len(fw["controls"]) > 0

    def test_returns_nist_with_controls(self):
        """get_framework('NIST_CSF_2.0') returns the framework with controls."""
        svc = _make_service()
        fw = svc.get_framework("NIST_CSF_2.0")
        assert fw["id"] == "NIST_CSF_2.0"
        assert "controls" in fw
        assert len(fw["controls"]) > 0

    def test_raises_key_error_for_unknown_framework(self):
        """get_framework() raises KeyError for an unknown framework_id."""
        svc = _make_service()
        with pytest.raises(KeyError, match="MADE_UP_FW"):
            svc.get_framework("MADE_UP_FW")

    def test_soc2_includes_cc6_controls(self):
        """SOC2_2017 contains the critical CC6 access-control series."""
        svc = _make_service()
        fw = svc.get_framework("SOC2_2017")
        cc6_keys = [k for k in fw["controls"] if k.startswith("CC6")]
        assert len(cc6_keys) > 0, "Expected CC6.x controls in SOC2_2017"

    def test_nist_includes_all_six_functions(self):
        """NIST_CSF_2.0 covers all 6 CSF functions (GV, ID, PR, DE, RS, RC)."""
        svc = _make_service()
        fw = svc.get_framework("NIST_CSF_2.0")
        function_ids = {
            v.get("function_id") for v in fw["controls"].values() if "function_id" in v
        }
        expected = {"GV", "ID", "PR", "DE", "RS", "RC"}
        missing = expected - function_ids
        assert not missing, "Missing CSF functions: " + str(missing)


# ---------------------------------------------------------------------------
# 4. get_control()
# ---------------------------------------------------------------------------


class TestGetControl:
    """Tests for ComplianceFrameworksService.get_control()."""

    def test_returns_soc2_cc6_1(self):
        """get_control('SOC2_2017', 'CC6.1') returns the correct control."""
        svc = _make_service()
        ctrl = svc.get_control("SOC2_2017", "CC6.1")
        assert ctrl["id"] == "CC6.1"
        assert ctrl["framework_id"] == "SOC2_2017"
        assert "name" in ctrl

    def test_returns_nist_pr_ds_01(self):
        """get_control('NIST_CSF_2.0', 'PR.DS-01') returns the data-at-rest control."""
        svc = _make_service()
        ctrl = svc.get_control("NIST_CSF_2.0", "PR.DS-01")
        assert ctrl["id"] == "PR.DS-01"
        assert ctrl["framework_id"] == "NIST_CSF_2.0"

    def test_raises_for_unknown_control(self):
        """get_control() raises KeyError for an unknown control_id."""
        svc = _make_service()
        with pytest.raises(KeyError, match="FAKE_CTRL_99"):
            svc.get_control("SOC2_2017", "FAKE_CTRL_99")

    def test_raises_for_unknown_framework_in_get_control(self):
        """get_control() raises KeyError when framework_id is unknown."""
        svc = _make_service()
        with pytest.raises(KeyError):
            svc.get_control("UNKNOWN_FW", "CC6.1")


# ---------------------------------------------------------------------------
# 5. map_tags_to_controls()
# ---------------------------------------------------------------------------


class TestMapTagsToControls:
    """Tests for ComplianceFrameworksService.map_tags_to_controls()."""

    def test_maps_valid_soc2_tag(self):
        """Valid SOC2 tag resolves to the correct control."""
        svc = _make_service()
        result = svc.map_tags_to_controls(["SOC2_2017.CC6.1"])
        assert "SOC2_2017" in result
        assert any(c["id"] == "CC6.1" for c in result["SOC2_2017"])

    def test_maps_valid_nist_tag(self):
        """Valid NIST CSF 2.0 tag resolves to the correct control."""
        svc = _make_service()
        result = svc.map_tags_to_controls(["NIST_CSF_2.0.PR.DS-01"])
        assert "NIST_CSF_2.0" in result
        assert any(c["id"] == "PR.DS-01" for c in result["NIST_CSF_2.0"])

    def test_maps_tags_across_both_frameworks(self):
        """Tags from both frameworks are resolved and grouped correctly."""
        svc = _make_service()
        result = svc.map_tags_to_controls([
            "SOC2_2017.CC6.1",
            "SOC2_2017.CC7.4",
            "NIST_CSF_2.0.PR.DS-01",
        ])
        assert "SOC2_2017" in result
        assert "NIST_CSF_2.0" in result
        assert len(result["SOC2_2017"]) == 2
        assert len(result["NIST_CSF_2.0"]) == 1

    def test_gracefully_skips_unknown_tags(self):
        """Unknown/fabricated tags are silently skipped — no KeyError raised."""
        svc = _make_service()
        # Should not raise; unknown tags are ignored
        result = svc.map_tags_to_controls([
            "SOC2_2017.CC6.1",          # valid
            "SOC2_2017.FAKE_CTRL_999",  # unknown control in known framework
            "UNKNOWN_FW.CC6.1",          # unknown framework
            "NOT_A_TAG_AT_ALL",          # malformed
        ])
        # Only the valid tag should be returned
        assert "SOC2_2017" in result
        assert len(result["SOC2_2017"]) == 1
        assert "UNKNOWN_FW" not in result

    def test_empty_tag_list_returns_empty_dict(self):
        """An empty tag list returns an empty mapping."""
        svc = _make_service()
        result = svc.map_tags_to_controls([])
        assert result == {}

    def test_all_invalid_tags_returns_empty_dict(self):
        """When every tag is invalid, the result is an empty dict."""
        svc = _make_service()
        result = svc.map_tags_to_controls(["BAD.TAG.ONE", "BAD.TAG.TWO"])
        assert result == {}


# ---------------------------------------------------------------------------
# 6. get_frameworks_for_rule() — convenience alias
# ---------------------------------------------------------------------------


class TestGetFrameworksForRule:
    """Tests for ComplianceFrameworksService.get_frameworks_for_rule()."""

    def test_alias_is_equivalent_to_map_tags(self):
        """get_frameworks_for_rule delegates to map_tags_to_controls."""
        svc = _make_service()
        tags = ["SOC2_2017.CC6.1", "NIST_CSF_2.0.DE.CM-01"]
        assert svc.get_frameworks_for_rule(tags) == svc.map_tags_to_controls(tags)


# ---------------------------------------------------------------------------
# 7. is_valid_tag()
# ---------------------------------------------------------------------------


class TestIsValidTag:
    """Tests for ComplianceFrameworksService.is_valid_tag()."""

    def test_known_tag_is_valid(self):
        """A known fully-qualified tag is reported as valid."""
        svc = _make_service()
        assert svc.is_valid_tag("SOC2_2017.CC6.1") is True

    def test_unknown_tag_is_invalid(self):
        """A fabricated tag is reported as invalid."""
        svc = _make_service()
        assert svc.is_valid_tag("SOC2_FULLY_COMPLIANT") is False
        assert svc.is_valid_tag("SOC2_2017.NONEXISTENT_CTRL") is False


# ---------------------------------------------------------------------------
# 8. Route tests — GET /api/v1/compliance/frameworks
# ---------------------------------------------------------------------------


class TestListFrameworksRoute:
    """Tests for GET /api/v1/compliance/frameworks."""

    def test_returns_200_with_framework_list(self, authed_client):
        """Authenticated request returns 200 with a frameworks list."""
        response = authed_client.get("/api/v1/compliance/frameworks")
        assert response.status_code == 200
        data = response.json()
        assert "frameworks" in data
        assert "count" in data
        assert isinstance(data["frameworks"], list)

    def test_response_includes_both_frameworks(self, authed_client):
        """Response includes SOC2_2017 and NIST_CSF_2.0 summaries."""
        response = authed_client.get("/api/v1/compliance/frameworks")
        assert response.status_code == 200
        ids = {fw["id"] for fw in response.json()["frameworks"]}
        assert "SOC2_2017" in ids
        assert "NIST_CSF_2.0" in ids

    def test_count_matches_frameworks_list_length(self, authed_client):
        """The 'count' field matches the length of 'frameworks'."""
        response = authed_client.get("/api/v1/compliance/frameworks")
        data = response.json()
        assert data["count"] == len(data["frameworks"])

    def test_requires_auth_returns_401(self, client):
        """Unauthenticated request returns 401."""
        response = client.get("/api/v1/compliance/frameworks")
        assert response.status_code == 401

    def test_uses_mocked_service(self, authed_client):
        """Route uses the injected service and returns its data."""
        from app.api.routes.compliance_frameworks import _get_service
        from app.main import app

        mock_svc = _mock_service()
        app.dependency_overrides[_get_service] = lambda: mock_svc

        try:
            response = authed_client.get("/api/v1/compliance/frameworks")
            assert response.status_code == 200
            mock_svc.get_all_frameworks.assert_called_once()
        finally:
            app.dependency_overrides.pop(_get_service, None)


# ---------------------------------------------------------------------------
# 9. Route tests — GET /api/v1/compliance/frameworks/{framework_id}
# ---------------------------------------------------------------------------


class TestGetFrameworkRoute:
    """Tests for GET /api/v1/compliance/frameworks/{framework_id}."""

    def test_returns_200_for_soc2(self, authed_client):
        """Authenticated request for SOC2_2017 returns 200."""
        response = authed_client.get("/api/v1/compliance/frameworks/SOC2_2017")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "SOC2_2017"
        assert "controls" in data

    def test_returns_200_for_nist(self, authed_client):
        """Authenticated request for NIST_CSF_2.0 returns 200."""
        response = authed_client.get("/api/v1/compliance/frameworks/NIST_CSF_2.0")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "NIST_CSF_2.0"

    def test_returns_404_for_unknown_framework(self, authed_client):
        """Unknown framework_id returns 404."""
        response = authed_client.get("/api/v1/compliance/frameworks/FAKE_FW_99")
        assert response.status_code == 404

    def test_requires_auth_returns_401(self, client):
        """Unauthenticated request returns 401."""
        response = client.get("/api/v1/compliance/frameworks/SOC2_2017")
        assert response.status_code == 401

    def test_response_has_control_count(self, authed_client):
        """Framework response includes a control_count field."""
        response = authed_client.get("/api/v1/compliance/frameworks/SOC2_2017")
        assert response.status_code == 200
        data = response.json()
        assert "control_count" in data
        assert data["control_count"] > 0


# ---------------------------------------------------------------------------
# 10. Route tests — GET /api/v1/compliance/frameworks/{fw}/controls/{ctrl}
# ---------------------------------------------------------------------------


class TestGetControlRoute:
    """Tests for GET /api/v1/compliance/frameworks/{framework_id}/controls/{control_id}."""

    def test_returns_200_for_known_control(self, authed_client):
        """Authenticated request for a known control returns 200."""
        response = authed_client.get(
            "/api/v1/compliance/frameworks/SOC2_2017/controls/CC6.1"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "CC6.1"
        assert data["framework_id"] == "SOC2_2017"

    def test_returns_200_for_nist_control_with_dots(self, authed_client):
        """Control IDs containing dots (NIST style) are resolved correctly."""
        response = authed_client.get(
            "/api/v1/compliance/frameworks/NIST_CSF_2.0/controls/PR.DS-01"
        )
        assert response.status_code == 200
        assert response.json()["id"] == "PR.DS-01"

    def test_returns_404_for_unknown_control(self, authed_client):
        """Unknown control_id returns 404."""
        response = authed_client.get(
            "/api/v1/compliance/frameworks/SOC2_2017/controls/no-such-control"
        )
        assert response.status_code == 404

    def test_returns_404_for_unknown_framework(self, authed_client):
        """Unknown framework_id on the control route returns 404."""
        response = authed_client.get(
            "/api/v1/compliance/frameworks/FAKE_FW/controls/CC6.1"
        )
        assert response.status_code == 404

    def test_requires_auth_returns_401(self, client):
        """Unauthenticated control request returns 401."""
        response = client.get(
            "/api/v1/compliance/frameworks/SOC2_2017/controls/CC6.1"
        )
        assert response.status_code == 401
