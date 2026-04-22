"""Riverside preflight check: RiversideAPIEndpointCheck.

Split from the monolithic app/preflight/riverside_checks.py
(issue 6oj7, 2026-04-22).
"""

import time

import httpx

from app.core.config import get_settings
from app.preflight.base import BasePreflightCheck
from app.preflight.models import CheckCategory, CheckResult, CheckStatus
from app.preflight.riverside_checks._common import SeverityLevel


class RiversideAPIEndpointCheck(BasePreflightCheck):
    """Check Riverside API endpoint availability.

    Validates that all Riverside API endpoints are accessible and
    returning expected responses.
    """

    def __init__(self):
        super().__init__(
            check_id="riverside_api_endpoints",
            name="Riverside API Endpoint Availability",
            category=CheckCategory.RIVERSIDE,
            description="Verify all Riverside API endpoints are accessible",
            timeout_seconds=20.0,
        )

    async def _execute_check(self, tenant_id: str | None = None) -> CheckResult:
        """Execute API endpoint availability check."""
        start_time = time.perf_counter()
        settings = get_settings()

        # Define endpoints to check
        endpoints = [
            {
                "name": "Riverside Summary",
                "path": "/api/v1/riverside/summary",
                "method": "GET",
            },
            {
                "name": "Riverside MFA Status",
                "path": "/api/v1/riverside/mfa-status",
                "method": "GET",
            },
            {
                "name": "Riverside Maturity Scores",
                "path": "/api/v1/riverside/maturity-scores",
                "method": "GET",
            },
            {
                "name": "Riverside Requirements",
                "path": "/api/v1/riverside/requirements",
                "method": "GET",
            },
            {
                "name": "Riverside Gaps",
                "path": "/api/v1/riverside/gaps",
                "method": "GET",
            },
        ]

        results = {}
        failed_endpoints = []

        # Build base URL
        base_url = getattr(settings, "app_base_url", "http://localhost:8000")
        if not base_url:
            base_url = "http://localhost:8000"

        async with httpx.AsyncClient(timeout=10.0) as client:
            for endpoint in endpoints:
                try:
                    url = f"{base_url}{endpoint['path']}"
                    response = await client.request(
                        method=endpoint["method"],
                        url=url,
                        follow_redirects=True,
                    )

                    # Consider 200-499 as "accessible" (even auth errors mean endpoint exists)
                    is_accessible = 200 <= response.status_code < 500

                    results[endpoint["name"]] = {
                        "accessible": is_accessible,
                        "status_code": response.status_code,
                        "response_time_ms": response.elapsed.total_seconds() * 1000
                        if hasattr(response, "elapsed")
                        else None,
                    }

                    if not is_accessible:
                        failed_endpoints.append(endpoint["name"])

                except Exception as e:
                    results[endpoint["name"]] = {
                        "accessible": False,
                        "error": str(e)[:100],
                    }
                    failed_endpoints.append(endpoint["name"])

        duration_ms = (time.perf_counter() - start_time) * 1000

        accessible_count = sum(1 for r in results.values() if r.get("accessible"))

        if failed_endpoints:
            severity = SeverityLevel.CRITICAL if accessible_count == 0 else SeverityLevel.WARNING
            status = CheckStatus.FAIL if accessible_count == 0 else CheckStatus.WARNING

            return CheckResult(
                check_id=self.check_id,
                name=self.name,
                category=self.category,
                status=status,
                message=f"API endpoint issues: {len(failed_endpoints)} of {len(endpoints)} endpoints failed",
                details={
                    "endpoint_results": results,
                    "failed_endpoints": failed_endpoints,
                    "base_url": base_url,
                    "severity": severity,
                },
                duration_ms=duration_ms,
                recommendations=[
                    "Verify the application is running and accessible",
                    "Check that all Riverside API routes are registered in FastAPI",
                    "Review reverse proxy/load balancer configuration",
                    "Check authentication middleware is not blocking health checks",
                ],
                tenant_id=tenant_id,
            )

        return CheckResult(
            check_id=self.check_id,
            name=self.name,
            category=self.category,
            status=CheckStatus.PASS,
            message=f"All {len(endpoints)} Riverside API endpoints accessible",
            details={
                "endpoint_results": results,
                "base_url": base_url,
                "severity": SeverityLevel.INFO,
            },
            duration_ms=duration_ms,
            tenant_id=tenant_id,
        )


async def check_riverside_api_endpoints(tenant_id: str | None = None) -> CheckResult:
    """Check Riverside API endpoint availability.

    Args:
        tenant_id: Optional tenant ID for tenant-specific checks

    Returns:
        CheckResult with API endpoint status
    """
    check = RiversideAPIEndpointCheck()
    return await check.run(tenant_id=tenant_id)
