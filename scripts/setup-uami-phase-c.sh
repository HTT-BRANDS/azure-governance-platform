#!/bin/bash
# Setup script for Phase C: Zero-Secrets Authentication via UAMI + Federated Identity
# Creates User-Assigned Managed Identity with Federated Identity Credential on multi-tenant app
#
# Usage: ./scripts/setup-uami-phase-c.sh [--tenant-id <home-tenant-id>] [--app-id <multi-tenant-app-id>]
#
# Requirements:
#   - Azure CLI (az) installed and logged in
#   - Owner or Global Admin role in home tenant (HTT)
#   - Existing multi-tenant app registration from Phase B
#   - jq installed for JSON parsing

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
UAMI_NAME="mi-governance-platform"
RESOURCE_GROUP="rg-governance-production"
LOCATION="australiaeast"
FIC_NAME="github-actions-federation"

# GitHub OIDC Configuration
GITHUB_REPO="${GITHUB_REPO:-riverside/governance-platform}"
GITHUB_BRANCH="${GITHUB_BRANCH:-main}"

# Default values (will be prompted or overridden via CLI)
HOME_TENANT_ID=""
MULTI_TENANT_APP_ID=""

# ============================================================================
# Helper Functions
# ============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

require_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "$1 is required but not installed."
        exit 1
    fi
}

show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Creates a User-Assigned Managed Identity with Federated Identity Credential
for zero-secrets authentication in the Azure Governance Platform.

This enables GitHub Actions to authenticate to Azure without storing secrets,
using OIDC federation between GitHub and Azure AD.

OPTIONS:
    --tenant-id <id>      Home tenant ID (where UAMI will be created)
    --app-id <id>         Multi-tenant app registration ID (from Phase B)
    --resource-group <rg> Resource group for UAMI (default: $RESOURCE_GROUP)
    --location <loc>      Azure region (default: $LOCATION)
    --github-repo <repo>  GitHub repository (default: $GITHUB_REPO)
    --github-branch <br>  GitHub branch for OIDC (default: $GITHUB_BRANCH)
    --dry-run             Show what would be done without making changes
    --help                Show this help message

EXAMPLES:
    # Interactive mode (will prompt for tenant and app selection)
    $0

    # Specify all parameters explicitly
    $0 --tenant-id 00000000-0000-0000-0000-000000000000 \\
       --app-id 00000000-0000-0000-0000-000000000001 \\
       --github-repo "myorg/myrepo"

    # Dry run to preview changes
    $0 --dry-run

ENVIRONMENT VARIABLES:
    AZURE_TENANT_ID       Default tenant ID for non-interactive mode
    AZURE_MULTI_TENANT_APP_ID  Default multi-tenant app ID
    GITHUB_REPO           GitHub repository for OIDC federation
    GITHUB_BRANCH         GitHub branch for OIDC federation
EOF
}

# ============================================================================
# Azure Functions
# ============================================================================

select_tenant() {
    log_info "Fetching available tenants..."

    local tenants
    tenants=$(az account list --query "[].{name:name, tenantId:tenantId}" -o json)

    if [[ $(echo "$tenants" | jq length) -eq 0 ]]; then
        log_error "No Azure subscriptions found. Please run 'az login' first."
        exit 1
    fi

    if [[ $(echo "$tenants" | jq length) -eq 1 ]]; then
        local tenant_id
        tenant_id=$(echo "$tenants" | jq -r '.[0].tenantId')
        log_info "Using single available tenant: $tenant_id"
        echo "$tenant_id"
        return
    fi

    echo
    echo "Available tenants:"
    echo "$tenants" | jq -r '.[] | "\(.tenantId): \(.name)"' | nl
    echo

    read -p "Select tenant number (or paste tenant ID): " selection

    # Check if numeric selection
    if [[ "$selection" =~ ^[0-9]+$ ]]; then
        local tenant_id
        tenant_id=$(echo "$tenants" | jq -r ".[$selection-1].tenantId")
        if [[ "$tenant_id" == "null" ]]; then
            log_error "Invalid selection"
            exit 1
        fi
        echo "$tenant_id"
    else
        # Assume it's a tenant ID
        echo "$selection"
    fi
}

