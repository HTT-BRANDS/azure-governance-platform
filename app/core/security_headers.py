"""Enhanced Security Headers Middleware.

Provides comprehensive security headers including:
- Content-Security-Policy with nonce support
- Permissions-Policy (feature policy)
- Cross-Origin-Resource-Policy
- Cross-Origin-Opener-Policy
- Cross-Origin-Embedder-Policy
- Document-Policy
- Strict-Transport-Security (HSTS)
- X-Frame-Options, X-Content-Type-Options, X-XSS-Protection
- Referrer-Policy

SECURITY: These headers protect against:
- Clickjacking (X-Frame-Options, CSP frame-ancestors)
- XSS attacks (CSP, X-XSS-Protection)
- MIME sniffing (X-Content-Type-Options)
- Information leakage (Referrer-Policy)
- Spectre attacks (Cross-Origin-Opener-Policy, Cross-Origin-Embedder-Policy)
- Feature abuse (Permissions-Policy)
- Resource hijacking (Cross-Origin-Resource-Policy)
"""

import logging
import secrets
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Security header constants
DEFAULT_PERMISSIONS_POLICY = (
    "accelerometer=(), "
    "autoplay=(), "
    "camera=(), "
    "display-capture=(), "
    "encrypted-media=(), "
    "fullscreen=(self), "
    "geolocation=(), "
    "gyroscope=(), "
    "magnetometer=(), "
    "microphone=(), "
    "midi=(), "
    "payment=(), "
    "picture-in-picture=(), "
    "publickey-credentials-get=(), "
    "screen-wake-lock=(), "
    "sync-xhr=(), "
    "usb=(), "
    "web-share=(), "
    "xr-spatial-tracking=()"
)

