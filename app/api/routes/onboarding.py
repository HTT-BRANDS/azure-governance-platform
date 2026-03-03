"""Onboarding API routes for tenant management.

This module provides endpoints for onboarding new tenants via Azure Lighthouse,
including ARM template generation, delegation verification, and tenant creation.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.rate_limit import rate_limit
from app.models.tenant import Tenant
from app.services.lighthouse_client import LighthouseAzureClient, LighthouseDelegationError

router = APIRouter(
    prefix="/onboarding",
    tags=["onboarding"],
)


async def get_lighthouse_client():
    """Get Lighthouse Azure client instance."""
    return LighthouseAzureClient()


@router.get("/")
async def onboarding_landing_page(request: Request):
    """Render the onboarding landing page with HTMX.
    
    Returns HTML with onboarding form and instructions.
    """
    # For now, return a simple HTML response
    # In production, this would use Jinja2 templates
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Azure Governance Platform - Onboarding</title>
        <script src="https://unpkg.com/htmx.org@1.9.12"></script>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            h1 { color: #0078d4; }
            .form-group { margin: 20px 0; }
            label { display: block; margin-bottom: 5px; }
            input, button { padding: 10px; margin: 5px 0; }
            button { background: #0078d4; color: white; border: none; cursor: pointer; }
            button:hover { background: #005a9e; }
            .result { margin-top: 20px; padding: 15px; border: 1px solid #ddd; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Azure Governance Platform</h1>
            <h2>Tenant Onboarding</h2>
            <p>Welcome! This page helps you onboard your Azure tenant to the 
               Azure Governance Platform using Azure Lighthouse delegation.</p>
            
            <form hx-post="/onboarding/generate-template" 
                  hx-target="#template-result"
                  hx-swap="innerHTML">
                <div class="form-group">
                    <button type="submit">Generate Lighthouse ARM Template</button>
                </div>
            </form>
            
            <div id="template-result" class="result"></div>
        </div>
    </body>
    </html>
    """
    return html_content


@router.post("/generate-template")
async def generate_template(settings: Settings = Depends(get_settings)):
    """Generate Azure Lighthouse ARM template for tenant onboarding.
    
    Returns a JSON ARM template that customers can deploy to delegate
    access to their subscription.
    """
    # Get MSP tenant ID from settings
    msp_tenant_id = settings.azure_tenant_id or "YOUR-TENANT-ID"
    
    # Generate the ARM template
    template = {
        "$schema": "https://schema.management.azure.com/schemas/2019-08-01/subscriptionDeploymentTemplate.json#",
        "contentVersion": "1.0.0.0",
        "parameters": {
            "mspOfferName": {
                "type": "string",
                "defaultValue": "Azure Governance Platform"
            },
            "mspOfferDescription": {
                "type": "string",
                "defaultValue": "Multi-tenant governance and compliance management"
            },
            "managedByTenantId": {
                "type": "string",
                "defaultValue": msp_tenant_id
            },
            "authorizations": {
                "type": "array",
                "defaultValue": [
                    {
                        "principalId": settings.azure_managed_identity_object_id or "MANAGED-IDENTITY-ID",
                        "principalIdDisplayName": "Governance Platform",
                        "roleDefinitionId": "b24988ac-6180-42a0-ab88-20f7382dd24c",
                        "roleDisplayName": "Contributor"
                    },
                    {
                        "principalId": settings.azure_managed_identity_object_id or "MANAGED-IDENTITY-ID",
                        "principalIdDisplayName": "Governance Platform - Cost Management",
                        "roleDefinitionId": "72fafb9e-0641-4937-9268-a91bfd8191a3",
                        "roleDisplayName": "Cost Management Reader"
                    },
                    {
                        "principalId": settings.azure_managed_identity_object_id or "MANAGED-IDENTITY-ID",
                        "principalIdDisplayName": "Governance Platform - Security",
                        "roleDefinitionId": "39bc4728-0917-49c7-9d2c-d95423bc2eb4",
                        "roleDisplayName": "Security Reader"
                    }
                ]
            }
        },
        "resources": [
            {
                "type": "Microsoft.ManagedServices/registrationDefinitions",
                "apiVersion": "2022-10-01",
                "name": "[guid(parameters('mspOfferName'))]",
                "properties": {
                    "registrationDefinitionName": "[parameters('mspOfferName')]",
                    "description": "[parameters('mspOfferDescription')]",
                    "managedByTenantId": "[parameters('managedByTenantId')]",
                    "authorizations": "[parameters('authorizations')]"
                }
            },
            {
                "type": "Microsoft.ManagedServices/registrationAssignments",
                "apiVersion": "2022-10-01",
                "name": "[guid(parameters('mspOfferName'))]",
                "dependsOn": [
                    "[resourceId('Microsoft.ManagedServices/registrationDefinitions', guid(parameters('mspOfferName')))]"
                ],
                "properties": {
                    "registrationDefinitionId": "[resourceId('Microsoft.ManagedServices/registrationDefinitions', guid(parameters('mspOfferName')))]"
                }
            }
        ]
    }
    
    return template


