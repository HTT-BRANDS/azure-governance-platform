# Preflight Check System - Security Guide

> **Document Version:** 1.0  
> **Last Updated:** February 2025  
> **Classification:** Internal Use  
> **Owner:** Security & Governance Team

---

## 🔐 Security Considerations Summary

| Risk Area | Threat Level | Key Mitigation |
|-----------|--------------|----------------|
| Credential Exposure | 🔴 Critical | Never log secrets, mask in outputs, use Key Vault |
| Information Disclosure | 🟠 High | Sanitize error messages, limit detail based on audience |
| API Rate Limiting | 🟡 Medium | Implement caching, stagger checks, exponential backoff |
| Access Control | 🟠 High | Role-based access, rate limiting, audit logging |
| Audit Trail | 🟡 Medium | Log all preflight runs, retain 90 days, integrate SIEM |

---

## 1. Security Checklist for Preflight Implementation

### Pre-Deployment Security Review

#### Credential Handling
- [ ] Client secrets never logged to console, files, or APIs
- [ ] Secrets masked in all output (UI, logs, API responses)
- [ ] Key Vault integration implemented for production
- [ ] Secret rotation process documented and scheduled
- [ ] Temporary credential validation uses time-limited tokens only
- [ ] No secrets stored in memory longer than necessary
- [ ] Memory cleared after credential validation

#### Permission Verification
- [ ] Least-privilege access verified for all tenants
- [ ] Overly permissive roles flagged (Owner, Contributor warnings)
- [ ] Required vs actual permissions compared and reported
- [ ] Graph API permissions validated without exposing user data
- [ ] Service principal scope boundaries checked

#### Error Handling
- [ ] Error messages sanitized to prevent information disclosure
- [ ] Tenant IDs never exposed in error messages to end users
- [ ] Client IDs never logged or displayed
- [ ] Stack traces only shown in debug mode to authorized users
- [ ] Helpful debugging info available for admins only

#### API Rate Limiting
- [ ] Per-tenant rate limits implemented
- [ ] Caching layer for check results (TTL: 5 minutes minimum)
- [ ] Exponential backoff for transient failures
- [ ] Circuit breaker pattern for failing tenants
- [ ] Concurrent request limits enforced

#### Audit Logging
- [ ] All preflight runs logged (success and failure)
- [ ] Log format includes: timestamp, user, tenant, check type, result
- [ ] Sensitive data redacted from logs
- [ ] 90-day log retention policy implemented
- [ ] Integration with Azure Monitor/Application Insights
- [ ] Alerting on anomalous preflight activity

#### Access Control
- [ ] Authentication required to run preflight checks
- [ ] Role-based access (admin vs read-only)
- [ ] Rate limiting per user/IP address
- [ ] Preflight results access controlled by role
- [ ] Abuse prevention mechanisms in place

---

## 2. Credential Handling Guidelines

### 2.1 Core Principles

1. **Never log secrets** - Secrets must never appear in logs, error messages, or API responses
2. **Mask in outputs** - Always mask secrets in UI displays and debug output
3. **Time-limited validation** - Use temporary tokens for credential verification
4. **Memory safety** - Clear secrets from memory immediately after use
5. **Key Vault for production** - Use Azure Key Vault for all production credentials

### 2.2 Safe Credential Handling Code Examples

#### Example 1: Secret Masking Utility

```python
"""Secure credential handling utilities."""

import re
from typing import Optional
from datetime import datetime, timedelta


class SecureCredentialHandler:
    """Handles credentials securely without exposing values."""
    
    # Patterns to detect and mask secrets in strings
    SECRET_PATTERNS = [
        (r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '***-GUID-***'),
        (r'[A-Za-z0-9]{40,}', '***-SECRET-***'),
        (r'eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*', '***-JWT-***'),
    ]
    
    @staticmethod
    def mask_secret(value: Optional[str], visible_chars: int = 4) -> str:
        """Mask a secret value, showing only first/last N characters.
        
        Args:
            value: The secret value to mask
            visible_chars: Number of characters to show at start/end
            
        Returns:
            Masked string like "abcd****wxyz"
        """
        if not value:
            return "[NOT SET]"
        
        if len(value) <= visible_chars * 2:
            return "*" * len(value)
        
        return f"{value[:visible_chars]}{'*' * (len(value) - visible_chars * 2)}{value[-visible_chars:]}"
    
    @staticmethod
    def sanitize_string(input_str: str) -> str:
        """Remove potential secrets from a string.
        
        Use this for sanitizing log messages and error outputs.
        """
        if not input_str:
            return input_str
            
        result = input_str
        for pattern, replacement in SecureCredentialHandler.SECRET_PATTERNS:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        return result
    
    @staticmethod
    def validate_credential_format(credential: str, credential_type: str) -> bool:
        """Validate credential format without exposing the value.
        
        Returns True if format appears valid, False otherwise.
        """
        if not credential or len(credential) < 10:
            return False
            
        if credential_type == "client_secret":
            # Azure client secrets are typically 34-40 characters
            return 20 <= len(credential) <= 128
        elif credential_type == "tenant_id":
            # Tenant IDs are GUIDs
            return re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', 
                          credential, re.IGNORECASE) is not None
        elif credential_type == "client_id":
            # Client IDs are GUIDs
            return re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', 
                          credential, re.IGNORECASE) is not None
        
        return True


# Convenience functions
def mask_secret(value: Optional[str], visible_chars: int = 4) -> str:
    """Mask a secret value."""
    return SecureCredentialHandler.mask_secret(value, visible_chars)


def sanitize_for_logs(message: str) -> str:
    """Sanitize a message for safe logging."""
    return SecureCredentialHandler.sanitize_string(message)
```