DEFAULT_CSP_DIRECTIVES = {
    "default-src": "'self'",
    "script-src": "'self' 'nonce-{nonce}' https://unpkg.com https://cdn.jsdelivr.net",
    "style-src": "'self' 'unsafe-inline' https://fonts.googleapis.com",
    "font-src": "'self' https://fonts.gstatic.com",
    "img-src": "'self' data: blob:",
    "connect-src": "'self' https://cdn.jsdelivr.net",
    "media-src": "'self'",
    "object-src": "'none'",
    "frame-src": "'none'",
    "frame-ancestors": "'none'",
    "form-action": "'self'",
    "base-uri": "'self'",
    "upgrade-insecure-requests": "",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Comprehensive security headers middleware.

    Adds security headers to all responses with configurable policies.
    Generates CSP nonces per-request for script integrity.
    """

    def __init__(
        self,
        app,
        permissions_policy: str | None = None,
        corp_policy: str = "same-origin",
        coop_policy: str = "same-origin-allow-popups",
        coep_policy: str = "require-corp",
        document_policy: str = "force-load-at-top",
        referrer_policy: str = "strict-origin-when-cross-origin",
        csp_directives: dict[str, str] | None = None,
        hsts_max_age: int = 31536000,
        hsts_include_subdomains: bool = True,
        hsts_preload: bool = False,
        skip_paths: tuple[str, ...] = ("/metrics",),
    ):
        """Initialize security headers middleware.

        Args:
            app: The ASGI application
            permissions_policy: Feature Policy string (default: restrictive)
            corp_policy: Cross-Origin-Resource-Policy (default: same-origin)
            coop_policy: Cross-Origin-Opener-Policy (default: same-origin-allow-popups)
            coep_policy: Cross-Origin-Embedder-Policy (default: require-corp)
            document_policy: Document-Policy header (default: force-load-at-top)
            referrer_policy: Referrer-Policy (default: strict-origin-when-cross-origin)
            csp_directives: Override default CSP directives
            hsts_max_age: HSTS max-age in seconds (default: 1 year)
            hsts_include_subdomains: Include subdomains in HSTS (default: True)
            hsts_preload: Request HSTS preload (default: False)
            skip_paths: Paths to skip header injection (e.g., health checks)
        """
        super().__init__(app)
        self.permissions_policy = permissions_policy or DEFAULT_PERMISSIONS_POLICY
        self.corp_policy = corp_policy
        self.coop_policy = coop_policy
        self.coep_policy = coep_policy
        self.document_policy = document_policy
        self.referrer_policy = referrer_policy
        self.csp_directives = csp_directives or DEFAULT_CSP_DIRECTIVES
        self.hsts_max_age = hsts_max_age
        self.hsts_include_subdomains = hsts_include_subdomains
        self.hsts_preload = hsts_preload
        self.skip_paths = skip_paths
        self.settings = get_settings()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and add security headers to response."""
        # Generate CSP nonce for this request
        nonce = secrets.token_urlsafe(32)
        request.state.csp_nonce = nonce

        response = await call_next(request)

        # Skip headers for certain paths (health checks, metrics)
        if request.url.path in self.skip_paths:
            return response

        # Add security headers
        self._add_security_headers(response, nonce)

        return response

    def _add_security_headers(self, response: Response, nonce: str) -> None:
        """Add all security headers to response."""
        # X-Frame-Options: Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # X-Content-Type-Options: Prevent MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # X-XSS-Protection: Legacy XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer-Policy: Control referrer information
        response.headers["Referrer-Policy"] = self.referrer_policy

        # Permissions-Policy: Restrict browser features (formerly Feature-Policy)
        response.headers["Permissions-Policy"] = self.permissions_policy

        # Cross-Origin-Resource-Policy: Control resource sharing
        response.headers["Cross-Origin-Resource-Policy"] = self.corp_policy

        # Cross-Origin-Opener-Policy: Isolate window references
        response.headers["Cross-Origin-Opener-Policy"] = self.coop_policy

        # Cross-Origin-Embedder-Policy: Control cross-origin embedding
        response.headers["Cross-Origin-Embedder-Policy"] = self.coep_policy

        # Document-Policy: Control document behavior
        response.headers["Document-Policy"] = self.document_policy

        # Content-Security-Policy: Comprehensive content restrictions
        csp = self._build_csp(nonce)
        response.headers["Content-Security-Policy"] = csp

        # HSTS: HTTPS enforcement (production only)
        if not self.settings.is_development:
            hsts_value = f"max-age={self.hsts_max_age}"
            if self.hsts_include_subdomains:
                hsts_value += "; includeSubDomains"
            if self.hsts_preload:
                hsts_value += "; preload"
            response.headers["Strict-Transport-Security"] = hsts_value

        # Server header minimization (remove version info)
        response.headers["Server"] = "Azure-Governance-Platform"

    def _build_csp(self, nonce: str) -> str:
        """Build Content-Security-Policy header value."""
        directives = []
        for directive, value in self.csp_directives.items():
            # Replace nonce placeholder
            if "{nonce}" in value:
                value = value.format(nonce=nonce)
            # Handle directives without values
            if value:
                directives.append(f"{directive} {value}")
            else:
                directives.append(directive)
        return "; ".join(directives)


class SecurityHeadersConfig:
    """Configuration for security headers.

    Provides preset configurations for different security levels.
    """

    @staticmethod
    def strict() -> dict:
        """Most restrictive security configuration.

        Use for high-security environments where minimal external
        resources are needed.
        """
        return {
            "permissions_policy": (
                "accelerometer=(), "
                "autoplay=(), "
                "camera=(), "
                "display-capture=(), "
                "encrypted-media=(), "
                "fullscreen=(), "
                "geolocation=(), "
                "gyroscope=(), "
                "magnetometer=(), "
                "microphone=(), "
                "midi=(), "
                "payment=(), "
                "picture-in-picture=(), "
                "publickey-credentials-get=(), "
                "screen-wake-lock=(), "
                "sync-xhr=(), "
                "usb=(), "
                "web-share=(), "
                "xr-spatial-tracking=()"
            ),
            "corp_policy": "same-origin",
            "coop_policy": "same-origin",
            "coep_policy": "require-corp",
            "document_policy": "force-load-at-top",
            "csp_directives": {
                "default-src": "'self'",
                "script-src": "'self' 'nonce-{nonce}'",
                "style-src": "'self'",
                "font-src": "'self'",
                "img-src": "'self' data:",
                "connect-src": "'self'",
                "media-src": "'none'",
                "object-src": "'none'",
                "frame-src": "'none'",
                "frame-ancestors": "'none'",
                "form-action": "'self'",
                "base-uri": "'self'",
                "upgrade-insecure-requests": "",
            },
        }

    @staticmethod
    def balanced() -> dict:
        """Balanced security configuration.

        Default configuration with reasonable security while
        allowing CDN resources and necessary functionality.
        """
        return {
            "permissions_policy": DEFAULT_PERMISSIONS_POLICY,
            "corp_policy": "same-origin",
            "coop_policy": "same-origin-allow-popups",
            "coep_policy": "require-corp",
            "document_policy": "force-load-at-top",
            "csp_directives": DEFAULT_CSP_DIRECTIVES,
        }

    @staticmethod
    def relaxed() -> dict:
        """Relaxed security configuration for development.

        Allows more external resources and features for easier
        local development. NOT for production use.
        """
        return {
            "permissions_policy": (
                "accelerometer=(), "
                "camera=(), "
                "geolocation=(), "
                "gyroscope=(), "
                "magnetometer=(), "
                "microphone=(), "
                "payment=()"
            ),
            "corp_policy": "cross-origin",
            "coop_policy": "unsafe-none",
            "coep_policy": "unsafe-none",
            "document_policy": "",
            "csp_directives": {
                "default-src": "'self'",
                "script-src": "'self' 'nonce-{nonce}' 'unsafe-eval' https: http:",
                "style-src": "'self' 'unsafe-inline' https: http:",
                "font-src": "'self' https: http:",
                "img-src": "'self' data: https: http:",
                "connect-src": "'self' https: http:",
                "frame-ancestors": "'none'",
            },
        }


def create_security_middleware(security_level: str = "balanced") -> type[BaseHTTPMiddleware]:
    """Create security headers middleware with specified configuration.

    Args:
        security_level: One of "strict", "balanced", "relaxed"

    Returns:
        Configured SecurityHeadersMiddleware class
    """
    config_map = {
        "strict": SecurityHeadersConfig.strict(),
        "balanced": SecurityHeadersConfig.balanced(),
        "relaxed": SecurityHeadersConfig.relaxed(),
    }

    config = config_map.get(security_level, SecurityHeadersConfig.balanced())

    def factory(app):
        return SecurityHeadersMiddleware(app, **config)

    return factory


# Convenience middleware classes for direct use
class StrictSecurityHeadersMiddleware(SecurityHeadersMiddleware):
    """Strict security headers configuration."""

    def __init__(self, app):
        super().__init__(app, **SecurityHeadersConfig.strict())


class BalancedSecurityHeadersMiddleware(SecurityHeadersMiddleware):
    """Balanced security headers configuration (default)."""

    def __init__(self, app):
        super().__init__(app, **SecurityHeadersConfig.balanced())


class RelaxedSecurityHeadersMiddleware(SecurityHeadersMiddleware):
    """Relaxed security headers configuration (development only)."""

    def __init__(self, app):
        super().__init__(app, **SecurityHeadersConfig.relaxed())