select_multi_tenant_app() {
    local tenant_id=$1

    log_info "Fetching multi-tenant app registrations in tenant $tenant_id..."

    local apps
    apps=$(az ad app list \
        --filter "signInAudience eq 'AzureADMultipleOrgs'" \
        --query "[].{name:displayName, appId:appId, objectId:id}" \
        -o json 2>/dev/null || echo "[]")

    if [[ $(echo "$apps" | jq length) -eq 0 ]]; then
        log_error "No multi-tenant apps found in tenant $tenant_id"
        log_info "Run scripts/setup-multi-tenant-app.sh first to create a multi-tenant app"
        exit 1
    fi

    echo
    echo "Multi-tenant applications:"
    echo "$apps" | jq -r '.[] | "\(.appId): \(.name)"' | nl
    echo

    read -p "Select app number (or paste App ID): " selection

    # Check if numeric selection
    if [[ "$selection" =~ ^[0-9]+$ ]]; then
        local app_id
        app_id=$(echo "$apps" | jq -r ".[$selection-1].appId")
        if [[ "$app_id" == "null" ]]; then
            log_error "Invalid selection"
            exit 1
        fi
        echo "$app_id"
    else
        # Assume it's an App ID
        echo "$selection"
    fi
}

check_existing_uami() {
    local uami_name=$1
    local resource_group=$2

    log_info "Checking for existing UAMI..."

    local existing_uami
    existing_uami=$(az identity show \
        --name "$uami_name" \
        --resource-group "$resource_group" \
        --query "{clientId:clientId, principalId:principalId, id:id}" \
        -o json 2>/dev/null || echo "null")

    if [[ "$existing_uami" != "null" ]]; then
        log_warn "UAMI '$uami_name' already exists in resource group '$resource_group'!"
        local client_id
        client_id=$(echo "$existing_uami" | jq -r '.clientId')
        log_warn "Client ID: $client_id"
        read -p "Continue with existing UAMI? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Exiting. To create a new UAMI, delete the existing one first."
            exit 0
        fi
        echo "$existing_uami"
        return
    fi

    echo "null"
}

create_resource_group() {
    local resource_group=$1
    local location=$2

    log_info "Ensuring resource group exists: $resource_group"

    if ! az group show --name "$resource_group" &>/dev/null; then
        log_info "Creating resource group: $resource_group in $location"
        az group create \
            --name "$resource_group" \
            --location "$location" \
            --tags \
                "Environment=production" \
                "Project=azure-governance-platform" \
                "Phase=C" \
                "ManagedBy=terraform"
        log_success "Created resource group"
    else
        log_info "Resource group already exists"
    fi
}

create_uami() {
    local uami_name=$1
    local resource_group=$2
    local location=$3

    log_info "Creating User-Assigned Managed Identity..."
    log_info "  Name: $uami_name"
    log_info "  Resource Group: $resource_group"
    log_info "  Location: $location"

    local uami_data
    uami_data=$(az identity create \
        --name "$uami_name" \
        --resource-group "$resource_group" \
        --location "$location" \
        --query "{clientId:clientId, principalId:principalId, id:id, tenantId:tenantId}" \
        -o json)

    local client_id
    client_id=$(echo "$uami_data" | jq -r '.clientId')
    local principal_id
    principal_id=$(echo "$uami_data" | jq -r '.principalId')

    log_success "Created UAMI"
    log_info "  Client ID: $client_id"
    log_info "  Principal ID: $principal_id"

    echo "$uami_data"
}

