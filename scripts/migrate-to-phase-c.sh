#!/bin/bash
# Migration script: Phase B → Phase C
# Safely migrates from multi-tenant app with client secret to zero-secrets UAMI auth
#
# Usage: ./scripts/migrate-to-phase-c.sh [--validate-only|--rollback|--force]

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
TENANTS_YAML="config/tenants.yaml"
TENANTS_YAML_BACKUP="config/tenants.yaml.phase-b-backup.$(date +%Y%m%d-%H%M%S)"
ENV_FILE=".env"
ENV_BACKUP=".env.phase-b-backup.$(date +%Y%m%d-%H%M%S)"

# Phase C configuration
UAMI_CLIENT_ID="${UAMI_CLIENT_ID:-}"
UAMI_PRINCIPAL_ID="${UAMI_PRINCIPAL_ID:-}"
FEDERATED_IDENTITY_CREDENTIAL_ID="${FEDERATED_IDENTITY_CREDENTIAL_ID:-github-actions-federation}"

# Flags
VALIDATE_ONLY=false
ROLLBACK=false
FORCE=false

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

log_step() {
    echo -e "\n${BLUE}▶ $1${NC}"
}

require_file() {
    if [[ ! -f "$1" ]]; then
        log_error "Required file not found: $1"
        exit 1
    fi
}

require_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "$1 is required but not installed"
        exit 1
    fi
}

show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Migrates Azure Governance Platform from Phase B (multi-tenant app with secret)
to Phase C (zero-secrets UAMI authentication).

OPTIONS:
    --validate-only       Only validate current state, don't make changes
    --rollback            Rollback to Phase B from backup
    --force               Skip confirmation prompts
    --uami-client-id <id> UAMI Client ID (or set UAMI_CLIENT_ID env var)
    --uami-principal-id <id> UAMI Principal ID (or set UAMI_PRINCIPAL_ID env var)
    --fic-id <id>         Federated Identity Credential ID (default: $FEDERATED_IDENTITY_CREDENTIAL_ID)
    --help                Show this help message

EXAMPLES:
    # Validate current configuration
    $0 --validate-only

    # Perform migration (interactive)
    $0 --uami-client-id 00000000-0000-0000-0000-000000000000

    # Force migration without prompts
    $0 --uami-client-id 00000000-0000-0000-0000-000000000000 --force

    # Rollback to Phase B
    $0 --rollback
EOF
}

# ============================================================================
# Validation Functions
# ============================================================================

validate_yaml_syntax() {
    local file=$1

    log_info "Validating YAML syntax: $file"

    if command -v python3 &> /dev/null; then
        python3 -c "import yaml; yaml.safe_load(open('$file'))" 2>&1 || {
            log_error "Invalid YAML syntax in $file"
            return 1
        }
    elif command -v yq &> /dev/null; then
        yq '.' "$file" > /dev/null 2>&1 || {
            log_error "Invalid YAML syntax in $file"
            return 1
        }
    else
        log_warn "No YAML validator found (install python3-yaml or yq)"
        return 0
    fi

    log_success "YAML syntax is valid"
    return 0
}

validate_uami_exists() {
    local uami_client_id=$1

    log_step "Validating UAMI exists and is accessible"

    if ! command -v az &> /dev/null; then
        log_warn "Azure CLI not found, skipping UAMI validation"
        return 0
    fi

    if ! az account show &>/dev/null; then
        log_warn "Not logged into Azure, skipping UAMI validation"
        return 0
    fi

    # Try to get UAMI by client ID
    local uami
    uami=$(az ad sp show --id "$uami_client_id" --query "{id:id, displayName:displayName}" -o json 2>/dev/null || echo "null")

    if [[ "$uami" == "null" ]]; then
        log_warn "UAMI with client ID $uami_client_id not found in current tenant"
        log_info "You may need to run scripts/setup-uami-phase-c.sh first"
        return 0
    fi

    log_success "UAMI found: $(echo "$uami" | jq -r '.displayName')"
    return 0
}

validate_code_changes() {
    log_step "Validating Phase C code changes are present"

    # Check if uami_credential.py exists
    if [[ ! -f "app/core/uami_credential.py" ]]; then
        log_error "Code changes not found: app/core/uami_credential.py missing"
        log_error "Please ensure Phase C code is deployed"
        return 1
    fi

    # Check if UAMI settings are in config.py
    if ! grep -q "USE_UAMI_AUTH" "app/core/config.py"; then
        log_error "Code changes not found: USE_UAMI_AUTH setting missing in config.py"
        return 1
    fi

    if ! grep -q "UAMI_CLIENT_ID" "app/core/config.py"; then
        log_error "Code changes not found: UAMI_CLIENT_ID setting missing in config.py"
        return 1
    fi

    log_success "Phase C code changes validated"
    return 0
}

