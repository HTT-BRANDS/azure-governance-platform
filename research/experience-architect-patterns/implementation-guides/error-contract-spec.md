# Frontend-Backend Accessibility Error Contract Specification

**Date:** March 6, 2026  
**Version:** 1.0  
**Status:** Draft  
**Target:** Azure Governance Platform

---

## Overview

This specification defines a standardized error response format that supports accessibility requirements for screen readers and assistive technologies.

### Goals

1. Provide structured error information for programmatic handling
2. Include ARIA-compatible metadata for assistive technologies
3. Support focus management and error recovery
4. Enable consistent error presentation across all API endpoints

---

## Error Response Schema

### Base Error Response

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "AccessibilityErrorResponse",
  "type": "object",
  "required": ["error"],
  "properties": {
    "error": {
      "type": "object",
      "required": ["code", "message", "aria"],
      "properties": {
        "code": {
          "type": "string",
          "description": "Machine-readable error code",
          "example": "VALIDATION_ERROR"
        },
        "message": {
          "type": "string",
          "description": "Human-readable error message",
          "example": "Please check your input and try again."
        },
        "details": {
          "type": "string",
          "description": "Additional context about the error",
          "example": "The form contains 3 fields with errors."
        },
        "aria": {
          "type": "object",
          "description": "ARIA accessibility metadata",
          "properties": {
            "live": {
              "type": "string",
              "enum": ["off", "polite", "assertive"],
              "default": "assertive",
              "description": "ARIA live region behavior"
            },
            "atomic": {
              "type": "boolean",
              "default": true,
              "description": "Whether to announce entire region"
            },
            "relevant": {
              "type": "string",
              "default": "additions text",
              "description": "What changes to announce"
            }
          }
        },
        "fields": {
          "type": "array",
          "description": "Field-level error details",
          "items": {
            "$ref": "#/definitions/FieldError"
          }
        },
        "suggestions": {
          "type": "array",
          "description": "Suggested actions to resolve the error",
          "items": {
            "$ref": "#/definitions/Suggestion"
          }
        },
        "help_url": {
          "type": "string",
          "format": "uri",
          "description": "Link to documentation about this error"
        },
        "request_id": {
          "type": "string",
          "description": "Unique identifier for support requests"
        },
        "timestamp": {
          "type": "string",
          "format": "date-time",
          "description": "ISO 8601 timestamp of error"
        }
      }
    }
  },
  "definitions": {
    "FieldError": {
      "type": "object",
      "required": ["id", "message"],
      "properties": {
        "id": {
          "type": "string",
          "description": "Field identifier (matches HTML id)"
        },
        "name": {
          "type": "string",
          "description": "Field name attribute"
        },
        "message": {
          "type": "string",
          "description": "Error message for this field"
        },
        "aria": {
          "type": "object",
          "properties": {
            "describedBy": {
              "type": "string",
              "description": "ID of element describing this field"
            },
            "errormessage": {
              "type": "string",
              "description": "ID of error message element"
            },
            "invalid": {
              "type": "boolean",
              "default": true
            }
          }
        },
        "value": {
          "type": "string",
          "description": "Submitted value (sanitized)"
        },
        "constraints": {
          "type": "object",
          "description": "Validation constraints that failed",
          "properties": {
            "min_length": {
              "type": "integer"
            },
            "max_length": {
              "type": "integer"
            },
            "pattern": {
              "type": "string"
            },
            "required": {
              "type": "boolean"
            }
          }
        }
      }
    },
    "Suggestion": {
      "type": "object",
      "required": ["action", "label"],
      "properties": {
        "action": {
          "type": "string",
          "description": "Action identifier"
        },
        "label": {
          "type": "string",
          "description": "Human-readable label"
        },
        "href": {
          "type": "string",
          "format": "uri",
          "description": "URL for navigation action"
        },
        "method": {
          "type": "string",
          "enum": ["GET", "POST", "PATCH", "DELETE"],
          "default": "GET"
        }
      }
    }
  }
}
```

---

## Error Code Reference

### Validation Errors (4xx)

| Code | HTTP Status | Description | ARIA Live |
|------|-------------|-------------|-----------|
| `VALIDATION_ERROR` | 400 | Generic validation failure | assertive |
| `REQUIRED_FIELD` | 400 | Required field missing | assertive |
| `INVALID_FORMAT` | 400 | Field format incorrect | assertive |
| `INVALID_VALUE` | 400 | Field value invalid | assertive |
| `TOO_SHORT` | 400 | Input too short | assertive |
| `TOO_LONG` | 400 | Input too long | assertive |
| `ALREADY_EXISTS` | 409 | Resource already exists | polite |
| `INVALID_DATE` | 400 | Date format/value invalid | assertive |
| `INVALID_EMAIL` | 400 | Email format invalid | assertive |
| `INVALID_PHONE` | 400 | Phone format invalid | assertive |

### Authentication Errors (401/403)

| Code | HTTP Status | Description | ARIA Live |
|------|-------------|-------------|-----------|
| `UNAUTHORIZED` | 401 | Authentication required | assertive |
| `FORBIDDEN` | 403 | Permission denied | assertive |
| `TOKEN_EXPIRED` | 401 | Session expired | assertive |
| `INVALID_CREDENTIALS` | 401 | Login failed | assertive |
| `ACCOUNT_LOCKED` | 403 | Account temporarily locked | polite |
| `MFA_REQUIRED` | 401 | Multi-factor auth required | assertive |

### Resource Errors (404/409)

| Code | HTTP Status | Description | ARIA Live |
|------|-------------|-------------|-----------|
| `NOT_FOUND` | 404 | Resource not found | polite |
| `GONE` | 410 | Resource permanently removed | polite |
| `CONFLICT` | 409 | Resource state conflict | assertive |

### Server Errors (5xx)

| Code | HTTP Status | Description | ARIA Live |
|------|-------------|-------------|-----------|
| `INTERNAL_ERROR` | 500 | Generic server error | assertive |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily down | assertive |
| `TIMEOUT` | 504 | Request timeout | assertive |
| `RATE_LIMITED` | 429 | Too many requests | polite |

---

## Implementation Examples

### Python (FastAPI)

```python
# app/core/exceptions.py
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
from fastapi import Request

