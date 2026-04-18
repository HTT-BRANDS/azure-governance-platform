# SPN / Role Matrix — Governance Platform

> **Purpose:** Single source of truth for which Azure Service Principal holds
> which role in each tenant. Enables fast audit, rapid drift detection, and
> clean onboarding of new tenants.
>
> **Last reconciled:** 2026-04-17 (bd-5xd5)

---

## Tenants

Each Riverside tenant has its own Azure AD tenant + app registration (SPN).
The SPN is created per-tenant; there is **no cross-tenant SPN**. Role
assignments are therefore scoped inside each tenant's subscription.

| Code | Tenant Name   | Primary Subscription | Notes                             |
|------|---------------|----------------------|-----------------------------------|
| HTT  | Head-To-Toe   | HTT-CORE             | Home tenant; contains prod infra  |
| BCC  | Bishops       | BCC-CORE             | Riverside tenant                  |
| FN   | Frenchies     | FN-CORE              | Riverside tenant                  |
| TLL  | Lash Lounge   | TLL-CORE             | Riverside tenant                  |
| DCE  | DCE           | (see `tenants.yaml`) | Standalone (non-Riverside) tenant |

> **Concrete IDs** (tenant IDs, subscription IDs, `app_id` values) live in
> `config/tenants.yaml` which is **gitignored** as sensitive organizational
> metadata (security audit LOW-1). See `config/tenants.yaml.example` for the
> committed template of the expected shape.

---

## Required Role Assignments (per tenant)

Every tenant's SPN **must** carry both of the following subscription-scoped
role assignments. These are the minimum required for the sync jobs to
populate all `/api/v1/health/data` domains.

| Role                      | Why it's needed                                                                    |
|---------------------------|------------------------------------------------------------------------------------|
| `Reader`                  | Resources sync, Azure Resource Graph queries, tenant compliance metadata           |
| `Cost Management Reader`  | Costs sync — **required** because plain `Reader` does NOT grant Cost Mgmt APIs     |

### Microsoft Graph app permissions (separate from RBAC above)

The SPN also needs Microsoft Graph application permissions for identity/MFA
sync. These are granted via app consent, not via `az role assignment create`,
and are documented under each app registration in Azure Portal. Typical set:
`Directory.Read.All`, `User.Read.All`, `AuditLog.Read.All`, `Policy.Read.All`.

---

## Verify current state

Pull the IDs from the gitignored config, then query Azure:

```bash
# Set the tenant you're auditing
TENANT_CODE=BCC                  # or HTT, FN, TLL, DCE

# Extract tenant_id + app_id from tenants.yaml (gitignored)
eval $(python3 -c "
import yaml
d = yaml.safe_load(open('config/tenants.yaml'))['tenants']['$TENANT_CODE']
print(f'TID={d[\"tenant_id\"]}; APP_ID={d[\"app_id\"]}')
")

# Auth + verify roles
az login --tenant "$TID"
SUB=$(az account show --query id -o tsv)

az role assignment list --assignee "$APP_ID" --subscription "$SUB" \
  --query "[].roleDefinitionName" -o tsv | sort -u
```

**Expected output** (both lines must appear):

```
Cost Management Reader
Reader
```

If `Cost Management Reader` is missing, grant it with:

```bash
az role assignment create \
  --assignee "$APP_ID" \
  --role "Cost Management Reader" \
  --scope "/subscriptions/$SUB"
```

---

## History

| Date       | Change                                                          | Issue    |
|------------|-----------------------------------------------------------------|----------|
| earlier    | Initial `Reader` grants on BCC/FN/TLL                           | `igi`    |
| 2026-04-17 | Added `Cost Management Reader` on BCC/FN/TLL (costs were null)  | `5xd5`   |

---

## Related

- `config/tenants.yaml` — tenant metadata (gitignored; template at `tenants.yaml.example`)
- `app/api/services/cost_service/` — consumers of Cost Management API
- `app/alerts/mfa_alerts.py` — uses Graph permissions
- bd-5xd5 (this grant), bd-igi (the original Reader-only grant)
