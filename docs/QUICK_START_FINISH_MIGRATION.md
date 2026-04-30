# Finish the Production Migration (5 Minutes)

## Step 1: Fix GHCR Access (Choose One)

### Option A - Web UI (Easiest - 1 minute):

1. Visit https://github.com/HTT-BRANDS/control-tower/pkgs/container/control-tower
2. Click "Package settings" (gear icon)
3. Scroll to "Change package visibility"
4. Click "Change visibility" → Select "Public" → Confirm
5. Done! Skip to Step 2

### Option B - gh CLI (2 minutes):

```bash
gh auth refresh --hostname github.com --scopes read:packages,write:packages
# Follow browser prompts
# Then run:
gh api PATCH /orgs/HTT-BRANDS/packages/container/azure-governance-platform -f visibility=public
```

## Step 2: Restart Production (Husky will do this)

```bash
az webapp restart --name app-governance-prod --resource-group rg-governance-production
```

## Step 3: Validate (QA will do this)

```bash
curl -s https://app-governance-prod.azurewebsites.net/health | jq .
```

Expected: `{"status": "healthy", "version": "1.9.0"}`

## Step 4: Done! 🎉