#### Example 2: Safe Credential Validation

```python
"""Safe credential validation without exposing secrets."""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from azure.identity import ClientSecretCredential
from azure.core.exceptions import ClientAuthenticationError

logger = logging.getLogger(__name__)


class CredentialValidator:
    """Validates Azure credentials without exposing secret values."""
    
    def __init__(self):
        self._validation_cache: Dict[str, Tuple[bool, datetime]] = {}
        self._cache_ttl = timedelta(minutes=5)
    
    async def validate_tenant_credentials(
        self, 
        tenant_id: str, 
        client_id: str, 
        client_secret: str
    ) -> Dict:
        """Validate credentials for a tenant.
        
        Returns validation result without exposing secret values.
        """
        # Create cache key (hash of non-secret identifiers)
        cache_key = f"{tenant_id}:{client_id}"
        
        # Check cache
        if cache_key in self._validation_cache:
            is_valid, timestamp = self._validation_cache[cache_key]
            if datetime.utcnow() - timestamp < self._cache_ttl:
                return {
                    "tenant_id": mask_id(tenant_id),
                    "client_id": mask_id(client_id),
                    "valid": is_valid,
                    "cached": True,
                    "timestamp": timestamp.isoformat(),
                }
        
        # Perform validation
        result = await self._perform_validation(tenant_id, client_id, client_secret)
        
        # Cache result (not the secret!)
        self._validation_cache[cache_key] = (result["valid"], datetime.utcnow())
        
        return result
    
    async def _perform_validation(
        self, 
        tenant_id: str, 
        client_id: str, 
        client_secret: str
    ) -> Dict:
        """Perform actual credential validation."""
        result = {
            "tenant_id": mask_id(tenant_id),
            "client_id": mask_id(client_id),
            "valid": False,
            "cached": False,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {},
        }
        
        try:
            # Attempt to create credential and get token
            credential = ClientSecretCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret,
            )
            
            # Get token (proves credential is valid)
            token = credential.get_token("https://management.azure.com/.default")
            
            result["valid"] = True
            result["checks"]["authentication"] = "passed"
            result["checks"]["token_acquired"] = True
            result["checks"]["token_expires"] = datetime.fromtimestamp(
                token.expires_on
            ).isoformat()
            
            # Clear credential from memory
            del credential
            
        except ClientAuthenticationError as e:
            result["checks"]["authentication"] = "failed"
            # Sanitize error message before including
            result["error"] = sanitize_for_logs(str(e))
            logger.warning(f"Credential validation failed for tenant {mask_id(tenant_id)}")
            
        except Exception as e:
            result["checks"]["authentication"] = "error"
            result["error"] = "Unexpected error during validation"
            logger.error(f"Unexpected error validating tenant {mask_id(tenant_id)}: {sanitize_for_logs(str(e))}")
        
        return result
    
    def clear_cache(self):
        """Clear validation cache."""
        self._validation_cache.clear()


def mask_id(guid: str) -> str:
    """Mask a GUID, showing only first and last 4 characters."""
    if not guid or len(guid) < 12:
        return "***"
    return f"{guid[:4]}...{guid[-4:]}"
```

#### Example 3: Key Vault Integration for Production

```python
"""Azure Key Vault integration for secure credential storage."""

import logging
from typing import Optional
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

logger = logging.getLogger(__name__)


class KeyVaultCredentialProvider:
    """Provides credentials from Azure Key Vault."""
    
    def __init__(self, key_vault_url: str):
        self.key_vault_url = key_vault_url
        self._credential = DefaultAzureCredential()
        self._client = SecretClient(
            vault_url=key_vault_url,
            credential=self._credential
        )
    
    async def get_tenant_credentials(self, tenant_id: str) -> Optional[Dict]:
        """Retrieve credentials for a tenant from Key Vault.
        
        Secrets should be stored with naming convention:
        - {tenant-id}-client-id
        - {tenant-id}-client-secret
        """
        try:
            client_id_secret = await self._client.get_secret(f"{tenant_id}-client-id")
            client_secret_secret = await self._client.get_secret(f"{tenant_id}-client-secret")
            
            return {
                "tenant_id": tenant_id,
                "client_id": client_id_secret.value,
                "client_secret": client_secret_secret.value,
            }
        except Exception as e:
            logger.error(f"Failed to retrieve credentials for tenant {mask_id(tenant_id)}")
            return None
    
    async def rotate_secret(self, tenant_id: str) -> bool:
        """Rotate client secret for a tenant.
        
        This should be called as part of regular secret rotation.
        """
        # Implementation would:
        # 1. Generate new secret via Azure AD API
        # 2. Store new secret in Key Vault
        # 3. Update secret rotation timestamp
        # 4. Schedule old secret expiration
        logger.info(f"Initiating secret rotation for tenant {mask_id(tenant_id)}")
        # ... implementation details
        return True


def get_credential_provider():
    """Factory function to get appropriate credential provider."""
    from app.core.config import get_settings
    
    settings = get_settings()
    
    if settings.key_vault_url:
        return KeyVaultCredentialProvider(settings.key_vault_url)
    else:
        # Fall back to environment variables (dev only)
        logger.warning("Key Vault not configured - using environment variables")
        return EnvironmentCredentialProvider()
```

