"""Riverside preflight check: RiversideEvidenceCheck.

Split from the monolithic app/preflight/riverside_checks.py
(issue 6oj7, 2026-04-22).
"""

import time
from typing import Any

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.riverside import (
    RiversideRequirement,
)
from app.preflight.base import BasePreflightCheck
from app.preflight.models import CheckCategory, CheckResult, CheckStatus
from app.preflight.riverside_checks._common import SeverityLevel


class RiversideEvidenceCheck(BasePreflightCheck):
    """Check requirement evidence for completed requirements.

    Verifies that completed requirements have evidence attached,
    validates evidence format and size, checks evidence file existence,
    and reports missing evidence based on requirement priority.
    """

    # Valid evidence file extensions
    VALID_EVIDENCE_EXTENSIONS = {
        # Documents
        ".pdf",
        ".doc",
        ".docx",
        ".txt",
        ".md",
        # Images
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".svg",
        ".webp",
        # Spreadsheets
        ".xls",
        ".xlsx",
        ".csv",
        # Archives
        ".zip",
        ".tar",
        ".gz",
        # External links (no extension check)
        "http",
        "https",
    }

    # Maximum evidence file size (50 MB)
    MAX_EVIDENCE_SIZE_BYTES = 50 * 1024 * 1024

    def __init__(self):
        super().__init__(
            check_id="riverside_requirement_evidence",
            name="Riverside Requirement Evidence Verification",
            category=CheckCategory.RIVERSIDE,
            description="Verify completed requirements have valid evidence attached",
            timeout_seconds=30.0,
        )

    def _get_severity_for_priority(self, priority: str) -> str:
        """Get severity level based on requirement priority.

        Args:
            priority: Requirement priority (P0, P1, P2)

        Returns:
            Severity level string
        """
        priority_map = {
            "P0": SeverityLevel.CRITICAL,
            "P1": SeverityLevel.WARNING,
            "P2": SeverityLevel.INFO,
        }
        return priority_map.get(priority, SeverityLevel.INFO)

    def _validate_evidence_format(self, evidence_url: str | None) -> dict[str, Any]:
        """Validate evidence URL format and type.

        Args:
            evidence_url: URL or path to evidence file

        Returns:
            Dictionary with validation results
        """
        if not evidence_url:
            return {
                "valid": False,
                "reason": "no_evidence_url",
                "message": "No evidence URL provided",
            }

        evidence_url_lower = evidence_url.lower()

        # Check if it's an external URL
        if evidence_url_lower.startswith(("http://", "https://")):
            return {
                "valid": True,
                "type": "external_url",
                "message": "External evidence link",
            }

        # Check file extension for local files
        import os

        _, ext = os.path.splitext(evidence_url_lower)

        if ext in self.VALID_EVIDENCE_EXTENSIONS:
            return {
                "valid": True,
                "type": "local_file",
                "extension": ext,
                "message": f"Valid evidence file ({ext})",
            }

        return {
            "valid": False,
            "type": "local_file",
            "extension": ext,
            "reason": "invalid_extension",
            "message": f"Invalid file extension: {ext}",
        }

    def _check_evidence_exists(self, evidence_url: str | None) -> dict[str, Any]:
        """Check if evidence file exists in storage.

        Args:
            evidence_url: URL or path to evidence file

        Returns:
            Dictionary with existence check results
        """
        if not evidence_url:
            return {
                "exists": False,
                "reason": "no_url",
            }

        # External URLs - assume they exist (can't check without HTTP request)
        if evidence_url.lower().startswith(("http://", "https://")):
            return {
                "exists": True,
                "type": "external",
                "note": "External URL - existence not verified",
            }

        # Local file path check
        import os

        try:
            if os.path.exists(evidence_url):
                size = os.path.getsize(evidence_url)
                return {
                    "exists": True,
                    "type": "local",
                    "size_bytes": size,
                    "size_valid": size <= self.MAX_EVIDENCE_SIZE_BYTES,
                }
            else:
                return {
                    "exists": False,
                    "type": "local",
                    "reason": "file_not_found",
                }
        except Exception as e:
            return {
                "exists": False,
                "type": "local",
                "reason": "access_error",
                "error": str(e)[:100],
            }

    async def _execute_check(self, tenant_id: str | None = None) -> CheckResult:
        """Execute evidence verification check for completed requirements."""
        start_time = time.perf_counter()
        db: Session | None = None

        try:
            from app.models.riverside import (
                RequirementStatus,
            )

            db = SessionLocal()

            # Query for completed requirements
            query = db.query(RiversideRequirement).filter(
                RiversideRequirement.status == RequirementStatus.COMPLETED.value
            )

            if tenant_id:
                query = query.filter(RiversideRequirement.tenant_id == tenant_id)

            completed_requirements = query.all()

            if not completed_requirements:
                duration_ms = (time.perf_counter() - start_time) * 1000
                return CheckResult(
                    check_id=self.check_id,
                    name=self.name,
                    category=self.category,
                    status=CheckStatus.PASS,
                    message="No completed requirements to verify",
                    details={
                        "completed_count": 0,
                        "with_evidence": 0,
                        "missing_evidence": 0,
                        "severity": SeverityLevel.INFO,
                    },
                    duration_ms=duration_ms,
                    tenant_id=tenant_id,
                )

            # Analyze each completed requirement
            evidence_results = []
            missing_evidence_items = []
            invalid_evidence_items = []
            p0_missing = []
            p1_missing = []

            for req in completed_requirements:
                # Validate evidence format
                format_check = self._validate_evidence_format(req.evidence_url)

                # Check evidence existence
                existence_check = self._check_evidence_exists(req.evidence_url)

                result = {
                    "requirement_id": req.requirement_id,
                    "title": req.title,
                    "priority": req.priority.value if req.priority else "unknown",
                    "tenant_id": req.tenant_id,
                    "evidence_url": req.evidence_url,
                    "format_valid": format_check["valid"],
                    "format_details": format_check,
                    "exists": existence_check.get("exists", False),
                    "existence_details": existence_check,
                }

                evidence_results.append(result)

                # Track issues by priority
                has_valid_evidence = format_check["valid"] and existence_check.get("exists", False)

                if not has_valid_evidence:
                    priority = req.priority.value if req.priority else "P2"

                    issue = {
                        "requirement_id": req.requirement_id,
                        "title": req.title,
                        "priority": priority,
                        "reason": (
                            "missing_url"
                            if not req.evidence_url
                            else "invalid_format"
                            if not format_check["valid"]
                            else "file_not_found"
                        ),
                    }

                    missing_evidence_items.append(issue)

                    if priority == "P0":
                        p0_missing.append(issue)
                    elif priority == "P1":
                        p1_missing.append(issue)

                elif not format_check["valid"]:
                    invalid_evidence_items.append(
                        {
                            "requirement_id": req.requirement_id,
                            "title": req.title,
                            "priority": req.priority.value if req.priority else "unknown",
                            "reason": format_check.get("reason", "unknown"),
                            "message": format_check.get("message", ""),
                        }
                    )

            # Calculate statistics
            total_completed = len(completed_requirements)
            with_evidence = total_completed - len(missing_evidence_items)
            missing_count = len(missing_evidence_items)

            duration_ms = (time.perf_counter() - start_time) * 1000

            # Determine overall status and severity
            if p0_missing:
                status = CheckStatus.FAIL
                severity = SeverityLevel.CRITICAL
                message = f"Critical: {len(p0_missing)} P0 requirements missing evidence ({missing_count} total)"
            elif p1_missing:
                status = CheckStatus.WARNING
                severity = SeverityLevel.WARNING
                message = f"Warning: {len(p1_missing)} P1 requirements missing evidence ({missing_count} total)"
            elif missing_count > 0:
                status = CheckStatus.WARNING
                severity = SeverityLevel.INFO
                message = f"{missing_count} P2 requirements missing evidence"
            elif invalid_evidence_items:
                status = CheckStatus.WARNING
                severity = SeverityLevel.WARNING
                message = f"All {total_completed} completed requirements have evidence, but {len(invalid_evidence_items)} have format issues"
            else:
                status = CheckStatus.PASS
                severity = SeverityLevel.INFO
                message = f"All {total_completed} completed requirements have valid evidence"

            # Build recommendations
            recommendations = []

            if p0_missing:
                req_ids = ", ".join([i["requirement_id"] for i in p0_missing[:3]])
                recommendations.append(
                    f"CRITICAL: Immediately add evidence for P0 requirements: {req_ids}"
                    + ("..." if len(p0_missing) > 3 else "")
                )

            if p1_missing:
                req_ids = ", ".join([i["requirement_id"] for i in p1_missing[:3]])
                recommendations.append(
                    f"High Priority: Add evidence for P1 requirements: {req_ids}"
                    + ("..." if len(p1_missing) > 3 else "")
                )

            if invalid_evidence_items:
                recommendations.append(
                    "Review evidence with invalid formats - use PDF, images, or valid URLs"
                )

            if missing_evidence_items:
                recommendations.append(
                    "Upload evidence via API: POST /api/v1/riverside/requirements/{id}/evidence"
                )
                recommendations.append("Ensure evidence files are accessible and under 50MB limit")

            return CheckResult(
                check_id=self.check_id,
                name=self.name,
                category=self.category,
                status=status,
                message=message,
                details={
                    "completed_count": total_completed,
                    "with_evidence": with_evidence,
                    "missing_evidence": missing_count,
                    "p0_missing": len(p0_missing),
                    "p1_missing": len(p1_missing),
                    "p2_missing": missing_count - len(p0_missing) - len(p1_missing),
                    "invalid_format_count": len(invalid_evidence_items),
                    "evidence_results": evidence_results[:10],  # Limit details
                    "missing_evidence_items": missing_evidence_items[:10],
                    "invalid_evidence_items": invalid_evidence_items[:10],
                    "severity": severity,
                },
                duration_ms=duration_ms,
                recommendations=recommendations
                if recommendations
                else ["Evidence validation passed"],
                tenant_id=tenant_id,
            )

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            return CheckResult(
                check_id=self.check_id,
                name=self.name,
                category=self.category,
                status=CheckStatus.FAIL,
                message=f"Evidence verification check failed: {str(e)}",
                details={
                    "error_type": type(e).__name__,
                    "severity": SeverityLevel.CRITICAL,
                },
                duration_ms=duration_ms,
                recommendations=[
                    "Verify database connectivity to riverside_requirements table",
                    "Check that RequirementStatus and RequirementPriority enums are properly defined",
                    "Review application logs for detailed error information",
                ],
                tenant_id=tenant_id,
            )
        finally:
            if db:
                db.close()


async def check_riverside_requirement_evidence(
    tenant_id: str | None = None,
) -> CheckResult:
    """Check requirement evidence for completed requirements.

    Args:
        tenant_id: Optional tenant ID for tenant-specific checks

    Returns:
        CheckResult with evidence verification status
    """
    check = RiversideEvidenceCheck()
    return await check.run(tenant_id=tenant_id)