class FieldError(BaseModel):
    """Field-level error with ARIA metadata."""
    
    id: str
    name: Optional[str] = None
    message: str
    value: Optional[str] = None
    aria_described_by: Optional[str] = None
    aria_errormessage: Optional[str] = None
    aria_invalid: bool = True
    constraints: Optional[Dict[str, Any]] = None
    
    def to_aria_attrs(self) -> Dict[str, str]:
        """Generate ARIA attributes for HTML element."""
        attrs = {"aria-invalid": "true"}
        if self.aria_described_by:
            attrs["aria-describedby"] = self.aria_described_by
        if self.aria_errormessage:
            attrs["aria-errormessage"] = self.aria_errormessage
        return attrs


class AccessibilityError(BaseModel):
    """Accessibility-enhanced error response."""
    
    code: str
    message: str
    details: Optional[str] = None
    aria_live: str = "assertive"
    aria_atomic: bool = True
    aria_relevant: str = "additions text"
    fields: List[FieldError] = []
    suggestions: List[Dict[str, str]] = []
    help_url: Optional[str] = None
    request_id: str
    timestamp: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": "VALIDATION_ERROR",
                "message": "Please check your input and try again.",
                "details": "The form contains 3 fields with errors.",
                "aria_live": "assertive",
                "aria_atomic": True,
                "fields": [
                    {
                        "id": "email",
                        "name": "email",
                        "message": "Email format is invalid",
                        "aria_described_by": "email-hint",
                        "aria_errormessage": "email-error",
                        "value": "invalid-email"
                    }
                ],
                "suggestions": [
                    {
                        "action": "reset",
                        "label": "Clear form and start over",
                        "href": "/form"
                    }
                ],
                "help_url": "/docs/errors/VALIDATION_ERROR",
                "request_id": "req_abc123",
                "timestamp": "2026-03-06T10:30:00Z"
            }
        }


