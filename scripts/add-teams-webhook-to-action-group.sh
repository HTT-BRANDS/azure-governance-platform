#!/bin/bash
# =============================================================================
# add-teams-webhook-to-action-group.sh — 6wyk
# =============================================================================
#
# Adds a Teams incoming webhook receiver to the governance-alerts action group.
# This is the "placeholder now, real URL later" scaffold — SharePoint sites and
# Teams channels are still being finalized. Once decided, just update the
# TEAMS_WEBHOOK_URL value and re-run.
#
# PREREQUISITES:
#   1. Teams channel exists (ops/alerts or wherever you land it)
#   2. Teams incoming webhook created in that channel:
#      - Channel → ⋯ → Connectors → Incoming Webhook → Configure
#      - Name it: "governance-alerts"
#      - Upload logo if desired
#      - Copy the generated webhook URL
#   3. az CLI authenticated to HTT-CORE subscription
#
# USAGE:
#   TEAMS_WEBHOOK_URL='https://httbrands.webhook.office.com/...' \
#     ./scripts/add-teams-webhook-to-action-group.sh
#
#   # Or edit the placeholder below and run without env var:
#   ./scripts/add-teams-webhook-to-action-group.sh
#
# =============================================================================

set -euo pipefail

# ── Config ──────────────────────────────────────────────────────────────────
SUBSCRIPTION="HTT-CORE"
RESOURCE_GROUP="rg-governance-production"
ACTION_GROUP="governance-alerts"
RECEIVER_NAME="teams-alerts"

# Placeholder. Override via env var OR replace inline when the real URL is ready.
TEAMS_WEBHOOK_URL="${TEAMS_WEBHOOK_URL:-REPLACE_WITH_REAL_TEAMS_WEBHOOK_URL}"

# ── Colors ──
if [ -t 1 ]; then
    RED=$'\033[0;31m'; GREEN=$'\033[0;32m'; YELLOW=$'\033[1;33m'; NC=$'\033[0m'
else
    RED=""; GREEN=""; YELLOW=""; NC=""
fi

# ── Guard against the placeholder ──
if [[ "$TEAMS_WEBHOOK_URL" == REPLACE_* ]] || [[ -z "$TEAMS_WEBHOOK_URL" ]]; then
    echo -e "${RED}✗ TEAMS_WEBHOOK_URL is still a placeholder.${NC}"
    echo ""
    echo "  Set it via env var:"
    echo "    TEAMS_WEBHOOK_URL='https://httbrands.webhook.office.com/...' \\"
    echo "      ./scripts/add-teams-webhook-to-action-group.sh"
    echo ""
    echo "  …or edit this script and replace the placeholder inline."
    exit 1
fi

# Basic sanity check on URL shape (Teams webhooks are *.webhook.office.com)
if [[ ! "$TEAMS_WEBHOOK_URL" =~ ^https://.*\.webhook\.office\.com/.* ]]; then
    echo -e "${YELLOW}⚠ URL doesn't look like a Teams incoming webhook.${NC}"
    echo "  Expected: https://<tenant>.webhook.office.com/webhookb2/..."
    echo "  Got:      $TEAMS_WEBHOOK_URL"
    read -r -p "  Continue anyway? [y/N] " reply
    case "$reply" in y|Y|yes|YES) ;; *) echo "Aborted."; exit 0 ;; esac
fi

echo -e "${YELLOW}→${NC} Setting subscription to $SUBSCRIPTION..."
az account set --subscription "$SUBSCRIPTION"

echo -e "${YELLOW}→${NC} Adding '$RECEIVER_NAME' webhook receiver to '$ACTION_GROUP'..."
az monitor action-group update \
    --name "$ACTION_GROUP" \
    --resource-group "$RESOURCE_GROUP" \
    --add-action webhook "$RECEIVER_NAME" "$TEAMS_WEBHOOK_URL"

echo ""
echo -e "${GREEN}✓ Webhook added.${NC}"
echo ""
echo "Verify in portal:"
echo "  https://portal.azure.com/#@/resource/subscriptions/32a28177-6fb2-4668-a528-6d6cafb9665e/resourceGroups/$RESOURCE_GROUP/providers/microsoft.insights/actionGroups/$ACTION_GROUP"
echo ""
echo "Test it by firing a test alert:"
echo "  az monitor action-group test-notifications create \\"
echo "    --action-group $ACTION_GROUP \\"
echo "    --resource-group $RESOURCE_GROUP \\"
echo "    --notification-type Webhook \\"
echo "    --receivers $RECEIVER_NAME \\"
echo "    --alert-type servicehealth"
