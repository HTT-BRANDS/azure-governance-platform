# Analysis: API Design Governance

## Overview

API design governance ensures consistency, quality, and security across API specifications through automated linting and style enforcement. This analysis covers leading standards and tools for an Azure governance platform.

## Leading Standards (2024-2025)

### 1. OpenAPI Specification

**Version:** 3.1.0 (current), 3.0.x (widely adopted), 2.0 (legacy)  
**Status:** Industry standard, OpenAPI Initiative  
**Format:** YAML or JSON

**Key Elements:**
- `openapi`: Version declaration
- `info`: API metadata
- `paths`: Endpoints and operations
- `components`: Reusable schemas
- `security`: Authentication schemes

**Adoption:**
- Azure API Management: Full support
- FastAPI: Native OpenAPI generation
- Documentation: Swagger UI, ReDoc

### 2. AsyncAPI

**Version:** 2.x (current)  
**Purpose:** Event-driven and async APIs  
**Status:** Growing adoption, messaging systems

**Use Cases:**
- WebSocket APIs
- MQTT-based IoT
- Message queue APIs
- Event streaming (Kafka, Event Hubs)

### 3. JSON Schema

**Version:** 2020-12 (current)  
**Purpose:** Data validation  
**Integration:** Used by OpenAPI, AsyncAPI

**Azure Relevance:**
- Azure API Management policies
- Azure Functions bindings
- Data validation layer

## Leading Linting Tools

### 1. Spectral (Stoplight)

**GitHub:** https://github.com/stoplightio/spectral  
**Status:** 3k+ stars, actively maintained  
**License:** Apache 2.0

**Capabilities:**
- OpenAPI (2.0, 3.0, 3.1) linting
- AsyncAPI support
- Arazzo workflow linting
- Custom rulesets
- Custom functions (JS/TS)

**Built-in Rulesets:**
```yaml
extends:
  - "spectral:oas"       # OpenAPI rules
  - "spectral:asyncapi"  # AsyncAPI rules
  - "spectral:arazzo"    # Arazzo workflow rules
```

**Key Rules:**
| Rule | Severity | Purpose |
|------|----------|---------|
| `operation-operationId` | Error | Unique operation IDs |
| `operation-description` | Warning | Document operations |
| `info-contact` | Error | Contact information |
| `oas3-api-servers` | Warning | Server definitions |

**Custom Ruleset Example:**
```yaml
# .spectral.yaml
extends: ["spectral:oas"]

rules:
  # Require operation summaries
  operation-summary-required:
    description: Operations must have summaries
    given: "$.paths.*.*"
    then:
      field: summary
      function: truthy
    severity: error

  # Enforce naming conventions
  operation-id-naming:
    description: Operation IDs must use camelCase
    given: "$.paths.*.*.operationId"
    then:
      function: pattern
      functionOptions:
        match: "^[a-z][a-zA-Z0-9]*$"
    severity: error

  # Require security on all operations
  operation-security-required:
    description: All operations must have security
    given: "$.paths.*.*"
    then:
      field: security
      function: truthy
    severity: error

  # Azure-specific: Require x-ms- extensions
  azure-extensions:
    description: Azure APIs should use x-ms extensions
    given: "$.paths.*.*"
    then:
      function: schema
      functionOptions:
        schema:
          type: object
          properties:
            x-ms-summary:
              type: string
    severity: warn
```

**Azure-Specific Rules:**
```yaml
# Azure API Style Guide compliance
rules:
  azure-versioned-paths:
    description: Paths should include API version
    given: "$.paths"
    then:
      function: pattern
      functionOptions:
        match: "/api/v[0-9]+/"
    severity: error

  azure-tenant-id-param:
    description: Tenant-scoped operations need tenantId parameter
    given: "$.paths.*.get.parameters"
    then:
      function: schema
      functionOptions:
        schema:
          contains:
            properties:
              name:
                const: "tenantId"
    severity: warn
```

**Integration Options:**

| Integration | Method | Status |
|-------------|--------|--------|
| **CLI** | `spectral lint` | ✅ Production |
| **GitHub Action** | `stoplightio/spectral-action` | ✅ Production |
| **VS Code** | Extension | ✅ Production |
| **JetBrains** | Plugin | ✅ Production |
| **CI/CD** | Docker/container | ✅ Production |

### 2. Optic

**GitHub:** https://github.com/opticdev/optic  
**Status:** Active development, newer entrant  
**License:** MIT

**Capabilities:**
- API change detection
- Diff-based review
- Contract testing
- Documentation generation

