# Production Migration Plan

**Azure Governance Platform - Dev to Production Migration Guide**

**Version:** 1.0.0  
**Last Updated:** 2025-01-XX  
**Status:** Ready for Review  

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Pre-Migration Checklist](#pre-migration-checklist)
3. [Migration Steps](#migration-steps)
4. [Rollback Plan](#rollback-plan)
5. [Post-Migration](#post-migration)
6. [Risk Assessment](#risk-assessment)
7. [Emergency Contacts](#emergency-contacts)
8. [Appendix](#appendix)

---

## Executive Summary

This document provides a comprehensive guide for migrating the Azure Governance Platform from development to production environment. It covers all phases from pre-migration validation through post-monitoring and cleanup.

### Migration Overview

| Phase | Duration | Key Activities |
|-------|----------|----------------|
| Pre-Migration | 1-2 days | Validation, backups, stakeholder notification |
| Migration | 2-4 hours | Staging deployment, production cutover |
| Post-Migration | 24-48 hours | Monitoring, validation, cleanup |

### Success Criteria

- [ ] All health check endpoints return 200 OK
- [ ] Database connectivity verified
- [ ] Azure AD authentication functional
- [ ] Critical user workflows tested
- [ ] Performance metrics within SLAs
- [ ] Zero unplanned downtime during cutover

---

## Pre-Migration Checklist

### 1. Development Environment Validation

- [ ] **Unit Tests Passing**
  ```bash
  make test
  # Or: pytest tests/unit -v --tb=short
  ```
  - Expected: 100% pass rate on critical paths
  - Document any known flaky tests

- [ ] **Integration Tests Passing**
  ```bash
  make test-integration
  # Or: pytest tests/integration -v --tb=short
  ```
  - Expected: 95%+ pass rate
  - Document any environment-specific failures

- [ ] **E2E Tests Passing**
  ```bash
  make test-e2e
  # Or: pytest tests/e2e -v --tb=short
  ```

- [ ] **Code Quality Checks**
  ```bash
  make lint
  make typecheck
  make security-scan
  ```

- [ ] **Test Coverage**
  - Minimum 80% overall coverage
  - 100% coverage on critical paths (auth, data sync)

### 2. Azure SQL Production Configuration

- [ ] **Database Server Provisioned**
  - Server Name: `sql-governance-prod`
  - Region: Same as App Service (for low latency)
  - Tier: Standard S2 or higher (production workload)

- [ ] **Database Created**
  - Database Name: `governance-prod`
  - Collation: `SQL_Latin1_General_CP1_CI_AS`
  - Backup: 7-day retention minimum

- [ ] **Firewall Rules Configured**
  - Allow Azure services: Enabled
  - App Service outbound IPs whitelisted
  - Admin workstation IPs for emergency access

- [ ] **Connection String Validated**
  ```bash
  # Test from deployment agent
  sqlcmd -S sql-governance-prod.database.windows.net -d governance-prod -U <admin> -P <pass> -Q "SELECT 1"
  ```

- [ ] **Performance Baseline Established**
  - DTU usage < 50% at peak
  - Query response time < 500ms p95
  - Connection pool size validated

### 3. Azure Key Vault Secrets

- [ ] **Key Vault Created**
  - Name: `kv-governance-prod`
  - Region: Same as App Service
  - Soft-delete enabled
  - Purge protection enabled

- [ ] **Required Secrets Populated**

| Secret Name | Description | Source |
|-------------|-------------|--------|
| `azure-ad-client-secret` | Azure AD app secret | Azure AD App Registration |
| `azure-ad-client-id` | Azure AD app ID | Azure AD App Registration |
| `azure-ad-tenant-id` | Azure AD tenant ID | Azure Portal |
| `jwt-secret-key` | JWT signing key | Generate new (32+ bytes) |
| `database-url` | SQL connection string | Azure SQL |
| `staging-admin-key` | Staging test key (if needed) | Generate new |
| `teams-webhook-url` | Teams notification URL | Teams channel |
| `sendgrid-api-key` | Email service API key | SendGrid |

- [ ] **Access Policies Configured**
  - App Service managed identity has GET access
  - Deployment service principal has GET/SET access
  - Admin group has full access (emergency)

- [ ] **Secret Rotation Schedule**
  - JWT secret: Rotate every 90 days
  - Azure AD secret: Follow Azure AD rotation policy (180 days)
  - Database credentials: Rotate every 90 days

### 4. Backup Strategy Verification

- [ ] **Database Backups**
  - Automated backups: Enabled (daily)
  - Long-term retention: 35 days minimum
  - Geo-redundant backup storage: Enabled
  - Point-in-time restore tested

- [ ] **Configuration Backup**
  ```bash
  # Export App Service configuration
  az webapp config appsettings list --name app-governance-prod --resource-group rg-governance-prod > backup/prod-appsettings-$(date +%Y%m%d).json
  ```

- [ ] **Key Vault Backup**
  - Soft-delete enabled (30-day retention)
  - Regular export of secret names (not values) for inventory

- [ ] **Documentation Backup**
  - All runbooks stored in version control
  - Emergency contact list updated

### 5. Rollback Plan Documentation

- [ ] **Database Rollback Tested**
  - Point-in-time restore validated
  - Estimated restore time documented
  - Rollback procedure tested in staging

- [ ] **Previous Version Tagged**
  ```bash
  git tag -a production-stable-$(date +%Y%m%d) -m "Last known stable production version"
  git push origin production-stable-$(date +%Y%m%d)
  ```

- [ ] **Rollback Decision Tree**
  - Define criteria for triggering rollback
  - Document rollback approval chain
  - Set rollback time limit (e.g., 30 minutes)

---

## Migration Steps

### Phase 1: Staging Deployment (30 minutes)

**Goal:** Validate the build in a production-like environment before production deployment.

1. **Deploy to Staging Slot**
   ```bash
   # Using Azure CLI
   az webapp deployment source config-zip \
     --name app-governance-prod \
     --resource-group rg-governance-prod \
     --slot staging \
     --src ./deploy/governance-app-$(VERSION).zip
   ```

2. **Verify Staging Deployment**
   ```bash
   # Check staging health endpoint
   curl -s https://app-governance-prod-staging.azurewebsites.net/api/v1/health | jq .
   ```
   Expected response:
   ```json
   {
     "status": "healthy",
     "version": "1.0.0",
     "environment": "production",
     "checks": {
       "database": { "status": "healthy" },
       "cache": { "status": "healthy" },
       "scheduler": { "status": "healthy" }
     }
   }
   ```

3. **Run Staging Smoke Tests**
   ```bash
   cd tests/staging
   pytest test_smoke.py -v --tb=short
   ```

4. **Run API Coverage Tests**
   ```bash
   pytest test_api_coverage.py -v
   ```

5. **Validate Critical Workflows**
   - [ ] Login flow works
   - [ ] Dashboard loads
   - [ ] Cost data visible
   - [ ] Compliance checks running

**Success Criteria:**
- All health checks pass
- Smoke tests 100% pass
- No critical errors in logs

### Phase 2: Database Migration (if needed) (15-30 minutes)

**Note:** Skip if no schema changes required.

1. **Create Database Backup**
   ```bash
   az sql db export \
     --name governance-prod \
     --server sql-governance-prod \
     --resource-group rg-governance-prod \
     --storage-uri "https://stgovernanceprod.blob.core.windows.net/backups/pre-migration-$(date +%Y%m%d).bacpac" \
     --storage-key-type StorageAccessKey \
     --storage-key <key>
   ```

2. **Run Migrations**
   ```bash
   # From deployment agent with network access to SQL
   alembic upgrade head
   ```

3. **Verify Migration**
   ```bash
   # Check schema version
   alembic current
   # Verify key tables exist
   sqlcmd -S <server> -d <db> -Q "SELECT COUNT(*) FROM tenants"
   ```

### Phase 3: Production Deployment (15-30 minutes)

1. **Pre-Deployment Checks**
   - [ ] Confirm staging validation passed
   - [ ] Notify stakeholders (maintenance window start)
   - [ ] Enable maintenance mode (optional)
   - [ ] Ensure rollback plan is ready

2. **Swap Staging to Production**
   ```bash
   az webapp deployment slot swap \
     --name app-governance-prod \
     --resource-group rg-governance-prod \
     --slot staging \
     --target-slot production
   ```

   **Alternative: Direct Deployment (if not using slots)**
   ```bash
   az webapp deployment source config-zip \
     --name app-governance-prod \
     --resource-group rg-governance-prod \
     --src ./deploy/governance-app-$(VERSION).zip
   ```

3. **Warm-Up Period (5 minutes)**
   - Allow application pool to initialize
   - Pre-warm critical endpoints:
     ```bash
     curl -s https://app-governance-prod.azurewebsites.net/api/v1/health
     curl -s https://app-governance-prod.azurewebsites.net/api/v1/auth/health
     curl -s https://app-governance-prod.azurewebsites.net/api/v1/dashboard/summary
     ```

### Phase 4: Validation Tests (15 minutes)

1. **Health Check Validation**
   ```bash
   # Run health checks
   curl -s https://app-governance-prod.azurewebsites.net/api/v1/health | jq -e '.status == "healthy"'
   curl -s https://app-governance-prod.azurewebsites.net/api/v1/health/detailed | jq -e '.status == "healthy"'
   curl -s https://app-governance-prod.azurewebsites.net/health | jq -e '.status == "healthy"'
   ```

2. **Authentication Validation**
   - [ ] Azure AD login works
   - [ ] JWT token generation works
   - [ ] Token refresh works
   - [ ] Logout works

3. **Critical API Endpoints**
   ```bash
   # Test key endpoints
   curl -s -H "Authorization: Bearer $TOKEN" https://app-governance-prod.azurewebsites.net/api/v1/costs/summary
   curl -s -H "Authorization: Bearer $TOKEN" https://app-governance-prod.azurewebsites.net/api/v1/compliance/summary
   curl -s -H "Authorization: Bearer $TOKEN" https://app-governance-prod.azurewebsites.net/api/v1/identity/users
   curl -s -H "Authorization: Bearer $TOKEN" https://app-governance-prod.azurewebsites.net/api/v1/resources
   ```

4. **Run Production Smoke Tests**
   ```bash
   cd tests/production
   pytest test_smoke.py -v
   ```

5. **Log Verification**
   ```bash
   # Check for errors in last 15 minutes
   az webapp log tail --name app-governance-prod --resource-group rg-governance-prod --since 15
   ```
   - [ ] No CRITICAL errors
   - [ ] No database connection failures
   - [ ] No authentication failures (except expected 401s)

### Phase 5: Monitoring Period (24 hours)

1. **Immediate Monitoring (First Hour)**
   - Watch for 5xx errors
   - Monitor response times
   - Check error rates

2. **24-Hour Monitoring**
   - Daily error rate < 0.1%
   - P95 response time < 1000ms
   - Availability > 99.9%
   - Cache hit rate > 70%

3. **Alert Configuration**
   Ensure alerts are configured for:
   - [ ] 5xx error rate > 1%
   - [ ] Response time > 2000ms p95
   - [ ] Database connection failures
   - [ ] Authentication failures > 10/minute
   - [ ] Health check failures

---

## Rollback Plan

### Rollback Triggers

**Immediate Rollback (within 30 minutes):**
- Health check failures > 5 minutes
- 5xx error rate > 10%
- Database connectivity lost
- Authentication completely broken
- Data corruption detected

**Standard Rollback (within 4 hours):**
- Performance degradation > 50%
- Critical feature non-functional
- Security vulnerability detected

### Database Rollback Procedure

1. **Stop Application** (prevent new writes)
   ```bash
   az webapp stop --name app-governance-prod --resource-group rg-governance-prod
   ```

2. **Restore from Backup**
   ```bash
   # Point-in-time restore (if within 35 days)
   az sql db restore \
     --dest-name governance-prod-restored \
     --name governance-prod \
     --server sql-governance-prod \
     --resource-group rg-governance-prod \
     --restore-point-in-time "2025-01-15T10:00:00Z"
   
   # Or from BACPAC export
   az sql db import \
     --name governance-prod \
     --server sql-governance-prod \
     --resource-group rg-governance-prod \
     --storage-uri "https://stgovernanceprod.blob.core.windows.net/backups/pre-migration-20250115.bacpac"
   ```

3. **Update Connection String** (if using restored DB)
   ```bash
   az webapp config appsettings set \
     --name app-governance-prod \
     --resource-group rg-governance-prod \
     --settings "DATABASE_URL=<new-connection-string>"
   ```

4. **Restart Application**
   ```bash
   az webapp start --name app-governance-prod --resource-group rg-governance-prod
   ```

### Application Rollback Procedure

1. **Slot Swap Back** (if using deployment slots)
   ```bash
   az webapp deployment slot swap \
     --name app-governance-prod \
     --resource-group rg-governance-prod \
     --slot production \
     --target-slot staging
   ```

2. **Redeploy Previous Version** (if direct deployment)
   ```bash
   # Checkout previous stable tag
   git checkout production-stable-20250114
   
   # Build and deploy
   make deploy-prod VERSION=1.0.0-stable
   ```

### Traffic Routing Rollback

If using Azure Front Door or Traffic Manager:

1. **Route Traffic Away**
   ```bash
   # Disable production endpoint
   az network front-door backend-pool backend remove \
     --front-door-name fd-governance \
     --resource-group rg-governance-prod \
     --pool-name production \
     --backend-name prod-app
   ```

2. **Enable Maintenance Page** (optional)
   Configure static maintenance page or redirect to status page.

---

## Post-Migration

### Immediate (0-1 hour)

- [ ] **Disable Maintenance Mode** (if enabled)
- [ ] **Verify All Services Operational**
  - Run full smoke test suite
  - Verify health endpoints
- [ ] **Notify Stakeholders** (migration complete)

### Short-term (1-24 hours)

- [ ] **Monitor Metrics**
  - Response times
  - Error rates
  - Database performance
  - Cache hit rates
- [ ] **Review Logs** for warnings/errors
- [ ] **Validate Scheduled Jobs**
  - Data sync jobs running
  - Alert jobs functioning
  - Report generation working

### Long-term (24-48 hours)

- [ ] **Performance Review**
  - Compare metrics to baseline
  - Identify any degradation
  - Tune if necessary
- [ ] **Cost Review**
  - Verify Azure spend within budget
  - Check for unexpected resource usage
- [ ] **Documentation Update**
  - Update runbooks with any changes
  - Document any issues encountered
  - Update architecture diagrams if changed

### Cleanup Tasks

- [ ] **Remove Staging Deployment** (if no longer needed)
  ```bash
  az webapp deployment slot delete \
    --name app-governance-prod \
    --resource-group rg-governance-prod \
    --slot staging
  ```

- [ ] **Clean Up Backup Files**
  - Remove local build artifacts
  - Archive deployment packages to blob storage

- [ ] **Update CMDB/Documentation**
  - Record new version deployed
  - Update change management records
  - Close related tickets

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Database migration failure | Low | High | Full backup taken; tested restore procedure; rollback plan ready |
| Authentication issues | Medium | High | Staging validation; health checks; fallback to previous JWT secret |
| Performance degradation | Medium | Medium | Load testing in staging; auto-scaling enabled; performance monitoring |
| Azure AD rate limiting | Low | Medium | Circuit breakers; caching; exponential backoff; monitoring |
| Data sync failures | Low | High | Independent sync scheduler; manual trigger available; alerting configured |
| Key Vault access issues | Low | High | Managed identity pre-configured; fallback connection string documented |
| Network connectivity | Low | High | Multi-region not needed; Azure SLA 99.95%; monitoring alerts |
| Dependency failures | Low | Medium | Health checks detect issues; graceful degradation; fallback data |

### Contingency Plans

**Scenario 1: Complete Service Failure**
1. Immediately roll back to previous version
2. If rollback fails, deploy emergency maintenance page
3. Escalate to on-call engineer + Azure support
4. Communicate to users via status page

**Scenario 2: Partial Feature Failure**
1. Assess which features are impacted
2. If critical feature (auth, data sync), initiate rollback
3. If non-critical, continue with mitigation in place
4. Deploy hotfix if available

**Scenario 3: Data Corruption**
1. Stop all writes immediately
2. Restore from last known good backup
3. Identify and quarantine corrupted data
4. Audit logs to determine cause
5. Manual data reconciliation if needed

---

## Emergency Contacts

| Role | Name | Contact | Escalation |
|------|------|---------|------------|
| Primary On-Call | TBD | PagerDuty | Auto-escalate after 15 min |
| Engineering Lead | TBD | Phone/Slack | Level 2 |
| Product Owner | TBD | Phone/Email | Business decisions |
| Azure Support | Microsoft | Premier Portal | For Azure service issues |
| Database Admin | TBD | Phone/Slack | For SQL Server issues |

### Escalation Chain

1. **Level 1**: On-call engineer (first 30 minutes)
2. **Level 2**: Engineering lead + infrastructure team (30-60 minutes)
3. **Level 3**: CTO + all engineering leads (60+ minutes or major incident)

---

## Appendix

### A. Quick Reference Commands

**Health Checks:**
```bash
# Basic health
curl -s https://app-governance-prod.azurewebsites.net/health

# Detailed health
curl -s https://app-governance-prod.azurewebsites.net/api/v1/health/detailed

# Auth health
curl -s https://app-governance-prod.azurewebsites.net/api/v1/auth/health

# Sync health
curl -s https://app-governance-prod.azurewebsites.net/api/v1/sync/status/health
```

**Log Streaming:**
```bash
# Stream logs
az webapp log tail --name app-governance-prod --resource-group rg-governance-prod

# Download logs
az webapp log download --name app-governance-prod --resource-group rg-governance-prod
```

**Restart App:**
```bash
az webapp restart --name app-governance-prod --resource-group rg-governance-prod
```

**Scale App:**
```bash
az appservice plan update --name plan-governance-prod --resource-group rg-governance-prod --sku P2v2
```

### B. Environment Variables

**Required for Production:**

| Variable | Source | Example |
|----------|--------|---------|
| `ENVIRONMENT` | Hardcoded | `production` |
| `DATABASE_URL` | Key Vault | `mssql+pyodbc://...` |
| `AZURE_AD_TENANT_ID` | Key Vault | `guid` |
| `AZURE_AD_CLIENT_ID` | Key Vault | `guid` |
| `AZURE_AD_CLIENT_SECRET` | Key Vault | `secret` |
| `JWT_SECRET_KEY` | Key Vault | `32-byte-secret` |
| `KEY_VAULT_NAME` | App Setting | `kv-governance-prod` |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | App Setting | `InstrumentationKey=...` |

### C. Validation Checklist

**Pre-Go-Live:**
- [ ] All health endpoints return 200
- [ ] Database connectivity verified
- [ ] Azure AD login works
- [ ] Cost data loads
- [ ] Compliance checks run
- [ ] Identity sync working
- [ ] Notifications sending
- [ ] Scheduled jobs running

**Post-Go-Live (24 hours):**
- [ ] No critical errors in logs
- [ ] Error rate < 0.1%
- [ ] Response time p95 < 1000ms
- [ ] All scheduled jobs completed
- [ ] Cache hit rate > 70%
- [ ] User feedback positive

---

## Sign-Off

**Migration Approved By:**

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Engineering Lead | | | |
| Product Owner | | | |
| DevOps Lead | | | |
| Security Lead | | | |

---

*This document is a living document. Update it after each migration with lessons learned and process improvements.*
