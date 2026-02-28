#!/bin/bash
# =============================================================================
# Azure Governance Platform - Deploy to Dev Environment
# =============================================================================
# Deploy to dev environment using gh CLI and git workflows
#
# Usage:
#   ./scripts/gh-deploy-dev.sh [options]
#
# Options:
#   -w, --watch          Watch deployment progress (default)
#   --no-watch           Don't watch, just trigger
#   -f, --force          Force push (use with caution)
#   -s, --sync           Sync with main before deploying
#   --skip-tests         Skip test execution
#   -h, --help           Show help
#
# Examples:
#   ./scripts/gh-deploy-dev.sh           # Deploy to dev with watch
#   ./scripts/gh-deploy-dev.sh --no-watch # Trigger and exit
#   ./scripts/gh-deploy-dev.sh -s -f     # Sync, force push, watch
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Default values
WATCH=true
FORCE=false
SYNC=false
SKIP_TESTS=false

# Help function
show_help() {
    cat << 'EOF'
Azure Governance Platform - Dev Deployment

Usage: ./scripts/gh-deploy-dev.sh [options]

Options:
  -w, --watch      Watch deployment progress (default: true)
  --no-watch       Don't watch, just trigger deployment
  -f, --force      Force push (use with caution)
  -s, --sync       Sync with main before deploying
  --skip-tests     Skip test execution
  -h, --help       Show this help

Examples:
  ./scripts/gh-deploy-dev.sh              # Deploy with watch
  ./scripts/gh-deploy-dev.sh --no-watch   # Trigger and exit
  ./scripts/gh-deploy-dev.sh -s -f        # Sync, force push

Description:
  This script deploys the current branch to the development environment
  by pushing to the 'dev' branch, which triggers GitHub Actions workflows.
EOF
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -w|--watch)
            WATCH=true
            shift
            ;;
        --no-watch)
            WATCH=false
            shift
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        -s|--sync)
            SYNC=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Header
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}🚀 Deploying to Development${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

# Check git
if ! git rev-parse --git-dir &> /dev/null; then
    echo -e "${RED}❌ Not in a git repository${NC}"
    exit 1
fi
echo -e "  ${GREEN}✓${NC} Git repository found"

# Check gh CLI
if ! command -v gh &> /dev/null; then
    echo -e "${RED}❌ gh CLI not found. Install: https://cli.github.com/${NC}"
    exit 1
fi
echo -e "  ${GREEN}✓${NC} gh CLI found"

# Check gh auth
if ! gh auth status &> /dev/null; then
    echo -e "${RED}❌ Not logged in to GitHub. Run: gh auth login${NC}"
    exit 1
fi
echo -e "  ${GREEN}✓${NC} GitHub authenticated"

# Get current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo -e "  Current branch: ${CYAN}$CURRENT_BRANCH${NC}"

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo -e "${YELLOW}⚠️  You have uncommitted changes${NC}"
    read -p "Commit changes before deploying? (y/n): " COMMIT_CHANGES
    if [[ "$COMMIT_CHANGES" =~ ^[Yy]$ ]]; then
        read -p "Enter commit message: " COMMIT_MSG
        git add -A
        git commit -m "${COMMIT_MSG:-Deploy to dev}"
        echo -e "  ${GREEN}✓${NC} Changes committed"
    else
        echo -e "${YELLOW}⚠️  Proceeding with uncommitted changes...${NC}"
    fi
fi

# Sync with main if requested
if [[ "$SYNC" == true ]]; then
    echo ""
    echo -e "${YELLOW}Syncing with main...${NC}"
    git fetch origin main
    git merge origin/main --no-edit || {
        echo -e "${RED}❌ Merge conflict with main. Please resolve manually.${NC}"
        exit 1
    }
    echo -e "  ${GREEN}✓${NC} Synced with main"
fi

# Push to dev branch
echo ""
echo -e "${YELLOW}Pushing to dev branch...${NC}"

# Create dev branch if it doesn't exist
if ! git show-ref --verify --quiet refs/heads/dev; then
    echo "  Creating dev branch..."
    git branch dev
fi

# Checkout dev branch
git checkout dev

# Merge current branch
echo "  Merging $CURRENT_BRANCH into dev..."
git merge "$CURRENT_BRANCH" --no-edit -m "Merge $CURRENT_BRANCH for dev deployment"

# Push to origin
PUSH_FLAGS=""
if [[ "$FORCE" == true ]]; then
    echo -e "  ${YELLOW}⚠️  Force pushing...${NC}"
    PUSH_FLAGS="--force-with-lease"
fi

echo "  Pushing to origin/dev..."
git push origin dev $PUSH_FLAGS

echo -e "  ${GREEN}✓${NC} Pushed to dev branch"

# Switch back to original branch
git checkout "$CURRENT_BRANCH"

# Watch deployment
echo ""
if [[ "$WATCH" == true ]]; then
    echo -e "${YELLOW}Monitoring deployment...${NC}"
    echo ""
    
    # Wait a moment for the workflow to start
    sleep 3
    
    # Get the latest run
    LATEST_RUN=$(gh run list --branch dev --limit 1 --json databaseId -q '.[0].databaseId')
    
    if [[ -n "$LATEST_RUN" ]]; then
        echo -e "Watching run: ${CYAN}$LATEST_RUN${NC}"
        echo ""
        gh run watch "$LATEST_RUN"
        
        # Check result
        RUN_STATUS=$(gh run view "$LATEST_RUN" --json conclusion -q '.conclusion')
        
        echo ""
        if [[ "$RUN_STATUS" == "success" ]]; then
            echo -e "${GREEN}✅ Deployment successful!${NC}"
            
            # Run verification if available
            if [[ -f "$SCRIPT_DIR/verify-dev-deployment.sh" ]]; then
                echo ""
                echo -e "${YELLOW}Running deployment verification...${NC}"
                "$SCRIPT_DIR/verify-dev-deployment.sh"
            fi
            
            # Show deployment URL
            echo ""
            echo -e "${CYAN}Deployment URL:${NC}"
            echo "  https://app-governance-dev-001.azurewebsites.net"
            
        else
            echo -e "${RED}❌ Deployment failed with status: $RUN_STATUS${NC}"
            echo ""
            echo -e "View logs: ${CYAN}gh run view $LATEST_RUN${NC}"
            exit 1
        fi
    else
        echo -e "${YELLOW}⚠️  No workflow run found yet${NC}"
        echo "Check status with: gh run list"
    fi
else
    echo -e "${GREEN}✓${NC} Deployment triggered (not watching)"
    echo ""
    echo -e "Monitor with: ${CYAN}gh run watch --branch dev${NC}"
    echo -e "View runs:    ${CYAN}gh run list --branch dev${NC}"
fi

# Run tests if not skipped
if [[ "$SKIP_TESTS" == false ]] && [[ "$WATCH" == true ]]; then
    echo ""
    echo -e "${YELLOW}Running tests...${NC}"
    
    if [[ -f "$PROJECT_ROOT/pyproject.toml" ]]; then
        cd "$PROJECT_ROOT"
        if python -m pytest tests/ -v --tb=short 2>/dev/null; then
            echo -e "  ${GREEN}✓${NC} Tests passed"
        else
            echo -e "  ${YELLOW}⚠${NC} Some tests failed (check output above)"
        fi
    else
        echo -e "  ${YELLOW}⚠${NC} No test configuration found"
    fi
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}🎉 Dev deployment complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Quick commands:"
echo "  gh run list --branch dev    # List dev runs"
echo "  gh run watch --branch dev   # Watch latest run"
echo "  gh repo view --web          # Open repo in browser"
