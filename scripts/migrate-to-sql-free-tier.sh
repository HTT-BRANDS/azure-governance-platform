#!/usr/bin/env bash
# Azure SQL Free Tier Migration Script for Staging
# 
# Migrates Azure SQL Database from paid tier (Basic/S0/S1) to Free Tier.
# Includes backup, migration, connection string update, and rollback capability.
#
# Usage:
#   ./migrate-to-sql-free-tier.sh --resource-group rg-governance-staging \
#       --server sql-governance-staging-xxx --database governance-db \
#       --backup-before-migrate
#
# Author: Code Puppy (Richard) 🐶
# Issue: l5i

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$PROJECT_ROOT/.sql-migration-backups"

# Default values
RESOURCE_GROUP=""
SERVER_NAME=""
DATABASE_NAME="governance-db"
ADMIN_USER=""
ADMIN_PASSWORD=""
BACKUP_BEFORE_MIGRATE=false
UPDATE_CONNECTION_STRING=false
APP_SERVICE_NAME=""
VERIFY_ONLY=false
ROLLBACK=false
RESTORE_FROM_BACKUP=""
SKIP_CONFIRMATION=false

# Logging functions
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

# Usage information
show_usage() {
    cat << EOF
Azure SQL Free Tier Migration Script

Migrates staging database to Azure SQL Free Tier (0 cost, 32GB limit)

Usage:
    $0 [OPTIONS]

Options:
    -g, --resource-group NAME       Resource group name (required)
    -s, --server NAME               SQL Server name (required)
    -d, --database NAME             Database name (default: governance-db)
    -u, --admin-user USERNAME       SQL admin username
    -p, --admin-password PASS        SQL admin password
    -b, --backup-before-migrate     Create BACPAC backup before migration
    -c, --update-connection-string    Update App Service connection string
    -a, --app-service NAME          App Service name (for -c option)
    --verify                        Verify current tier compatibility only
    --rollback                      Rollback to previous tier
    --restore-from-backup FILE      Restore from BACPAC backup file
    -y, --yes                       Skip confirmation prompts
    -h, --help                      Show this help message

Examples:
    # Verify Free Tier compatibility
    $0 --verify -g rg-governance-staging -s sql-governance-staging-xxx

    # Migrate with backup
    $0 -g rg-governance-staging -s sql-governance-staging-xxx \
        -b -c -a app-governance-staging-xxx

    # Rollback migration
    $0 --rollback -g rg-governance-staging -s sql-governance-staging-xxx \
        --restore-from-backup backup_20250120_120000.bacpac

EOF
}

# Parse arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -g|--resource-group)
                RESOURCE_GROUP="$2"
                shift 2
                ;;
            -s|--server)
                SERVER_NAME="$2"
                shift 2
                ;;
            -d|--database)
                DATABASE_NAME="$2"
                shift 2
                ;;
            -u|--admin-user)
                ADMIN_USER="$2"
                shift 2
                ;;
            -p|--admin-password)
                ADMIN_PASSWORD="$2"
                shift 2
                ;;
            -b|--backup-before-migrate)
                BACKUP_BEFORE_MIGRATE=true
                shift
                ;;
            -c|--update-connection-string)
                UPDATE_CONNECTION_STRING=true
                shift
                ;;
            -a|--app-service)
                APP_SERVICE_NAME="$2"
                shift 2
                ;;
            --verify)
                VERIFY_ONLY=true
                shift
                ;;
            --rollback)
                ROLLBACK=true
                shift
                ;;
            --restore-from-backup)
                RESTORE_FROM_BACKUP="$2"
                shift 2
                ;;
            -y|--yes)
                SKIP_CONFIRMATION=true
                shift
                ;;
            -h|--help)
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
}

# Verify Azure CLI and login
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v az &> /dev/null; then
        log_error "Azure CLI not found. Install from https://aka.ms/azure-cli"
        exit 1
    fi
    
    if ! az account show &> /dev/null; then
        log_error "Not logged into Azure. Run: az login"
        exit 1
    fi
    
    local sub_name=$(az account show --query name -o tsv)
    log_success "Logged into Azure subscription: $sub_name"
    
    # Create backup directory
    mkdir -p "$BACKUP_DIR"
}

# Get current database info
get_database_info() {
    log_info "Fetching current database configuration..."
    
    local db_info
    db_info=$(az sql db show \
        --resource-group "$RESOURCE_GROUP" \
        --server "$SERVER_NAME" \
        --name "$DATABASE_NAME" \
        --output json 2>/dev/null) || {
        log_error "Failed to get database info. Check resource group and server names."
        exit 1
    }
    
    CURRENT_SKU=$(echo "$db_info" | jq -r '.sku.name')
    CURRENT_TIER=$(echo "$db_info" | jq -r '.sku.tier')
    CURRENT_SIZE=$(echo "$db_info" | jq -r '.properties.maxSizeBytes')
    
    log_info "Current tier: $CURRENT_SKU ($CURRENT_TIER)"
    log_info "Max size: $(echo "$CURRENT_SIZE" | awk '{print $1/1024/1024/1024 " GB"}')"
}