class AccessibilityException(Exception):
    """Base exception with accessibility metadata."""
    
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: Optional[str] = None,
        fields: Optional[List[FieldError]] = None,
        suggestions: Optional[List[Dict[str, str]]] = None,
        help_url: Optional[str] = None,
        request: Optional[Request] = None
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        self.fields = fields or []
        self.suggestions = suggestions or []
        self.help_url = help_url
        self.request_id = getattr(request, 'state', {}).get('request_id', 'unknown')
        self.timestamp = datetime.utcnow().isoformat()
    
    def to_response(self) -> Dict[str, Any]:
        """Convert to JSON response."""
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
                "aria": {
                    "live": self.get_aria_live(),
                    "atomic": True,
                    "relevant": "additions text"
                },
                "fields": [
                    {
                        "id": f.id,
                        "name": f.name,
                        "message": f.message,
                        "value": f.value,
                        "aria": {
                            "describedBy": f.aria_described_by,
                            "errormessage": f.aria_errormessage,
                            "invalid": f.aria_invalid
                        },
                        "constraints": f.constraints
                    }
                    for f in self.fields
                ],
                "suggestions": self.suggestions,
                "help_url": self.help_url,
                "request_id": self.request_id,
                "timestamp": self.timestamp
            }
        }
    
    def get_aria_live(self) -> str:
        """Determine appropriate ARIA live value."""
        # Validation errors should be assertive
        if self.status_code == 400:
            return "assertive"
        # Not found can be polite
        elif self.status_code == 404:
            return "polite"
        # Auth errors should be assertive
        elif self.status_code in (401, 403):
            return "assertive"
        return "assertive"


class ValidationException(AccessibilityException):
    """Validation error with field-level details."""
    
    def __init__(self, fields: List[FieldError], **kwargs):
        super().__init__(
            code="VALIDATION_ERROR",
            message="Please check your input and try again.",
            status_code=400,
            fields=fields,
            **kwargs
        )


class AuthenticationException(AccessibilityException):
    """Authentication error."""
    
    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(
            code="UNAUTHORIZED",
            message=message,
            status_code=401,
            **kwargs
        )
```

### Exception Handler

```python
# app/core/error_handlers.py
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.exceptions import AccessibilityException
import traceback

async def accessibility_exception_handler(
    request: Request,
    exc: AccessibilityException
) -> JSONResponse:
    """Handle accessibility exceptions with structured response."""
    
    response_data = exc.to_response()
    
    # Log the error
    logger.error(
        f"Accessibility exception: {exc.code}",
        extra={
            "request_id": exc.request_id,
            "code": exc.code,
            "status_code": exc.status_code,
            "fields": [f.id for f in exc.fields],
            "path": request.url.path
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_data
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException
) -> JSONResponse:
    """Convert standard HTTP exceptions to accessibility format."""
    
    # Map to accessibility exception
    mapped = map_http_to_accessibility(exc)
    
    return await accessibility_exception_handler(request, mapped)


def map_http_to_accessibility(exc: StarletteHTTPException) -> AccessibilityException:
    """Map standard HTTP exceptions to accessibility format."""
    
    code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMITED",
        500: "INTERNAL_ERROR",
        503: "SERVICE_UNAVAILABLE"
    }
    
    return AccessibilityException(
        code=code_map.get(exc.status_code, "UNKNOWN_ERROR"),
        message=str(exc.detail),
        status_code=exc.status_code
    )


