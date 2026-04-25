#!/usr/bin/env python3
"""Validate current rollback/waiver state against deploy-production workflow.

This is the machine-verifiable counterpart to the prose rollback/runbook docs.
It answers the boring but important question: does the current rollback state
artifact still match the production deploy workflow and waiver metadata?
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

EXIT_OK = 0
EXIT_VALIDATION = 1
EXIT_IO = 2


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class WorkflowSpec(StrictModel):
    path: str
    name: str
    trigger: str


class AppServiceSpec(StrictModel):
    name: str
    resource_group: str
    url: str


class ImageSpec(StrictModel):
    registry: str
    repository: str
    deploy_reference: str
    rollback_reference: str


class HealthChecksSpec(StrictModel):
    primary: str
    additional: list[str]


class DeploymentControlsSpec(StrictModel):
    ghcr_registry_password_secret: str
    azure_oidc_secrets: list[str]
    required_environment: str
    required_reviewers_expected: bool


class ProductionSpec(StrictModel):
    workflow: WorkflowSpec
    app_service: AppServiceSpec
    image: ImageSpec
    health_checks: HealthChecksSpec
    deployment_controls: DeploymentControlsSpec


class RollbackSpec(StrictModel):
    mechanic: str
    authoritative_steps: list[Any]
    digest_evidence_sources: list[str]


class WaiverVerificationSpec(StrictModel):
    requires_second_human_issue_link: bool
    requires_expiry_date: bool
    requires_current_authorized_humans: bool


class WaiverSpec(StrictModel):
    status: str
    type: str
    owner: str
    current_authorized_humans: list[str]
    second_human_issue: str
    expires_on: str
    evidence_note: str
    machine_verification: WaiverVerificationSpec


class ReferencesSpec(StrictModel):
    current_runbook: str
    historical_release_plan: str
    release_evidence_aggregator_issue: str
    waiver_follow_up_issue: str


class RollbackStateDocument(StrictModel):
    schema_version: int = Field(..., ge=1)
    reviewed_on: str
    source_of_truth: str
    repository: str
    production: ProductionSpec
    rollback: RollbackSpec
    waiver: WaiverSpec
    references: ReferencesSpec


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "state_file",
        nargs="?",
        default="docs/release-gate/rollback-current-state.yaml",
        help="Path to rollback-current-state YAML",
    )
    parser.add_argument(
        "--workflow",
        default=".github/workflows/deploy-production.yml",
        help="Path to deploy-production workflow YAML",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable output")
    return parser.parse_args()


def load_yaml(path: Path) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise RuntimeError(f"unable to read {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise RuntimeError(f"invalid yaml in {path}: {exc}") from exc


def extract_workflow_contract(workflow_path: Path) -> dict[str, Any]:
    data = load_yaml(workflow_path)
    env = data.get("env") or {}
    on_block = data.get("on") or data.get(True) or {}
    jobs = data.get("jobs") or {}
    deploy_job = jobs.get("deploy") or {}
    environment = deploy_job.get("environment") or {}

    trigger = "workflow_dispatch" if "workflow_dispatch" in on_block else None
    health_checks = {
        "primary": "/health",
        "additional": ["/health/detailed", "/healthz/data"],
    }

    return {
        "name": data.get("name"),
        "trigger": trigger,
        "app_name": env.get("AZURE_APP_NAME"),
        "resource_group": env.get("AZURE_RESOURCE_GROUP"),
        "url": env.get("PRODUCTION_URL"),
        "registry": env.get("GHCR_REGISTRY"),
        "repository": env.get("GHCR_REPOSITORY"),
        "environment_name": environment.get("name"),
        "health_checks": health_checks,
    }


def validate_document(doc: RollbackStateDocument, workflow: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    if doc.production.workflow.name != workflow["name"]:
        errors.append(
            f"workflow name mismatch: state={doc.production.workflow.name!r} workflow={workflow['name']!r}"
        )
    if doc.production.workflow.trigger != workflow["trigger"]:
        errors.append(
            f"workflow trigger mismatch: state={doc.production.workflow.trigger!r} workflow={workflow['trigger']!r}"
        )
    if doc.production.app_service.name != workflow["app_name"]:
        errors.append(
            f"app service mismatch: state={doc.production.app_service.name!r} workflow={workflow['app_name']!r}"
        )
    if doc.production.app_service.resource_group != workflow["resource_group"]:
        errors.append(
            "resource group mismatch: "
            f"state={doc.production.app_service.resource_group!r} "
            f"workflow={workflow['resource_group']!r}"
        )
    if doc.production.app_service.url != workflow["url"]:
        errors.append(
            f"production url mismatch: state={doc.production.app_service.url!r} workflow={workflow['url']!r}"
        )
    if doc.production.image.registry != workflow["registry"]:
        errors.append(
            f"registry mismatch: state={doc.production.image.registry!r} workflow={workflow['registry']!r}"
        )
    if doc.production.image.repository != workflow["repository"]:
        errors.append(
            f"repository mismatch: state={doc.production.image.repository!r} workflow={workflow['repository']!r}"
        )
    if doc.production.deployment_controls.required_environment != workflow["environment_name"]:
        errors.append(
            "required environment mismatch: "
            f"state={doc.production.deployment_controls.required_environment!r} "
            f"workflow={workflow['environment_name']!r}"
        )
    if doc.production.health_checks.primary != workflow["health_checks"]["primary"]:
        errors.append("primary health endpoint drifted from workflow contract")
    if doc.production.health_checks.additional != workflow["health_checks"]["additional"]:
        errors.append("additional health endpoints drifted from workflow contract")
    if doc.production.image.deploy_reference != "digest":
        errors.append("deploy_reference must remain 'digest'")
    if doc.production.image.rollback_reference != "digest":
        errors.append("rollback_reference must remain 'digest'")
    if (
        doc.waiver.machine_verification.requires_second_human_issue_link
        and not doc.waiver.second_human_issue
    ):
        errors.append("waiver requires a linked second-human issue")
    if doc.references.waiver_follow_up_issue != doc.waiver.second_human_issue:
        errors.append("waiver follow-up issue must match waiver.second_human_issue")
    if (
        doc.waiver.machine_verification.requires_current_authorized_humans
        and not doc.waiver.current_authorized_humans
    ):
        errors.append("waiver requires at least one currently authorized human")
    if doc.waiver.status == "active" and len(doc.waiver.current_authorized_humans) != 1:
        errors.append("active single-human waiver must list exactly one currently authorized human")
    if doc.waiver.type != "single_human_rollback_coverage":
        errors.append("waiver.type must remain single_human_rollback_coverage")
    if doc.rollback.mechanic != "repin_previous_known_good_digest_and_restart":
        errors.append("rollback mechanic drifted from digest-based deploy contract")
    return errors


def build_output(
    state_path: Path, doc: RollbackStateDocument, workflow: dict[str, Any], errors: list[str]
) -> dict[str, Any]:
    return {
        "ok": not errors,
        "state_file": str(state_path),
        "workflow_path": doc.production.workflow.path,
        "validated_contract": {
            "workflow_name": workflow["name"],
            "trigger": workflow["trigger"],
            "app_service": workflow["app_name"],
            "resource_group": workflow["resource_group"],
            "url": workflow["url"],
            "image_reference_mode": doc.production.image.deploy_reference,
            "waiver_status": doc.waiver.status,
            "waiver_follow_up_issue": doc.waiver.second_human_issue,
        },
        "errors": errors,
    }


def main() -> int:
    args = parse_args()
    state_path = Path(args.state_file)
    workflow_path = Path(args.workflow)

    try:
        raw = load_yaml(state_path)
        doc = RollbackStateDocument.model_validate(raw)
        workflow = extract_workflow_contract(workflow_path)
    except (RuntimeError, ValidationError) as exc:
        payload = {"ok": False, "errors": [str(exc)]}
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"ERROR: {payload['errors'][0]}")
        return EXIT_IO if isinstance(exc, RuntimeError) else EXIT_VALIDATION

    errors = validate_document(doc, workflow)
    payload = build_output(state_path, doc, workflow, errors)

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        if errors:
            print("ROLLBACK STATE INVALID")
            for error in errors:
                print(f"- {error}")
        else:
            print("ROLLBACK STATE OK")
            print(
                f"- workflow={workflow['name']} trigger={workflow['trigger']} app={workflow['app_name']}"
            )
            print(f"- resource_group={workflow['resource_group']} url={workflow['url']}")
            print(
                f"- waiver={doc.waiver.status} owner={doc.waiver.owner} follow_up={doc.waiver.second_human_issue}"
            )
    return EXIT_OK if not errors else EXIT_VALIDATION


if __name__ == "__main__":
    raise SystemExit(main())