### 2.3 Credential Handling Anti-Patterns

❌ **NEVER DO THIS:**

```python
# NEVER: Logging secrets
logger.info(f"Using secret: {client_secret}")

# NEVER: Including secrets in error messages
raise ValueError(f"Invalid secret: {client_secret}")

# NEVER: Returning secrets in API responses
return {"status": "ok", "secret": client_secret}

# NEVER: Storing secrets in plain text files
with open("secrets.txt", "w") as f:
    f.write(client_secret)

# NEVER: Passing secrets in URL parameters
requests.get(f"https://api.example.com?secret={client_secret}")
```

✅ **ALWAYS DO THIS:**

```python
# ALWAYS: Mask secrets in logs
logger.info(f"Credential validated for tenant: {mask_id(tenant_id)}")

# ALWAYS: Sanitize error messages
raise ValueError(sanitize_for_logs(str(error)))

# ALWAYS: Return only status, never the secret
return {"status": "ok", "tenant": mask_id(tenant_id)}

# ALWAYS: Use secure storage (Key Vault)
secret_client.set_secret(secret_name, client_secret)

# ALWAYS: Pass secrets in headers or body (HTTPS only)
requests.post(url, headers={"Authorization": f"Bearer {token}"})
```

---

## 3. Permission Verification Security

### 3.1 Least-Privilege Verification

The preflight system should verify that the service principal has only the minimum required permissions.

#### Required Permissions Reference

| Resource Type | Minimum Required | Warning If | Critical If |
|---------------|------------------|------------|-------------|
| Azure Resources | Reader | Contributor | Owner |
| Cost Data | Cost Management Reader | - | Contributor |
| Security Data | Security Reader | - | Contributor |
| Graph API | User.Read.All, Directory.Read.All | Write permissions | Directory.ReadWrite.All |
| RBAC | Read only | Role assignments | Privileged Role Admin |

#### Permission Verification Implementation

```python
"""Permission verification with least-privilege checks."""

from enum import Enum
from typing import List, Dict
from dataclasses import dataclass


class PermissionLevel(Enum):
    """Permission risk levels."""
    SAFE = "safe"
    WARNING = "warning"  # More permissive than needed
    CRITICAL = "critical"  # Dangerously permissive


@dataclass
class PermissionCheck:
    """Result of a permission check."""
    permission: str
    level: PermissionLevel
    message: str
    recommendation: str


class PermissionVerifier:
    """Verifies service principal permissions."""
    
    # Overly permissive roles that should trigger warnings
    WARNING_ROLES = [
        "Contributor",
        "User Access Administrator",
        "Log Analytics Contributor",
    ]
    
    # Critical roles that should never be assigned
    CRITICAL_ROLES = [
        "Owner",
        "Privileged Role Administrator",
        "Global Administrator",
    ]
    
    # Required minimum permissions
    REQUIRED_PERMISSIONS = [
        "User.Read.All",
        "Directory.Read.All",
        "RoleManagement.Read.All",
    ]
    
    async def verify_permissions(self, tenant_id: str, credential) -> Dict:
        """Verify permissions for a tenant."""
        results = {
            "tenant_id": mask_id(tenant_id),
            "overall_status": "pass",
            "checks": [],
            "recommendations": [],
        }
        
        # Check Azure RBAC roles
        rbac_checks = await self._check_rbac_roles(tenant_id, credential)
        results["checks"].extend(rbac_checks)
        
        # Check Graph API permissions
        graph_checks = await self._check_graph_permissions(tenant_id, credential)
        results["checks"].extend(graph_checks)
        
        # Determine overall status
        if any(c.level == PermissionLevel.CRITICAL for c in results["checks"]):
            results["overall_status"] = "critical"
        elif any(c.level == PermissionLevel.WARNING for c in results["checks"]):
            results["overall_status"] = "warning"
        
        # Generate recommendations
        results["recommendations"] = [
            c.recommendation for c in results["checks"] 
            if c.level != PermissionLevel.SAFE
        ]
        
        return results
    
    async def _check_rbac_roles(self, tenant_id: str, credential) -> List[PermissionCheck]:
        """Check Azure RBAC role assignments."""
        checks = []
        
        # Get role assignments (simplified - actual implementation would query Azure)
        role_assignments = await self._get_role_assignments(tenant_id, credential)
        
        for role in role_assignments:
            if role in self.CRITICAL_ROLES:
                checks.append(PermissionCheck(
                    permission=role,
                    level=PermissionLevel.CRITICAL,
                    message=f"CRITICAL: '{role}' grants excessive privileges",
                    recommendation=f"Remove '{role}' and use 'Reader' instead",
                ))
            elif role in self.WARNING_ROLES:
                checks.append(PermissionCheck(
                    permission=role,
                    level=PermissionLevel.WARNING,
                    message=f"WARNING: '{role}' is more permissive than required",
                    recommendation=f"Consider replacing '{role}' with 'Reader'",
                ))
            elif role in ["Reader", "Cost Management Reader", "Security Reader"]:
                checks.append(PermissionCheck(
                    permission=role,
                    level=PermissionLevel.SAFE,
                    message=f"'{role}' is appropriate for read-only access",
                    recommendation="No action needed",
                ))
        
        return checks
    
    async def _check_graph_permissions(self, tenant_id: str, credential) -> List[PermissionCheck]:
        """Check Microsoft Graph API permissions."""
        checks = []
        
        # Get granted permissions
        granted_permissions = await self._get_graph_permissions(tenant_id, credential)
        
        # Check for write permissions
        write_permissions = [p for p in granted_permissions if ".Write" in p or ".Manage" in p]
        for perm in write_permissions:
            checks.append(PermissionCheck(
                permission=perm,
                level=PermissionLevel.CRITICAL,
                message=f"CRITICAL: Write permission '{perm}' detected",
                recommendation=f"Remove '{perm}' - read-only permissions are sufficient",
            ))
        
        # Verify required permissions are present
        for required in self.REQUIRED_PERMISSIONS:
            if required not in granted_permissions:
                checks.append(PermissionCheck(
                    permission=required,
                    level=PermissionLevel.CRITICAL,
                    message=f"CRITICAL: Required permission '{required}' not granted",
                    recommendation=f"Grant '{required}' via Azure Portal",
                ))
        
        return checks
```

