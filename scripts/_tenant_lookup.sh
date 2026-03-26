#!/usr/bin/env bash
# scripts/_tenant_lookup.sh — Shared tenant lookup functions for shell scripts.
#
# Reads tenant IDs and app IDs from config/tenants.yaml (or .example fallback)
# using a tiny Python helper, eliminating hardcoded values from shell scripts.
#
# USAGE: source this file, then call get_tenant_id/get_app_id/is_valid_code.
#
# NOTE: Requires Python 3 with PyYAML installed.

# Resolve the project root (parent of scripts/)
_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_PROJECT_ROOT="$(cd "$_SCRIPT_DIR/.." && pwd)"

# Find the YAML config (real file first, example fallback)
_TENANTS_YAML="${TENANTS_CONFIG_PATH:-}"
if [ -z "$_TENANTS_YAML" ] || [ ! -f "$_TENANTS_YAML" ]; then
    _TENANTS_YAML="$_PROJECT_ROOT/config/tenants.yaml"
fi
if [ ! -f "$_TENANTS_YAML" ]; then
    _TENANTS_YAML="$_PROJECT_ROOT/config/tenants.yaml.example"
fi
if [ ! -f "$_TENANTS_YAML" ]; then
    echo "ERROR: No tenant config found. Expected config/tenants.yaml" >&2
    exit 1
fi

# Build TENANT_ORDER from the YAML keys
TENANT_ORDER=$(python3 -c "
import yaml, sys
with open('$_TENANTS_YAML') as f:
    data = yaml.safe_load(f)
print(' '.join(k.upper() for k in data['tenants']))
" 2>/dev/null) || { echo "ERROR: Failed to parse $_TENANTS_YAML" >&2; exit 1; }

get_tenant_id() {
    python3 -c "
import yaml, sys
with open('$_TENANTS_YAML') as f:
    data = yaml.safe_load(f)
code = sys.argv[1].upper()
for k, v in data['tenants'].items():
    if k.upper() == code:
        print(v['tenant_id'])
        sys.exit(0)
sys.exit(1)
" "$1"
}

get_app_id() {
    python3 -c "
import yaml, sys
with open('$_TENANTS_YAML') as f:
    data = yaml.safe_load(f)
code = sys.argv[1].upper()
for k, v in data['tenants'].items():
    if k.upper() == code:
        print(v['app_id'])
        sys.exit(0)
sys.exit(1)
" "$1"
}

is_valid_code() {
    python3 -c "
import yaml, sys
with open('$_TENANTS_YAML') as f:
    data = yaml.safe_load(f)
code = sys.argv[1].upper()
codes = [k.upper() for k in data['tenants']]
sys.exit(0 if code in codes else 1)
" "$1"
}
