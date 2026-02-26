"""Tests for tenant API endpoints."""

import uuid


def test_list_tenants_empty(client):
    """Test listing tenants when none exist."""
    response = client.get("/api/v1/tenants")
    assert response.status_code == 200
    assert response.json() == []


def test_create_tenant(client):
    """Test creating a new tenant."""
    tenant_data = {
        "name": "Test Tenant",
        "tenant_id": "12345678-1234-1234-1234-123456789012",
        "description": "A test tenant",
    }
    response = client.post("/api/v1/tenants", json=tenant_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == tenant_data["name"]
    assert data["tenant_id"] == tenant_data["tenant_id"]
    assert data["is_active"] is True


def test_create_duplicate_tenant(client):
    """Test that duplicate tenant IDs are rejected."""
    tenant_data = {
        "name": "Test Tenant",
        "tenant_id": "12345678-1234-1234-1234-123456789012",
    }
    # Create first tenant
    response = client.post("/api/v1/tenants", json=tenant_data)
    assert response.status_code == 201

    # Try to create duplicate
    response = client.post("/api/v1/tenants", json=tenant_data)
    assert response.status_code == 409


def test_get_tenant_not_found(client):
    """Test getting a non-existent tenant."""
    response = client.get(f"/api/v1/tenants/{uuid.uuid4()}")
    assert response.status_code == 404


def test_update_tenant(client):
    """Test updating a tenant."""
    # Create tenant
    tenant_data = {
        "name": "Original Name",
        "tenant_id": "12345678-1234-1234-1234-123456789012",
    }
    response = client.post("/api/v1/tenants", json=tenant_data)
    tenant_id = response.json()["id"]

    # Update tenant
    update_data = {"name": "Updated Name", "is_active": False}
    response = client.patch(f"/api/v1/tenants/{tenant_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["is_active"] is False


def test_delete_tenant(client):
    """Test deleting a tenant."""
    # Create tenant
    tenant_data = {
        "name": "To Delete",
        "tenant_id": "12345678-1234-1234-1234-123456789012",
    }
    response = client.post("/api/v1/tenants", json=tenant_data)
    tenant_id = response.json()["id"]

    # Delete tenant
    response = client.delete(f"/api/v1/tenants/{tenant_id}")
    assert response.status_code == 204

    # Verify deleted
    response = client.get(f"/api/v1/tenants/{tenant_id}")
    assert response.status_code == 404
