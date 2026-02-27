"""Database models module."""

from app.models.compliance import ComplianceSnapshot, PolicyState
from app.models.cost import CostAnomaly, CostSnapshot
from app.models.identity import IdentitySnapshot, PrivilegedUser
from app.models.monitoring import Alert, SyncJobLog, SyncJobMetrics
from app.models.notifications import NotificationLog
from app.models.resource import IdleResource, Resource, ResourceTag
from app.models.recommendation import Recommendation
from app.models.riverside import (
    RequirementCategory,
    RequirementPriority,
    RequirementStatus,
    RiversideCompliance,
    RiversideDeviceCompliance,
    RiversideMFA,
    RiversideRequirement,
    RiversideThreatData,
)
from app.models.dmarc import (
    DMARCRecord,
    DKIMRecord,
    DMARCReport,
    DMARCAlert,
)
from app.models.sync import SyncJob
from app.models.tenant import Subscription, Tenant, UserTenant

__all__ = [
    "Tenant",
    "Subscription",
    "UserTenant",
    "CostSnapshot",
    "CostAnomaly",
    "ComplianceSnapshot",
    "PolicyState",
    "Resource",
    "ResourceTag",
    "IdleResource",
    "IdentitySnapshot",
    "PrivilegedUser",
    "SyncJob",
    # Monitoring models
    "SyncJobLog",
    "SyncJobMetrics",
    "Alert",
    "NotificationLog",
    # Recommendation models
    "Recommendation",
    # Riverside models
    "RequirementCategory",
    "RequirementPriority",
    "RequirementStatus",
    "RiversideCompliance",
    "RiversideDeviceCompliance",
    "RiversideMFA",
    "RiversideRequirement",
    "RiversideThreatData",
    # DMARC/DKIM models
    "DMARCRecord",
    "DKIMRecord",
    "DMARCReport",
    "DMARCAlert",
]