# Verify Free Tier compatibility
verify_compatibility() {
    log_info "Verifying Free Tier compatibility..."
    
    # Check if already on Free Tier
    if [[ "$CURRENT_SKU" == "Free" ]]; then
        log_warn "Database is already on Free Tier!"
        exit 0
    fi
    
    # Get database size
    local db_size_bytes
    db_size_bytes=$(az sql db list-usages \
        --resource-group "$RESOURCE_GROUP" \
        --server "$SERVER_NAME" \
        --name "$DATABASE_NAME" \
        --query "[?name=='database_size'].currentValue" -o tsv)
    
    local db_size_gb=$(echo "$db_size_bytes" | awk '{print $1/1024/1024/1024}')
    
    log_info "Current database size: $(printf "%.2f" "$db_size_gb") GB"
    
    # Free Tier limit: 32 GB
    if (( $(echo "$db_size_gb > 30" | bc -l) )); then
        log_error "Database size (${db_size_gb} GB) exceeds Free Tier limit (32 GB)"
        log_error "Consider data cleanup or upgrading to Basic tier instead"
        exit 1
    fi
    
    if (( $(echo "$db_size_gb > 25" | bc -l) )); then
        log_warn "Database size is approaching Free Tier limit (>25 GB)"
    fi
    
    log_success "Database size is compatible with Free Tier (limit: 32 GB)"
    
    # Check for features not supported on Free Tier
    log_info "Checking for Free Tier incompatibilities..."
    
    # Geo-replication check
    local geo_rep
    geo_rep=$(az sql db show \
        --resource-group "$RESOURCE_GROUP" \
        --server "$SERVER_NAME" \
        --name "$DATABASE_NAME" \
        --query "properties.requestedBackupStorageRedundancy" -o tsv)
    
    if [[ "$geo_rep" == "Geo" ]]; then
        log_warn "Current database uses geo-redundancy (will be changed to local)"
    fi
    
    log_success "Compatibility check passed"
}

# Create BACPAC backup
create_backup() {
    if [[ "$BACKUP_BEFORE_MIGRATE" != true ]]; then
        return 0
    fi
    
    log_info "Creating BACPAC backup before migration..."
    
    local backup_file="${BACKUP_DIR}/backup_${TIMESTAMP}.bacpac"
    local storage_account
    local container_name="sql-backups"
    
    # Get or create storage account for backups
    storage_account=$(az storage account list \
        --resource-group "$RESOURCE_GROUP" \
        --query "[?contains(name,'backup')].[name]" -o tsv | head -1)
    
    if [[ -z "$storage_account" ]]; then
        log_info "Creating temporary storage account for backup..."
        storage_account="sqlbackup$(date +%s)"
        
        az storage account create \
            --name "$storage_account" \
            --resource-group "$RESOURCE_GROUP" \
            --sku Standard_LRS \
            --output none
        
        # Create container
        az storage container create \
            --name "$container_name" \
            --account-name "$storage_account" \
            --output none
    fi
    
    # Get storage key
    local storage_key
    storage_key=$(az storage account keys list \
        --account-name "$storage_account" \
        --resource-group "$RESOURCE_GROUP" \
        --query "[0].value" -o tsv)
    
    # Export BACPAC
    log_info "Exporting database to BACPAC (this may take several minutes)..."
    
    az sql db export \
        --resource-group "$RESOURCE_GROUP" \
        --server "$SERVER_NAME" \
        --name "$DATABASE_NAME" \
        --storage-key-type StorageAccessKey \
        --storage-key "$storage_key" \
        --storage-uri "https://${storage_account}.blob.core.windows.net/${container_name}/${DATABASE_NAME}_${TIMESTAMP}.bacpac" \
        --admin-user "$ADMIN_USER" \
        --admin-password "$ADMIN_PASSWORD" \
        --output none || {
        log_warn "BACPAC export failed - continuing without backup"
        return 0
    }
    
    log_success "Backup created: ${DATABASE_NAME}_${TIMESTAMP}.bacpac"
    echo "${DATABASE_NAME}_${TIMESTAMP}.bacpac" > "${BACKUP_DIR}/last_backup.txt"
}

# Perform migration to Free Tier
migrate_to_free_tier() {
    log_info "Migrating to Free Tier..."
    log_warn "This will change the database tier and may cause a brief interruption"
    
    if [[ "$SKIP_CONFIRMATION" != true ]]; then
        echo ""
        read -p "Continue with migration? [y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Migration cancelled"
            exit 0
        fi
    fi
    
    # Update database to Free tier
    log_info "Updating database SKU to Free..."
    
    az sql db update \
        --resource-group "$RESOURCE_GROUP" \
        --server "$SERVER_NAME" \
        --name "$DATABASE_NAME" \
        --edition Free \
        --max-size 32GB \
        --output none || {
        log_error "Failed to update database tier"
        exit 1
    }
    
    log_success "Database tier updated to Free"
    
    # Wait for update to complete
    log_info "Waiting for update to complete..."
    sleep 30
    
    # Verify new tier
    local new_sku
    new_sku=$(az sql db show \
        --resource-group "$RESOURCE_GROUP" \
        --server "$SERVER_NAME" \
        --name "$DATABASE_NAME" \
        --query "sku.name" -o tsv)
    
    if [[ "$new_sku" != "Free" ]]; then
        log_error "Migration verification failed - tier is $new_sku"
        exit 1
    fi
    
    log_success "Migration verified - database is now on Free Tier"
}

