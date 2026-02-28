#!/bin/bash
# Configure Riverside tenants using GitHub CLI
# Sets up tenant-specific variables and secrets

set -e

REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)

echo "🔧 Configuring Riverside Tenants for $REPO"
echo ""

# Define Riverside tenants
TENANTS=(
  "HTT:0c0e35dc-188a-4eb3-b8ba-61752154b407:tyler.granlund-admin@httbrands.com"
  "BCC:b5380912-79ec-452d-a6ca-6d897b19b294:tyler.granlund-Admin@bishopsbs.onmicrosoft.com"
  "FN:98723287-044b-4bbb-9294-19857d4128a0:tyler.granlund-Admin@ftgfrenchiesoutlook.onmicrosoft.com"
  "TLL:3c7d2bf3-b597-4766-b5cb-2b489c2904d6:tyler.granlund-Admin@LashLoungeFranchise.onmicrosoft.com"
)

echo "Setting up GitHub Variables for tenants..."
echo ""

for tenant in "${TENANTS[@]}"; do
  IFS=':' read -r CODE ID EMAIL <<< "$tenant"
  
  echo "  Setting variables for $CODE..."
  
  # Set as GitHub Variables (not secrets - these are IDs, not credentials)
  echo "$ID" | gh variable set "RIVERSIDE_${CODE}_TENANT_ID" --repo $REPO
  echo "$EMAIL" | gh variable set "RIVERSIDE_${CODE}_ADMIN_EMAIL" --repo $REPO
  
  echo "    ✓ RIVERSIDE_${CODE}_TENANT_ID"
  echo "    ✓ RIVERSIDE_${CODE}_ADMIN_EMAIL"
done

echo ""
echo "Setting up placeholder secrets (to be filled in later)..."
echo ""

for tenant in "${TENANTS[@]}"; do
  IFS=':' read -r CODE ID EMAIL <<< "$tenant"
  
  echo "  Setting placeholder for $CODE client ID..."
  echo "placeholder" | gh secret set "RIVERSIDE_${CODE}_CLIENT_ID" --repo $REPO 2>/dev/null || true
  
echo ""
echo "✅ Tenant configuration complete!"
echo ""
echo "Next: Set up app registrations and update secrets:"
echo "  ./scripts/setup-tenant-apps.ps1"
echo ""
echo "Current tenant variables:"
gh variable list --repo $REPO | grep RIVERSIDE
