# ✅ Quick Start Checklist

Print this page and check off items as you complete them.

---

## Phase 1: Before You Start

- [ ] I have **Global Admin** or **Application Admin** access to all 4 tenants
- [ ] I have **Owner** or **User Access Admin** on the Azure subscriptions
- [ ] I have Python 3.11+ installed (`python3 --version`)
- [ ] I have Git installed (`git --version`)
- [ ] I have uv installed (`uv --version`)
- [ ] I have Azure CLI installed (`az --version`)
- [ ] I have collected all 4 Tenant IDs (GUIDs)

---

## Phase 2: Azure Setup (Repeat for Each Tenant)

### Tenant 1: ________________________

- [ ] Created App Registration named `governance-platform-reader`
- [ ] Recorded **Client ID**: `________________________________`
- [ ] Created Client Secret (expires: ___________)
- [ ] Recorded **Secret Value**: `________________________________`
- [ ] Added all 7 Microsoft Graph API permissions
- [ ] Clicked "Grant admin consent" (green checkmarks visible)
- [ ] Assigned **Reader** role on all subscriptions
- [ ] Assigned **Cost Management Reader** role on all subscriptions
- [ ] Assigned **Security Reader** role on all subscriptions

### Tenant 2: ________________________

- [ ] Created App Registration named `governance-platform-reader`
- [ ] Recorded **Client ID**: `________________________________`
- [ ] Created Client Secret (expires: ___________)
- [ ] Recorded **Secret Value**: `________________________________`
- [ ] Added all 7 Microsoft Graph API permissions
- [ ] Clicked "Grant admin consent" (green checkmarks visible)
- [ ] Assigned **Reader** role on all subscriptions
- [ ] Assigned **Cost Management Reader** role on all subscriptions
- [ ] Assigned **Security Reader** role on all subscriptions

### Tenant 3: ________________________

- [ ] Created App Registration named `governance-platform-reader`
- [ ] Recorded **Client ID**: `________________________________`
- [ ] Created Client Secret (expires: ___________)
- [ ] Recorded **Secret Value**: `________________________________`
- [ ] Added all 7 Microsoft Graph API permissions
- [ ] Clicked "Grant admin consent" (green checkmarks visible)
- [ ] Assigned **Reader** role on all subscriptions
- [ ] Assigned **Cost Management Reader** role on all subscriptions
- [ ] Assigned **Security Reader** role on all subscriptions

### Tenant 4: ________________________

- [ ] Created App Registration named `governance-platform-reader`
- [ ] Recorded **Client ID**: `________________________________`
- [ ] Created Client Secret (expires: ___________)
- [ ] Recorded **Secret Value**: `________________________________`
- [ ] Added all 7 Microsoft Graph API permissions
- [ ] Clicked "Grant admin consent" (green checkmarks visible)
- [ ] Assigned **Reader** role on all subscriptions
- [ ] Assigned **Cost Management Reader** role on all subscriptions
- [ ] Assigned **Security Reader** role on all subscriptions

---

## Phase 3: Local Setup

- [ ] Navigated to project folder
- [ ] Created virtual environment (`uv venv ...`)
- [ ] Activated virtual environment (see `(.venv)` in terminal)
- [ ] Installed dependencies (`uv pip install -e .`)
- [ ] Copied `.env.example` to `.env`
- [ ] Edited `.env` with primary tenant credentials

---

## Phase 4: Testing

- [ ] Started app (`uvicorn app.main:app --reload`)
- [ ] Dashboard loads at http://localhost:8000
- [ ] Health check returns "healthy" (`curl localhost:8000/health`)
- [ ] Seeded sample data (`python scripts/seed_data.py`)
- [ ] Dashboard shows sample data
- [ ] Registered all 4 tenants via API
- [ ] Triggered manual sync successfully

---

## Phase 5: Deployment (Optional)

- [ ] Created Azure Resource Group
- [ ] Created App Service Plan (B1)
- [ ] Created Web App
- [ ] Configured environment variables
- [ ] Deployed code
- [ ] Enabled HTTPS-only
- [ ] Verified production URL works

---

## Post-Setup

- [ ] Set calendar reminder for secret rotation (12 months)
- [ ] Documented credentials in secure location (NOT plain text)
- [ ] Shared dashboard URL with stakeholders
- [ ] Scheduled weekly review of cost anomalies

---

**Setup completed on:** _______________

**Setup completed by:** _______________

**Notes:**

_________________________________________________________________

_________________________________________________________________

_________________________________________________________________