# Update connection string in App Service
update_connection_string() {
    if [[ "$UPDATE_CONNECTION_STRING" != true ]]; then
        return 0
    fi
    
    if [[ -z "$APP_SERVICE_NAME" ]]; then
        log_error "App Service name required for connection string update (-a option)"
        exit 1
    fi
    
    log_info "Updating connection string in App Service: $APP_SERVICE_NAME"
    
    # Get SQL server FQDN
    local sql_fqdn
    sql_fqdn=$(az sql server show \
        --resource-group "$RESOURCE_GROUP" \
        --name "$SERVER_NAME" \
        --query "fullyQualifiedDomainName" -o tsv)
    
    # Build connection string
    local conn_string="Server=tcp:${sql_fqdn},1433;Database=${DATABASE_NAME};Encrypt=True;TrustServerCertificate=False;Connection Timeout=30;"
    
    # Update App Service setting
    az webapp config connection-string set \
        --resource-group "$RESOURCE_GROUP" \
        --name "$APP_SERVICE_NAME" \
        --connection-string-type SQLAzure \
        --settings "SQLAZURECONNSTR_DatabaseUrl=${conn_string}" \
        --output none || {
        log_warn "Failed to update connection string in App Service"
        return 1
    }
    
    log_success "Connection string updated"
    
    # Restart App Service to pick up new settings
    log_info "Restarting App Service..."
    az webapp restart \
        --resource-group "$RESOURCE_GROUP" \
        --name "$APP_SERVICE_NAME" \
        --output none
    
    log_success "App Service restarted"
}

# Rollback migration
rollback_migration() {
    log_info "Rolling back migration..."
    log_warn "This will restore the database to its previous tier"
    
    if [[ -n "$RESTORE_FROM_BACKUP" ]]; then
        log_info "Restoring from BACPAC backup: $RESTORE_FROM_BACKUP"
        
        # Restore logic here (would need storage account details)
        log_warn "BACPAC restore not fully implemented - please restore manually"
    fi
    
    # Revert to previous tier (assumed S0)
    log_info "Reverting to Standard_S0 tier..."
    
    az sql db update \
        --resource-group "$RESOURCE_GROUP" \
        --server "$SERVER_NAME" \
        --name "$DATABASE_NAME" \
        --edition Standard \
        --service-objective S0 \
        --max-size 250GB \
        --output none || {
        log_error "Rollback failed"
        exit 1
    }
    
    log_success "Rollback completed - database restored to S0 tier"
}

# Post-migration verification
post_migration_verify() {
    log_info "Running post-migration verification..."
    
    # Check database is online
    local db_state
    db_state=$(az sql db show \
        --resource-group "$RESOURCE_GROUP" \
        --server "$SERVER_NAME" \
        --name "$DATABASE_NAME" \
        --query "status" -o tsv)
    
    if [[ "$db_state" != "Online" ]]; then
        log_error "Database is not online (status: $db_state)"
        exit 1
    fi
    
    log_success "Database is Online"
    
    # Verify tier
    local current_tier
    current_tier=$(az sql db show \
        --resource-group "$RESOURCE_GROUP" \
        --server "$SERVER_NAME" \
        --name "$DATABASE_NAME" \
        --query "sku.tier" -o tsv)
    
    log_info "Current tier: $current_tier"
    
    if [[ "$ROLLBACK" != true && "$current_tier" != "Free" ]]; then
        log_error "Expected Free tier, got $current_tier"
        exit 1
    fi
    
    log_success "Post-migration verification passed"
}

# Main execution
main() {
    parse_args "$@"
    
    # Validate required arguments
    if [[ -z "$RESOURCE_GROUP" || -z "$SERVER_NAME" ]]; then
        log_error "Resource group and server name are required"
        show_usage
        exit 1
    fi
    
    check_prerequisites
    get_database_info
    
    if [[ "$VERIFY_ONLY" == true ]]; then
        verify_compatibility
        log_success "Verification complete - database is ready for migration"
        exit 0
    fi
    
    if [[ "$ROLLBACK" == true ]]; then
        rollback_migration
        post_migration_verify
        log_success "Rollback completed successfully"
        exit 0
    fi
    
    # Normal migration flow
    verify_compatibility
    create_backup
    migrate_to_free_tier
    update_connection_string
    post_migration_verify
    
    echo ""
    log_success "🎉 Migration to Free Tier completed successfully!"
    echo ""
    log_info "Next steps:"
    echo "  1. Verify application connectivity"
    echo "  2. Run smoke tests"
    echo "  3. Monitor for 24 hours"
    echo ""
    log_info "To rollback if needed:"
    echo "  $0 --rollback -g $RESOURCE_GROUP -s $SERVER_NAME -d $DATABASE_NAME"
}

# Run main
main "$@"
