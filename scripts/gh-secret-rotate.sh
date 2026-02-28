#!/bin/bash
# =============================================================================
# Azure Governance Platform - Secret Rotation
# =============================================================================
# Rotate GitHub secrets securely
#
# Usage:
#   ./scripts/gh-secret-rotate.sh [options] <secret-name>
#
# Options:
#   -e, --env            Environment (dev|staging|prod) [default: repository]
#   -r, --repo           GitHub repo (owner/repo) [auto-detected]
#   -g, --generate       Generate new random value
#   -v, --value          New value (prompt if not provided)
#   --delete             Delete secret instead of rotating
#   -h, --help           Show help
#
# Examples:
#   ./scripts/gh-secret-rotate.sh DATABASE_ENCRYPTION_KEY --generate
#   ./scripts/gh-secret-rotate.sh API_KEY -v "new-value"
#   ./scripts/gh-secret-rotate.sh OLD_SECRET --delete
# =============================================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Defaults
ENV=""
GITHUB_REPO=""
GENERATE=false
VALUE=""
DELETE=false
SECRET_NAME=""

# Help
show_help() {
    cat << 'EOF'
Secret Rotation Utility

Usage: ./scripts/gh-secret-rotate.sh [options] <secret-name>

Options:
  -e, --env        Environment (dev|staging|prod) [default: repository]
  -r, --repo       GitHub repo (owner/repo) [auto-detected]
  -g, --generate   Generate new random value
  -v, --value      New value (prompt if not provided)
  --delete         Delete secret instead of rotating
  -h, --help       Show this help

Examples:
  ./scripts/gh-secret-rotate.sh DATABASE_KEY -g
  ./scripts/gh-secret-rotate.sh API_KEY -v "secret123" -e production
  ./scripts/gh-secret-rotate.sh OLD_SECRET --delete

Security Note:
  - Values are never logged or displayed
  - Generated secrets use cryptographically secure random
  - Old values are not recoverable after rotation
EOF
}

# Parse args
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--env) ENV="$2"; shift 2 ;;
        -r|--repo) GITHUB_REPO="$2"; shift 2 ;;
        -g|--generate) GENERATE=true; shift ;;
        -v|--value) VALUE="$2"; shift 2 ;;
        --delete) DELETE=true; shift ;;
        -h|--help) show_help; exit 0 ;;
        -*)
            if [[ "$1" == -* ]]; then
                echo -e "${RED}Unknown option: $1${NC}"
                show_help
                exit 1
            fi
            SECRET_NAME="$1"
            shift
            ;;
        *)
            SECRET_NAME="$1"
            shift
            ;;
    esac
done

# Validate
if [[ -z "$SECRET_NAME" ]]; then
    echo -e "${RED}Error: Secret name required${NC}"
    show_help
    exit 1
fi

# Check gh
if ! command -v gh &> /dev/null; then
    echo -e "${RED}gh CLI not found${NC}"
    exit 1
fi

# Get repo
if [[ -z "$GITHUB_REPO" ]]; then
    GITHUB_REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo "")
fi
[[ -z "$GITHUB_REPO" ]] && { echo -e "${RED}Could not detect repo${NC}"; exit 1; }

# Header
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}🔐 Secret Rotation${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Repository: ${CYAN}${GITHUB_REPO}${NC}"
echo -e "Secret: ${CYAN}${SECRET_NAME}${NC}"
[[ -n "$ENV" ]] && echo -e "Environment: ${CYAN}${ENV}${NC}"
echo ""

# Check if secret exists
ENV_FLAG=""
[[ -n "$ENV" ]] && ENV_FLAG="--env $ENV"

if ! gh secret list --repo "$GITHUB_REPO" $ENV_FLAG 2>/dev/null | grep -q "^${SECRET_NAME}\s"; then
    echo -e "${YELLOW}⚠️  Secret '${SECRET_NAME}' does not exist${NC}"
    if [[ "$DELETE" == true ]]; then
        echo "Nothing to delete."
        exit 0
    fi
    echo "Will create new secret."
fi

# Delete mode
if [[ "$DELETE" == true ]]; then
    read -p "Are you sure you want to delete '${SECRET_NAME}'? (yes/no): " CONFIRM
    if [[ "$CONFIRM" == "yes" ]]; then
        gh secret remove "$SECRET_NAME" --repo "$GITHUB_REPO" $ENV_FLAG
        echo -e "${GREEN}✓ Secret deleted${NC}"
    else
        echo "Cancelled."
        exit 0
    fi
    exit 0
fi

# Get new value
if [[ "$GENERATE" == true ]]; then
    # Generate cryptographically secure random value
    VALUE=$(openssl rand -base64 32)
    echo -e "${GREEN}✓ Generated new random value${NC}"
elif [[ -z "$VALUE" ]]; then
    # Prompt for value (hidden input)
    read -s -p "Enter new value for '${SECRET_NAME}': " VALUE
    echo ""
    read -s -p "Confirm value: " CONFIRM_VALUE
    echo ""
    
    if [[ "$VALUE" != "$CONFIRM_VALUE" ]]; then
        echo -e "${RED}Error: Values do not match${NC}"
        exit 1
    fi
    
    if [[ -z "$VALUE" ]]; then
        echo -e "${RED}Error: Value cannot be empty${NC}"
        exit 1
    fi
fi

# Set secret
echo "Setting secret..."
echo "$VALUE" | gh secret set "$SECRET_NAME" --repo "$GITHUB_REPO" $ENV_FLAG

# Verify
if gh secret list --repo "$GITHUB_REPO" $ENV_FLAG 2>/dev/null | grep -q "^${SECRET_NAME}\s"; then
    echo -e "${GREEN}✓ Secret '${SECRET_NAME}' updated successfully${NC}"
else
    echo -e "${RED}✗ Failed to verify secret${NC}"
    exit 1
fi

# Show next steps
echo ""
echo -e "${YELLOW}Next steps:${NC}"
if [[ -n "$ENV" ]]; then
    echo "  - Trigger deployment to ${ENV} environment"
else
    echo "  - Re-run workflows that use this secret"
fi
echo "  - Verify application functionality"
echo "  - Update any dependent documentation"
