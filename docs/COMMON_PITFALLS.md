# ⚠️ Common Pitfalls & How to Avoid Them

This document covers the most common mistakes people make when setting up the Azure Governance Platform, and how to avoid or fix them.

---

## 🚨 Top 5 Show-Stoppers

### 1. Forgetting Admin Consent

**The Problem:**
You added all the Graph API permissions, but forgot to click "Grant admin consent."

**Symptoms:**
- Error: `AADSTS65001: The user or administrator has not consented to use the application`
- Identity sync fails
- No user data appears

**The Fix:**
1. Go to Azure Portal → Azure AD → App registrations
2. Select your app
3. Click "API permissions"
4. Click "Grant admin consent for [Your Tenant]"
5. Confirm all permissions show green checkmarks

**Prevention:**
Always verify green checkmarks before moving on.

---

### 2. Wrong Permission Type (Delegated vs Application)

**The Problem:**
You added "Delegated" permissions instead of "Application" permissions.

**Symptoms:**
- Error: `Insufficient privileges to complete the operation`
- Sync jobs fail intermittently
- Some data loads, some doesn't

**The Fix:**
1. Go to API permissions
2. Remove all Delegated permissions
3. Add the same permissions as "Application" type
4. Grant admin consent again

**How to Tell the Difference:**
- Delegated = "On behalf of a signed-in user" 
- Application = "Without a signed-in user" ← **This is what you need**

---

### 3. Missing RBAC Roles on Subscriptions

**The Problem:**
You configured Graph API permissions but forgot to assign Azure RBAC roles.

**Symptoms:**
- Error: `AuthorizationFailed`
- Cost data is empty
- Resource inventory shows nothing
- Graph data works, but Azure resource data doesn't

**The Fix:**
1. Go to each Subscription → Access control (IAM)
2. Add role assignment
3. Assign Reader, Cost Management Reader, Security Reader
4. Select your App Registration as the member

**Common Mistake:**
People assign roles at the Resource Group level instead of Subscription level. Always assign at **Subscription** level for full visibility.

---

### 4. Client Secret Expired or Wrong

**The Problem:**
The client secret expired, was typed wrong, or you copied the Secret ID instead of the Secret Value.

**Symptoms:**
- Error: `AADSTS7000215: Invalid client secret provided`
- Nothing works after it was working before
- Error: `AADSTS7000222: The provided client secret keys are expired`

**The Fix:**
1. Go to App Registration → Certificates & secrets
2. Create a new secret
3. Copy the **Value** (NOT the Secret ID!)
4. Update your `.env` file
5. Restart the application

**Prevention:**
- Set a calendar reminder 30 days before expiration
- Use 24-month expiration (maximum allowed)
- Consider Azure Key Vault for production

---

### 5. Wrong Tenant ID in Configuration

**The Problem:**
You mixed up tenant IDs or copied the wrong GUID.

**Symptoms:**
- Error: `AADSTS90002: Tenant not found`
- Error: `AADSTS700016: Application with identifier 'X' was not found`
- Can't authenticate to any tenant

**The Fix:**
1. Go to Azure Portal → Azure AD → Overview
2. Copy the **Directory (tenant) ID** exactly
3. Update your `.env` file
4. Restart the application

**Prevention:**
Double-check GUIDs character by character. They're easy to mix up!

---

## 🟡 Medium-Impact Issues

### 6. Virtual Environment Not Activated

**The Problem:**
You're running commands outside the virtual environment.

**Symptoms:**
- `ModuleNotFoundError: No module named 'fastapi'`
- Commands work sometimes, fail other times
- Conflicting package versions

**The Fix:**
```bash
# Mac/Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

**How to Tell if Activated:**
Look for `(.venv)` at the beginning of your terminal prompt.

---

### 7. Database Locked Errors

**The Problem:**
SQLite database is locked because multiple processes are accessing it.

**Symptoms:**
- Error: `database is locked`
- App hangs during sync
- Intermittent failures

**The Fix:**
1. Stop all running instances of the app
2. Check for zombie processes: `ps aux | grep uvicorn`
3. Kill any stuck processes: `kill -9 <pid>`
4. Restart the app

**Prevention:**
Only run one instance of the app at a time when using SQLite.

---

### 8. Port Already in Use

**The Problem:**
Another application is using port 8000.

**Symptoms:**
- Error: `Address already in use`
- Error: `Port 8000 is already allocated`

**The Fix:**
```bash
# Find what's using the port
lsof -i :8000

