"""Tenant management API routes."""

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.tenant import Subscription, Tenant
from app.schemas.tenant import (
    SubscriptionResponse,
    TenantCreate,
    TenantResponse,
    TenantUpdate,
)

router = APIRouter(prefix="/api/v1/tenants", tags=["tenants"])


@router.get("", response_model=List[TenantResponse])
async def list_tenants(db: Session = Depends(get_db)):
    """List all configured tenants."""
    tenants = db.query(Tenant).all()
    return [
        TenantResponse(
            id=t.id,
            name=t.name,
            tenant_id=t.tenant_id,
            description=t.description,
            is_active=t.is_active,
            use_lighthouse=t.use_lighthouse,
            subscription_count=len(t.subscriptions),
            created_at=t.created_at,
            updated_at=t.updated_at,
        )
        for t in tenants
    ]


@router.post("", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(tenant: TenantCreate, db: Session = Depends(get_db)):
    """Create a new tenant configuration."""
    # Check for duplicate tenant_id
    existing = db.query(Tenant).filter(Tenant.tenant_id == tenant.tenant_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tenant with Azure tenant ID {tenant.tenant_id} already exists",
        )

    db_tenant = Tenant(
        id=str(uuid.uuid4()),
        name=tenant.name,
        tenant_id=tenant.tenant_id,
        client_id=tenant.client_id,
        client_secret_ref=tenant.client_secret_ref,
        description=tenant.description,
        use_lighthouse=tenant.use_lighthouse,
    )
    db.add(db_tenant)
    db.commit()
    db.refresh(db_tenant)

    return TenantResponse(
        id=db_tenant.id,
        name=db_tenant.name,
        tenant_id=db_tenant.tenant_id,
        description=db_tenant.description,
        is_active=db_tenant.is_active,
        use_lighthouse=db_tenant.use_lighthouse,
        subscription_count=0,
        created_at=db_tenant.created_at,
        updated_at=db_tenant.updated_at,
    )


@router.get("/{id}", response_model=TenantResponse)
async def get_tenant(id: str, db: Session = Depends(get_db)):
    """Get a specific tenant."""
    tenant = db.query(Tenant).filter(Tenant.id == id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {id} not found",
        )

    return TenantResponse(
        id=tenant.id,
        name=tenant.name,
        tenant_id=tenant.tenant_id,
        description=tenant.description,
        is_active=tenant.is_active,
        use_lighthouse=tenant.use_lighthouse,
        subscription_count=len(tenant.subscriptions),
        created_at=tenant.created_at,
        updated_at=tenant.updated_at,
    )


@router.patch("/{id}", response_model=TenantResponse)
async def update_tenant(
    id: str, tenant_update: TenantUpdate, db: Session = Depends(get_db)
):
    """Update a tenant configuration."""
    tenant = db.query(Tenant).filter(Tenant.id == id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {id} not found",
        )

    update_data = tenant_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tenant, field, value)

    db.commit()
    db.refresh(tenant)

    return TenantResponse(
        id=tenant.id,
        name=tenant.name,
        tenant_id=tenant.tenant_id,
        description=tenant.description,
        is_active=tenant.is_active,
        use_lighthouse=tenant.use_lighthouse,
        subscription_count=len(tenant.subscriptions),
        created_at=tenant.created_at,
        updated_at=tenant.updated_at,
    )


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(id: str, db: Session = Depends(get_db)):
    """Delete a tenant configuration."""
    tenant = db.query(Tenant).filter(Tenant.id == id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {id} not found",
        )

    db.delete(tenant)
    db.commit()


@router.get("/{id}/subscriptions", response_model=List[SubscriptionResponse])
async def get_tenant_subscriptions(id: str, db: Session = Depends(get_db)):
    """Get subscriptions for a tenant."""
    tenant = db.query(Tenant).filter(Tenant.id == id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {id} not found",
        )

    return [
        SubscriptionResponse(
            id=s.id,
            subscription_id=s.subscription_id,
            display_name=s.display_name,
            state=s.state,
            tenant_id=tenant.id,
            synced_at=s.synced_at,
        )
        for s in tenant.subscriptions
    ]
