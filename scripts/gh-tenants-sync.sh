#!/bin/bash
# Trigger tenant data sync via GitHub Actions

TENANT=${1:-all}

echo "🔄 Triggering sync for tenant: $TENANT"

# Trigger workflow dispatch
echo "Workflow dispatch for tenant-sync not yet configured."
echo "To trigger manually:"
echo "  gh workflow run tenant-sync.yml -f tenant=$TENANT"
