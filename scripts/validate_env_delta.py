#!/usr/bin/env python3
"""env-delta.yaml schema validator + literal-rejection gate.

Enforces HTT P0 Security Requirement #7 (release-gate-arbiter Finding N-4).

Two independent checks run on every invocation:

  1. SCHEMA — parsed YAML conforms to the canonical structure defined by the
     Pydantic models in this module. Missing required keys, wrong types, or
     extra top-level keys fail the check.

  2. LITERAL REJECTION — no secret-looking literal values are present anywhere
     in the tree. Reference fields (subscription_ref, tenant_ref) must look
     like GitHub variable names, not UUIDs. Freeform strings are scanned for
     UUID, connection-string, and common secret-prefix patterns.

Exit codes (POSIX convention — zero is success):

  0 — file is valid
  1 — schema violation
  2 — literal-rejection violation
  3 — I/O error (file missing / unreadable / bad YAML)

Usage:
  $ python scripts/validate_env_delta.py env-delta.yaml
  $ python scripts/validate_env_delta.py --json env-delta.yaml   # machine-readable

Refs: bd my5r
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictInt,
    ValidationError,
    field_validator,
)

# =============================================================================
# Exit codes — exported so tests + CI callers share the same contract.
# =============================================================================

EXIT_OK = 0
EXIT_SCHEMA = 1
EXIT_LITERAL = 2
EXIT_IO = 3


# =============================================================================
# Schema (Pydantic models)
#
# Kept strict: extra=forbid on every model so that silent typos (e.g.
# "subscritpion_ref" or "resource_grp_pattern") fail the gate instead of
# being accepted and silently ignored by downstream consumers.
# =============================================================================


class _StrictModel(BaseModel):
    """Base for all env-delta models — forbids unknown keys."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class AzureConfig(_StrictModel):
    subscription_ref: str = Field(..., description="GitHub variable name, NOT a literal UUID.")
    location: str
    secondary_location: str | None = None
    resource_group_pattern: str
    app_service_name: str
    app_service_url: str | None = None
    container_image: str
    container_registry: str | None = None

    @field_validator("subscription_ref")
    @classmethod
    def _ref_is_not_uuid(cls, v: str) -> str:
        if _UUID_RE.fullmatch(v):
            raise ValueError(
                "subscription_ref MUST be a GitHub variable name (e.g. "
                "AZURE_STAGING_SUBSCRIPTION_ID), NOT a literal UUID."
            )
        return v


class DataConfig(_StrictModel):
    sql_sku: str
    # StrictBool: no string-coercion. A bare "no" or "false" in YAML is a
    # schema error rather than being silently turned into False, which would
    # be a terrible security footgun on flags like enable_redis.
    sql_deployed: StrictBool
    enable_azure_sql_flag: StrictBool
    enable_redis: StrictBool


class AuthConfig(_StrictModel):
    tenant_ref: str
    multi_tenant: StrictBool

    @field_validator("tenant_ref")
    @classmethod
    def _ref_is_not_uuid(cls, v: str) -> str:
        if _UUID_RE.fullmatch(v):
            raise ValueError(
                "tenant_ref MUST be a reference name (e.g. 'production-tenant'), "
                "NOT a literal tenant UUID."
            )
        return v


class ObservabilityConfig(_StrictModel):
    log_retention_days: StrictInt = Field(..., ge=1, le=3650)


class KnownIssue(_StrictModel):
    ticket: str
    summary: str


class EnvironmentSpec(_StrictModel):
    purpose: str
    azure: AzureConfig
    data: DataConfig
    auth: AuthConfig
    observability: ObservabilityConfig
    tags: dict[str, str] = Field(default_factory=dict)
    cors_origins: list[str] | None = None
    known_issues: list[KnownIssue] | None = None


class InfrastructureDelta(_StrictModel):
    file: str
    line: int
    key: str
    old: Any
    new: Any
    commit: str
    bd_ticket: str
    classification: str
    runtime_impact: str
    rationale: str | None = None


class DeltasSincePreviousRelease(_StrictModel):
    previous_tag: str
    current_tag: str
    head_sha: str
    scan_command: str
    infrastructure_parameters: list[InfrastructureDelta] = Field(default_factory=list)


class SecretsInventory(_StrictModel):
    github_environment_secrets: list[str] = Field(default_factory=list)
    azure_keyvault_secrets: list[str] = Field(default_factory=list)
    repo_variables: list[str] = Field(default_factory=list)


class EnvDeltaDocument(_StrictModel):
    """Top-level schema. Mirrors the on-disk env-delta.yaml."""

    schema_version: int = Field(..., ge=1)
    reference_environment: str
    environments: dict[str, EnvironmentSpec]
    deltas_since_previous_release: DeltasSincePreviousRelease
    secrets_inventory: SecretsInventory