create_federated_identity_credential() {
    local app_id=$1
    local uami_principal_id=$2
    local fic_name=$3
    local github_repo=$4
    local github_branch=$5

    log_info "Creating Federated Identity Credential on multi-tenant app..."
    log_info "  App ID: $app_id"
    log_info "  UAMI Principal ID: $uami_principal_id"
    log_info "  FIC Name: $fic_name"
    log_info "  GitHub Repo: $github_repo"
    log_info "  GitHub Branch: $github_branch"

    # Get the app object ID (needed for FIC creation)
    local app_object_id
    app_object_id=$(az ad app show --id "$app_id" --query "id" -o tsv)

    # Check if FIC already exists
    local existing_fic
    existing_fic=$(az ad app federated-credential list \
        --id "$app_object_id" \
        --query "[?name=='$fic_name']" \
        -o json 2>/dev/null || echo "[]")

    if [[ $(echo "$existing_fic" | jq length) -gt 0 ]]; then
        log_warn "Federated Identity Credential '$fic_name' already exists"
        read -p "Recreate it? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            # Delete existing FIC
            local fic_id
            fic_id=$(echo "$existing_fic" | jq -r '.[0].id')
            az ad app federated-credential delete \
                --id "$app_object_id" \
                --federated-credential-id "$fic_id" \
                --yes 2>/dev/null || true
            log_info "Deleted existing FIC"
        else
            echo "$existing_fic"
            return
        fi
    fi

    # Build the issuer URL for GitHub Actions
    local issuer="https://token.actions.githubusercontent.com"
    local subject="repo:${github_repo}:ref:refs/heads/${github_branch}"

    # Create FIC parameters
    local fic_params
    fic_params=$(jq -n \
        --arg name "$fic_name" \
        --arg issuer "$issuer" \
        --arg subject "$subject" \
        --arg desc "GitHub Actions OIDC federation for Azure Governance Platform" \
        '{
            name: $name,
            issuer: $issuer,
            subject: $subject,
            description: $desc,
            audiences: ["api://AzureADTokenExchange"]
        }')

    local fic_data
    fic_data=$(az ad app federated-credential create \
        --id "$app_object_id" \
        --parameters "$fic_params" \
        --query "{name:name, issuer:issuer, subject:subject, audiences:audiences}" \
        -o json)

    log_success "Created Federated Identity Credential"
    log_info "  Issuer: $issuer"
    log_info "  Subject: $subject"

    echo "$fic_data"
}

assign_key_vault_roles() {
    local uami_principal_id=$1

    log_info "Assigning Key Vault roles to UAMI..."

    # Get Key Vault resource ID
    local key_vault_name
    key_vault_name=$(az keyvault list --query "[?contains(name, 'gov')].name | [0]" -o tsv)

    if [[ -z "$key_vault_name" ]]; then
        log_warn "No Key Vault found with 'gov' in name, skipping role assignment"
        return
    fi

    log_info "Found Key Vault: $key_vault_name"

    # Assign Key Vault Secrets User role
    local role_assignment
    role_assignment=$(az role assignment create \
        --assignee-object-id "$uami_principal_id" \
        --assignee-principal-type ServicePrincipal \
        --role "Key Vault Secrets User" \
        --scope "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.KeyVault/vaults/$key_vault_name" \
        --query "{id:id, roleDefinitionName:roleDefinitionName}" \
        -o json 2>/dev/null || echo "null")

    if [[ "$role_assignment" != "null" ]]; then
        log_success "Assigned Key Vault Secrets User role"
    else
        log_warn "Failed to assign Key Vault role (may already exist or insufficient permissions)"
    fi
}

configure_github_secrets() {
    local uami_client_id=$1
    local tenant_id=$2
    local subscription_id=$3

    log_info "GitHub repository configuration needed"
    log_info "======================================="
    log_info "Add the following secrets to your GitHub repository ($GITHUB_REPO):"
    echo
    echo "AZURE_CLIENT_ID: $uami_client_id"
    echo "AZURE_TENANT_ID: $tenant_id"
    echo "AZURE_SUBSCRIPTION_ID: $subscription_id"
    echo
    log_info "These can be set via GitHub CLI:"
    echo "  gh secret set AZURE_CLIENT_ID --body \"$uami_client_id\" -R $GITHUB_REPO"
    echo "  gh secret set AZURE_TENANT_ID --body \"$tenant_id\" -R $GITHUB_REPO"
    echo "  gh secret set AZURE_SUBSCRIPTION_ID --body \"$subscription_id\" -R $GITHUB_REPO"
}

