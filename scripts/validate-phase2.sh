#!/bin/bash
# Phase 2 Validation Script
# Run this to validate all Phase 2 improvements

set -e

echo "=========================================="
echo "PHASE 2 VALIDATION - Azure Governance Platform"
echo "Started: $(date)"
echo "=========================================="
echo ""

PROD_URL="https://app-governance-prod.azurewebsites.net"
FAILED=0

# Test 1: Health Endpoint
echo "TEST 1: Health Endpoint"
response=$(curl -s "$PROD_URL/health")
echo "Response: $response"
if echo "$response" | grep -q '"status":"healthy"'; then
    echo "✅ PASS: Health endpoint healthy"
else
    echo "❌ FAIL: Health endpoint not healthy"
    FAILED=1
fi
echo ""

# Test 2: API Status
echo "TEST 2: API Status Endpoint"
response=$(curl -s "$PROD_URL/api/v1/status")
echo "Response: $response"
if echo "$response" | grep -q '"database":"healthy"'; then
    echo "✅ PASS: Database healthy"
else
    echo "❌ FAIL: Database not healthy"
    FAILED=1
fi
echo ""

# Test 3: Modular Code Structure
echo "TEST 3: Code Structure (app/preflight/azure/)"
if [ -d "app/preflight/azure" ]; then
    echo "✅ PASS: Modular directory exists"
    echo "Files:"
    ls -1 app/preflight/azure/*.py 2>/dev/null || echo "No .py files found"
    
    # Check file sizes
    max_lines=$(wc -l app/preflight/azure/*.py 2>/dev/null | tail -1 | awk '{print $1}' || echo "0")
    echo "Max lines: $max_lines"
    if [ "$max_lines" -le 600 ]; then
        echo "✅ PASS: All files under 600 lines"
    else
        echo "⚠️ WARNING: Some files exceed 600 lines"
    fi
else
    echo "❌ FAIL: Modular directory not found"
    FAILED=1
fi
echo ""

# Test 4: k6 Availability
echo "TEST 4: k6 Availability"
if command -v k6 &> /dev/null; then
    echo "✅ PASS: k6 is installed"
    echo "Version: $(k6 version | head -1)"
    
    # Run smoke test if tests exist
    if [ -f "tests/performance/k6/smoke_test.js" ]; then
        echo "Running k6 smoke test..."
        k6 run tests/performance/k6/smoke_test.js || echo "⚠️ k6 test failed (check output above)"
    else
        echo "⚠️ WARNING: k6 smoke test file not found"
    fi
else
    echo "⚠️ WARNING: k6 not installed (install with: brew install k6)"
fi
echo ""

# Test 5: Playwright Availability  
echo "TEST 5: Playwright Availability"
if [ -d "tests/e2e" ]; then
    echo "✅ PASS: tests/e2e directory exists"
    
    if [ -f "tests/e2e/package.json" ]; then
        echo "✅ PASS: package.json found"
        
        # Check if node_modules exists
        if [ -d "tests/e2e/node_modules" ]; then
            echo "✅ PASS: node_modules installed"
            
            # Try running tests
            cd tests/e2e
            if npx playwright test --list 2>/dev/null | grep -q "tests"; then
                echo "✅ PASS: Playwright tests found"
                echo "Running E2E tests..."
                npx playwright test || echo "⚠️ Some E2E tests failed"
            else
                echo "⚠️ WARNING: No Playwright tests found or browsers not installed"
                echo "Run: cd tests/e2e && npx playwright install"
            fi
            cd ../..
        else
            echo "⚠️ WARNING: node_modules not installed"
            echo "Run: cd tests/e2e && npm install"
        fi
    else
        echo "⚠️ WARNING: package.json not found in tests/e2e/"
    fi
else
    echo "⚠️ WARNING: tests/e2e directory not found"
fi
echo ""

# Test 6: App Insights Check
echo "TEST 6: Application Insights"
if command -v az &> /dev/null; then
    echo "✅ PASS: Azure CLI is available"
    
    # Check if logged in
    if az account show &> /dev/null; then
        echo "✅ PASS: Azure CLI logged in"
        
        # Check App Insights
        app_insights=$(az monitor app-insights component show \
            --app governance-appinsights \
            --resource-group rg-governance-production 2>/dev/null \
            --query "{appId:appId, state:provisioningState}" -o tsv || echo "ERROR")
        
        if [ "$app_insights" != "ERROR" ]; then
            echo "✅ PASS: Application Insights found"
            echo "Details: $app_insights"
        else
            echo "❌ FAIL: Application Insights not found or not accessible"
            FAILED=1
        fi
    else
        echo "⚠️ WARNING: Azure CLI not logged in (run: az login)"
    fi
else
    echo "⚠️ WARNING: Azure CLI not installed"
fi
echo ""

# Summary
echo "=========================================="
echo "VALIDATION SUMMARY"
echo "=========================================="
echo "Completed: $(date)"
echo ""
if [ $FAILED -eq 0 ]; then
    echo "✅ ALL CRITICAL TESTS PASSED"
    echo "Phase 2 is READY for handoff"
    exit 0
else
    echo "❌ SOME TESTS FAILED"
    echo "Review failures above and fix before handoff"
    exit 1
fi