**Comparison:**
| Feature | Spectral | Optic |
|---------|----------|-------|
| Linting | ✅ Comprehensive | ✅ Good |
| Custom rules | ✅ Excellent | ✅ Good |
| Change detection | ❌ No | ✅ Yes |
| Diff visualization | ❌ No | ✅ Yes |
| CI integration | ✅ Excellent | ✅ Good |
| Learning curve | Low | Medium |

**Recommendation:** Use Spectral for primary linting, Optic for change management.

### 3. OpenAPI Generator

**Purpose:** Code generation from specs  
**Integration:** Can validate specs before generation

### 4. Azure API Management Validation

**Native:** Built-in validation policies  
**Use:** Runtime validation

## Real-World Rulesets

### Adidas API Style Guide
```yaml
# From: https://github.com/adidas/api-guidelines
extends: "spectral:oas"

rules:
  # No trailing slashes
  adidas-no-trailing-slash:
    description: Paths should not end with a slash
    given: "$.paths"
    then:
      function: pattern
      functionOptions:
        notMatch: "/$"
    severity: error

  # Kebab-case for path segments
  adidas-path-segments-kebab-case:
    description: Path segments should be kebab-case
    given: "$.paths"
    then:
      function: pattern
      functionOptions:
        match: "^(/[a-z0-9-]+)+$"
    severity: error
```

### Azure API Style Guide
```yaml
# From: https://github.com/Azure/azure-api-style-guide
extends: "spectral:oas"

rules:
  # Version in path
  azure-version-in-path:
    description: API version should be in path
    given: "$.servers"
    then:
      function: pattern
      functionOptions:
        match: "v[0-9]+"
    severity: error

  # CamelCase for property names
  azure-camel-case-properties:
    description: Schema properties should be camelCase
    given: "$.components.schemas.*.properties"
    then:
      function: pattern
      functionOptions:
        match: "^[a-z][a-zA-Z0-9]*$"
    severity: warn
```

### OWASP API Security
```yaml
# From: https://apistylebook.stoplight.io/docs/owasp-top-10
extends: "spectral:oas"

rules:
  # API2: Broken Authentication
  owasp-auth-security-schemes:
    description: API must define security schemes
    given: "$.components.securitySchemes"
    then:
      function: truthy
    severity: error

  # API1: Broken Object Level Authorization
  owasp-object-level-auth:
    description: Operations should document authorization
    given: "$.paths.*.*"
    then:
      field: description
      function: pattern
      functionOptions:
        match: "(?i)(auth|permission|role)"
    severity: warn
```

## Multi-Dimensional Analysis

### Security
- **Rating:** ⭐⭐⭐⭐⭐ (Critical)
- Spectral includes OWASP security rules
- Validates authentication schemes
- Enforces security best practices
- Prevents common API vulnerabilities

### Cost
- **Rating:** ⭐⭐⭐⭐⭐ (Very Low)
- Spectral: Open source, free
- Optic: Freemium model
- Minimal infrastructure
- Prevents costly API redesigns

### Implementation Complexity
- **Rating:** ⭐⭐⭐☆☆ (Medium)
- Basic setup: Low (15 minutes)
- Custom rulesets: Medium (hours)
- Full governance: Medium-High (days)

### Stability
- **Rating:** ⭐⭐⭐⭐⭐ (High)
- Spectral: Production-ready, widely used
- OpenAPI: Industry standard
- Tooling ecosystem mature

### Optimization
- **Rating:** ⭐⭐⭐⭐☆ (Good)
- Fast linting (<1s for typical specs)
- Incremental checking
- Parallel execution
- Caching supported

### Compatibility
- **Rating:** ⭐⭐⭐⭐⭐ (Excellent)
- Multi-format support (OpenAPI, AsyncAPI)
- CI/CD agnostic
- IDE integration
- Azure native support

### Maintenance
- **Rating:** ⭐⭐⭐☆☆ (Medium)
- Rulesets require updates
- Tool version updates
- Periodic review recommended

## Recommendations for Azure Governance Platform

### Immediate Implementation

1. **Install Spectral**
   ```bash
   npm install -g @stoplight/spectral-cli
   ```

