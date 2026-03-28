# Container Apps vs App Service B1 — Feature Comparison

## Source
- https://learn.microsoft.com/en-us/azure/container-apps/compare-options
- https://learn.microsoft.com/en-us/azure/app-service/overview-hosting-plans
- https://azure.microsoft.com/en-us/pricing/details/container-apps/
- https://azure.microsoft.com/en-us/pricing/details/app-service/linux/

## Key Architectural Differences

### App Service B1 (Current)
- **Fixed compute allocation:** 1 vCPU, 1.75 GB RAM — always provisioned
- **No Always-On on B1:** App idles after 20 minutes of inactivity
- **Cold start on B1:** 5-15 seconds when app wakes from idle
- **Single instance:** B1 does not support auto-scaling
- **No VNet integration:** Requires S1+ tier ($73/mo+)
- **Deployment slots:** 1 slot available on B1+

### Container Apps Consumption
- **Dynamic compute:** 0.25-4 vCPU, 0.5-8 GiB per container
- **True scale-to-zero:** No charges when no replicas running
- **Cold start:** 2-8 seconds from zero to first response
- **Auto-scaling:** 0 to 1000 replicas based on HTTP/events
- **VNet integration:** Available even on consumption plan
- **Revision-based traffic splitting:** Better than deployment slots

## Feature-by-Feature Comparison

### Docker Container Support
- **App Service B1:** ✅ Full Docker support on Linux. Pull from ACR, GHCR, Docker Hub.
  Config: `az webapp config container set --docker-custom-image-name`
- **Container Apps:** ✅ Full Docker support. Pull from any registry.
  Config: `az containerapp create --image`

### Persistent Storage
- **App Service B1:** `/home` directory backed by Azure Files SMB. 1 GB on B1.
  Always available, survives restarts.
- **Container Apps:** Three types:
  1. Container-scoped (ephemeral) — lost on restart
  2. Replica-scoped (ephemeral) — lost on scale-down
  3. Azure Files mount (persistent) — requires explicit volume mount
  Must explicitly configure Azure Files for persistence.

### Custom Domains
- **App Service B1:** ✅ Unlimited custom domains. Configure via portal or CLI.
- **Container Apps:** ✅ Custom domains supported. Bind via `az containerapp hostname bind`.

### SSL/TLS Certificates
- **App Service B1:** ✅ Free App Service Managed Certificate. Auto-renewed.
- **Container Apps:** ✅ Free managed certificate via DigiCert. Auto-renewed.
  Requires app to be publicly accessible from DigiCert IP addresses.

### Health Probes
- **App Service B1:** Basic health check endpoint. Configure via portal.
  Single endpoint check, 2-10 minute intervals.
- **Container Apps:** ✅ Kubernetes-style probes:
  - Startup probe (wait for app to start)
  - Liveness probe (restart unhealthy containers)
  - Readiness probe (stop sending traffic to unready containers)
  Much more sophisticated than App Service.

### Background Jobs
- **App Service B1:** ✅ APScheduler runs in-process. WebJobs also available.
  Scheduler survives as long as the app is running (but B1 idles!).
- **Container Apps:** ⚠️ In-process schedulers don't work with scale-to-zero.
  Must use Container Apps Jobs with Schedule trigger type (cron).
  Jobs are billed separately (active rate only during execution).

### Managed Identity
- **App Service B1:** ✅ System-assigned managed identity. Auto-created.
- **Container Apps:** ✅ Both system-assigned and user-assigned managed identity.

### Networking
- **App Service B1:** ❌ No VNet integration (requires S1+).
  No private endpoints. Public internet only.
- **Container Apps:** ✅ VNet integration on consumption plan.
  Internal/external ingress. Private endpoints available (adds Dedicated Plan Management charge of $0.10/hr).

### Logging
- **App Service B1:** App Service Logs (filesystem or blob). App Insights integration.
- **Container Apps:** Container Apps system logs + App Insights integration.
  Log Analytics workspace for centralized logging.

### CI/CD
- **App Service B1:** GitHub Actions, Azure DevOps, Bitbucket. Deployment Center.
- **Container Apps:** GitHub Actions, Azure DevOps. Azure CLI commands.

### Cost Model
- **App Service B1:** $13.14/month fixed. Pay whether used or not.
- **Container Apps:** $0-X/month usage-based. Free grants cover light workloads.
  Active rate: $0.000024/vCPU-sec + $0.000003/GiB-sec.
  Idle rate: $0.000003/vCPU-sec + $0.000003/GiB-sec.
