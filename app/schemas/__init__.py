"""Pydantic schemas for API request/response validation."""

from app.schemas.compliance import (
    ComplianceScore,
    ComplianceSummary,
    PolicyStatus,
)
from app.schemas.cost import (
    CostAnomaly,
    CostByTenant,
    CostSummary,
    CostTrend,
)
from app.schemas.identity import (
    GuestAccount,
    IdentitySummary,
    PrivilegedAccount,
)
from app.schemas.resource import (
    ResourceInventory,
    ResourceItem,
    TaggingCompliance,
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
    # Dashboard/Summary
    RiversideDashboardSummary,
    RiversideTenantSummary,
    # Riverside Device Compliance
    RiversideDeviceComplianceBase,
    RiversideDeviceComplianceResponse,
    # Riverside MFA
    RiversideMFABase,
    RiversideMFAResponse,
    # Pagination and Bulk Operations
    PaginatedResponse,
    # Riverside Requirements
    RiversideRequirementBase,
    RiversideRequirementFilter,
    RiversideRequirementResponse,
    RiversideRequirementUpdate,
    # Bulk Operations
    BulkUpdateItem,
    BulkUpdateRequest,
    BulkUpdateResponse,
    # Riverside Threat Data
    RiversideThreatDataBase,
    RiversideThreatDataResponse,
)
from app.schemas.tenant import (
    SubscriptionResponse,
    TenantCreate,
    TenantResponse,
    TenantUpdate,
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