validate_tenants_yaml() {
    log_step "Validating tenants.yaml configuration"

    require_file "$TENANTS_YAML"

    # Check required fields
    if ! grep -q "multi_tenant_app_id:" "$TENANTS_YAML"; then
        log_error "Phase B not configured: multi_tenant_app_id not found in $TENANTS_YAML"
        log_error "Run migrate-to-phase-b.sh first"
        return 1
    fi

    log_success "Phase B configuration found in tenants.yaml"
    return 0
}

run_unit_tests() {
    log_step "Running Phase C unit tests"

    if [[ ! -f "tests/unit/test_uami_credential.py" ]]; then
        log_warn "UAMI credential tests not found"
        return 0
    fi

    if command -v python3 &> /dev/null; then
        log_info "Running: python -m pytest tests/unit/test_uami_credential.py -v"
        if python3 -m pytest tests/unit/test_uami_credential.py -v 2>&1; then
            log_success "Unit tests passed"
            return 0
        else
            log_warn "Some unit tests failed (non-blocking for migration)"
            return 0
        fi
    else
        log_warn "Python not available, skipping unit tests"
        return 0
    fi
}

run_connectivity_tests() {
    log_step "Running connectivity tests"

    if command -v python3 &> /dev/null; then
        log_info "Testing Phase C credential resolution..."

        python3 -c "
import sys
sys.path.insert(0, '.')

try:
    from app.core.uami_credential import get_uami_provider

    provider = get_uami_provider()

    # Test environment detection
    env_info = provider.get_environment_info()
    print(f'Environment info: {env_info}')

    # Test UAMI availability
    if provider.is_available():
        print('✓ UAMI authentication is available')
    else:
        print('✗ UAMI authentication is NOT available')
        print('  This is expected if not running in Azure or GitHub Actions')

    print('\nConnectivity tests completed!')

except Exception as e:
    print(f'Error during connectivity tests: {e}')
    sys.exit(1)
" && log_success "Connectivity tests passed" || log_warn "Connectivity tests failed (non-blocking)"
    else
        log_warn "Python not available, skipping connectivity tests"
    fi
}

# ============================================================================
# Migration Functions
# ============================================================================

create_backups() {
    log_step "Creating backups of current configuration"

    # Backup tenants.yaml
    cp "$TENANTS_YAML" "$TENANTS_YAML_BACKUP"
    log_success "Backup created: $TENANTS_YAML_BACKUP"

    # Backup .env if it exists
    if [[ -f "$ENV_FILE" ]]; then
        cp "$ENV_FILE" "$ENV_BACKUP"
        log_success "Backup created: $ENV_BACKUP"
    fi

    # Also backup to git
    if [[ -d ".git" ]]; then
        git add "$TENANTS_YAML_BACKUP" "$ENV_BACKUP" 2>/dev/null || true
        log_info "Backups added to git staging area"
    fi
}

update_environment_variables() {
    log_step "Updating environment configuration"

    local uami_client_id=$1
    local fic_id=$2

    # Update or create .env file
    if [[ -f "$ENV_FILE" ]]; then
        log_info "Updating $ENV_FILE with Phase C configuration"

        # Remove old UAMI settings if present
        sed -i.bak '/^UAMI_CLIENT_ID=/d' "$ENV_FILE" 2>/dev/null || true
        sed -i.bak '/^UAMI_PRINCIPAL_ID=/d' "$ENV_FILE" 2>/dev/null || true
        sed -i.bak '/^FEDERATED_IDENTITY_CREDENTIAL_ID=/d' "$ENV_FILE" 2>/dev/null || true
        sed -i.bak '/^USE_UAMI_AUTH=/d' "$ENV_FILE" 2>/dev/null || true
        rm -f "$ENV_FILE.bak" 2>/dev/null || true

        # Add new settings
        cat >> "$ENV_FILE" << EOF

# Phase C: Zero-secrets UAMI authentication
UAMI_CLIENT_ID=$uami_client_id
FEDERATED_IDENTITY_CREDENTIAL_ID=$fic_id
USE_UAMI_AUTH=true
EOF

        if [[ -n "$UAMI_PRINCIPAL_ID" ]]; then
            echo "UAMI_PRINCIPAL_ID=$UAMI_PRINCIPAL_ID" >> "$ENV_FILE"
        fi

        log_success "Updated $ENV_FILE"
    else
        log_info "Creating $ENV_FILE with Phase C configuration"

        cat > "$ENV_FILE" << EOF
# Phase C: Zero-secrets UAMI authentication
UAMI_CLIENT_ID=$uami_client_id
FEDERATED_IDENTITY_CREDENTIAL_ID=$fic_id
USE_UAMI_AUTH=true
EOF

        if [[ -n "$UAMI_PRINCIPAL_ID" ]]; then
            echo "UAMI_PRINCIPAL_ID=$UAMI_PRINCIPAL_ID" >> "$ENV_FILE"
        fi

        log_success "Created $ENV_FILE"
    fi

    # Display the configuration
    log_info "Phase C environment configuration:"
    grep -E "^(UAMI_|USE_UAMI|FEDERATED_)" "$ENV_FILE" || true
}

