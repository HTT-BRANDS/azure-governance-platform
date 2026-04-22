"""Riverside preflight check: RiversideDatabaseCheck.

Split from the monolithic app/preflight/riverside_checks.py
(issue 6oj7, 2026-04-22).
"""

import time

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.riverside import (
    RiversideCompliance,
    RiversideMFA,
    RiversideRequirement,
)
from app.preflight.base import BasePreflightCheck
from app.preflight.models import CheckCategory, CheckResult, CheckStatus
from app.preflight.riverside_checks._common import SeverityLevel


class RiversideDatabaseCheck(BasePreflightCheck):
    """Check connectivity to Riverside database tables.

    Validates that the riverside_compliance, riverside_mfa, and
    riverside_requirements tables are accessible and contain expected data.
    """

    def __init__(self):
        super().__init__(
            check_id="riverside_database_connectivity",
            name="Riverside Database Connectivity",
            category=CheckCategory.RIVERSIDE,
            description="Verify database connectivity to all Riverside tables",
            timeout_seconds=15.0,
        )

    async def _execute_check(self, tenant_id: str | None = None) -> CheckResult:
        """Execute database connectivity check for Riverside tables."""
        start_time = time.perf_counter()
        db: Session | None = None

        try:
            db = SessionLocal()
            table_status = {}
            errors = []

            # Check riverside_compliance table
            try:
                compliance_count = db.query(RiversideCompliance).count()
                table_status["riverside_compliance"] = {
                    "accessible": True,
                    "record_count": compliance_count,
                }
            except Exception as e:
                table_status["riverside_compliance"] = {
                    "accessible": False,
                    "error": str(e)[:100],
                }
                errors.append(f"riverside_compliance: {str(e)[:100]}")

            # Check riverside_mfa table
            try:
                mfa_count = db.query(RiversideMFA).count()
                table_status["riverside_mfa"] = {
                    "accessible": True,
                    "record_count": mfa_count,
                }
            except Exception as e:
                table_status["riverside_mfa"] = {
                    "accessible": False,
                    "error": str(e)[:100],
                }
                errors.append(f"riverside_mfa: {str(e)[:100]}")

            # Check riverside_requirements table
            try:
                requirements_count = db.query(RiversideRequirement).count()
                table_status["riverside_requirements"] = {
                    "accessible": True,
                    "record_count": requirements_count,
                }
            except Exception as e:
                table_status["riverside_requirements"] = {
                    "accessible": False,
                    "error": str(e)[:100],
                }
                errors.append(f"riverside_requirements: {str(e)[:100]}")

            # Check for recent data if tenant_id provided
            recent_data_check = {}
            if tenant_id:
                try:
                    # Check for recent compliance data
                    recent_compliance = (
                        db.query(RiversideCompliance)
                        .filter(RiversideCompliance.tenant_id == tenant_id)
                        .order_by(RiversideCompliance.updated_at.desc())
                        .first()
                    )
                    recent_data_check["compliance_data"] = (
                        "found" if recent_compliance else "not_found"
                    )

                    # Check for recent MFA data
                    recent_mfa = (
                        db.query(RiversideMFA)
                        .filter(RiversideMFA.tenant_id == tenant_id)
                        .order_by(RiversideMFA.snapshot_date.desc())
                        .first()
                    )
                    recent_data_check["mfa_data"] = "found" if recent_mfa else "not_found"

                    # Check for requirements
                    recent_req = (
                        db.query(RiversideRequirement)
                        .filter(RiversideRequirement.tenant_id == tenant_id)
                        .first()
                    )
                    recent_data_check["requirements_data"] = "found" if recent_req else "not_found"

                except Exception as e:
                    recent_data_check["error"] = str(e)[:100]

            duration_ms = (time.perf_counter() - start_time) * 1000

            if errors:
                return CheckResult(
                    check_id=self.check_id,
                    name=self.name,
                    category=self.category,
                    status=CheckStatus.FAIL,
                    message=f"Database connectivity issues: {'; '.join(errors)}",
                    details={
                        "table_status": table_status,
                        "recent_data_check": recent_data_check,
                        "severity": SeverityLevel.CRITICAL,
                    },
                    duration_ms=duration_ms,
                    recommendations=[
                        "Verify database migrations have been run: alembic upgrade head",
                        "Check database file permissions and disk space",
                        "Review SQLAlchemy model definitions for table schema mismatches",
                    ],
                    tenant_id=tenant_id,
                )

            total_records = sum(
                status.get("record_count", 0)
                for status in table_status.values()
                if status.get("accessible")
            )

            return CheckResult(
                check_id=self.check_id,
                name=self.name,
                category=self.category,
                status=CheckStatus.PASS,
                message=f"All Riverside tables accessible ({total_records} total records)",
                details={
                    "table_status": table_status,
                    "recent_data_check": recent_data_check,
                    "severity": SeverityLevel.INFO,
                },
                duration_ms=duration_ms,
                tenant_id=tenant_id,
            )

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            return CheckResult(
                check_id=self.check_id,
                name=self.name,
                category=self.category,
                status=CheckStatus.FAIL,
                message=f"Database connectivity check failed: {str(e)}",
                details={
                    "error_type": type(e).__name__,
                    "severity": SeverityLevel.CRITICAL,
                },
                duration_ms=duration_ms,
                recommendations=[
                    "Check database connection string configuration",
                    "Verify database server is running and accessible",
                    "Review application logs for connection errors",
                ],
                tenant_id=tenant_id,
            )
        finally:
            if db:
                db.close()


async def check_riverside_database(tenant_id: str | None = None) -> CheckResult:
    """Check Riverside database connectivity.

    Args:
        tenant_id: Optional tenant ID for tenant-specific checks

    Returns:
        CheckResult with database connectivity status
    """
    check = RiversideDatabaseCheck()
    return await check.run(tenant_id=tenant_id)