# Register handlers
def register_error_handlers(app):
    """Register all error handlers with FastAPI app."""
    
    app.add_exception_handler(
        AccessibilityException,
        accessibility_exception_handler
    )
    
    app.add_exception_handler(
        StarletteHTTPException,
        http_exception_handler
    )
    
    # Catch-all handler
    @app.exception_handler(Exception)
    async def catch_all_handler(request: Request, exc: Exception):
        """Handle unexpected exceptions."""
        
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        logger.error(
            f"Unhandled exception: {exc}",
            exc_info=True,
            extra={"request_id": request_id}
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred. Please try again later.",
                    "aria": {
                        "live": "assertive",
                        "atomic": True
                    },
                    "suggestions": [
                        {
                            "action": "retry",
                            "label": "Try again",
                            "href": str(request.url)
                        },
                        {
                            "action": "support",
                            "label": "Contact support",
                            "href": "/support"
                        }
                    ],
                    "request_id": request_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        )
```

---

## Frontend Implementation

### JavaScript Error Handler

```javascript
// static/js/error-handler.js
class AccessibilityErrorHandler {
  constructor() {
    this.errorContainer = null;
    this.focusedElement = null;
    this.setup();
  }
  
  setup() {
    // Create error container if not exists
    if (!document.getElementById('accessibility-error-container')) {
      this.createErrorContainer();
    }
    
    // Set up fetch interceptor
    this.interceptFetch();
    
    // Set up form error handling
    this.setupFormHandling();
  }
  
  createErrorContainer() {
    this.errorContainer = document.createElement('div');
    this.errorContainer.id = 'accessibility-error-container';
    this.errorContainer.setAttribute('role', 'region');
    this.errorContainer.setAttribute('aria-live', 'assertive');
    this.errorContainer.setAttribute('aria-atomic', 'true');
    this.errorContainer.className = 'accessibility-error-container';
    this.errorContainer.setAttribute('hidden', '');
    
    document.body.insertBefore(
      this.errorContainer,
      document.body.firstChild
    );
  }
  
  interceptFetch() {
    const originalFetch = window.fetch;
    
    window.fetch = async (...args) => {
      const response = await originalFetch(...args);
      
      if (!response.ok) {
        try {
          const errorData = await response.json();
          if (errorData.error) {
            this.handleErrorResponse(errorData.error);
          }
        } catch (e) {
          // Not JSON response
        }
      }
      
      return response;
    };
  }
  
  handleErrorResponse(error) {
    // Store focus for restoration
    this.focusedElement = document.activeElement;
    
    // Update error container
    this.renderError(error);
    
    // Announce to screen readers
    this.announceError(error);
    
    // Handle field-level errors
    if (error.fields && error.fields.length > 0) {
      this.applyFieldErrors(error.fields);
    }
    
    // Set focus
    this.setFocus(error);
  }
  
  renderError(error) {
    const container = document.getElementById('accessibility-error-container');
    
    container.innerHTML = `
      <div class="error-summary" role="alert">
        <h2 class="error-summary__title">
          ${this.escapeHtml(error.message)}
        </h2>
        
        ${error.details ? `
          <p class="error-summary__details">
            ${this.escapeHtml(error.details)}
          </p>
        ` : ''}
        
        ${error.fields && error.fields.length > 0 ? `
          <div class="error-summary__fields">
            <p>Please fix the following:</p>
            <ul>
              ${error.fields.map(field => `
                <li>
                  <a href="#${field.id}" class="error-link">
                    ${this.escapeHtml(field.message)}
                  </a>
                </li>
              `).join('')}
            </ul>
          </div>
        ` : ''}
        
        ${error.suggestions && error.suggestions.length > 0 ? `
          <div class="error-summary__actions">
            <p>You can also:</p>
            <ul>
              ${error.suggestions.map(suggestion => `
                <li>
                  <a href="${suggestion.href}" class="error-action">
                    ${this.escapeHtml(suggestion.label)}
                  </a>
                </li>
              `).join('')}
            </ul>
          </div>
        ` : ''}
        
        ${error.help_url ? `
          <p class="error-summary__help">
            <a href="${error.help_url}" target="_blank">
              Learn more about this error
            </a>
          </p>
        ` : ''}
        
        <p class="error-summary__request-id">
          Reference: ${error.request_id}
        </p>
      </div>
    `;
    
    container.removeAttribute('hidden');
  }
  