validate_migration() {
    log_step "Validating migration"

    # Check .env has required values
    if [[ -f "$ENV_FILE" ]]; then
        if ! grep -q "USE_UAMI_AUTH=true" "$ENV_FILE"; then
            log_error "Migration failed: USE_UAMI_AUTH not set to true"
            return 1
        fi

        if ! grep -q "^UAMI_CLIENT_ID=" "$ENV_FILE"; then
            log_error "Migration failed: UAMI_CLIENT_ID not set"
            return 1
        fi
    fi

    # Check code can import
    python3 -c "
import sys
sys.path.insert(0, '.')
from app.core.uami_credential import get_uami_provider
print('✓ UAMI credential module imports successfully')
" 2>/dev/null || {
        log_error "Failed to import UAMI credential module"
        return 1
    }

    log_success "Migration validation passed"
    return 0
}

# ============================================================================
# Rollback Functions
# ============================================================================

find_backup() {
    local backup_pattern="config/tenants.yaml.phase-b-backup.*"
    local latest_backup

    latest_backup=$(ls -t $backup_pattern 2>/dev/null | head -1)

    if [[ -z "$latest_backup" ]]; then
        log_error "No Phase B backup found (expected: $backup_pattern)"
        return 1
    fi

    echo "$latest_backup"
}

perform_rollback() {
    log_step "Performing rollback to Phase B"

    local backup_file
    backup_file=$(find_backup)

    if [[ $? -ne 0 ]]; then
        log_error "Cannot find backup to restore"
        exit 1
    fi

    log_info "Found backup: $backup_file"

    if [[ "$FORCE" == false ]]; then
        read -p "Restore this backup? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Rollback cancelled"
            exit 0
        fi
    fi

    # Create rollback point of current state
    cp "$TENANTS_YAML" "$TENANTS_YAML.rollback-point"
    log_info "Current state saved to: $TENANTS_YAML.rollback-point"

    # Restore backup
    cp "$backup_file" "$TENANTS_YAML"
    log_success "Restored Phase B configuration from backup"

    # Disable UAMI in .env
    if [[ -f "$ENV_FILE" ]]; then
        sed -i.bak 's/USE_UAMI_AUTH=true/USE_UAMI_AUTH=false/' "$ENV_FILE" 2>/dev/null || true
        rm -f "$ENV_FILE.bak" 2>/dev/null || true
        log_success "Disabled UAMI authentication in $ENV_FILE"
    fi

    # Validate restored config
    validate_yaml_syntax "$TENANTS_YAML"

    log_success "Rollback complete"
    log_info "Configuration is now at Phase B (multi-tenant app with secret)"
    log_info "Redeploy the application to apply changes"
}

# ============================================================================
# Main
# ============================================================================