# Kill it (be careful not to kill Microsoft Teams on 8080!)
kill -9 <pid>

# Or use a different port
uvicorn app.main:app --reload --port 8001
```

---

### 9. Firewall Blocking Azure APIs

**The Problem:**
Corporate firewall is blocking outbound connections to Azure.

**Symptoms:**
- Timeout errors during sync
- `Connection refused`
- Works on personal network, fails on corporate

**The Fix:**
Use the corporate proxy:
```bash
export HTTP_PROXY=http://sysproxy.wal-mart.com:8080
export HTTPS_PROXY=http://sysproxy.wal-mart.com:8080
```

Or add to your `.env`:
```
HTTP_PROXY=http://sysproxy.wal-mart.com:8080
HTTPS_PROXY=http://sysproxy.wal-mart.com:8080
```

---

### 10. Cost Data Takes 24-48 Hours to Appear

**The Problem:**
You set everything up correctly but cost data is empty.

**Symptoms:**
- All other data works
- Cost summary shows $0
- No errors in logs

**The Truth:**
This might not be a problem! Azure Cost Management data has a delay:
- **Actual costs**: 24-48 hours behind
- **Forecasts**: May take longer
- **New subscriptions**: Up to 72 hours to appear

**The Fix:**
Wait 24-48 hours after setup, then check again.

---

## 🟢 Minor Annoyances

### 11. Dashboard Shows Stale Data

**The Problem:**
Dashboard isn't reflecting recent Azure changes.

**Explanation:**
Data is synced on a schedule, not real-time:
- Costs: Every 24 hours
- Compliance: Every 4 hours
- Resources: Every 1 hour
- Identity: Every 24 hours

**The Fix:**
Trigger a manual sync:
```bash
curl -X POST http://localhost:8000/api/v1/sync/resources
```

---

### 12. Charts Not Rendering

**The Problem:**
Dashboard loads but charts are blank.

**Symptoms:**
- Page loads, cards show data
- Chart areas are empty
- No JavaScript errors in console

**The Fix:**
1. Clear browser cache (Ctrl+Shift+R or Cmd+Shift+R)
2. Check if Chart.js CDN is accessible
3. Try a different browser
4. Check browser console for errors (F12 → Console)

---

### 13. Swagger Docs Don't Load

**The Problem:**
API documentation at `/docs` returns an error.

**Symptoms:**
- 404 error on `/docs`
- Blank page

**The Fix:**
Swagger should work by default. Try:
1. Restart the application
2. Access `/docs` (not `/docs/`)
3. Check for errors in terminal

---

## 📚 Quick Reference: Error Messages

| Error | Meaning | Fix |
|-------|---------|-----|
| `AADSTS65001` | No admin consent | Grant admin consent |
| `AADSTS7000215` | Bad client secret | Create new secret |
| `AADSTS700016` | App not found | Check client ID |
| `AADSTS90002` | Tenant not found | Check tenant ID |
| `AuthorizationFailed` | No RBAC role | Assign Reader role |
| `ModuleNotFoundError` | Venv not active | Activate venv |
| `database is locked` | Concurrent access | Restart app |
| `Connection refused` | Service not running | Start the app |
| `Address already in use` | Port conflict | Kill other process |

---

## 🎯 Prevention Checklist

Before going live, verify:

- [ ] All 4 tenants have App Registrations
- [ ] All permissions show green checkmarks (admin consent)
- [ ] All subscriptions have RBAC roles assigned
- [ ] Client secrets are stored securely
- [ ] Calendar reminders set for secret expiration
- [ ] Tested with sample data first
- [ ] Triggered manual sync successfully
- [ ] Reviewed logs for errors
- [ ] Documented credentials securely

---

## 🆘 Still Stuck?

1. **Enable debug logging:**
   ```bash
   # In .env
   DEBUG=true
   LOG_LEVEL=DEBUG
   ```

2. **Check the logs:**
   Look at the terminal where the app is running for detailed errors.

3. **Test Azure credentials directly:**
   ```bash
   az login --service-principal \
     --username <client-id> \
     --password <client-secret> \
     --tenant <tenant-id>
   ```

4. **Start fresh:**
   If all else fails, delete `data/governance.db` and start over with sample data.

5. **Ask for help:**
   Share the exact error message, what you've tried, and your environment details.