  applyFieldErrors(fields) {
    fields.forEach(field => {
      const element = document.getElementById(field.id);
      if (element) {
        // Apply ARIA attributes
        element.setAttribute('aria-invalid', 'true');
        if (field.aria.describedBy) {
          element.setAttribute('aria-describedby', field.aria.describedBy);
        }
        if (field.aria.errormessage) {
          element.setAttribute('aria-errormessage', field.aria.errormessage);
        }
        
        // Add error class
        element.classList.add('input--error');
        
        // Add inline error message
        this.addInlineError(field);
      }
    });
  }
  
  addInlineError(field) {
    const element = document.getElementById(field.id);
    if (!element) return;
    
    // Remove existing error
    const existing = document.getElementById(`${field.id}-error`);
    if (existing) existing.remove();
    
    // Create error message
    const errorId = `${field.id}-error`;
    const errorSpan = document.createElement('span');
    errorSpan.id = errorId;
    errorSpan.className = 'error-message';
    errorSpan.setAttribute('role', 'alert');
    errorSpan.textContent = field.message;
    
    // Insert after input
    element.parentNode.insertBefore(errorSpan, element.nextSibling);
    
    // Update aria-describedby
    const describedBy = element.getAttribute('aria-describedby') || '';
    element.setAttribute('aria-describedby', 
      describedBy ? `${describedBy} ${errorId}` : errorId
    );
  }
  
  announceError(error) {
    // Use live region for announcement
    const container = document.getElementById('accessibility-error-container');
    
    // Ensure live region behavior
    container.setAttribute('aria-live', error.aria?.live || 'assertive');
    container.setAttribute('aria-atomic', error.aria?.atomic ? 'true' : 'false');
  }
  
  setFocus(error) {
    const container = document.getElementById('accessibility-error-container');
    
    // Focus first field with error or error container
    if (error.fields && error.fields.length > 0) {
      const firstField = document.getElementById(error.fields[0].id);
      if (firstField) {
        firstField.focus();
        return;
      }
    }
    
    // Focus error summary
    const title = container.querySelector('.error-summary__title');
    if (title) {
      title.setAttribute('tabindex', '-1');
      title.focus();
    }
  }
  
  clearErrors() {
    const container = document.getElementById('accessibility-error-container');
    if (container) {
      container.setAttribute('hidden', '');
      container.innerHTML = '';
    }
    
    // Clear field errors
    document.querySelectorAll('.input--error').forEach(el => {
      el.classList.remove('input--error');
      el.removeAttribute('aria-invalid');
      
      const describedBy = el.getAttribute('aria-describedby');
      if (describedBy) {
        // Remove error references
        const ids = describedBy.split(' ').filter(id => !id.endsWith('-error'));
        if (ids.length > 0) {
          el.setAttribute('aria-describedby', ids.join(' '));
        } else {
          el.removeAttribute('aria-describedby');
        }
      }
    });
    
    // Remove inline errors
    document.querySelectorAll('.error-message').forEach(el => el.remove());
  }
  
  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  window.errorHandler = new AccessibilityErrorHandler();
});
```

---

## HTML Template Integration

```html
<!-- templates/components/error-summary.html -->
{% if errors %}
<div 
  class="error-summary"
  role="alert"
  aria-live="assertive"
  aria-atomic="true"
  tabindex="-1"
  autofocus
>
  <h2 class="error-summary__title">
    {% if errors.message %}
      {{ errors.message }}
    {% else %}
      There is a problem
    {% endif %}
  </h2>
  
  {% if errors.details %}
    <p class="error-summary__details">{{ errors.details }}</p>
  {% endif %}
  
  {% if errors.fields %}
    <div class="error-summary__list">
      <p>Please fix the following errors:</p>
      <ul>
        {% for field in errors.fields %}
          <li>
            <a 
              href="#{{ field.id }}"
              class="error-summary__link"
            >
              {{ field.message }}
            </a>
          </li>
        {% endfor %}
      </ul>
    </div>
  {% endif %}
