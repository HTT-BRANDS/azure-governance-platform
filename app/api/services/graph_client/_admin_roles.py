"""Admin-roles mixin for GraphClient: directory roles, PIM, assignments.

Split from the monolithic graph_client.py (issue 6oj7, 2026-04-22).
This is a pure mixin — it relies on self.tenant_id and self._request
being provided by _GraphClientCore via MRO composition.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from app.api.services.graph_client._constants import (
    ADMIN_ROLE_TEMPLATE_IDS,
    GRAPH_API_BASE,
    GRAPH_BETA_API_BASE,
)
from app.api.services.graph_client._models import (
    AdminRoleSummary,
    DirectoryRole,
    PrivilegedAccessAssignment,
    RoleAssignment,
)
from app.core.circuit_breaker import GRAPH_API_BREAKER, circuit_breaker
from app.core.config import get_settings
from app.core.retry import GRAPH_API_POLICY, retry_with_backoff

logger = logging.getLogger(__name__)
settings = get_settings()


class _AdminRolesMixin:
    """Mixin: directory roles, PIM role assignments, admin role summary."""

    @circuit_breaker(GRAPH_API_BREAKER)
    @retry_with_backoff(GRAPH_API_POLICY)
    async def get_directory_roles(self) -> list[dict]:
        """Get all directory roles with members."""
        endpoint = "/directoryRoles"
        params = {"$expand": "members"}
        data = await self._request("GET", endpoint, params)
        return data.get("value", [])

    @circuit_breaker(GRAPH_API_BREAKER)
    @retry_with_backoff(GRAPH_API_POLICY)
    async def get_privileged_role_assignments(self) -> list[dict]:
        """Get privileged role assignments."""
        endpoint = "/roleManagement/directory/roleAssignments"
        params = {"$expand": "principal,roleDefinition"}
        data = await self._request("GET", endpoint, params)
        return data.get("value", [])

    @circuit_breaker(GRAPH_API_BREAKER)
    @retry_with_backoff(GRAPH_API_POLICY)
    async def get_directory_role_definitions(
        self,
        include_built_in: bool = True,
    ) -> list[DirectoryRole]:
        """Get all directory role definitions.

        Retrieves Azure AD built-in and custom directory roles.

        Args:
            include_built_in: Include built-in roles (default: True)

        Returns:
            List of DirectoryRole objects
        """
        endpoint = "/directoryRoles"
        params: dict[str, Any] = {
            "$select": "id,displayName,description,roleTemplateId,isBuiltIn",
        }

        roles: list[DirectoryRole] = []
        current_endpoint = endpoint

        while current_endpoint:
            data = await self._request("GET", current_endpoint, params)
            items = data.get("value", [])

            for role in items:
                is_built_in = role.get("isBuiltIn", True)
                if not include_built_in and is_built_in:
                    continue

                roles.append(
                    DirectoryRole(
                        role_id=role.get("id", ""),
                        display_name=role.get("displayName", ""),
                        description=role.get("description", ""),
                        role_template_id=role.get("roleTemplateId", ""),
                        is_built_in=is_built_in,
                    )
                )

            # Handle pagination
            next_link = data.get("@odata.nextLink")
            if next_link:
                current_endpoint = next_link.replace(GRAPH_API_BASE, "")
                params = None
                await asyncio.sleep(0.05)  # Rate limiting
            else:
                current_endpoint = None

        return roles

    @circuit_breaker(GRAPH_API_BREAKER)
    @retry_with_backoff(GRAPH_API_POLICY)
    async def get_role_assignments_paginated(
        self,
        batch_size: int = 100,
        include_inactive: bool = False,
    ) -> list[RoleAssignment]:
        """Get all directory role assignments with full details.

        Retrieves role assignments including principal and role definition details.
        Handles pagination for large result sets.

        Args:
            batch_size: Number of assignments per page (max 999)
            include_inactive: Include inactive assignments

        Returns:
            List of RoleAssignment objects
        """
        endpoint = "/roleManagement/directory/roleAssignments"
        params: dict[str, Any] = {
            "$top": min(batch_size, 999),
            "$expand": "principal($select=id,displayName,userPrincipalName,appId,userType),roleDefinition($select=id,displayName,description,templateId,isBuiltIn)",
        }

        assignments: list[RoleAssignment] = []
        current_endpoint = endpoint

        while current_endpoint:
            data = await self._request("GET", current_endpoint, params)
            items = data.get("value", [])

            for assignment in items:
                principal = assignment.get("principal", {})
                role_def = assignment.get("roleDefinition", {})

                # Determine principal type and name
                principal_type = principal.get("@odata.type", "").replace("#microsoft.graph.", "")
                if "user" in principal_type.lower():
                    principal_type = "User"
                    display_name = principal.get("userPrincipalName") or principal.get(
                        "displayName", ""
                    )
                elif "servicePrincipal" in principal_type.lower():
                    principal_type = "ServicePrincipal"
                    display_name = principal.get("appId") or principal.get("displayName", "")
                elif "group" in principal_type.lower():
                    principal_type = "Group"
                    display_name = principal.get("displayName", "")
                else:
                    principal_type = "Unknown"
                    display_name = principal.get("displayName", "Unknown")

                # Determine scope (simplified for directory-scoped roles)
                scope_type = "Directory"
                scope_id = None

                # Check for scope information if available
                directory_scope = assignment.get("directoryScope", {})
                app_scope = assignment.get("appScope", {})

                if directory_scope:
                    scope_id = directory_scope.get("id")
                elif app_scope:
                    scope_type = "Application"
                    scope_id = app_scope.get("id")

                # Determine assignment type
                assignment_type = "Direct"
                if principal_type == "Group":
                    assignment_type = "Group"

                role_template_id = role_def.get("templateId", "")
                if isinstance(role_template_id, dict):
                    # Handle OData metadata issue
                    role_template_id = ""

                assignments.append(
                    RoleAssignment(
                        assignment_id=assignment.get("id", ""),
                        principal_id=principal.get("id", ""),
                        principal_type=principal_type,
                        principal_display_name=display_name,
                        role_definition_id=role_def.get("id", ""),
                        role_name=role_def.get("displayName", ""),
                        role_template_id=role_template_id,
                        scope_type=scope_type,
                        scope_id=scope_id,
                        created_date_time=assignment.get("createdDateTime"),
                        assignment_type=assignment_type,
                    )
                )

            # Handle pagination
            next_link = data.get("@odata.nextLink")
            if next_link:
                current_endpoint = next_link.replace(GRAPH_API_BASE, "")
                params = None
                await asyncio.sleep(0.1)  # Rate limiting between pages
            else:
                current_endpoint = None

        return assignments

    @circuit_breaker(GRAPH_API_BREAKER)
    @retry_with_backoff(GRAPH_API_POLICY)
    async def get_pim_role_assignments(
        self,
        batch_size: int = 100,
        include_eligible: bool = True,
        include_active: bool = True,
    ) -> list[PrivilegedAccessAssignment]:
        """Get PIM (Privileged Identity Management) role assignments.

        Uses the beta API for PIM role assignment schedules.

        Args:
            batch_size: Number of assignments per page
            include_eligible: Include eligible (not yet activated) assignments
            include_active: Include currently active assignments

        Returns:
            List of PrivilegedAccessAssignment objects
        """
        assignments: list[PrivilegedAccessAssignment] = []

        # Get active assignments (beta endpoint)
        if include_active:
            active_assignments = await self._get_pim_assignments_by_type("active", batch_size)
            assignments.extend(active_assignments)

        # Get eligible assignments (beta endpoint)
        if include_eligible:
            eligible_assignments = await self._get_pim_assignments_by_type("eligible", batch_size)
            assignments.extend(eligible_assignments)

        return assignments

    async def _get_pim_assignments_by_type(
        self,
        assignment_type: str,
        batch_size: int,
    ) -> list[PrivilegedAccessAssignment]:
        """Helper to get PIM assignments of a specific type."""
        endpoint = f"/roleManagement/directory/roleAssignmentSchedules/{assignment_type}"
        params: dict[str, Any] = {
            "$top": min(batch_size, 999),
            "$expand": "principal($select=id,displayName,userPrincipalName,appId),roleDefinition($select=id,displayName,templateId)",
        }

        assignments: list[PrivilegedAccessAssignment] = []
        current_endpoint = endpoint

        while current_endpoint:
            try:
                # Use beta API for PIM
                token = await self._get_token()
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                }

                async with httpx.AsyncClient() as client:
                    url = f"{GRAPH_BETA_API_BASE}{current_endpoint}"
                    response = await client.request(
                        method="GET",
                        url=url,
                        headers=headers,
                        params=params,
                        timeout=30.0,
                    )
                    response.raise_for_status()
                    data = response.json()

            except Exception as e:
                logger.warning(f"PIM {assignment_type} assignments query failed: {e}")
                break

            items = data.get("value", [])

            for assignment in items:
                principal = assignment.get("principal", {})
                role_def = assignment.get("roleDefinition", {})

                # Determine principal type
                principal_type = principal.get("@odata.type", "").replace("#microsoft.graph.", "")
                if "user" in principal_type.lower():
                    principal_type = "User"
                    display_name = principal.get("userPrincipalName") or principal.get(
                        "displayName", ""
                    )
                elif "servicePrincipal" in principal_type.lower():
                    principal_type = "ServicePrincipal"
                    display_name = principal.get("appId") or principal.get("displayName", "")
                elif "group" in principal_type.lower():
                    principal_type = "Group"
                    display_name = principal.get("displayName", "")
                else:
                    principal_type = "Unknown"
                    display_name = principal.get("displayName", "Unknown")

                # Calculate duration from start/end times
                start_time = assignment.get("startDateTime")
                end_time = assignment.get("endDateTime")
                duration = None
                if start_time and end_time:
                    try:
                        from datetime import datetime

                        start = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                        end = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
                        duration = str(end - start)
                    except Exception:
                        duration = None

                assignments.append(
                    PrivilegedAccessAssignment(
                        assignment_id=assignment.get("id", ""),
                        principal_id=principal.get("id", ""),
                        principal_type=principal_type,
                        principal_display_name=display_name,
                        role_definition_id=role_def.get("id", ""),
                        role_name=role_def.get("displayName", ""),
                        assignment_state=assignment_type,
                        start_date_time=start_time,
                        end_date_time=end_time,
                        duration=duration,
                    )
                )

            # Handle pagination
            next_link = data.get("@odata.nextLink")
            if next_link:
                current_endpoint = next_link.replace(GRAPH_BETA_API_BASE, "")
                params = None
                await asyncio.sleep(0.1)
            else:
                current_endpoint = None

        return assignments

    @circuit_breaker(GRAPH_API_BREAKER)
    @retry_with_backoff(GRAPH_API_POLICY)
    async def get_service_principal_role_assignments(
        self,
        batch_size: int = 100,
    ) -> list[RoleAssignment]:
        """Get role assignments specifically for service principals.

        Retrieves service principals with admin role assignments.

        Args:
            batch_size: Number of assignments per page

        Returns:
            List of RoleAssignment objects for service principals
        """
        # Get all role assignments and filter for service principals
        all_assignments = await self.get_role_assignments_paginated(batch_size)
        return [a for a in all_assignments if a.principal_type == "ServicePrincipal"]

    async def get_admin_role_summary(
        self,
        batch_size: int = 100,
    ) -> AdminRoleSummary:
        """Get comprehensive summary of admin roles in the tenant.

        Aggregates directory roles, role assignments, and PIM data to provide
        a complete picture of privileged access.

        Args:
            batch_size: Number of items per page for paginated queries

        Returns:
            AdminRoleSummary with complete admin role statistics
        """
        # Get role definitions
        role_defs = await self.get_directory_role_definitions()
        {r.role_id: r for r in role_defs}

        # Get all role assignments
        assignments = await self.get_role_assignments_paginated(batch_size)

        # Get PIM assignments
        try:
            pim_assignments = await self.get_pim_role_assignments(batch_size)
        except Exception as e:
            logger.warning(f"Failed to get PIM assignments: {e}")
            pim_assignments = []

        # Categorize by admin type
        privileged_users: list[dict[str, Any]] = []
        privileged_sps: list[dict[str, Any]] = []
        roles_with_members: set[str] = set()

        global_admin_count = 0
        security_admin_count = 0
        privileged_role_admin_count = 0
        other_admin_count = 0

        for assignment in assignments:
            role_template_id = assignment.role_template_id
            is_privileged = role_template_id in ADMIN_ROLE_TEMPLATE_IDS

            if not is_privileged:
                continue

            roles_with_members.add(assignment.role_definition_id)

            # Count by admin type
            if role_template_id == "62e90394-69f5-4237-9190-012177145e10":
                global_admin_count += 1
            elif role_template_id == "194ae4cb-b126-40b2-bd5b-6091b380977d":
                security_admin_count += 1
            elif role_template_id == "e8611ab8-c189-46e8-94e1-60213ab1f814":
                privileged_role_admin_count += 1
            else:
                other_admin_count += 1

            # Build user/SP lists
            if assignment.principal_type == "User":
                privileged_users.append(
                    {
                        "principal_id": assignment.principal_id,
                        "principal_display_name": assignment.principal_display_name,
                        "role_name": assignment.role_name,
                        "role_template_id": role_template_id,
                        "scope_type": assignment.scope_type,
                        "is_permanent": assignment.assignment_type == "Direct",
                    }
                )
            elif assignment.principal_type == "ServicePrincipal":
                privileged_sps.append(
                    {
                        "principal_id": assignment.principal_id,
                        "principal_display_name": assignment.principal_display_name,
                        "role_name": assignment.role_name,
                        "role_template_id": role_template_id,
                    }
                )

        # Find roles without members
        all_role_ids = {r.role_id for r in role_defs if r.is_built_in}
        roles_without_members = list(all_role_ids - roles_with_members)

        # Format PIM assignments
        formatted_pim = [
            {
                "principal_id": p.principal_id,
                "principal_display_name": p.principal_display_name,
                "principal_type": p.principal_type,
                "role_name": p.role_name,
                "assignment_state": p.assignment_state,
                "start_date_time": p.start_date_time,
                "end_date_time": p.end_date_time,
                "duration": p.duration,
            }
            for p in pim_assignments
        ]

        return AdminRoleSummary(
            tenant_id=self.tenant_id,
            total_roles=len(role_defs),
            total_assignments=len(assignments),
            privileged_users=privileged_users,
            privileged_service_principals=privileged_sps,
            pim_assignments=formatted_pim,
            roles_without_members=roles_without_members,
            global_admin_count=global_admin_count,
            security_admin_count=security_admin_count,
            privileged_role_admin_count=privileged_role_admin_count,
            other_admin_count=other_admin_count,
        )
