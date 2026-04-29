"""Authentication route support services.

This module contains behavior-preserving helpers extracted from
`app.api.routes.auth` during Phase 1.5. Route handlers remain in the route module;
stateful token and tenant-mapping mechanics live here so the router stops being a
940-line trash panda.
"""

import logging
from datetime import UTC, datetime

import httpx
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.auth import (
    TokenData,
    azure_ad_validator,
    blacklist_token,
    is_token_blacklisted,
    jwt_manager,
)
from app.core.config import get_settings
from app.models.tenant import Tenant, UserTenant
from app.schemas.auth import TokenResponse

logger = logging.getLogger(__name__)


def create_token_response_with_cookies(
    token_response: TokenResponse, request: Request | None
) -> JSONResponse:
    """Create JSON response with HttpOnly Secure cookies."""
    response = JSONResponse(
        content=token_response.model_dump(exclude={"access_token", "refresh_token"})
    )

    settings = get_settings()

    # Determine if we should use Secure flag (always in production)
    secure = settings.environment == "production"

    # Set access token as HttpOnly cookie
    if token_response.access_token:
        response.set_cookie(
            key="access_token",
            value=token_response.access_token,
            httponly=True,
            secure=secure,
            samesite="lax",
            max_age=token_response.expires_in,
            path="/",
        )

    # Set refresh token as HttpOnly cookie (longer lived)
    if token_response.refresh_token:
        response.set_cookie(
            key="refresh_token",
            value=token_response.refresh_token,
            httponly=True,
            secure=secure,
            samesite="lax",
            max_age=settings.jwt_refresh_token_expire_days * 24 * 3600,
            path="/",
        )

    return response


async def handle_refresh_token(
    refresh_token: str | None,
    db: Session,
    request: Request,
) -> TokenResponse:
    """Handle refresh token grant."""
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token required",
        )

    # Check if refresh token has been revoked (e.g., already rotated)
    if is_token_blacklisted(refresh_token):
        logger.warning("Attempted use of blacklisted refresh token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Validate refresh token
        payload = jwt_manager.decode_token(refresh_token)

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        # Get user info from database
        user_tenant_mappings = (
            db.query(UserTenant)
            .filter(UserTenant.user_id == user_id, UserTenant.is_active == True)  # noqa: E712
            .all()
        )

        tenant_ids = [m.tenant.tenant_id for m in user_tenant_mappings if m.tenant]
        roles = list({m.role for m in user_tenant_mappings}) or ["admin"]  # dev user gets admin

        # Generate new tokens
        settings = get_settings()
        new_access_token = jwt_manager.create_access_token(
            user_id=user_id,
            roles=roles,
            tenant_ids=tenant_ids,
        )
        new_refresh_token = jwt_manager.create_refresh_token(user_id=user_id)

        # Blacklist the old refresh token (rotation = one-time use)
        blacklist_token(refresh_token)

        logger.info("Token refreshed for user: %s", user_id)

        token_response = TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.jwt_access_token_expire_minutes * 60,
        )

        return create_token_response_with_cookies(token_response, request)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Token refresh failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        ) from e


async def handle_authorization_code(
    code: str | None,
    redirect_uri: str | None,
    client_id: str | None,
    client_secret: str | None,
    request: Request | None = None,
) -> TokenResponse:
    """Handle authorization code grant with Azure AD."""
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code required",
        )

    settings = get_settings()

    # ── Validate redirect URI against whitelist ─────────────────
    effective_redirect = redirect_uri or "http://localhost:8000/auth/callback"
    if effective_redirect not in settings.allowed_redirect_uris:
        logger.warning(
            "Rejected authorization_code grant with unauthorized redirect_uri: %s",
            effective_redirect[:100],
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid redirect URI",
        )

    # Exchange code for tokens with Azure AD
    token_endpoint = settings.azure_ad_token_endpoint

    async with httpx.AsyncClient() as client:
        token_request = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri or "http://localhost:8000/auth/callback",
            "client_id": client_id or settings.azure_ad_client_id,
        }

        if client_secret:
            token_request["client_secret"] = client_secret

        response = await client.post(
            token_endpoint,
            data=token_request,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if response.status_code != 200:
            logger.error("Azure AD token exchange failed: %s", response.text)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to exchange authorization code",
            )

        token_data = response.json()

        # Validate the ID token and create our own tokens
        id_token = token_data.get("id_token")
        if id_token:
            validated = await azure_ad_validator.validate_token(id_token)

            # Create internal tokens
            access_token = jwt_manager.create_access_token(
                user_id=validated.sub,
                email=validated.email,
                name=validated.name,
                roles=validated.roles,
                tenant_ids=validated.tenant_ids,
            )

            refresh_token = jwt_manager.create_refresh_token(user_id=validated.sub)

            token_response = TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                expires_in=settings.jwt_access_token_expire_minutes * 60,
            )

            return create_token_response_with_cookies(token_response, request)

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Failed to process authorization code",
    )


async def sync_user_tenant_mappings(db: Session, token_data: TokenData) -> list[str]:
    """Sync user tenant mappings based on Azure AD token claims.

    Creates UserTenant records for any tenants the user has access to via Azure
    AD group memberships. Falls back to the Azure AD 'tid' claim when no
    group-based tenant IDs are found.
    """
    import uuid

    # Start with group-based tenant IDs; fall back to tid claim
    candidate_ids = list(token_data.tenant_ids)
    if not candidate_ids and token_data.azure_tenant_id:
        candidate_ids = [token_data.azure_tenant_id]
        logger.info(
            "No group-based tenants for %s, falling back to Azure AD tid: %s",
            token_data.sub,
            token_data.azure_tenant_id,
        )

    resolved: list[str] = []

    for tenant_id in candidate_ids:
        try:
            # Find tenant by Azure tenant ID
            tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
            if not tenant:
                logger.debug("No local tenant record for Azure tenant %s, skipping", tenant_id)
                continue

            resolved.append(tenant_id)

            # Ensure a UserTenant mapping exists
            existing = (
                db.query(UserTenant)
                .filter(
                    UserTenant.user_id == token_data.sub,
                    UserTenant.tenant_id == tenant.id,
                )
                .first()
            )

            if not existing:
                mapping = UserTenant(
                    id=str(uuid.uuid4()),
                    user_id=token_data.sub,
                    tenant_id=tenant.id,
                    role="viewer",  # Default role
                    is_active=True,
                    can_view_costs=True,
                    granted_by="azure_ad_sync",
                    granted_at=datetime.now(UTC),
                )
                db.add(mapping)
                db.commit()

                logger.info("Created user tenant mapping: %s -> %s", token_data.sub, tenant_id)
        except OperationalError as e:
            logger.error("Database connection error syncing tenant %s: %s", tenant_id, e)
            db.rollback()
            continue
        except SQLAlchemyError as e:
            logger.error("Database error syncing tenant mapping for %s: %s", tenant_id, e)
            db.rollback()
            continue
        except Exception as e:
            logger.error(
                "Failed to sync tenant mapping for %s: %s: %s",
                tenant_id,
                type(e).__name__,
                e,
            )
            db.rollback()
            continue

    return resolved
