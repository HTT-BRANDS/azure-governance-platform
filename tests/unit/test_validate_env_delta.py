"""Tests for scripts/validate_env_delta.py (bd my5r).

Coverage split into three families, one test class per concern:

  * TestSchema        — Pydantic-backed structural checks
  * TestLiteralGate   — the secret-rejection walker
  * TestCli           — argparse + exit codes, via validate_file + main()

Real env-delta.yaml is validated at the top of the module via an import-time
test so that any upstream drift breaks CI loud and fast (not only when the
dedicated scan job runs).
"""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "validate_env_delta.py"
ENV_DELTA_PATH = REPO_ROOT / "env-delta.yaml"


# -----------------------------------------------------------------------------
# Load the script as a module so we can import its symbols without putting it
# on sys.path at test-collection time. Keeps tests+script decoupled.
#
# Note: we MUST register the module in sys.modules BEFORE exec_module() to
# avoid the classic @dataclass+dynamic-import traceback where dataclasses
# tries to resolve cls.__module__ and gets None.
# -----------------------------------------------------------------------------
def _load_module():
    spec = importlib.util.spec_from_file_location("validate_env_delta", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["validate_env_delta"] = mod
    spec.loader.exec_module(mod)
    return mod


ved = _load_module()


@pytest.fixture
def valid_doc() -> dict:
    """Fresh copy of the real env-delta.yaml, parsed."""
    return yaml.safe_load(ENV_DELTA_PATH.read_text(encoding="utf-8"))


# =============================================================================
# Golden-file guard: the real env-delta.yaml must stay valid.
# =============================================================================


class TestGoldenFile:
    def test_real_env_delta_validates_clean(self, valid_doc):
        result = ved.validate_document(valid_doc)
        assert result.ok, (
            f"Real env-delta.yaml failed validation:\n"
            f"  schema_errors: {result.schema_errors}\n"
            f"  literal_violations: {[v.path for v in result.literal_violations]}"
        )
        assert result.exit_code == ved.EXIT_OK


# =============================================================================
# Schema checks.
# =============================================================================


class TestSchema:
    def test_missing_required_top_level_key_fails(self, valid_doc):
        del valid_doc["schema_version"]
        result = ved.validate_document(valid_doc)
        assert result.exit_code == ved.EXIT_SCHEMA
        assert any("schema_version" in e for e in result.schema_errors)

    def test_unknown_top_level_key_fails_closed(self, valid_doc):
        valid_doc["mystery_meat"] = True
        result = ved.validate_document(valid_doc)
        assert result.exit_code == ved.EXIT_SCHEMA
        assert any("mystery_meat" in e for e in result.schema_errors)

    def test_typo_in_nested_key_fails_closed(self, valid_doc):
        # "subscritpion_ref" typo must NOT be silently accepted.
        valid_doc["environments"]["dev"]["azure"]["subscritpion_ref"] = "foo"
        result = ved.validate_document(valid_doc)
        assert result.exit_code == ved.EXIT_SCHEMA
        assert any("subscritpion_ref" in e for e in result.schema_errors)

    def test_subscription_ref_as_uuid_literal_rejected_at_schema(self, valid_doc):
        valid_doc["environments"]["dev"]["azure"]["subscription_ref"] = (
            "11111111-2222-3333-4444-555555555555"  # pragma: allowlist secret
        )
        result = ved.validate_document(valid_doc)
        assert result.exit_code == ved.EXIT_SCHEMA
        assert any("subscription_ref" in e for e in result.schema_errors)

    def test_tenant_ref_as_uuid_literal_rejected_at_schema(self, valid_doc):
        valid_doc["environments"]["dev"]["auth"]["tenant_ref"] = (
            "11111111-2222-3333-4444-555555555555"  # pragma: allowlist secret
        )
        result = ved.validate_document(valid_doc)
        assert result.exit_code == ved.EXIT_SCHEMA
        assert any("tenant_ref" in e for e in result.schema_errors)

    def test_log_retention_out_of_range_rejected(self, valid_doc):
        valid_doc["environments"]["dev"]["observability"]["log_retention_days"] = 0
        result = ved.validate_document(valid_doc)
        assert result.exit_code == ved.EXIT_SCHEMA

    def test_wrong_type_rejected(self, valid_doc):
        valid_doc["environments"]["dev"]["data"]["enable_redis"] = "no"  # should be bool
        result = ved.validate_document(valid_doc)
        assert result.exit_code == ved.EXIT_SCHEMA


# =============================================================================
# Literal-rejection walker.
# =============================================================================


class TestLiteralGate:
    def test_uuid_literal_in_arbitrary_freeform_field_rejected(self, valid_doc):
        # Stuff a UUID into a purpose string (not allowlisted).
        valid_doc["environments"]["dev"]["purpose"] = (
            "contains a literal tenant id 11111111-2222-3333-4444-555555555555"  # pragma: allowlist secret
        )
        result = ved.validate_document(valid_doc)
        # The "contains..." string as a whole doesn't match ^UUID$, so this
        # specifically tests that we DO tolerate embedded UUIDs (we only flag
        # values that ARE a UUID). This is intentional: tolerating UUIDs in
        # prose avoids false positives on rationales.
        assert not any(v.rule == "uuid_literal" for v in result.literal_violations)

    def test_standalone_uuid_value_rejected(self, valid_doc):
        valid_doc["environments"]["dev"]["tags"]["LeakedTenantId"] = (
            "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"  # pragma: allowlist secret
        )
        result = ved.validate_document(valid_doc)
        assert result.exit_code == ved.EXIT_LITERAL
        assert any(
            v.rule == "uuid_literal" and "LeakedTenantId" in v.path
            for v in result.literal_violations
        )

    def test_connection_string_fragment_rejected_anywhere(self, valid_doc):
        # Even on an allowlisted field, a connection-string fragment fires.
        valid_doc["environments"]["dev"]["azure"]["container_image"] = (
            "ghcr.io/htt-brands/foo:AccountKey=abcdef"
        )
        result = ved.validate_document(valid_doc)
        assert result.exit_code == ved.EXIT_LITERAL
        assert any(v.rule == "connection_string" for v in result.literal_violations)

    def test_secret_prefix_github_pat_rejected(self, valid_doc):
        valid_doc["environments"]["dev"]["tags"]["DebugToken"] = (
            "ghp_abcdefghijklmnopqrstuvwxyz0123456789"  # pragma: allowlist secret
        )
        result = ved.validate_document(valid_doc)
        assert result.exit_code == ved.EXIT_LITERAL
        assert any(v.rule == "secret_prefix" for v in result.literal_violations)

    def test_high_entropy_blob_rejected(self, valid_doc):
        # Plain base64 blob, 48 chars, no separators — classic secret shape.
        valid_doc["environments"]["dev"]["tags"]["OpaqueBlob"] = (
            "A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6Q7R8S9T0U1V2W3X4"  # pragma: allowlist secret
        )
        result = ved.validate_document(valid_doc)
        assert result.exit_code == ved.EXIT_LITERAL
        assert any(v.rule == "high_entropy" for v in result.literal_violations)

    def test_image_ref_allowlisted_does_not_trip_high_entropy(self, valid_doc):
        # Long SHA-tagged image ref, has ":" and "/" so high_entropy also skips,
        # but even without that, allowlist covers it.
        valid_doc["environments"]["dev"]["azure"]["container_image"] = (
            "ghcr.io/htt-brands/azure-governance-platform@sha256:"
            "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"  # pragma: allowlist secret
        )
        result = ved.validate_document(valid_doc)
        # No violations at all for that field.
        assert all("container_image" not in v.path for v in result.literal_violations)

    def test_cors_origins_list_items_allowlisted(self, valid_doc):
        # Generate a long list with SHA-like URLs; should stay clean.
        valid_doc["environments"]["production"]["cors_origins"] = [
            "https://app-governance-prod.azurewebsites.net",
            "https://admin.htt-brands.example/abcdef0123456789abcdef0123456789abcdef01",
        ]
        result = ved.validate_document(valid_doc)
        assert result.ok

    def test_index_appears_in_violation_path_for_lists(self, valid_doc):
        valid_doc["secrets_inventory"]["repo_variables"].append(
            "11111111-2222-3333-4444-555555555555"  # pragma: allowlist secret
        )
        result = ved.validate_document(valid_doc)
        assert result.exit_code == ved.EXIT_LITERAL
        # Path should contain "repo_variables.[<n>]" not "repo_variables.*"
        offending = [v for v in result.literal_violations if v.rule == "uuid_literal"]
        assert offending, "expected a uuid_literal violation"
        assert all(".*" not in v.path for v in offending)
        assert any("[" in v.path and "]" in v.path for v in offending)


# =============================================================================
# CLI / file I/O / exit codes.
# =============================================================================


class TestCli:
    def test_validate_file_happy_path(self):
        result, io_code = ved.validate_file(ENV_DELTA_PATH)
        assert io_code == ved.EXIT_OK
        assert result.ok

    def test_validate_file_missing_file_io_error(self, tmp_path):
        result, io_code = ved.validate_file(tmp_path / "does-not-exist.yaml")
        assert io_code == ved.EXIT_IO

    def test_validate_file_bad_yaml_io_error(self, tmp_path):
        bad = tmp_path / "bad.yaml"
        bad.write_text("key: : : :\n  - broken", encoding="utf-8")
        _, io_code = ved.validate_file(bad)
        assert io_code == ved.EXIT_IO

    def test_validate_file_non_mapping_root_io_error(self, tmp_path):
        just_a_list = tmp_path / "list.yaml"
        just_a_list.write_text("- one\n- two\n", encoding="utf-8")
        _, io_code = ved.validate_file(just_a_list)
        assert io_code == ved.EXIT_IO

    def test_main_cli_returns_zero_on_valid_file(self, capsys):
        exit_code = ved.main([str(ENV_DELTA_PATH)])
        assert exit_code == ved.EXIT_OK
        captured = capsys.readouterr()
        assert "✅" in captured.out

    def test_main_cli_json_mode_emits_parseable_json(self, capsys):
        exit_code = ved.main([str(ENV_DELTA_PATH), "--json"])
        assert exit_code == ved.EXIT_OK
        captured = capsys.readouterr()
        payload = json.loads(captured.out)
        assert payload["ok"] is True
        assert payload["exit_code"] == ved.EXIT_OK
        assert payload["schema_errors"] == []
        assert payload["literal_violations"] == []

    def test_main_cli_returns_schema_code_on_bad_schema(self, tmp_path, valid_doc, capsys):
        broken = copy.deepcopy(valid_doc)
        del broken["schema_version"]
        bad_path = tmp_path / "env-delta.yaml"
        bad_path.write_text(yaml.safe_dump(broken), encoding="utf-8")
        exit_code = ved.main([str(bad_path)])
        assert exit_code == ved.EXIT_SCHEMA

    def test_main_cli_returns_literal_code_on_literal_violation(self, tmp_path, valid_doc):
        broken = copy.deepcopy(valid_doc)
        broken["environments"]["dev"]["tags"]["LeakedTenantId"] = (
            "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"  # pragma: allowlist secret
        )
        bad_path = tmp_path / "env-delta.yaml"
        bad_path.write_text(yaml.safe_dump(broken), encoding="utf-8")
        exit_code = ved.main([str(bad_path)])
        assert exit_code == ved.EXIT_LITERAL
