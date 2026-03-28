# Entra ID Governance — Cross-Tenant Identity Governance via Lighthouse

## Source
- **URL**: https://learn.microsoft.com/en-us/entra/id-governance/identity-governance-overview
- **URL**: https://learn.microsoft.com/en-us/entra/id-governance/licensing-fundamentals
- **URL**: https://learn.microsoft.com/en-us/entra/identity/multi-tenant-organizations/overview
- **Tier**: 1 (Official Microsoft Documentation)
- **Last verified**: 2026-03-27

## CRITICAL ARCHITECTURAL LIMITATION

> **Azure Lighthouse delegates AZURE RESOURCE MANAGEMENT, NOT Microsoft Entra ID (identity) management.**

This is the single most important finding for the identity governance module. Lighthouse cannot provide cross-tenant Entra ID visibility.

## Key Findings

### What Entra ID Governance Provides (PER-TENANT ONLY)
- **Identity lifecycle**: Automate creation, updating, and removal of user identities
- **Access lifecycle**: Entitlement management, access packages, access reviews
- **Privileged access lifecycle**: Privileged Identity Management (PIM), access reviews for privileged roles
- **Lifecycle workflows**: Automate onboarding/offboarding processes
- **Access Review Agent** (Preview): Automated access reviews

### What Multi-Tenant Organization Capabilities Provide
Entra ID multi-tenant capabilities are focused on **B2B COLLABORATION, NOT GOVERNANCE**:
- **B2B collaboration**: External user access to applications — NOT governance auditing
- **Cross-tenant synchronization**: Automates creating/updating/deleting B2B collaboration users — NOT governance reporting
- **Multitenant organization**: Defines a boundary around owned tenants for Teams/M365 collaboration — NOT identity auditing
- **Microsoft 365 admin center for multitenant collaboration**: Admin portal for creating multitenant org — NOT cross-tenant governance
- **B2B direct connect**: Teams Connect shared channels only — NOT governance

### Cross-Tenant Synchronization Constraints
- Synchronized users have same cross-tenant Teams/M365 experiences as any B2B collaboration user
- **Doesn't synchronize devices or contacts**
- Governed by cross-tenant access settings
- This is a user provisioning service, NOT governance reporting

### What CANNOT Be Done Cross-Tenant via Native Tools
1. **Cross-tenant MFA compliance reporting** — must sign into each tenant individually
2. **Cross-tenant stale account detection** — must check each tenant
3. **Cross-tenant privileged access reviews** — reviews are per-tenant
4. **Cross-tenant guest user management audit** — per-tenant only
5. **Cross-tenant Conditional Access policy audit** — per-tenant only
6. **Cross-tenant service principal inventory** — per-tenant only
7. **Cross-tenant license utilization tracking** — per-tenant only
8. **Cross-tenant role assignment analysis** — per-tenant only (Lighthouse delegations visible but NOT Entra roles)

### Microsoft Graph API Alternative
- Microsoft Graph API CAN query identity data across tenants
- BUT requires app registrations with appropriate permissions IN EACH tenant
- This is exactly what the custom platform already does via `graph_client.py`
- Not a "native tool" advantage — same integration effort as custom platform

### Licensing
- **Microsoft Entra ID Governance**: Standalone license (requires Entra ID P1 or P2 as prerequisite)
- **Microsoft Entra ID Governance Add-on**: For Entra ID P2 customers
- **Microsoft Entra Suite**: Complete cloud-based solution (includes ID Governance + Private Access + Internet Access + ID Protection + Verified ID)
- **Pricing**: ~$7/user/month for Entra ID Governance
- **Per-tenant licensing**: Must be licensed in EACH tenant separately
- For 4 tenants × 30 users: ~$840/month — and still NO cross-tenant governance

### Key Insight
Even with Entra ID Governance licensed in all 4 tenants, you would STILL need to:
1. Sign into each tenant separately to view governance data
2. Build custom reporting to aggregate across tenants
3. Use Microsoft Graph API (which requires per-tenant app registrations — what the custom platform already does)