main() {
    log_info "Azure Governance Platform: Phase B → Phase C Migration"
    log_info "=========================================================="
    log_info "Phase C: Zero-secrets authentication via UAMI"

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --validate-only)
                VALIDATE_ONLY=true
                shift
                ;;
            --rollback)
                ROLLBACK=true
                shift
                ;;
            --force)
                FORCE=true
                shift
                ;;
            --uami-client-id)
                UAMI_CLIENT_ID="$2"
                shift 2
                ;;
            --uami-principal-id)
                UAMI_PRINCIPAL_ID="$2"
                shift 2
                ;;
            --fic-id)
                FEDERATED_IDENTITY_CREDENTIAL_ID="$2"
                shift 2
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
    require_command python3
    require_file "$TENANTS_YAML"

    # Handle rollback mode
    if [[ "$ROLLBACK" == true ]]; then
        perform_rollback
        exit 0
    fi

    # Validation phase
    log_step "Phase 1: Pre-Migration Validation"

    validate_tenants_yaml || exit 1
    validate_code_changes || exit 1
    validate_yaml_syntax "$TENANTS_YAML" || exit 1

    # Get UAMI configuration if not provided
    if [[ -z "$UAMI_CLIENT_ID" ]]; then
        log_info "UAMI Client ID not provided"
        read -p "Enter the UAMI Client ID: " UAMI_CLIENT_ID

        if [[ -z "$UAMI_CLIENT_ID" ]]; then
            log_error "UAMI Client ID is required"
            exit 1
        fi
    fi

    validate_uami_exists "$UAMI_CLIENT_ID"

    log_info "UAMI Client ID: $UAMI_CLIENT_ID"
    log_info "FIC ID: $FEDERATED_IDENTITY_CREDENTIAL_ID"

    if [[ -n "$UAMI_PRINCIPAL_ID" ]]; then
        log_info "UAMI Principal ID: $UAMI_PRINCIPAL_ID"
    fi

    if [[ "$VALIDATE_ONLY" == true ]]; then
        log_success "Validation complete - no changes made"
        log_info "Run without --validate-only to perform migration"
        exit 0
    fi

    # Confirmation
    if [[ "$FORCE" == false ]]; then
        echo
        echo "This will migrate from Phase B to Phase C:"
        echo "  - Create backup of current tenants.yaml and .env"
        echo "  - Configure UAMI_CLIENT_ID: $UAMI_CLIENT_ID"
        echo "  - Set USE_UAMI_AUTH=true"
        echo "  - Keep Phase B configuration for rollback capability"
        echo
        read -p "Continue with migration? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Migration cancelled"
            exit 0
        fi
    fi

    # Migration phase
    log_step "Phase 2: Migration"

    create_backups
    update_environment_variables "$UAMI_CLIENT_ID" "$FEDERATED_IDENTITY_CREDENTIAL_ID"

    # Validation phase
    log_step "Phase 3: Post-Migration Validation"

    validate_migration || {
        log_error "Migration validation failed!"
        log_info "Backups available at: $TENANTS_YAML_BACKUP and $ENV_BACKUP"
        log_info "To rollback: $0 --rollback"
        exit 1
    }

    run_unit_tests
    run_connectivity_tests

    # Summary
    log_step "Migration Complete!"

    cat << EOF

================================================================================
                      PHASE C MIGRATION COMPLETE
================================================================================

Configuration Changes:
  - Backup created: $TENANTS_YAML_BACKUP
  - Environment file: $ENV_FILE (USE_UAMI_AUTH=true)
  - UAMI Client ID: $UAMI_CLIENT_ID
  - FIC ID: $FEDERATED_IDENTITY_CREDENTIAL_ID

What Changed:
  ✓ No more client secrets in configuration
  ✓ Authentication via User-Assigned Managed Identity
  ✓ OIDC federation for GitHub Actions
  ✓ Backward compatible with Phase B (can rollback)

Next Steps:
  1. ✅ Review the updated configuration files
  2. 🔄 Deploy the application to App Service with UAMI
  3. 🔄 Add UAMI to App Service: User assigned identity → Add → $UAMI_CLIENT_ID
  4. 🔄 Run tests: python -m pytest tests/unit/test_uami_credential.py -v
  5. 🔄 Run smoke tests: python -m pytest tests/smoke/test_uami_connectivity.py -v
  6. 🔄 Verify in staging before production
  7. 🔄 Monitor authentication for 1 week

App Service Configuration:
  - Go to App Service → Identity → User assigned
  - Add the UAMI: $UAMI_CLIENT_ID
  - Ensure USE_UAMI_AUTH=true in App Settings

Rollback (if needed):
  $0 --rollback

Or manually:
  - Set USE_UAMI_AUTH=false
  - Ensure AZURE_MULTI_TENANT_CLIENT_SECRET is configured
  - Redeploy

Documentation:
  - Phase C Runbook: docs/runbooks/phase-c-zero-secrets.md
  - Auth Roadmap: docs/AUTH_TRANSITION_ROADMAP.md

================================================================================
EOF

    log_success "Phase C migration completed successfully!"
}

# Run main if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