@router.post("/verify")
async def verify_onboarding(
    request_data: dict,
    db: Session = Depends(get_db),
    lighthouse_client: LighthouseAzureClient = Depends(get_lighthouse_client)
):
    """Verify tenant onboarding and create tenant record.
    
    Args:
        request_data: Tenant information including tenant_id, subscription_id
        db: Database session
        lighthouse_client: Lighthouse client instance
        
    Returns:
        Tenant creation result
    """
    # Extract required fields
    tenant_id = request_data.get("tenant_id")
    tenant_name = request_data.get("tenant_name")
    subscription_id = request_data.get("subscription_id")
    
    if not all([tenant_id, tenant_name, subscription_id]):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Missing required fields: tenant_id, tenant_name, subscription_id"
        )
    
    # Verify delegation
    try:
        verification = await lighthouse_client.verify_delegation(subscription_id)
        
        if not verification.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Delegation verification failed: {verification.get('error')}"
            )
        
        if not verification.get("is_delegated"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subscription is not delegated via Lighthouse"
            )
        
        # Check for existing tenant
        existing = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Tenant {tenant_id} already exists"
            )
        
        # Create tenant record
        db_tenant = Tenant(
            id=str(uuid4()),
            name=tenant_name,
            tenant_id=tenant_id,
            description=request_data.get("description", ""),
            use_lighthouse=True,
            is_active=True
        )
        db.add(db_tenant)
        db.commit()
        db.refresh(db_tenant)
        
        # Trigger initial sync (async)
        from app.core.sync.tenant_sync import sync_tenant_data
        await sync_tenant_data(db_tenant.id)
        
        return {
            "success": True,
            "id": db_tenant.id,
            "tenant_id": db_tenant.tenant_id,
            "name": db_tenant.name,
            "is_active": db_tenant.is_active,
            "message": "Tenant successfully onboarded"
        }
        
    except LighthouseDelegationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/status/{tenant_id}")
async def get_onboarding_status(
    tenant_id: str,
    db: Session = Depends(get_db)
):
    """Get onboarding status for a tenant.
    
    Args:
        tenant_id: The tenant UUID
        db: Database session
        
    Returns:
        Tenant onboarding status
    """
    from app.core.validation import validate_uuid_param
    
    # Validate UUID format
    try:
        validate_uuid_param(tenant_id)
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid tenant ID format"
        )
    
    # Get tenant
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )
    
    # Determine delegation status
    delegation_status = "active" if tenant.is_active else "pending"
    if hasattr(tenant, 'delegation_status') and tenant.delegation_status:
        delegation_status = tenant.delegation_status
    
    # Get subscription count
    subscription_count = len(tenant.subscriptions) if hasattr(tenant, 'subscriptions') else 0
    
    # Check if action is required
    requires_action = (
        not tenant.is_active or
        delegation_status == "pending" or
        subscription_count == 0
    )
    
    result = {
        "id": tenant.id,
        "name": tenant.name,
        "tenant_id": tenant.tenant_id,
        "is_active": tenant.is_active,
        "use_lighthouse": tenant.use_lighthouse,
        "subscription_count": subscription_count,
        "delegation_status": delegation_status,
        "created_at": tenant.created_at.isoformat() if tenant.created_at else None,
        "updated_at": tenant.updated_at.isoformat() if tenant.updated_at else None,
        "requires_action": requires_action
    }
    
    # Add optional fields if present
    if hasattr(tenant, 'last_synced_at') and tenant.last_synced_at:
        result["last_synced_at"] = tenant.last_synced_at.isoformat()
    
    if hasattr(tenant, 'delegation_error') and tenant.delegation_error:
        result["delegation_error"] = tenant.delegation_error
    
    return result


async def sync_tenant_data(tenant_id: str):
    """Trigger async data sync for a tenant.
    
    Args:
        tenant_id: The tenant ID to sync.
    """
    from app.core.scheduler import get_scheduler
    
    scheduler = get_scheduler()
    if scheduler:
        # Queue sync job
        scheduler.add_job(
            func=lambda: None,  # Would call actual sync function
            trigger='date',
            id=f'sync-tenant-{tenant_id}',
            replace_existing=True
        )