### 3.2 Graph API Permission Verification

When verifying Graph API permissions, the system should validate access without exposing sensitive user data:

```python
"""Safe Graph API permission verification."""

async def verify_graph_access_safe(credential) -> Dict:
    """Verify Graph API access without exposing user data.
    
    Instead of querying actual users (which could expose PII),
    we verify permissions by checking the /organization endpoint
    which requires Directory.Read.All but returns only tenant info.
    """
    try:
        token = credential.get_token("https://graph.microsoft.com/.default")
        
        # Use organization endpoint - requires permissions but no PII
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://graph.microsoft.com/v1.0/organization",
                headers={"Authorization": f"Bearer {token.token}"},
            )
            response.raise_for_status()
            data = response.json()
            
            # Only return count and verification status, not actual data
            return {
                "valid": True,
                "tenant_count": len(data.get("value", [])),
                "permissions_verified": ["Directory.Read.All"],
            }
            
    except Exception as e:
        return {
            "valid": False,
            "error": "Graph API access verification failed",
            "permissions_needed": ["Directory.Read.All"],
        }
```

---

## 4. Error Message Security

### 4.1 Error Message Classification

| Information Type | Admin/Developer | End User | Logs |
|-----------------|-----------------|----------|------|
| Error type/message | ✅ Full detail | ✅ Generic | ✅ Sanitized |
| Tenant ID | ✅ Visible | ❌ Masked | ✅ Masked |
| Client ID | ✅ Visible | ❌ Hidden | ✅ Masked |
| Stack traces | ✅ Full | ❌ Hidden | ✅ Available |
| Azure error codes | ✅ Full | ⚠️ Filtered | ✅ Sanitized |
| Secret values | ❌ Never | ❌ Never | ❌ Never |
| Subscription IDs | ✅ Visible | ⚠️ Masked | ✅ Masked |

### 4.2 Safe Error Message Templates

#### Safe Error Templates

```python
"""Secure error message templates."""

from enum import Enum
from typing import Optional


class ErrorCategory(Enum):
    """Categories of errors for appropriate messaging."""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    NETWORK = "network"
    CONFIGURATION = "configuration"
    RATE_LIMIT = "rate_limit"
    INTERNAL = "internal"


ERROR_TEMPLATES = {
    # Admin/Internal Messages (detailed)
    "admin": {
        ErrorCategory.AUTHENTICATION: {
            "title": "Authentication Failed",
            "message": "Failed to authenticate to tenant {tenant_id}. "
                      "Error: {error_detail}. Check client secret validity.",
            "action": "Verify credentials in Key Vault or environment variables.",
        },
        ErrorCategory.AUTHORIZATION: {
            "title": "Authorization Failed",
            "message": "Service principal {client_id} lacks required permissions. "
                      "Missing: {missing_permissions}.",
            "action": "Grant required permissions in Azure Portal.",
        },
        ErrorCategory.RATE_LIMIT: {
            "title": "Rate Limit Exceeded",
            "message": "Azure API rate limit hit for tenant {tenant_id}. "
                      "Retry after: {retry_after}s.",
            "action": "Implement backoff or reduce request frequency.",
        },
    },
    
    # User Messages (generic)
    "user": {
        ErrorCategory.AUTHENTICATION: {
            "title": "Connection Error",
            "message": "Unable to connect to Azure. Please contact your administrator.",
            "action": "Contact support with reference: {reference_id}",
        },
        ErrorCategory.AUTHORIZATION: {
            "title": "Access Denied",
            "message": "Insufficient permissions to access this resource.",
            "action": "Contact your administrator to request access.",
        },
        ErrorCategory.RATE_LIMIT: {
            "title": "Service Temporarily Unavailable",
            "message": "Service is experiencing high demand. Please try again later.",
            "action": "Wait a few minutes and retry.",
        },
        ErrorCategory.INTERNAL: {
            "title": "An Error Occurred",
            "message": "Something went wrong. Our team has been notified.",
            "action": "Reference: {reference_id}",
        },
    },
}


class SecureErrorHandler:
    """Generates appropriate error messages based on audience."""
    
    def __init__(self):
        self.error_counter = 0
    
    def get_error_response(
        self, 
        category: ErrorCategory,
        audience: str = "user",
        details: Optional[dict] = None,
        exception: Optional[Exception] = None
    ) -> dict:
        """Generate an error response appropriate for the audience.
        
        Args:
            category: Type of error
            audience: 'user', 'admin', or 'log'
            details: Additional context (will be sanitized)
            exception: Original exception (for logging)
        """
        self.error_counter += 1
        reference_id = f"ERR-{self.error_counter:06d}"
        
        template = ERROR_TEMPLATES.get(audience, {}).get(category, {})
        
        # Sanitize details
        safe_details = self._sanitize_details(details or {})
        
        response = {
            "success": False,
            "error": {
                "reference_id": reference_id,
                "title": template.get("title", "Error"),
                "message": template.get("message", "An error occurred").format(
                    reference_id=reference_id,
                    **safe_details
                ),
            }
        }
        
        # Add action for user-facing errors
        if audience == "user":
            response["error"]["action"] = template.get("action", "").format(
                reference_id=reference_id
            )
        
        # Log full error (sanitized) for debugging
        if exception:
            logger.error(
                f"Error {reference_id}: {sanitize_for_logs(str(exception))}",
                extra={"reference_id": reference_id, "category": category.value}
            )
        
        return response
    
    def _sanitize_details(self, details: dict) -> dict:
        """Sanitize detail values for safe output."""
        sanitized = {}
        for key, value in details.items():
            if isinstance(value, str):
                # Mask potential GUIDs
                if re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', 
                           value, re.IGNORECASE):
                    sanitized[key] = mask_id(value)
                else:
                    sanitized[key] = sanitize_for_logs(value)
            else:
                sanitized[key] = value
        return sanitized
```

