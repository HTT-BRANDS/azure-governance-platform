#!/bin/bash
# =============================================================================
# Pre-Swap Validation Script for Blue-Green Deployment
# Validates staging slot before swapping to production
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parameters
APP_NAME="${1:-}"
RESOURCE_GROUP="${2:-}"
SLOT_NAME="${3:-staging}"

# Validation
if [ -z "$APP_NAME" ] || [ -z "$RESOURCE_GROUP" ]; then
    echo -e "${RED}Error: Usage: $0 <app-name> <resource-group> [slot-name]${NC}"
    exit 1
fi

echo "🔍 Validating slot '$SLOT_NAME' for app '$APP_NAME'..."

# =============================================================================
# 1. Check slot exists and is running
# =============================================================================
echo "📋 Checking slot status..."
SLOT_STATE=$(az webapp show \
    --name "$APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --slot "$SLOT_NAME" \
    --query "state" \
    --output tsv 2>/dev/null || echo "")

if [ -z "$SLOT_STATE" ]; then
    echo -e "${RED}❌ Slot '$SLOT_NAME' not found${NC}"
    exit 1
fi

if [ "$SLOT_STATE" != "Running" ]; then
    echo -e "${RED}❌ Slot is not running (state: $SLOT_STATE)${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Slot is running${NC}"

# =============================================================================
# 2. Get slot URL and verify DNS resolution
# =============================================================================
echo "🌐 Checking slot URL..."
SLOT_URL=$(az webapp show \
    --name "$APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --slot "$SLOT_NAME" \
    --query "defaultHostName" \
    --output tsv)

FULL_URL="https://${SLOT_URL}"
echo "   Slot URL: $FULL_URL"

# Test DNS resolution
if ! nslookup "$SLOT_URL" > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️ DNS lookup failed, but continuing...${NC}"
fi

# =============================================================================
# 3. Health check with retries
# =============================================================================
echo "💓 Performing health checks..."
HEALTH_URL="${FULL_URL}/health"
MAX_RETRIES=5
RETRY_DELAY=10

for i in $(seq 1 $MAX_RETRIES); do
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
        --max-time 30 \
        --retry 0 \
        "$HEALTH_URL" 2>/dev/null || echo "000")
    
    if [ "$HTTP_STATUS" = "200" ]; then
        echo -e "${GREEN}✅ Health check passed (attempt $i)${NC}"
        break
    fi
    
    if [ $i -eq $MAX_RETRIES ]; then
        echo -e "${RED}❌ Health check failed after $MAX_RETRIES attempts (last status: $HTTP_STATUS)${NC}"
        exit 1
    fi
    
    echo "   Attempt $i failed (status: $HTTP_STATUS), retrying in ${RETRY_DELAY}s..."
    sleep $RETRY_DELAY
done

# =============================================================================
# 4. API readiness check
# =============================================================================
echo "🔌 Checking API readiness..."
API_HEALTH_URL="${FULL_URL}/api/health"
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    --max-time 30 \
    "$API_HEALTH_URL" 2>/dev/null || echo "000")

if [ "$API_STATUS" = "200" ]; then
    echo -e "${GREEN}✅ API health check passed${NC}"
else
    echo -e "${YELLOW}⚠️ API health check returned $API_STATUS (continuing...)${NC}"
fi

# =============================================================================
# 5. Check container startup logs
# =============================================================================
echo "📜 Checking recent logs..."
LOG_OUTPUT=$(az webapp log tail \
    --name "$APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --slot "$SLOT_NAME" \
    --duration 30 2>/dev/null || echo "")

# Check for error patterns in logs
if echo "$LOG_OUTPUT" | grep -qi "error\|exception\|failed\|fatal"; then
    echo -e "${YELLOW}⚠️ Found error patterns in logs (review recommended)${NC}"
else
    echo -e "${GREEN}✅ No obvious errors in recent logs${NC}"
fi

# =============================================================================
# 6. Check deployment slot configuration
# =============================================================================
echo "⚙️  Checking slot configuration..."

# Verify HTTPS only
HTTPS_ONLY=$(az webapp show \
    --name "$APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --slot "$SLOT_NAME" \
    --query "httpsOnly" \
    --output tsv)

if [ "$HTTPS_ONLY" = "true" ]; then
    echo -e "${GREEN}✅ HTTPS Only enabled${NC}"
else
    echo -e "${YELLOW}⚠️ HTTPS Only not enabled${NC}"
fi

# Check min TLS version
TLS_VERSION=$(az webapp show \
    --name "$APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --slot "$SLOT_NAME" \
    --query "siteConfig.minTlsVersion" \
    --output tsv)

if [ "$TLS_VERSION" = "1.2" ]; then
    echo -e "${GREEN}✅ Min TLS version is 1.2${NC}"
else
    echo -e "${YELLOW}⚠️ Min TLS version is $TLS_VERSION${NC}"
fi

# =============================================================================
# 7. Check application settings
# =============================================================================
echo "🔧 Checking critical app settings..."

REQUIRED_SETTINGS=(
    "ENVIRONMENT"
    "DATABASE_URL"
    "APPLICATIONINSIGHTS_CONNECTION_STRING"
)

for setting in "${REQUIRED_SETTINGS[@]}"; do
    VALUE=$(az webapp config appsettings list \
        --name "$APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --slot "$SLOT_NAME" \
        --query "[?name=='$setting'].value" \
        --output tsv)
    
    if [ -n "$VALUE" ]; then
        echo -e "${GREEN}✅ $setting is set${NC}"
    else
        echo -e "${RED}❌ $setting is missing!${NC}"
        exit 1
    fi
done

# =============================================================================
# 8. Performance baseline check
# =============================================================================
echo "⚡ Checking response time..."
RESPONSE_TIME=$(curl -s -o /dev/null -w "%{time_total}" \
    --max-time 30 \
    "$HEALTH_URL" 2>/dev/null || echo "999")

# Convert to milliseconds and check if under 2 seconds
RESPONSE_MS=$(echo "$RESPONSE_TIME * 1000" | bc | cut -d. -f1)
if [ "$RESPONSE_MS" -lt 2000 ]; then
    echo -e "${GREEN}✅ Response time: ${RESPONSE_MS}ms${NC}"
else
    echo -e "${YELLOW}⚠️ Response time high: ${RESPONSE_MS}ms${NC}"
fi

# =============================================================================
# 9. Database connectivity check (if applicable)
# =============================================================================
echo "🗄️  Checking database connectivity..."
DB_URL="${FULL_URL}/api/monitoring/health/db"
DB_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    --max-time 30 \
    "$DB_URL" 2>/dev/null || echo "000")

if [ "$DB_STATUS" = "200" ]; then
    echo -e "${GREEN}✅ Database connectivity confirmed${NC}"
elif [ "$DB_STATUS" = "404" ]; then
    echo -e "${YELLOW}⚠️ DB health endpoint not found (skipping)${NC}"
else
    echo -e "${YELLOW}⚠️ Database check returned $DB_STATUS${NC}"
fi

# =============================================================================
# Validation Summary
# =============================================================================
echo ""
echo "=========================================="
echo -e "${GREEN}🎉 All validation checks passed!${NC}"
echo "Slot '$SLOT_NAME' is ready for swap to production"
echo "=========================================="

exit 0
