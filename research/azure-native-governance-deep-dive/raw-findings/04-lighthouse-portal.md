# Azure Lighthouse Portal — Native Multi-Tenant Experience

## Source
- **URL**: https://learn.microsoft.com/en-us/azure/lighthouse/how-to/view-manage-customers
- **URL**: https://learn.microsoft.com/en-us/azure/lighthouse/concepts/cross-tenant-management-experience
- **Tier**: 1 (Official Microsoft Documentation)
- **Last verified**: 2026-03-27

## Key Findings

### What the Lighthouse Portal Provides

#### "My customers" Page
- View all delegated customers with name and customer ID (tenant ID)
- See Offer ID and Offer version associated with each engagement
- Delegations column shows number of delegated subscriptions and resource groups
- Sort, filter, and group by specific customers, offers, or keywords
- Drill down to see subscriptions, offers, delegations, and role assignments

#### Delegation Management
- View and manage delegations
- Remove delegations (with Managed Services Registration Assignment Delete Role)
- View delegation change activity — Activity log tracks every delegation/removal event
- Requires Monitoring Reader role at root scope to view activity

#### Subscription Context Switching
- Can work in the context of a delegated subscription via Directory + subscription filter
- Select "All directories" then "Select all" to include all subscriptions across all tenants
- When accessing an Azure service that supports cross-tenant management, it defaults to the delegated subscription context
- Can select specific subscriptions from any delegated tenant

### What the Portal Does Well
1. **Unified subscription picker**: See all delegated subscriptions across tenants in one filter
2. **Transparent delegation management**: Clear view of what's delegated and to whom
3. **Activity logging**: Track delegation changes
4. **Zero cost**: Free — no licensing required

### What the Portal CANNOT Do
1. **No unified governance dashboard** — it's a subscription switcher, not a dashboard
2. **No aggregated metrics** across tenants (cost totals, compliance scores, identity stats)
3. **No custom branding** per tenant — locked to Azure portal UX
4. **No role-based portal customization** for non-technical users
5. **No custom reporting or exports** — must use individual service reports
6. **No DMARC monitoring** integration
7. **No regulatory deadline tracking**
8. **No chargeback/showback reporting**
9. **No identity governance** — Lighthouse doesn't delegate Entra ID
10. **Requires Azure portal literacy** — not suitable for business users

### Lighthouse Delegation Limitations (from Cross-Tenant Management page)
1. **Role assignments must use Azure built-in roles** — no custom roles, no classic subscription administrator roles
2. **No Owner role** delegation
3. **No DataActions permission** in delegated roles
4. **User Access Administrator role** supported only for limited use (assigning roles to managed identities)
5. **`az role assignment list` doesn't show Lighthouse delegations** — only visible in Azure portal Delegations section or Lighthouse API
6. **Azure Databricks workspaces can't be launched** on delegated subscriptions
7. **Resource locks don't prevent managing tenant actions** — security concern
8. **Cross-national-cloud delegation not supported** (no Azure Gov ↔ Azure Public)

### Azure Resource Graph Integration
- Resource Graph queries **automatically include Lighthouse-delegated resources** when scope is not restricted
- Tenant ID is included in query results to identify which tenant a resource belongs to
- This is the strongest native cross-tenant capability — but requires KQL expertise
- Limited to Azure resources only — no Entra ID data