generate_summary() {
    local uami_client_id=$1
    local uami_principal_id=$2
    local uami_id=$3
    local tenant_id=$4
    local subscription_id=$5
    local app_id=$6
    local fic_name=$7

    cat << EOF

================================================================================
                      PHASE C SETUP COMPLETE
================================================================================

User-Assigned Managed Identity (UAMI)
---------------------------------------
Name:           $UAMI_NAME
Resource Group: $RESOURCE_GROUP
Location:       $LOCATION
Client ID:      $uami_client_id
Principal ID:   $uami_principal_id
Resource ID:    $uami_id

Multi-Tenant App Configuration
--------------------------------
App ID:         $app_id
FIC Name:       $fic_name
Federation:     GitHub Actions OIDC

Configuration Values
--------------------
Add to environment variables:

  AZURE_UAMI_CLIENT_ID="$uami_client_id"
  AZURE_UAMI_PRINCIPAL_ID="$uami_principal_id"
  USE_UAMI_AUTH="true"

Or in App Service Configuration:

  UAMI_CLIENT_ID="$uami_client_id"
  UAMI_PRINCIPAL_ID="$uami_principal_id"
  USE_UAMI_AUTH="true"
  FEDERATED_IDENTITY_CREDENTIAL_ID="$fic_name"

GitHub Actions OIDC (for CI/CD)
-------------------------------
Repository:     $GITHUB_REPO
Branch:         $GITHUB_BRANCH
Issuer:         https://token.actions.githubusercontent.com

Required GitHub Secrets:
  AZURE_CLIENT_ID:      $uami_client_id
  AZURE_TENANT_ID:      $tenant_id
  AZURE_SUBSCRIPTION_ID: $subscription_id

Role Assignments
----------------
The UAMI has been assigned:
  - Key Vault Secrets User (on governance Key Vault)

Next Steps
----------
1. ✅ Verify UAMI is created: az identity show -n $UAMI_NAME -g $RESOURCE_GROUP
2. ✅ Verify FIC is attached: az ad app federated-credential list --id $app_id
3. 🔄 Add GitHub secrets (shown above)
4. 🔄 Update GitHub Actions workflow to use OIDC login:

   - name: Azure Login
     uses: azure/login@v2
     with:
       client-id: \${{ secrets.AZURE_CLIENT_ID }}
       tenant-id: \${{ secrets.AZURE_TENANT_ID }}
       subscription-id: \${{ secrets.AZURE_SUBSCRIPTION_ID }}

5. 🔄 Update config/tenants.yaml or environment variables
6. 🔄 Deploy and test
7. 🔄 Run: python -m pytest tests/unit/test_uami_credential.py -v
8. 🔄 Run: python -m pytest tests/smoke/test_uami_connectivity.py -v

Architecture
------------
UAMI (User-Assigned Managed Identity)
  ↓ (federated token from GitHub Actions OIDC)
Federated Identity Credential on Multi-Tenant App
  ↓ (token exchange)
ClientAssertionCredential
  ↓ (access token)
Microsoft Graph API

Troubleshooting
---------------
- Verify federation: az ad app federated-credential show --id $app_id --federated-credential-id $fic_name
- Test UAMI token: az identity federated-credential generate-token (via REST)
- Check App Service identity: Ensure User-Assigned identity is added to App Service

Rollback (if needed)
--------------------
To return to Phase B (client secrets):
  1. Set USE_UAMI_AUTH="false"
  2. Redeploy with AZURE_MULTI_TENANT_CLIENT_SECRET configured

Documentation
-------------
- Phase C Runbook: docs/runbooks/phase-c-zero-secrets.md
- Auth Roadmap: docs/AUTH_TRANSITION_ROADMAP.md

================================================================================
EOF
}

# ============================================================================
# Main Script
# ============================================================================

