"""Dataclasses and exceptions shared across the graph_client package.

Split from the monolithic graph_client.py (issue 6oj7, 2026-04-22).
All types are part of the public API and re-exported from __init__.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class MFAMethodDetails:
    """MFA method details for a user."""

    method_type: str
    is_default: bool
    is_enabled: bool
    phone_number: str | None = None
    email_address: str | None = None
    display_name: str | None = None
    app_id: str | None = None


@dataclass
class UserMFAStatus:
    """Complete MFA status for a user."""

    user_id: str
    user_principal_name: str
    display_name: str
    is_mfa_registered: bool
    methods_registered: list[str]
    auth_methods: list[MFAMethodDetails]
    default_method: str | None
    last_updated: str | None


@dataclass
class TenantMFASummary:
    """MFA summary statistics for a tenant."""

    tenant_id: str
    total_users: int
    mfa_registered_users: int
    mfa_coverage_percentage: float
    admin_accounts_total: int
    admin_accounts_mfa: int
    admin_mfa_percentage: float
    method_breakdown: dict[str, int]
    users_without_mfa: list[dict[str, Any]]


@dataclass
class DirectoryRole:
    """Azure AD directory role definition."""

    role_id: str
    display_name: str
    description: str
    role_template_id: str
    is_built_in: bool


@dataclass
class RoleAssignment:
    """Azure AD role assignment with principal and role details."""

    assignment_id: str
    principal_id: str
    principal_type: str  # User, Group, ServicePrincipal
    principal_display_name: str
    role_definition_id: str
    role_name: str
    role_template_id: str
    scope_type: str  # Directory, Subscription, ResourceGroup
    scope_id: str | None
    created_date_time: str | None
    assignment_type: str  # Direct, Group, PIM


@dataclass
class PrivilegedAccessAssignment:
    """PIM (Privileged Identity Management) role assignment."""

    assignment_id: str
    principal_id: str
    principal_type: str
    principal_display_name: str
    role_definition_id: str
    role_name: str
    assignment_state: str  # active, eligible
    start_date_time: str | None
    end_date_time: str | None
    duration: str | None  # For time-bound assignments


@dataclass
class AdminRoleSummary:
    """Summary of admin roles and privileged access in a tenant."""

    tenant_id: str
    total_roles: int
    total_assignments: int
    privileged_users: list[dict[str, Any]]
    privileged_service_principals: list[dict[str, Any]]
    pim_assignments: list[dict[str, Any]]
    roles_without_members: list[str]
    global_admin_count: int
    security_admin_count: int
    privileged_role_admin_count: int
    other_admin_count: int


class MFAError(Exception):
    """Exception raised when MFA data collection fails."""

    def __init__(self, message: str, user_id: str | None = None) -> None:
        super().__init__(message)
        self.user_id = user_id
