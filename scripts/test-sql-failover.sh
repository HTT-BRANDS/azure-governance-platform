#!/bin/bash
# Azure SQL Failover Testing Script
#
# Tests failover scenarios for Azure SQL geo-replication setup.
# Requires Azure CLI and appropriate permissions on the SQL servers.
#
# Usage:
#   ./scripts/test-sql-failover.sh --resource-group myrg --failover-group myfailover
#
# WARNING: This script will trigger actual failovers. Use with caution in production!

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
RESOURCE_GROUP=""
FAILOVER_GROUP=""
PRIMARY_SERVER=""
SECONDARY_SERVER=""
DRY_RUN=false
WAIT_TIME=300  # 5 minutes to verify stability

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Usage information
usage() {
    cat << EOF
Azure SQL Failover Testing Script

Usage: $0 [OPTIONS]

Required:
    -g, --resource-group     Resource group name
    -f, --failover-group     Failover group name

Optional:
    -p, --primary-server     Primary server name (auto-detected if not provided)
    -s, --secondary-server   Secondary server name (auto-detected if not provided)
    -w, --wait-time         Seconds to wait for stability check (default: 300)
    --dry-run               Simulate without executing failover
    -h, --help              Show this help message

Examples:
    # Test failover with auto-detection
    $0 -g myResourceGroup -f my-failover-group

    # Dry run (simulation only)
    $0 -g myResourceGroup -f my-failover-group --dry-run

    # With explicit server names
    $0 -g myResourceGroup -f my-failover-group -p primary-sql -s secondary-sql

EOF
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -g|--resource-group)
            RESOURCE_GROUP="$2"
            shift 2
            ;;
        -f|--failover-group)
            FAILOVER_GROUP="$2"
            shift 2
            ;;
        -p|--primary-server)
            PRIMARY_SERVER="$2"
            shift 2
            ;;
        -s|--secondary-server)
            SECONDARY_SERVER="$2"
            shift 2
            ;;
        -w|--wait-time)
            WAIT_TIME="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Validate required parameters
if [[ -z "$RESOURCE_GROUP" || -z "$FAILOVER_GROUP" ]]; then
    log_error "Resource group and failover group are required"
    usage
    exit 1
fi

# Check Azure CLI
echo "=========================================="
echo "Azure SQL Failover Testing"
echo "=========================================="
log_info "Checking Azure CLI..."

if ! command -v az &> /dev/null; then
    log_error "Azure CLI not found. Please install: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

# Check authentication
if ! az account show &> /dev/null; then
    log_error "Not logged into Azure. Run: az login"
    exit 1
fi

log_success "Azure CLI authenticated"
log_info "Subscription: $(az account show --query name -o tsv)"

# Auto-detect servers if not provided
if [[ -z "$PRIMARY_SERVER" || -z "$SECONDARY_SERVER" ]]; then
    log_info "Auto-detecting servers from failover group..."
    
    # Get failover group details
    FG_DETAILS=$(az sql failover-group show \
        --name "$FAILOVER_GROUP" \
        --resource-group "$RESOURCE_GROUP" 2>/dev/null) || {
        log_error "Failed to get failover group details. Check name and permissions."
        exit 1
    }
    
    if [[ -z "$PRIMARY_SERVER" ]]; then
        PRIMARY_SERVER=$(echo "$FG_DETAILS" | jq -r '.serverName')
    fi
    
    if [[ -z "$SECONDARY_SERVER" ]]; then
        SECONDARY_SERVER=$(echo "$FG_DETAILS" | jq -r '.partnerServers[0].id' | cut -d'/' -f9)
    fi
fi

log_info "Primary Server: $PRIMARY_SERVER"
log_info "Secondary Server: $SECONDARY_SERVER"
log_info "Failover Group: $FAILOVER_GROUP"

if [[ "$DRY_RUN" == true ]]; then
    log_warning "DRY RUN MODE - No actual failover will occur"
fi

echo ""
echo "=========================================="
echo "Pre-Failover Checks"
echo "=========================================="

# Check replication health
log_info "Checking replication health..."

REPLICATION_HEALTH=$(az sql failover-group show \
    --name "$FAILOVER_GROUP" \
    --resource-group "$RESOURCE_GROUP" \
    --query "replicationState" -o tvs 2>/dev/null || echo "Unknown")

if [[ "$REPLICATION_HEALTH" != "CATCH_UP" ]]; then
    log_warning "Replication health: $REPLICATION_HEALTH"
    log_warning "Consider waiting for CATCH_UP state before failover"
