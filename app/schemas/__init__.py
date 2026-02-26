"""Pydantic schemas for API request/response validation."""

from app.schemas.cost import (
    CostSummary,
    CostByTenant,
    CostTrend,
    CostAnomaly,
)
from app.schemas.compliance import (
    ComplianceScore,
    ComplianceSummary,
    PolicyStatus,
)
from app.schemas.resource import (
    ResourceItem,
    ResourceInventory,
    TaggingCompliance,
)
from app.schemas.identity import (
    IdentitySummary,
    PrivilegedAccount,
    GuestAccount,
)
from app.schemas.tenant import (
    TenantCreate,
    TenantUpdate,
    TenantResponse,
    SubscriptionResponse,
)
from app.schemas.riverside import (
    # Enums
    RequirementCategory,
    RequirementPriority,
    RequirementStatus,
    # Riverside Compliance
    RiversideComplianceBase,
    RiversideComplianceResponse,
    RiversideComplianceUpdate,
    # Riverside MFA
    RiversideMFABase,
    RiversideMFAResponse,
    # Riverside Requirements
    RiversideRequirementBase,
    RiversideRequirementResponse,
    RiversideRequirementUpdate,
    RiversideRequirementFilter,
    # Riverside Device Compliance
    RiversideDeviceComplianceBase,
    RiversideDeviceComplianceResponse,
    # Riverside Threat Data
    RiversideThreatDataBase,
    RiversideThreatDataResponse,
    # Dashboard/Summary
    RiversideDashboardSummary,
    RiversideTenantSummary,
    # Pagination and Bulk Operations
    PaginatedResponse,
    BulkUpdateItem,
    BulkUpdateRequest,
    BulkUpdateResponse,
)

__all__ = [
    # Cost
    "CostSummary",
    "CostByTenant",
    "CostTrend",
    "CostAnomaly",
    # Compliance
    "ComplianceScore",
    "ComplianceSummary",
    "PolicyStatus",
    # Resource
    "ResourceItem",
    "ResourceInventory",
    "TaggingCompliance",
    # Identity
    "IdentitySummary",
    "PrivilegedAccount",
    "GuestAccount",
    # Tenant
    "TenantCreate",
    "TenantUpdate",
    "TenantResponse",
    "SubscriptionResponse",
    # Riverside - Enums
    "RequirementCategory",
    "RequirementPriority",
    "RequirementStatus",
    # Riverside - Compliance
    "RiversideComplianceBase",
    "RiversideComplianceResponse",
    "RiversideComplianceUpdate",
    # Riverside - MFA
    "RiversideMFABase",
    "RiversideMFAResponse",
    # Riverside - Requirements
    "RiversideRequirementBase",
    "RiversideRequirementResponse",
    "RiversideRequirementUpdate",
    "RiversideRequirementFilter",
    # Riverside - Device Compliance
    "RiversideDeviceComplianceBase",
    "RiversideDeviceComplianceResponse",
    # Riverside - Threat Data
    "RiversideThreatDataBase",
    "RiversideThreatDataResponse",
    # Riverside - Dashboard/Summary
    "RiversideDashboardSummary",
    "RiversideTenantSummary",
    # Riverside - Pagination and Bulk Operations
    "PaginatedResponse",
    "BulkUpdateItem",
    "BulkUpdateRequest",
    "BulkUpdateResponse",
]