### 4.3 Error Message Examples

#### ❌ Unsafe Error Messages

```python
# DON'T: Expose tenant IDs to users
{"error": "Tenant 12345678-1234-1234-1234-123456789012 not found"}

# DON'T: Include Azure error codes that reveal structure
{"error": "AADSTS7000215: Invalid client secret provided"}

# DON'T: Show stack traces to users
{"error": "Traceback (most recent call last): File '/app/main.py', line 42..."}

# DON'T: Reveal which permissions are missing
{"error": "Missing permission: Directory.ReadWrite.All"}
```

#### ✅ Safe Error Messages

```python
# DO: Generic message with reference ID
{
    "success": False,
    "error": {
        "reference_id": "ERR-000042",
        "title": "Connection Error",
        "message": "Unable to connect to Azure. Please contact your administrator.",
        "action": "Contact support with reference: ERR-000042"
    }
}

# DO: For admins (internal), include masked IDs
{
    "success": False,
    "error": {
        "reference_id": "ERR-000042",
        "tenant_id": "1234...9012",  # Masked
        "message": "Authentication failed. Check client secret validity.",
        "azure_error": "AADSTS7000215",  # Code only, no details
    }
}
```

---

## 5. Audit Logging Recommendations

### 5.1 What to Log

#### Required Log Events

| Event | Log Level | Data to Include | Retention |
|-------|-----------|-----------------|-----------|
| Preflight initiated | INFO | User, timestamp, tenant count | 90 days |
| Check started | DEBUG | Check type, tenant (masked) | 30 days |
| Check completed | INFO | Check type, result, duration | 90 days |
| Authentication failure | WARNING | Tenant (masked), error code | 90 days |
| Permission issue | WARNING | Tenant (masked), missing perms | 90 days |
| Rate limit hit | WARNING | Tenant (masked), retry-after | 90 days |
| Critical permission found | ERROR | Tenant (masked), role name | 1 year |
| Preflight completed | INFO | Overall result, duration | 90 days |

### 5.2 Secure Log Format

```python
"""Secure audit logging for preflight checks."""

import logging
import json
from datetime import datetime
from typing import Dict, Any
import hashlib


class PreflightAuditLogger:
    """Structured audit logging for preflight operations."""
    
    def __init__(self):
        self.logger = logging.getLogger("preflight.audit")
    
    def log_preflight_initiated(self, user_id: str, tenant_ids: list) -> str:
        """Log preflight check initiation."""
        trace_id = self._generate_trace_id()
        
        self.logger.info(
            "Preflight check initiated",
            extra={
                "event_type": "PREFLIGHT_INITIATED",
                "trace_id": trace_id,
                "user_id": hashlib.sha256(user_id.encode()).hexdigest()[:16],  # Hashed
                "tenant_count": len(tenant_ids),
                "tenant_ids": [mask_id(t) for t in tenant_ids],  # Masked
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
        return trace_id
    
    def log_check_completed(
        self, 
        trace_id: str, 
        tenant_id: str, 
        check_type: str, 
        result: str,
        duration_ms: int,
        details: Dict[str, Any]
    ):
        """Log individual check completion."""
        self.logger.info(
            f"Check completed: {check_type}",
            extra={
                "event_type": "CHECK_COMPLETED",
                "trace_id": trace_id,
                "tenant_id": mask_id(tenant_id),
                "check_type": check_type,
                "result": result,
                "duration_ms": duration_ms,
                "timestamp": datetime.utcnow().isoformat(),
                # Sanitize details before logging
                "details": self._sanitize_log_details(details),
            }
        )
    
    def log_security_finding(
        self,
        trace_id: str,
        tenant_id: str,
        finding_type: str,
        severity: str,
        description: str,
    ):
        """Log security-related findings."""
        self.logger.warning(
            f"Security finding: {finding_type}",
            extra={
                "event_type": "SECURITY_FINDING",
                "trace_id": trace_id,
                "tenant_id": mask_id(tenant_id),
                "finding_type": finding_type,
                "severity": severity,
                "description": description,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
    
    def _sanitize_log_details(self, details: Dict) -> Dict:
        """Remove sensitive data from log details."""
        sensitive_keys = ['secret', 'password', 'token', 'key', 'credential']
        sanitized = {}
        
        for key, value in details.items():
            if any(sk in key.lower() for sk in sensitive_keys):
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, str) and len(value) > 40:
                # Potentially a secret or token
                sanitized[key] = mask_secret(value)
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _generate_trace_id(self) -> str:
        """Generate unique trace ID for request correlation."""
        return hashlib.sha256(
            f"{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]


# JSON structured log format example:
# {
#     "timestamp": "2025-02-25T10:30:00Z",
#     "level": "INFO",
#     "logger": "preflight.audit",
#     "message": "Preflight check initiated",
#     "event_type": "PREFLIGHT_INITIATED",
#     "trace_id": "a1b2c3d4e5f67890",
#     "user_id": "hash1234...",
#     "tenant_count": 5,
#     "tenant_ids": ["1234...9012", "abcd...efgh", ...]
# }
```