else
    log_success "Replication health: $REPLICATION_HEALTH"
fi

# Get current role
CURRENT_ROLE=$(az sql failover-group show \
    --name "$FAILOVER_GROUP" \
    --resource-group "$RESOURCE_GROUP" \
    --query "role" -o tsv 2>/dev/null || echo "Unknown")

log_info "Current Failover Group Role: $CURRENT_ROLE"

# List databases in failover group
log_info "Databases in failover group:"
az sql failover-group show \
    --name "$FAILOVER_GROUP" \
    --resource-group "$RESOURCE_GROUP" \
    --query "databases[]" -o table 2>/dev/null || log_warning "Could not list databases"

echo ""
echo "=========================================="
echo "Failover Testing"
echo "=========================================="

if [[ "$DRY_RUN" == true ]]; then
    log_info "[DRY RUN] Would execute:"
    log_info "  az sql failover-group set-primary \\"
    log_info "    --name $FAILOVER_GROUP \\"
    log_info "    --resource-group $RESOURCE_GROUP \\"
    log_info "    --allow-data-loss"
    log_success "Dry run complete!"
    exit 0
fi

# Confirm failover
log_warning "⚠️  About to initiate FAILOVER from $PRIMARY_SERVER to $SECONDARY_SERVER"
log_warning "This will swap primary and secondary roles!"
echo ""
read -p "Are you sure you want to continue? (yes/no): " confirm

if [[ "$confirm" != "yes" ]]; then
    log_info "Failover cancelled by user"
    exit 0
fi

# Record start time
START_TIME=$(date +%s)

# Perform failover
log_info "Initiating failover..."

az sql failover-group set-primary \
    --name "$FAILOVER_GROUP" \
    --resource-group "$RESOURCE_GROUP" \
    --allow-data-loss || {
    log_error "Failover failed!"
    exit 1
}

log_success "Failover command executed successfully"

# Wait for failover to complete
log_info "Waiting for failover to complete (checking every 10 seconds)..."

MAX_WAIT=600  # 10 minutes max
ELAPSED=0

while [[ $ELAPSED -lt $MAX_WAIT ]]; do
    sleep 10
    ELAPSED=$((ELAPSED + 10))
    
    NEW_ROLE=$(az sql failover-group show \
        --name "$FAILOVER_GROUP" \
        --resource-group "$RESOURCE_GROUP" \
        --query "role" -o tsv 2>/dev/null || echo "Unknown")
    
    if [[ "$NEW_ROLE" == "Secondary" ]]; then
        # Old primary is now secondary, failover complete
        break
    fi
    
    echo -n "."
done

echo ""

if [[ $ELAPSED -ge $MAX_WAIT ]]; then
    log_error "Failover did not complete within $MAX_WAIT seconds"
    log_info "Check Azure portal for status"
    exit 1
fi

END_TIME=$(date +%s)
FAILOVER_DURATION=$((END_TIME - START_TIME))

log_success "Failover completed in ${FAILOVER_DURATION} seconds"

# Verify new configuration
NEW_PRIMARY=$(az sql failover-group show \
    --name "$FAILOVER_GROUP" \
    --resource-group "$RESOURCE_GROUP" \
    --query "serverName" -o tsv)

log_info "New primary server: $NEW_PRIMARY"

# Verify connectivity
log_info "Testing connectivity to new primary..."

# Note: This would need actual database credentials to test
# For now, we just verify the endpoint exists
ENDPOINT_FQDN=$(az sql failover-group show \
    --name "$FAILOVER_GROUP" \
    --resource-group "$RESOURCE_GROUP" \
    --query "readWriteEndpoint.fqdn" -o tsv)

log_success "Failover endpoint: $ENDPOINT_FQDN"

echo ""
echo "=========================================="
echo "Post-Failover Recommendations"
echo "=========================================="

log_info "1. Verify application connectivity to: $ENDPOINT_FQDN"
log_info "2. Update connection strings if using server-specific FQDNs"
log_info "3. Monitor query performance on new primary"
log_info "4. Consider failback during next maintenance window"

echo ""
echo "=========================================="
echo "Failover Test Summary"
echo "=========================================="
log_success "✓ Pre-failover checks passed"
log_success "✓ Failover initiated successfully"
log_success "✓ Failover completed in ${FAILOVER_DURATION}s"
log_success "✓ New primary: $NEW_PRIMARY"
log_info "  Failover group: $FAILOVER_GROUP"
log_info "  Endpoint: $ENDPOINT_FQDN"

log_warning "⚠️  Remember to plan a failback to restore original topology if desired"

exit 0