# =============================================================================
# Literal-rejection heuristics
#
# Fails closed on:
#   - UUIDs (Azure subscription / tenant / app IDs)
#   - Connection-string fragments (Password=, AccountKey=, EndpointSuffix=)
#   - Common secret prefixes (sk_, pk_, ghp_, gho_, ghu_, ghs_, ghr_)
#   - High-entropy base64-ish blobs >= 40 chars
#
# Allowlists intentional non-secrets by field path so a legitimate SHA, image
# tag, or URL doesn't trip the guard.
# =============================================================================

_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)

_CONNSTRING_RE = re.compile(
    r"(?:AccountKey|Password|PWD|DefaultEndpointsProtocol|EndpointSuffix|SharedAccessKey)\s*=",
    re.I,
)

_SECRET_PREFIX_RE = re.compile(
    r"^(?:sk_|pk_|ghp_|gho_|ghu_|ghs_|ghr_|xoxb-|xoxp-|AKIA|ASIA)[A-Za-z0-9_\-]{16,}$"
)

# Heuristic: 40+ char string that looks base64-ish AND has no slashes/colons
# (which are typical URL / image-ref / command separators). Tight on purpose;
# we'd rather miss a secret than file bogus alerts.
_HIGH_ENTROPY_RE = re.compile(r"^[A-Za-z0-9+/=_\-]{40,}$")

# Field paths that are allowed to hold free-form non-secret data. Matched as
# dotted paths like "environments.production.azure.container_image".
# Glob-style: segment "*" matches any single key, "**" matches any suffix.
_LITERAL_ALLOWLIST: tuple[tuple[str, ...], ...] = (
    # Image refs + registries
    ("environments", "*", "azure", "container_image"),
    ("environments", "*", "azure", "container_registry"),
    # URLs
    ("environments", "*", "azure", "app_service_url"),
    ("environments", "*", "cors_origins", "*"),
    # Git metadata
    ("deltas_since_previous_release", "previous_tag"),
    ("deltas_since_previous_release", "current_tag"),
    ("deltas_since_previous_release", "head_sha"),
    ("deltas_since_previous_release", "scan_command"),
    # Delta records can reference SHAs, tickets, etc.
    ("deltas_since_previous_release", "infrastructure_parameters", "*", "commit"),
    ("deltas_since_previous_release", "infrastructure_parameters", "*", "old"),
    ("deltas_since_previous_release", "infrastructure_parameters", "*", "new"),
    ("deltas_since_previous_release", "infrastructure_parameters", "*", "rationale"),
    # Known-issue summaries can mention URLs / hostnames
    ("environments", "*", "known_issues", "*", "summary"),
)


# =============================================================================
# Violation + result types
# =============================================================================


@dataclass
class LiteralViolation:
    """A literal-rejection hit — the most useful fields are path + rule."""

    path: str
    value: str
    rule: str

    def render(self) -> str:
        preview = (
            self.value
            if len(self.value) <= 64
            else f"{self.value[:32]}...({len(self.value)} chars)"
        )
        return f"  [{self.rule}] {self.path} = {preview!r}"


@dataclass
class ValidationResult:
    schema_errors: list[str] = field(default_factory=list)
    literal_violations: list[LiteralViolation] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.schema_errors and not self.literal_violations

    @property
    def exit_code(self) -> int:
        if self.schema_errors:
            return EXIT_SCHEMA
        if self.literal_violations:
            return EXIT_LITERAL
        return EXIT_OK

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "exit_code": self.exit_code,
            "schema_errors": list(self.schema_errors),
            "literal_violations": [
                {"path": v.path, "value": v.value, "rule": v.rule} for v in self.literal_violations
            ],
        }


# =============================================================================
# Allowlist path-matching
# =============================================================================


def _path_matches(actual: tuple[str, ...], pattern: tuple[str, ...]) -> bool:
    """Glob-match a field path against an allowlist pattern.

    Pattern supports "*" as a single-segment wildcard. Lengths must match
    exactly (no "**" multi-segment wildcard — YAGNI).
    """
    if len(actual) != len(pattern):
        return False
    return all(p == "*" or p == a for p, a in zip(pattern, actual, strict=False))


def _is_allowlisted(path: tuple[str, ...]) -> bool:
    return any(_path_matches(path, pat) for pat in _LITERAL_ALLOWLIST)


# =============================================================================
# Tree walker + literal detector
# =============================================================================


def _walk(node: Any, path: tuple[str, ...] = ()) -> list[LiteralViolation]:
    """Depth-first walk. Returns a list of violations."""
    if isinstance(node, dict):
        out: list[LiteralViolation] = []
        for k, v in node.items():
            out.extend(_walk(v, (*path, str(k))))
        return out

    if isinstance(node, list):
        out = []
        for i, v in enumerate(node):
            # Use a "*" marker in the path so allowlists stay index-agnostic,
            # while still showing the real index in the emitted path string.
            out.extend(_walk_with_index(v, path, i))
        return out

    return _check_leaf(node, path)


