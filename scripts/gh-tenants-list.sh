#!/bin/bash
# List all configured Riverside tenants

REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)

echo "🏢 Riverside Tenants Configuration"
echo "=================================="
echo ""

echo "Variables:"
gh variable list --repo $REPO | grep RIVERSIDE || echo "  None configured"

echo ""
echo "Secrets (IDs only):"
gh secret list --repo $REPO | grep RIVERSIDE || echo "  None configured"

echo ""
echo "To update secrets:"
echo "  gh secret set RIVERSIDE_<CODE>_CLIENT_ID -b '<client-id>'"
echo "  gh secret set RIVERSIDE_<CODE>_CLIENT_SECRET -b '<secret>'"