### 5.3 Azure Monitor Integration

```python
"""Azure Monitor integration for centralized logging."""

from opencensus.ext.azure.log_exporter import AzureLogHandler
import logging


def configure_azure_monitor_logging(instrumentation_key: str):
    """Configure logging to send to Azure Monitor."""
    
    # Create logger
    logger = logging.getLogger("preflight.audit")
    logger.setLevel(logging.INFO)
    
    # Add Azure Monitor handler
    handler = AzureLogHandler(
        connection_string=f"InstrumentationKey={instrumentation_key}"
    )
    handler.setLevel(logging.INFO)
    
    # Custom formatter for structured logs
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    
    return logger
```

### 5.4 Log Retention Policy

| Log Type | Retention Period | Storage Location | Access Control |
|----------|-----------------|------------------|----------------|
| Security findings | 1 year | Azure Monitor Logs + SIEM | Security team only |
| Preflight audit logs | 90 days | Azure Monitor Logs | Admin read-only |
| Debug logs | 30 days | Local (dev) / App Insights (prod) | Developers |
| Error logs | 90 days | Azure Monitor Logs | Operations team |

---

## 6. API Rate Limiting Strategy

### 6.1 Azure API Rate Limits

| Azure Service | Rate Limit | Preflight Impact |
|---------------|------------|------------------|
| Microsoft Graph | 10,000 requests/10 min | User/group queries |
| Azure Management | 12,000 requests/hour | Resource inventory |
| Cost Management | 30 requests/min | Cost data queries |
| Policy Insights | 300 requests/min | Compliance checks |

### 6.2 Rate Limiting Implementation

