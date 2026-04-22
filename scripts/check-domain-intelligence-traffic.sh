#!/bin/bash
# =============================================================================
# check-domain-intelligence-traffic.sh — rtwi (open, trigger ~2026-05-17)
# =============================================================================
#
# Zero-traffic verification + opt-in stop for domain-intelligence-prod.
# Discovered-from: bd-w1cc audit (closed 2026-04-17).
#
# CONTEXT:
#   The domain-intelligence-prod App Service had ZERO requests in 30+ days
#   when audited. If it remains zero-traffic at the 60-day mark, stop it to
#   save ~$28–30/mo ($13 App Service + $15–18 PostgreSQL flex).
#
# USAGE:
#   ./scripts/check-domain-intelligence-traffic.sh              # dry-run
#   ./scripts/check-domain-intelligence-traffic.sh --stop       # stop if zero
#   ./scripts/check-domain-intelligence-traffic.sh --force-stop # skip prompt
#
# EXIT CODES:
#   0 = no action taken (dry-run, or traffic found, or user declined)
#   1 = error (az CLI failure, auth, etc)
#   2 = zero traffic confirmed + resources stopped
#
# =============================================================================

set -euo pipefail

# ── Config ──────────────────────────────────────────────────────────────────
SUBSCRIPTION="HTT-CORE"
RESOURCE_GROUP="rg-htt-domain-intelligence"
APP_NAME="domain-intelligence-prod"
PG_NAME="domainiq-db-prod"
LOOKBACK_DAYS=30
TRIGGER_DATE_NOTE="~2026-05-17"

# ── Flags ──
STOP=false
FORCE=false
for arg in "$@"; do
    case "$arg" in
        --stop)       STOP=true ;;
        --force-stop) STOP=true; FORCE=true ;;
        -h|--help)
            sed -n '3,25p' "$0"
            exit 0
            ;;
        *) echo "Unknown flag: $arg" >&2; exit 1 ;;
    esac
done

# ── Colors ──
if [ -t 1 ]; then
    RED=$'\033[0;31m'; GREEN=$'\033[0;32m'; YELLOW=$'\033[1;33m'
    BLUE=$'\033[0;34m'; NC=$'\033[0m'
else
    RED=""; GREEN=""; YELLOW=""; BLUE=""; NC=""
fi

echo -e "${BLUE}╭─ domain-intelligence traffic check ───────────────────────────╮${NC}"
echo -e "${BLUE}│${NC}   Subscription:     $SUBSCRIPTION"
echo -e "${BLUE}│${NC}   Resource group:   $RESOURCE_GROUP"
echo -e "${BLUE}│${NC}   App Service:      $APP_NAME"
echo -e "${BLUE}│${NC}   PostgreSQL:       $PG_NAME"
echo -e "${BLUE}│${NC}   Lookback window:  last $LOOKBACK_DAYS days"
echo -e "${BLUE}│${NC}   Trigger date:     $TRIGGER_DATE_NOTE"
echo -e "${BLUE}│${NC}   Mode:             $([ "$STOP" = true ] && echo "STOP-IF-ZERO" || echo "DRY-RUN (pass --stop to enable)")"
echo -e "${BLUE}╰────────────────────────────────────────────────────────────────╯${NC}"
echo ""

# ── Ensure az CLI logged in ──
az account show >/dev/null 2>&1 || { echo -e "${RED}✗ Not logged in. Run: az login${NC}"; exit 1; }
az account set --subscription "$SUBSCRIPTION"

# ── Resolve App Service resource ID ──
APP_ID=$(az webapp show -g "$RESOURCE_GROUP" -n "$APP_NAME" --query id -o tsv 2>/dev/null || echo "")
if [ -z "$APP_ID" ]; then
    echo -e "${RED}✗ App Service $APP_NAME not found in $RESOURCE_GROUP${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} App Service resource: $APP_ID"

# ── Query request metric over lookback window ──
# macOS (BSD date) and Linux (GNU date) differ — prefer portable POSIX shell date.
if date -u -v-1d +%Y-%m-%dT%H:%M:%SZ >/dev/null 2>&1; then
    START=$(date -u -v-${LOOKBACK_DAYS}d +%Y-%m-%dT%H:%M:%SZ)
else
    START=$(date -u -d "-${LOOKBACK_DAYS} days" +%Y-%m-%dT%H:%M:%SZ)
fi

echo -e "${YELLOW}→${NC} Querying Requests metric since $START..."
TOTAL=$(az monitor metrics list \
    --resource "$APP_ID" \
    --metric Requests \
    --interval P1D \
    --start-time "$START" \
    --aggregation Total \
    --query 'value[0].timeseries[0].data[].total' -o tsv 2>/dev/null \
    | awk 'BEGIN{s=0} {s+=$1} END{print s+0}')

echo -e "${GREEN}✓${NC} Total requests in last $LOOKBACK_DAYS days: ${BLUE}$TOTAL${NC}"
echo ""

# ── Decide ──
if [ "$TOTAL" -gt 0 ]; then
    echo -e "${YELLOW}⚠ Traffic found — DO NOT STOP.${NC}"
    echo "  The app is being used. Re-evaluate in another 30 days,"
    echo "  or investigate the source of traffic before any cleanup."
    exit 0
fi

echo -e "${GREEN}✓${NC} Zero traffic confirmed in the last $LOOKBACK_DAYS days."

if [ "$STOP" != true ]; then
    echo ""
    echo "DRY-RUN MODE — no action taken. To stop the resources:"
    echo "  $0 --stop          # interactive confirmation"
    echo "  $0 --force-stop    # non-interactive (for CI / scripts)"
    echo ""
    echo "POTENTIAL SAVINGS: ~\$28–30/mo (\$13 App Service + \$15–18 PG)"
    echo "EFFORT TO RESUME:  ~30 seconds via az webapp start + az postgres flexible-server start"
    exit 0
fi

# ── Destructive path ──
if [ "$FORCE" != true ]; then
    echo ""
    echo -e "${YELLOW}About to run:${NC}"
    echo "  az webapp stop -g $RESOURCE_GROUP -n $APP_NAME"
    echo "  az postgres flexible-server stop -g $RESOURCE_GROUP -n $PG_NAME"
    read -r -p "Continue? [y/N] " reply
    case "$reply" in
        y|Y|yes|YES) ;;
        *) echo "Aborted."; exit 0 ;;
    esac
fi

echo -e "${YELLOW}→${NC} Stopping App Service..."
az webapp stop --resource-group "$RESOURCE_GROUP" --name "$APP_NAME"
echo -e "${GREEN}✓${NC} App Service stopped."

echo -e "${YELLOW}→${NC} Pausing PostgreSQL flex server..."
az postgres flexible-server stop --resource-group "$RESOURCE_GROUP" --name "$PG_NAME"
echo -e "${GREEN}✓${NC} PostgreSQL paused."
echo ""
echo -e "${GREEN}╭─ DONE ────────────────────────────────────────────────────────╮${NC}"
echo -e "${GREEN}│${NC} Both resources stopped. Savings: ~\$28–30/mo while paused."
echo -e "${GREEN}│${NC} Note: Azure auto-restarts paused PG flex servers after 7 days."
echo -e "${GREEN}│${NC}       Re-run this script to re-pause if traffic remains zero."
echo -e "${GREEN}╰────────────────────────────────────────────────────────────────╯${NC}"

exit 2