main() {
    local dry_run=false

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --tenant-id)
                HOME_TENANT_ID="$2"
                shift 2
                ;;
            --app-id)
                MULTI_TENANT_APP_ID="$2"
                shift 2
                ;;
            --resource-group)
                RESOURCE_GROUP="$2"
                shift 2
                ;;
            --location)
                LOCATION="$2"
                shift 2
                ;;
            --github-repo)
                GITHUB_REPO="$2"
                shift 2
                ;;
            --github-branch)
                GITHUB_BRANCH="$2"
                shift 2
                ;;
            --dry-run)
                dry_run=true
                shift
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done

    # Check prerequisites
    require_command az
    require_command jq

    log_info "Azure Governance Platform: Phase C Setup (Zero-Secrets UAMI)"
    log_info "==========================================================="

    if [[ "$dry_run" == true ]]; then
        log_warn "DRY RUN MODE - No changes will be made"
    fi

    # Select tenant
    if [[ -z "$HOME_TENANT_ID" ]]; then
        HOME_TENANT_ID=$(select_tenant)
    fi

    log_info "Using home tenant: $HOME_TENANT_ID"

    # Set active tenant
    az account set --tenant "$HOME_TENANT_ID" || {
        log_error "Failed to set tenant. Please run 'az login --tenant $HOME_TENANT_ID'"
        exit 1
    }

    # Get subscription ID
    local subscription_id
    subscription_id=$(az account show --query id -o tsv)
    log_info "Using subscription: $subscription_id"

    # Select multi-tenant app
    if [[ -z "$MULTI_TENANT_APP_ID" ]]; then
        MULTI_TENANT_APP_ID=$(select_multi_tenant_app "$HOME_TENANT_ID")
    fi

    log_info "Using multi-tenant app: $MULTI_TENANT_APP_ID"

    # Check for existing UAMI
    local existing_uami
    existing_uami=$(check_existing_uami "$UAMI_NAME" "$RESOURCE_GROUP")

    local uami_data
    local uami_client_id
    local uami_principal_id
    local uami_id

    if [[ "$existing_uami" != "null" ]]; then
        uami_data="$existing_uami"
        uami_client_id=$(echo "$uami_data" | jq -r '.clientId')
        uami_principal_id=$(echo "$uami_data" | jq -r '.principalId')
        uami_id=$(echo "$uami_data" | jq -r '.id')
        log_info "Using existing UAMI: $uami_client_id"
    else
        if [[ "$dry_run" == true ]]; then
            log_info "[DRY RUN] Would create resource group: $RESOURCE_GROUP"
            log_info "[DRY RUN] Would create UAMI: $UAMI_NAME"
            uami_client_id="00000000-0000-0000-0000-000000000000"
            uami_principal_id="00000000-0000-0000-0000-000000000001"
            uami_id="/subscriptions/$subscription_id/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.ManagedIdentity/userAssignedIdentities/$UAMI_NAME"
        else
            # Create resource group
            create_resource_group "$RESOURCE_GROUP" "$LOCATION"

            # Create UAMI
            uami_data=$(create_uami "$UAMI_NAME" "$RESOURCE_GROUP" "$LOCATION")
            uami_client_id=$(echo "$uami_data" | jq -r '.clientId')
            uami_principal_id=$(echo "$uami_data" | jq -r '.principalId')
            uami_id=$(echo "$uami_data" | jq -r '.id')
        fi
    fi

    # Create Federated Identity Credential
    local fic_data
    if [[ "$dry_run" == true ]]; then
        log_info "[DRY RUN] Would create FIC: $FIC_NAME on app $MULTI_TENANT_APP_ID"
        fic_data="{}"
    else
        fic_data=$(create_federated_identity_credential \
            "$MULTI_TENANT_APP_ID" \
            "$uami_principal_id" \
            "$FIC_NAME" \
            "$GITHUB_REPO" \
            "$GITHUB_BRANCH")
    fi

    # Assign Key Vault roles
    if [[ "$dry_run" == false ]]; then
        assign_key_vault_roles "$uami_principal_id"
    else
        log_info "[DRY RUN] Would assign Key Vault roles to UAMI"
    fi

    # Generate summary
    generate_summary \
        "$uami_client_id" \
        "$uami_principal_id" \
        "$uami_id" \
        "$HOME_TENANT_ID" \
        "$subscription_id" \
        "$MULTI_TENANT_APP_ID" \
        "$FIC_NAME"

    # GitHub configuration guidance
    if [[ "$dry_run" == false ]]; then
        configure_github_secrets "$uami_client_id" "$HOME_TENANT_ID" "$subscription_id"

        # Save summary to file
        local output_file="uami-phase-c-setup-$(date +%Y%m%d-%H%M%S).txt"
        generate_summary \
            "$uami_client_id" \
            "$uami_principal_id" \
            "$uami_id" \
            "$HOME_TENANT_ID" \
            "$subscription_id" \
            "$MULTI_TENANT_APP_ID" \
            "$FIC_NAME" > "$output_file"
        log_info "Summary saved to: $output_file"

        log_success "Phase C setup completed successfully!"
    else
        log_info "[DRY RUN] Setup would be complete. Run without --dry-run to create resources."
    fi
}

# Run main if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