```python
"""Rate limiting and caching for preflight checks."""

import asyncio
import time
from typing import Dict, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import hashlib


@dataclass
class RateLimitConfig:
    """Rate limiting configuration per service."""
    requests_per_minute: int
    burst_size: int
    retry_after_seconds: int


@dataclass
class TenantRateLimiter:
    """Per-tenant rate limiter with token bucket algorithm."""
    
    config: RateLimitConfig
    tokens: float = field(default=0)
    last_update: float = field(default_factory=time.time)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    
    async def acquire(self) -> bool:
        """Acquire a token, waiting if necessary."""
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            
            # Add tokens based on time elapsed
            self.tokens = min(
                self.config.burst_size,
                self.tokens + elapsed * (self.config.requests_per_minute / 60)
            )
            self.last_update = now
            
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            
            # Calculate wait time
            wait_time = (1 - self.tokens) / (self.config.requests_per_minute / 60)
            return False
    
    async def wait_and_acquire(self) -> None:
        """Wait until a token is available."""
        while not await self.acquire():
            await asyncio.sleep(1)


class PreflightRateLimiter:
    """Centralized rate limiting for preflight checks."""
    
    # Rate limit configs per Azure service
    SERVICE_LIMITS = {
        "graph": RateLimitConfig(1000, 100, 60),  # 1000/min, burst 100
        "azure_mgmt": RateLimitConfig(200, 50, 60),
        "cost_management": RateLimitConfig(30, 10, 60),
        "policy": RateLimitConfig(300, 50, 60),
    }
    
    def __init__(self):
        self._tenant_limiters: Dict[str, Dict[str, TenantRateLimiter]] = defaultdict(
            lambda: {
                service: TenantRateLimiter(config)
                for service, config in self.SERVICE_LIMITS.items()
            }
        )
        self._global_limiter = TenantRateLimiter(
            RateLimitConfig(5000, 500, 60)  # Global limit
        )
    
    async def acquire(self, tenant_id: str, service: str) -> None:
        """Acquire rate limit token for a tenant and service."""
        # Check global limit first
        await self._global_limiter.wait_and_acquire()
        
        # Check tenant-specific limit
        limiter = self._tenant_limiters[tenant_id][service]
        await limiter.wait_and_acquire()


class PreflightCache:
    """Caching layer for preflight check results."""
    
    def __init__(self, default_ttl_seconds: int = 300):
        self._cache: Dict[str, Dict] = {}
        self._default_ttl = default_ttl_seconds
    
    def _make_key(self, tenant_id: str, check_type: str, params: Dict) -> str:
        """Generate cache key from check parameters."""
        # Hash the parameters to create a safe key
        param_str = json.dumps(params, sort_keys=True)
        return hashlib.sha256(
            f"{tenant_id}:{check_type}:{param_str}".encode()
        ).hexdigest()
    
    def get(self, tenant_id: str, check_type: str, params: Dict) -> Optional[Dict]:
        """Get cached result if valid."""
        key = self._make_key(tenant_id, check_type, params)
        entry = self._cache.get(key)
        
        if entry and time.time() < entry["expires"]:
            return entry["result"]
        
        return None
    
    def set(
        self, 
        tenant_id: str, 
        check_type: str, 
        params: Dict, 
        result: Dict,
        ttl_seconds: Optional[int] = None
    ):
        """Cache a check result."""
        key = self._make_key(tenant_id, check_type, params)
        
        self._cache[key] = {
            "result": result,
            "expires": time.time() + (ttl_seconds or self._default_ttl),
            "tenant_id": mask_id(tenant_id),  # For debugging
            "check_type": check_type,
        }
    
    def invalidate(self, tenant_id: str) -> int:
        """Invalidate all cached results for a tenant."""
        keys_to_remove = [
            k for k, v in self._cache.items() 
            if v.get("tenant_id") == mask_id(tenant_id)
        ]
        for k in keys_to_remove:
            del self._cache[k]
        return len(keys_to_remove)


# Circuit breaker for failing tenants
class CircuitBreaker:
    """Circuit breaker pattern for unreliable tenants."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures: Dict[str, int] = defaultdict(int)
        self.last_failure: Dict[str, float] = {}
        self.states: Dict[str, str] = defaultdict(lambda: "CLOSED")
    
    def record_success(self, tenant_id: str):
        """Record successful operation."""
        self.failures[tenant_id] = 0
        self.states[tenant_id] = "CLOSED"
    
    def record_failure(self, tenant_id: str):
        """Record failed operation."""
        self.failures[tenant_id] += 1
        self.last_failure[tenant_id] = time.time()
        
        if self.failures[tenant_id] >= self.failure_threshold:
            self.states[tenant_id] = "OPEN"
    
    def can_execute(self, tenant_id: str) -> bool:
        """Check if operation can be executed."""
        if self.states[tenant_id] == "CLOSED":
            return True
        
        # Check if recovery timeout has passed
        if time.time() - self.last_failure.get(tenant_id, 0) > self.recovery_timeout:
            self.states[tenant_id] = "HALF_OPEN"
            return True
        
        return False
    
    def get_state(self, tenant_id: str) -> str:
        """Get current circuit state for tenant."""
        return self.states[tenant_id]
```

### 6.3 Staggering Multi-Tenant Checks

```python
"""Stagger preflight checks across multiple tenants."""

import asyncio
from typing import List


class StaggeredExecutor:
    """Executes checks across tenants with staggered delays."""
    
    def __init__(self, stagger_delay_seconds: float = 2.0, max_concurrent: int = 3):
        self.stagger_delay = stagger_delay_seconds
        self.max_concurrent = max_concurrent
    
    async def execute_staggered(
        self, 
        tenant_ids: List[str], 
        check_func,
        *args, 
        **kwargs
    ) -> List[Dict]:
        """Execute checks across tenants with staggered delays.
        
        Args:
            tenant_ids: List of tenant IDs to check
            check_func: Async function to call for each tenant
            *args, **kwargs: Arguments to pass to check_func
            
        Returns:
            List of results from each tenant
        """
        semaphore = asyncio.Semaphore(self.max_concurrent)
        results = []
        
        async def execute_with_delay(tenant_id: str, delay: float):
            await asyncio.sleep(delay)
            
            async with semaphore:
                try:
                    result = await check_func(tenant_id, *args, **kwargs)
                    return {"tenant_id": tenant_id, "result": result, "success": True}
                except Exception as e:
                    return {
                        "tenant_id": tenant_id, 
                        "error": str(e), 
                        "success": False
                    }
        
        # Create tasks with increasing delays
        tasks = [
            execute_with_delay(tid, i * self.stagger_delay)
            for i, tid in enumerate(tenant_ids)
        ]
        
        # Execute all tasks
        results = await asyncio.gather(*tasks)
        return results


# Usage example:
# executor = StaggeredExecutor(stagger_delay_seconds=2.0)
# results = await executor.execute_staggered(
#     tenant_ids=["tenant1", "tenant2", "tenant3", "tenant4", "tenant5"],
#     check_func=run_preflight_check,
#     check_type="authentication"
# )
```

---

## 7. Access Control for Preflight Endpoints

### 7.1 Authentication & Authorization