def _walk_with_index(node: Any, parent_path: tuple[str, ...], index: int) -> list[LiteralViolation]:
    """List items: match against allowlist using '*' wildcard, report with index."""
    if isinstance(node, dict):
        # Treat the list item itself as a "*" segment for matching purposes.
        wildcard_path = (*parent_path, "*")
        real_path = (*parent_path, f"[{index}]")
        # Recurse into the dict with the wildcard path for allowlist checks,
        # but substitute the real index in any violation's rendered path.
        violations = _walk(node, wildcard_path)
        return [_retarget(v, wildcard_path, real_path) for v in violations]
    # Scalar list item.
    return _check_leaf(node, (*parent_path, f"[{index}]"))


def _retarget(
    v: LiteralViolation, from_prefix: tuple[str, ...], to_prefix: tuple[str, ...]
) -> LiteralViolation:
    """Rewrite a violation's path so the "*" wildcard is replaced with the real index."""
    parts = v.path.split(".")
    from_segments = list(from_prefix)
    to_segments = list(to_prefix)
    if parts[: len(from_segments)] == from_segments:
        rewritten = ".".join(to_segments + parts[len(from_segments) :])
        return LiteralViolation(path=rewritten, value=v.value, rule=v.rule)
    return v


def _check_leaf(value: Any, path: tuple[str, ...]) -> list[LiteralViolation]:
    """Apply secret-literal rules to a single scalar value."""
    if not isinstance(value, str):
        return []

    # Allowlisted paths: skip content checks but still verify no connection-
    # string fragment sneaks in under a permissive key. (The allowlist trusts
    # the field, but not _everything_ — a container_image should never contain
    # "AccountKey=".)
    path_str = ".".join(path)
    violations: list[LiteralViolation] = []

    if _CONNSTRING_RE.search(value):
        violations.append(LiteralViolation(path_str, value, "connection_string"))

    if _is_allowlisted(path):
        return violations  # connection-string still fires; other rules suppressed.

    if _UUID_RE.fullmatch(value):
        violations.append(LiteralViolation(path_str, value, "uuid_literal"))

    if _SECRET_PREFIX_RE.match(value):
        violations.append(LiteralViolation(path_str, value, "secret_prefix"))

    if _HIGH_ENTROPY_RE.match(value) and ":" not in value and "/" not in value:
        violations.append(LiteralViolation(path_str, value, "high_entropy"))

    return violations


# =============================================================================
# Public API
# =============================================================================


def validate_document(data: dict[str, Any]) -> ValidationResult:
    """Validate a parsed YAML dict. Pure function — no I/O."""
    result = ValidationResult()

    # --- Schema check ------------------------------------------------------
    try:
        EnvDeltaDocument.model_validate(data)
    except ValidationError as e:
        for err in e.errors():
            loc = ".".join(str(p) for p in err["loc"])
            result.schema_errors.append(f"{loc}: {err['msg']}")

    # --- Literal-rejection check (runs even if schema fails, to surface more) --
    result.literal_violations.extend(_walk(data))
    return result


def validate_file(path: Path) -> tuple[ValidationResult, int]:
    """Validate a file on disk.

    Returns (result, io_exit_code). If io_exit_code != 0, result is empty and
    the caller should treat it as an I/O failure.
    """
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as e:
        print(f"ERROR: cannot read {path}: {e}", file=sys.stderr)
        return ValidationResult(), EXIT_IO

    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as e:
        print(f"ERROR: {path} is not valid YAML: {e}", file=sys.stderr)
        return ValidationResult(), EXIT_IO

    if not isinstance(data, dict):
        print(f"ERROR: {path} must contain a YAML mapping at the top level", file=sys.stderr)
        return ValidationResult(), EXIT_IO

    return validate_document(data), EXIT_OK


# =============================================================================
# CLI
# =============================================================================


def _render_human(result: ValidationResult, path: Path) -> None:
    if result.ok:
        print(f"✅ {path} — schema valid, no literal-rejection violations")
        return

    if result.schema_errors:
        print(f"❌ {path} — {len(result.schema_errors)} schema error(s):")
        for err in result.schema_errors:
            print(f"  {err}")

    if result.literal_violations:
        print(f"❌ {path} — {len(result.literal_violations)} literal-rejection violation(s):")
        for v in result.literal_violations:
            print(v.render())
        print(
            "\nHint: reference Azure IDs by GH variable / KV secret name instead of\n"
            "inlining the literal value. See env-delta.yaml comment block for examples.",
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate env-delta.yaml schema + reject literal secrets",
    )
    parser.add_argument(
        "file",
        nargs="?",
        default="env-delta.yaml",
        help="Path to env-delta.yaml (default: ./env-delta.yaml)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of human output",
    )
    args = parser.parse_args(argv)

    path = Path(args.file)
    result, io_code = validate_file(path)
    if io_code != EXIT_OK:
        return io_code

    if args.json:
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        _render_human(result, path)

    return result.exit_code


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
