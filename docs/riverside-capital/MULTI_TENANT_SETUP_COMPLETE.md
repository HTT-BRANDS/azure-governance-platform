# Riverside Capital - Multi-Tenant PE Governance Setup

**Date:** $(date +%Y-%m-%d)
**Status:** ✅ COMPLETE

## Executive Summary

Multi-tenant Azure governance platform successfully configured for Riverside Capital to monitor portfolio companies: HTT Brands, BCC Holding Co., Frenchies Nails (FN), and The Lash Lounge (TLL).

## Tenant Configuration

| Tenant | ID | SP ID | Admin UPN | Status |
|--------|-----|-------|-----------|--------|
| **HTT (Primary)** | 0c0e35dc-188a-4eb3-b8ba-61752154b407 | b8e67903-abf5-4b53-9ced-d194d43ca277 | tyler.granlund-admin@httbrands.com | ✅ Complete |
| **BCC** | b5380912-79ec-452d-a6ca-6d897b19b294 | 5d76b0f8-cb00-4dd2-86c4-cac7580101e1 | tyler.granlund-Admin@bishopsbs.onmicrosoft.com | ✅ Complete |
| **FN** | 98723287-044b-4bbb-9294-19857d4128a0 | 4a8351a9-44b6-4ef8-ac56-7de0658c0dd1 | tyler.granlund-Admin@ftgfrenchiesoutlook.onmicrosoft.com | ✅ Complete |
| **TLL** | 3c7d2bf3-b597-4766-b5cb-2b489c2904d6 | 26445929-1666-45fb-8eee-b333d5adbb45 | tyler.granlund-Admin@LashLoungeFranchise.onmicrosoft.com | ✅ Complete |

## App Registration

| Property | Value |
|----------|-------|
| **Display Name** | Riverside-Capital-PE-Governance-Platform |
| **App ID** | 1e3e8417-49f1-4d08-b7be-47045d8a12e9 |
| **Home Tenant** | HTT (0c0e35dc-188a-4eb3-b8ba-61752154b407) |
| **Sign-in Audience** | AzureADMultipleOrgs |

## API Permissions Granted

- AuditLog.Read.All
- Reports.Read.All
- Policy.Read.All
- Organization.Read.All
- Directory.Read.All
- RoleManagement.Read.Directory
- UserAuthenticationMethod.Read.All
- IdentityRiskyUser.Read.All
- IdentityRiskEvent.Read.All
- Application.Read.All
- User.Read.All
- Group.Read.All
- GroupMember.Read.All

## Azure RBAC Roles Assigned

- **Cost Management Reader** - Cost and billing data access
- **Reader** - General resource visibility

## Sync Configuration

- **Schedule:** Daily at 6:00 AM and 11:00 PM CT
- **Historical:** 12 months retroactive data collection
- **Data Types:** Cost, subscriptions, resources, identity, MFA, compliance
- **Billing Sources:** Direct, Sui Generis, Pax8, AppRiver

## Federated Credentials

| Name | Purpose |
|------|---------|
| github-actions-main | Main branch deployments |
| github-actions-pr | Pull request workflows |

## Next Steps

### 1. Complete Admin Consent (if not done)

Visit these URLs as Global Admin in each tenant:

- BCC: https://login.microsoftonline.com/b5380912-79ec-452d-a6ca-6d897b19b294/adminconsent?client_id=1e3e8417-49f1-4d08-b7be-47045d8a12e9
- FN: https://login.microsoftonline.com/98723287-044b-4bbb-9294-19857d4128a0/adminconsent?client_id=1e3e8417-49f1-4d08-b7be-47045d8a12e9
- TLL: https://login.microsoftonline.com/3c7d2bf3-b597-4766-b5cb-2b489c2904d6/adminconsent?client_id=1e3e8417-49f1-4d08-b7be-47045d8a12e9

### 2. Configure GitHub Secrets

Add these secrets to your GitHub repository:

- `AZURE_CLIENT_ID`: 1e3e8417-49f1-4d08-b7be-47045d8a12e9
- `AZURE_TENANT_ID`: 0c0e35dc-188a-4eb3-b8ba-61752154b407
- `AZURE_SUBSCRIPTION_ID`: [Your dev/test subscription ID]

### 3. Deploy to Production

- Copy workflow file to `.github/workflows/`
- Implement sync logic
- Test in dev environment
- Deploy to production

## Support

For questions or issues, refer to:
- `/tmp/pe_sync_config.json` - Full sync configuration
- `/tmp/.github/workflows/tenant-sync.yml` - GitHub Actions workflow template
- `/tmp/pe_governance_config.env` - Environment variables and IDs