2. **Create Base Ruleset**
   ```yaml
   # .spectral.yaml
   extends: ["spectral:oas"]
   
   rules:
     # Enforce operation IDs
     operation-operationId: error
     
     # Require descriptions
     operation-description: warn
     operation-summary: warn
     
     # Require contact info
     info-contact: error
     
     # Enforce server URLs
     oas3-api-servers: warn
     
     # Azure-specific
     azure-tenant-param:
       description: Tenant operations require tenantId parameter
       given: "$.paths.*.get.parameters"
       then:
         function: schema
         functionOptions:
           schema:
             contains:
               properties:
                 name:
                   enum: ["tenant_id", "tenantId"]
       severity: warn
   ```

3. **Add to CI Pipeline**
   ```yaml
   # .github/workflows/api-lint.yml
   name: API Lint
   on: [pull_request]
   jobs:
     lint:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         - name: Install Spectral
           run: npm install -g @stoplight/spectral-cli
         - name: Lint OpenAPI specs
           run: spectral lint '**/*.openapi.yaml'
   ```

### Short-term (Month 1)

1. **Custom Rules for Governance**
   ```yaml
   # .spectral/custom-rules.yaml
   extends: ["spectral:oas"]
   
   rules:
     # Multi-tenant pattern enforcement
     multi-tenant-operations:
       description: Operations should follow multi-tenant patterns
       given: "$.paths"
       then:
         function: pattern
         functionOptions:
           match: "/api/v[0-9]+/(tenants|{tenantId})"
       severity: warn
     
     # Cost-related endpoints documented
     cost-endpoints-require-rbac:
       description: Cost endpoints need RBAC documentation
       given: "$.paths['/api/v1/costs'].*"
       then:
         field: description
         function: pattern
         functionOptions:
           match: "(?i)(rbac|permission|role)"
       severity: error
   ```

2. **Pre-commit Integration**
   ```yaml
   # .pre-commit-config.yaml
   repos:
     - repo: local
       hooks:
         - id: spectral-lint
           name: Spectral Lint
           entry: spectral lint
           language: system
           files: '\.(yaml|json)$'
           pass_filenames: true
   ```

### Medium-term (Quarter 1)

1. **VS Code Integration**
   - Install Spectral extension
   - Configure workspace settings
   - Real-time linting

2. **Custom Functions**
   ```javascript
   // .spectral/functions/checkAzurePattern.js
   module.exports = (targetValue) => {
     if (!targetValue.includes('tenant')) {
       return [
         {
           message: 'Azure multi-tenant operations should include tenant in path',
         },
       ];
     }
     return [];
   };
   ```

3. **Documentation Integration**
   ```yaml
   # Link Spectral errors to ADRs
   rules:
     compliance-validation:
       description: "See ADR-0025: API Design Standards"
       # ...
   ```

## FastAPI-Specific Integration

### Automatic OpenAPI Generation

```python
# app/main.py
from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html

app = FastAPI(
    title="Azure Governance Platform",
    version="1.0.0",
    openapi_url="/api/v1/openapi.json",
    docs_url=None,  # Custom docs endpoint
)

# Spectral will lint this automatically
@app.get("/api/v1/tenants/{tenant_id}/costs", 
         operation_id="getTenantCosts",
         summary="Get tenant cost summary")
async def get_tenant_costs(tenant_id: str):
    """Returns cost summary for specified tenant.
    
    Requires: costs.read permission (see ADR-0018)
    """
    pass
```

### Schema Validation

```python
from pydantic import BaseModel

class TenantCostResponse(BaseModel):
    """Cost summary response schema."""
    tenant_id: str
    total_cost: float
    currency: str
    
    class Config:
        schema_extra = {
            "example": {
                "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
                "total_cost": 1234.56,
                "currency": "USD"
            }
        }
```

## Azure Integration

### API Management Import

```bash
# Export OpenAPI spec from FastAPI
curl http://localhost:8000/api/v1/openapi.json > openapi.json

# Import to API Management
az apim api import \
  --resource-group my-rg \
  --service-name my-apim \
  --api-id governance-api \
  --path /governance \
  --specification-format OpenAPI \
  --specification-path openapi.json
```

### Policy Validation

```xml
<!-- Spectral validates spec before this policy is applied -->
<policies>
  <inbound>
    <validate-jwt header-name="Authorization" />
    <check-header name="X-API-Version" />
  </inbound>
</policies>
```

---

## References

- Spectral Documentation: https://meta.stoplight.io/docs/spectral
- OpenAPI Specification: https://spec.openapis.org/
- AsyncAPI: https://www.asyncapi.com/
- Azure API Style Guide: https://github.com/Azure/azure-api-style-guide
- Adidas API Guidelines: https://github.com/adidas/api-guidelines
- APIs You Won't Hate Style Guide: https://github.com/apisyouwonthate/style-guide