```python
"""Access control for preflight endpoints."""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import time

security = HTTPBearer()


class PreflightAccessControl:
    """Access control for preflight operations."""
    
    def __init__(self):
        # Rate limiting per user
        self._user_requests: Dict[str, List[float]] = {}
        self._max_requests_per_minute = 10
        
        # Role definitions
        self.ROLES = {
            "admin": ["run_preflight", "view_all_results", "view_detailed_errors"],
            "operator": ["run_preflight", "view_own_results"],
            "viewer": ["view_own_results"],
        }
    
    async def authenticate(self, credentials: HTTPAuthorizationCredentials) -> Dict:
        """Authenticate user and return user info."""
        # Implementation depends on your auth provider (Azure AD, etc.)
        # This is a simplified example
        token = credentials.credentials
        
        # Validate token (JWT verification, etc.)
        user_info = await self._validate_token(token)
        
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        return user_info
    
    def check_permission(self, user_info: Dict, permission: str) -> bool:
        """Check if user has required permission."""
        user_role = user_info.get("role", "viewer")
        allowed_permissions = self.ROLES.get(user_role, [])
        return permission in allowed_permissions
    
    async def rate_limit_check(self, user_id: str) -> bool:
        """Check if user has exceeded rate limit."""
        now = time.time()
        minute_ago = now - 60
        
        # Get recent requests
        recent_requests = [
            req_time for req_time in self._user_requests.get(user_id, [])
            if req_time > minute_ago
        ]
        
        # Update requests list
        self._user_requests[user_id] = recent_requests
        
        if len(recent_requests) >= self._max_requests_per_minute:
            return False
        
        # Record this request
        recent_requests.append(now)
        return True
    
    def get_user_facing_error(self, error: Exception, user_role: str) -> Dict:
        """Get error message appropriate for user's role."""
        if user_role == "admin":
            return {
                "error": "Internal error",
                "detail": sanitize_for_logs(str(error)),
                "type": type(error).__name__,
            }
        else:
            return {
                "error": "An error occurred",
                "message": "Please contact your administrator",
            }


# FastAPI dependency
async def require_preflight_permission(
    permission: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Dependency to check preflight permissions."""
    access_control = PreflightAccessControl()
    
    # Authenticate
    user_info = await access_control.authenticate(credentials)
    
    # Rate limit check
    if not await access_control.rate_limit_check(user_info["id"]):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )
    
    # Permission check
    if not access_control.check_permission(user_info, permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    # Attach user info to request
    request.state.user = user_info
    return user_info


# Usage in routes:
# @router.post("/preflight/run")
# async def run_preflight(
#     user: Dict = Depends(lambda: require_preflight_permission("run_preflight"))
# ):
#     # Only users with "run_preflight" permission can access
#     pass
```

### 7.2 API Endpoint Security Matrix

| Endpoint | Method | Required Role | Rate Limit | Notes |
|----------|--------|---------------|------------|-------|
| /preflight/run | POST | operator | 10/min | Trigger preflight check |
| /preflight/status | GET | viewer | 30/min | Check running status |
| /preflight/results | GET | viewer | 30/min | View results (filtered) |
| /preflight/results/all | GET | admin | 10/min | View all results |
| /preflight/errors | GET | admin | 10/min | View detailed errors |
| /preflight/config | GET | operator | 10/min | View configuration |
| /preflight/config | PUT | admin | 5/min | Modify configuration |

---

## 8. Implementation Checklist

### Phase 1: Core Security (Required Before Deployment)

- [ ] Secret masking implemented in all outputs
- [ ] Key Vault integration configured for production
- [ ] Error message sanitization in place
- [ ] Tenant IDs masked in user-facing messages
- [ ] Audit logging configured
- [ ] Rate limiting implemented
- [ ] Authentication required for all endpoints
- [ ] Role-based access control configured

### Phase 2: Enhanced Security (Recommended)

- [ ] Circuit breaker pattern for failing tenants
- [ ] Caching layer for check results
- [ ] SIEM integration for security findings
- [ ] Automated alerting for anomalies
- [ ] Secret rotation automation
- [ ] Penetration testing completed
- [ ] Security review signed off

### Phase 3: Operational Excellence

- [ ] Runbooks for security incidents
- [ ] Regular access reviews
- [ ] Quarterly security audits
- [ ] DR testing for Key Vault
- [ ] Metrics dashboard for security KPIs

---

## 9. Security Metrics & KPIs

| Metric | Target | Measurement |
|--------|--------|-------------|
| Secrets exposed in logs | 0 | Automated log scanning |
| Unauthorized preflight attempts | <5/day | Audit log analysis |
| Rate limit violations | <1% of requests | API gateway metrics |
| Authentication failures | <2% of attempts | Auth logs |
| Cache hit rate | >50% | Cache metrics |
| Mean time to detect issues | <5 minutes | Alert response |
| Security finding resolution | <24 hours for critical | Ticket tracking |

---

## 10. References & Resources

### Azure Documentation
- [Azure AD Authentication Best Practices](https://docs.microsoft.com/en-us/azure/active-directory/develop/security-best-practices)
- [Key Vault Best Practices](https://docs.microsoft.com/en-us/azure/key-vault/general/best-practices)
- [Microsoft Graph Throttling](https://docs.microsoft.com/en-us/graph/throttling)

### Security Standards
- OWASP API Security Top 10
- NIST Cybersecurity Framework
- Azure Security Benchmark

### Internal Resources
- Incident Response Playbook
- Secret Rotation Procedures
- Security Escalation Contacts

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | February 2025 | Security & Governance Team | Initial release |

---

**END OF SECURITY GUIDE**
