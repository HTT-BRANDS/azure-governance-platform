"""URL constants and role-template-ID table for the Graph API client.

Split from the monolithic graph_client.py (issue 6oj7, 2026-04-22).
"""

from __future__ import annotations

GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"
GRAPH_BETA_API_BASE = "https://graph.microsoft.com/beta"
GRAPH_SCOPES = ["https://graph.microsoft.com/.default"]

ADMIN_ROLE_TEMPLATE_IDS = {
    "62e90394-69f5-4237-9190-012177145e10",  # Global Administrator
    "194ae4cb-b126-40b2-bd5b-6091b380977d",  # Security Administrator
    "f28a1f50-f6e7-4571-818b-6a12f2af6b6c",  # SharePoint Administrator
    "29232cdf-9323-42fd-ade2-1d097af3e4de",  # Exchange Administrator
    "b1be1c3e-b65d-4f19-8427-f6fa0d9feb5c",  # Conditional Access Administrator
    "729827e3-9c14-49f7-bb1b-9608f156bbb8",  # Helpdesk Administrator
    "966707d0-3269-4727-9be2-8c3a10f19b9d",  # Password Administrator
    "7be44c8a-adaf-4e2a-84d6-ab2649e08a13",  # Privileged Authentication Administrator
    "e8611ab8-c189-46e8-94e1-60213ab1f814",  # Privileged Role Administrator
    "fe930be7-5e62-47db-91af-98c3a49a38b1",  # User Administrator
    "a9ea8996-122f-4c74-9520-b03e91a63c5a",  # Application Administrator
    "3edaf663-341e-4475-9f94-5c398ef6c070",  # Cloud Application Administrator
}