</div>
{% endif %}

<!-- Field with error -->
<div class="form-group">
  <label for="email">
    Email address
  </label>
  
  <input 
    type="email"
    id="email"
    name="email"
    value="{{ form.email.data }}"
    class="form-control {% if errors and errors.get('email') %}input--error{% endif %}"
    aria-required="true"
    {% if errors and errors.get('email') %}
      aria-invalid="true"
      aria-describedby="email-error"
    {% endif %}
  >
  
  {% if errors and errors.get('email') %}
    <span 
      id="email-error"
      class="error-message"
      role="alert"
    >
      {{ errors.email.message }}
    </span>
  {% endif %}
</div>
```

---

## Testing

### Unit Tests

```python
# tests/unit/test_error_contract.py
import pytest
from app.core.exceptions import (
    AccessibilityException,
    FieldError,
    ValidationException
)

class TestAccessibilityException:
    def test_basic_error_response(self):
        exc = AccessibilityException(
            code="VALIDATION_ERROR",
            message="Invalid input",
            status_code=400
        )
        
        response = exc.to_response()
        
        assert response["error"]["code"] == "VALIDATION_ERROR"
        assert response["error"]["message"] == "Invalid input"
        assert response["error"]["aria"]["live"] == "assertive"
    
    def test_field_errors_included(self):
        fields = [
            FieldError(
                id="email",
                message="Invalid email format",
                aria_errormessage="email-error"
            )
        ]
        
        exc = ValidationException(fields=fields)
        response = exc.to_response()
        
        assert len(response["error"]["fields"]) == 1
        assert response["error"]["fields"][0]["id"] == "email"
        assert response["error"]["fields"][0]["aria"]["errormessage"] == "email-error"
    
    def test_aria_attributes_correct(self):
        exc = AccessibilityException(
            code="NOT_FOUND",
            message="Resource not found",
            status_code=404
        )
        
        # 404 should use polite
        assert exc.get_aria_live() == "polite"
    
    def test_suggestions_included(self):
        exc = AccessibilityException(
            code="UNAUTHORIZED",
            message="Please log in",
            suggestions=[
                {"action": "login", "label": "Log in", "href": "/login"}
            ]
        )
        
        response = exc.to_response()
        
        assert len(response["error"]["suggestions"]) == 1
        assert response["error"]["suggestions"][0]["action"] == "login"
```

### Integration Tests

```python
# tests/integration/test_error_api.py
import pytest
from fastapi.testclient import TestClient

class TestErrorContract:
    def test_validation_error_returns_accessibility_format(self, client: TestClient):
        response = client.post(
            "/api/v1/users",
            json={"email": "invalid-email"}
        )
        
        assert response.status_code == 400
        data = response.json()
        
        # Check structure
        assert "error" in data
        assert "code" in data["error"]
        assert "message" in data["error"]
        assert "aria" in data["error"]
        assert "fields" in data["error"]
        
        # Check ARIA metadata
        assert data["error"]["aria"]["live"] == "assertive"
        assert data["error"]["aria"]["atomic"] is True
    
    def test_field_errors_have_aria_attributes(self, client: TestClient):
        response = client.post(
            "/api/v1/users",
            json={"email": "invalid"}
        )
        
        data = response.json()
        fields = data["error"]["fields"]
        
        for field in fields:
            assert "id" in field
            assert "message" in field
            assert "aria" in field
            assert "invalid" in field["aria"]
```

---

## References

- [ARIA Live Regions](https://www.w3.org/WAI/ARIA/apg/patterns/alert/)
- [ARIA Error Message Pattern](https://www.w3.org/WAI/tutorials/forms/notifications/)
- [WCAG 3.3.1 Error Identification](https://www.w3.org/WAI/WCAG21/Understanding/error-identification.html)
- [WCAG 3.3.3 Error Suggestion](https://www.w3.org/WAI/WCAG21/Understanding/error-suggestion.html)

---

*Specification version 1.0 - March 6, 2026*
