#!/bin/bash
# =============================================================================
# Azure Governance Platform - GitHub Status Dashboard
# =============================================================================
# Quick status overview of repository, workflows, and deployments
#
# Usage:
#   ./scripts/gh-status.sh [options]
#
# Options:
#   -w, --watch          Continuous monitoring mode
#   -r, --repo           GitHub repo (owner/repo) [auto-detected]
   -l, --limit          Number of runs to show [default: 5]
#   -h, --help           Show help
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
WATCH=false
GITHUB_REPO=""
LIMIT=5

# Help
show_help() {
    cat << 'EOF'
GitHub Status Dashboard

Usage: ./scripts/gh-status.sh [options]

Options:
  -w, --watch      Continuous monitoring mode (refresh every 10s)
  -r, --repo       GitHub repo (owner/repo) [auto-detected]
  -l, --limit      Number of runs to show [default: 5]
  -h, --help       Show this help

Examples:
  ./scripts/gh-status.sh        # Show current status
  ./scripts/gh-status.sh -w     # Watch mode
  ./scripts/gh-status.sh -l 10  # Show 10 recent runs
EOF
}

# Parse args
while [[ $# -gt 0 ]]; do
    case $1 in
        -w|--watch) WATCH=true; shift ;;
        -r|--repo) GITHUB_REPO="$2"; shift 2 ;;
        -l|--limit) LIMIT="$2"; shift 2 ;;
        -h|--help) show_help; exit 0 ;;
        *) echo -e "${RED}Unknown option: $1${NC}"; show_help; exit 1 ;;
    esac
done

# Check gh CLI
if ! command -v gh &> /dev/null; then
    echo -e "${RED}gh CLI not found${NC}"
    exit 1
fi

# Get repo
if [[ -z "$GITHUB_REPO" ]]; then
    GITHUB_REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo "")
fi
[[ -z "$GITHUB_REPO" ]] && { echo -e "${RED}Could not detect repo${NC}"; exit 1; }

# Display function
display_status() {
    clear
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}📊 GitHub Status: ${CYAN}${GITHUB_REPO}${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    
    # Repository info
    echo -e "${YELLOW}Repository:${NC}"
    REPO_INFO=$(gh repo view --json defaultBranchRef,description,stargazerCount,forkCount -q '\(.defaultBranchRef.name) | Stars: \(.stargazerCount) | Forks: \(.forkCount)')
    echo "  $REPO_INFO"
    echo ""
    
    # Recent runs
    echo -e "${YELLOW}Recent Workflow Runs:${NC}"
    gh run list --limit "$LIMIT" --json databaseId,name,headBranch,status,conclusion,createdAt \
        -q '.[] | "  [\(.status)] \(.name) on \(.headBranch) - \(.conclusion // "running")"' 2>/dev/null || \
        echo "  (no runs found)"
    echo ""
    
    # Active runs
    ACTIVE=$(gh run list --status in_progress --json databaseId,name -q '.[] | "  \(.name)"' 2>/dev/null || echo "")
    if [[ -n "$ACTIVE" ]]; then
        echo -e "${YELLOW}🔄 Active Runs:${NC}"
        echo "$ACTIVE"
        echo ""
    fi
    
    # Pull requests
    echo -e "${YELLOW}Open Pull Requests:${NC}"
    PR_COUNT=$(gh pr list --json number --jq 'length')
    if [[ "$PR_COUNT" -gt 0 ]]; then
        gh pr list --limit 5 --json number,title,author,headRefName \
            -q '.[] | "  #\(.number): \(.title) by @\(.author.login)"'
    else
        echo "  (none)"
    fi
    echo ""
    
    # Environments
    echo -e "${YELLOW}Environments:${NC}"
    gh api "repos/$GITHUB_REPO/environments" --jq '.environments[] | "  - \(.name)"' 2>/dev/null || echo "  (none configured)"
    echo ""
    
    # Secrets count
    SECRET_COUNT=$(gh secret list --json name --jq 'length' 2>/dev/null || echo "0")
    echo -e "${YELLOW}Secrets: ${SECRET_COUNT} configured${NC}"
    echo ""
    
    echo -e "${BLUE}========================================${NC}"
    echo -e "Last updated: $(date '+%Y-%m-%d %H:%M:%S')"
}

# Main loop
if [[ "$WATCH" == true ]]; then
    echo -e "${YELLOW}Watch mode enabled. Press Ctrl+C to exit.${NC}"
    sleep 2
    while true; do
        display_status
        sleep 10
    done
else
    display_status
fi
