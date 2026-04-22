"""Public API for the riverside preflight checks package.

Re-exports every name that was importable from the former monolithic
``app.preflight.riverside_checks`` module so external callers (tests,
app.preflight.__init__, app.preflight.checks) keep working without a
code change.
"""

from __future__ import annotations

from app.preflight.riverside_checks._common import SeverityLevel
from app.preflight.riverside_checks._runner import (
    get_riverside_checks,
    run_all_riverside_checks,
)
from app.preflight.riverside_checks.api_endpoint import (
    RiversideAPIEndpointCheck,
    check_riverside_api_endpoints,
)
from app.preflight.riverside_checks.azure_ad_permissions import (
    RiversideAzureADPermissionsCheck,
    check_riverside_azure_ad_permissions,
)
from app.preflight.riverside_checks.database import (
    RiversideDatabaseCheck,
    check_riverside_database,
)
from app.preflight.riverside_checks.evidence import (
    RiversideEvidenceCheck,
    check_riverside_requirement_evidence,
)
from app.preflight.riverside_checks.mfa_data_source import (
    RiversideMFADataSourceCheck,
    check_riverside_mfa_data_source,
)
from app.preflight.riverside_checks.scheduler import (
    RiversideSchedulerCheck,
    check_riverside_scheduler,
)

__all__ = [
    "RiversideAPIEndpointCheck",
    "RiversideAzureADPermissionsCheck",
    "RiversideDatabaseCheck",
    "RiversideEvidenceCheck",
    "RiversideMFADataSourceCheck",
    "RiversideSchedulerCheck",
    "SeverityLevel",
    "check_riverside_api_endpoints",
    "check_riverside_azure_ad_permissions",
    "check_riverside_database",
    "check_riverside_mfa_data_source",
    "check_riverside_requirement_evidence",
    "check_riverside_scheduler",
    "get_riverside_checks",
    "run_all_riverside_checks",
]
