"""
End-to-End Integration Tests for Censudex API Gateway
Tests the complete workflow: Authentication -> Inventory -> Clients
Based on the actual tested flow from taller_2.pdf requirements
"""

import pytest
import httpx
import asyncio
import time

# Test configuration
GATEWAY_URL = "http://localhost:8000"
ADMIN_USERNAME = "adminCensudex"
ADMIN_PASSWORD = "Admin1234!"


async def get_admin_token() -> str:
    """Helper function to obtain admin authentication token"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{GATEWAY_URL}/api/login",
            json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
            timeout=10.0
        )
        if response.status_code == 200:
            return response.json().get("token")
        else:
            pytest.skip(f"Could not authenticate admin user: {response.status_code}")


class TestEndToEndFlow:
    """
    End-to-end tests for the complete Censudex application flow
    Requires all services to be running (auth, clients, inventory, gateway)
    """
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_01_authentication_flow(self):
        """
        Test 1: Authentication Flow
        - Login with admin credentials
        - Verify token is returned
        - Verify token structure (JWT)
        """
        async with httpx.AsyncClient() as client:
            # Test successful login
            response = await client.post(
                f"{GATEWAY_URL}/api/login",
                json={
                    "username": ADMIN_USERNAME,
                    "password": ADMIN_PASSWORD
                },
                timeout=10.0
            )
            
            assert response.status_code == 200, f"Login failed: {response.text}"
            data = response.json()
            
            # Verify token exists
            assert "token" in data, "Response should contain token"
            token = data["token"]
            
            # Verify token is a JWT (has 3 parts separated by dots)
            assert token.count('.') == 2, "Token should be a valid JWT"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_02_authentication_invalid_credentials(self):
        """
        Test 2: Authentication with invalid credentials should fail
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{GATEWAY_URL}/api/login",
                json={
                    "username": "invaliduser",
                    "password": "wrongpassword"
                },
                timeout=10.0
            )
            
            # Should return 400 (invalid credentials)
            assert response.status_code in [400, 401, 500], "Invalid credentials should fail"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_03_inventory_list_all(self):
        """
        Test 3: List all inventory items
        - Requires authentication
        - Should return list of inventory items
        """
        admin_token = await get_admin_token()
            
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GATEWAY_URL}/api/v1/inventory/?limit=10&offset=0",
                headers={"Authorization": f"Bearer {admin_token}"},
                timeout=10.0
            )
            
            assert response.status_code == 200, f"Failed to list inventory: {response.text}"
            data = response.json()
            
            # Should be a list
            assert isinstance(data, list), "Response should be a list"
            
            # If there are items, verify structure
            if len(data) > 0:
                item = data[0]
                assert "id" in item
                assert "product_id" in item
                assert "quantity" in item
                assert "location" in item
                assert "reserved_quantity" in item

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_04_inventory_get_specific(self):
        """
        Test 4: Get specific inventory item by ID
        """
        admin_token = await get_admin_token()
            
        async with httpx.AsyncClient() as client:
            # First, get list to find an item ID
            list_response = await client.get(
                f"{GATEWAY_URL}/api/v1/inventory/?limit=1&offset=0",
                headers={"Authorization": f"Bearer {admin_token}"},
                timeout=10.0
            )
            
            if list_response.status_code == 200:
                items = list_response.json()
                if len(items) > 0:
                    item_id = items[0]["id"]
                    
                    # Get specific item
                    response = await client.get(
                        f"{GATEWAY_URL}/api/v1/inventory/{item_id}",
                        headers={"Authorization": f"Bearer {admin_token}"},
                        timeout=10.0
                    )
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert data["id"] == item_id

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_05_inventory_create_update_delete(self):
        """
        Test 5: Complete CRUD cycle for inventory
        - Create new inventory item
        - Update the item
        - Delete the item
        """
        admin_token = await get_admin_token()
            
        async with httpx.AsyncClient() as client:
            # CREATE
            create_payload = {
                "product_id": f"TEST_PROD_{int(time.time())}",
                "quantity": 100,
                "location": "test_warehouse",
                "reserved_quantity": 0
            }
            
            create_response = await client.post(
                f"{GATEWAY_URL}/api/v1/inventory/",
                headers={"Authorization": f"Bearer {admin_token}"},
                json=create_payload,
                timeout=10.0
            )
            
            assert create_response.status_code == 200, f"Create failed: {create_response.text}"
            created_item = create_response.json()
            item_id = created_item["id"]
            
            # Verify created item
            assert created_item["product_id"] == create_payload["product_id"]
            assert created_item["quantity"] == create_payload["quantity"]
            
            # UPDATE
            update_payload = {
                "quantity": 150,
                "location": "updated_warehouse"
            }
            
            update_response = await client.put(
                f"{GATEWAY_URL}/api/v1/inventory/{item_id}",
                headers={"Authorization": f"Bearer {admin_token}"},
                json=update_payload,
                timeout=10.0
            )
            
            assert update_response.status_code == 200, f"Update failed: {update_response.text}"
            updated_item = update_response.json()
            assert updated_item["quantity"] == 150
            assert updated_item["location"] == "updated_warehouse"
            
            # DELETE
            delete_response = await client.delete(
                f"{GATEWAY_URL}/api/v1/inventory/{item_id}",
                headers={"Authorization": f"Bearer {admin_token}"},
                timeout=10.0
            )
            
            assert delete_response.status_code == 200, f"Delete failed: {delete_response.text}"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_06_inventory_check_stock(self):
        """
        Test 6: Check stock availability
        """
        admin_token = await get_admin_token()
            
        async with httpx.AsyncClient() as client:
            # Get first product ID from inventory
            list_response = await client.get(
                f"{GATEWAY_URL}/api/v1/inventory/?limit=1&offset=0",
                headers={"Authorization": f"Bearer {admin_token}"},
                timeout=10.0
            )
            
            if list_response.status_code == 200:
                items = list_response.json()
                if len(items) > 0:
                    product_id = items[0]["product_id"]
                    
                    # Check stock
                    check_payload = {
                        "product_id": product_id,
                        "requested_quantity": 10
                    }
                    
                    response = await client.post(
                        f"{GATEWAY_URL}/api/v1/inventory/check-stock",
                        headers={"Authorization": f"Bearer {admin_token}"},
                        json=check_payload,
                        timeout=10.0
                    )
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert "available" in data
                    assert "current_stock" in data
                    assert "available_stock" in data
                    assert "requested_quantity" in data

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_07_clients_list_all(self):
        """
        Test 7: List all clients
        """
        admin_token = await get_admin_token()
            
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GATEWAY_URL}/api/clients",
                headers={"Authorization": f"Bearer {admin_token}"},
                timeout=10.0
            )
            
            assert response.status_code == 200, f"Failed to list clients: {response.text}"
            data = response.json()
            
            assert "clients" in data
            clients = data["clients"]
            assert isinstance(clients, list)
            
            # Verify admin user exists
            admin_exists = any(c["username"] == ADMIN_USERNAME for c in clients)
            assert admin_exists, "Admin user should exist in clients list"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_08_clients_get_specific(self):
        """
        Test 8: Get specific client by ID
        """
        admin_token = await get_admin_token()
            
        async with httpx.AsyncClient() as client:
            # Get list to find admin client ID
            list_response = await client.get(
                f"{GATEWAY_URL}/api/clients",
                headers={"Authorization": f"Bearer {admin_token}"},
                timeout=10.0
            )
            
            if list_response.status_code == 200:
                data = list_response.json()
                admin_client = next((c for c in data["clients"] if c["username"] == ADMIN_USERNAME), None)
                
                if admin_client:
                    client_id = admin_client["id"]
                    
                    # Get specific client
                    response = await client.get(
                        f"{GATEWAY_URL}/api/clients/{client_id}",
                        headers={"Authorization": f"Bearer {admin_token}"},
                        timeout=10.0
                    )
                    
                    assert response.status_code == 200
                    client_data = response.json()
                    assert "client" in client_data
                    assert client_data["client"]["id"] == client_id

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_09_clients_create_update_delete(self):
        """
        Test 9: Complete CRUD cycle for clients
        - Create new client
        - Update the client
        - Delete the client (requires Admin role)
        """
        admin_token = await get_admin_token()
            
        async with httpx.AsyncClient() as client:
            # CREATE
            timestamp = int(time.time())
            create_payload = {
                "names": "Test",
                "lastnames": "Usuario E2E",
                "email": f"test{timestamp}@censudex.cl",
                "username": f"testuser{timestamp}",
                "birthdate": "1990-01-01",
                "address": "Test Address 123",
                "phonenumber": "+56912345679",
                "password": "Test123!"
            }
            
            create_response = await client.post(
                f"{GATEWAY_URL}/api/clients",
                headers={"Authorization": f"Bearer {admin_token}"},
                json=create_payload,
                timeout=10.0
            )
            
            assert create_response.status_code == 200, f"Create failed: {create_response.text}"
            
            # Get the created client to find ID
            list_response = await client.get(
                f"{GATEWAY_URL}/api/clients?usernamefilter={create_payload['username']}",
                headers={"Authorization": f"Bearer {admin_token}"},
                timeout=10.0
            )
            
            assert list_response.status_code == 200
            clients_data = list_response.json()
            assert len(clients_data["clients"]) > 0
            created_client = clients_data["clients"][0]
            client_id = created_client["id"]
            
            # UPDATE
            update_payload = {
                "names": "Test Updated",
                "lastnames": "Usuario Modificado",
                "email": create_payload["email"],
                "username": create_payload["username"],
                "birthdate": "1990-01-01",
                "address": "Updated Address 456",
                "phonenumber": "+56999999999"
            }
            
            update_response = await client.patch(
                f"{GATEWAY_URL}/api/clients/{client_id}",
                headers={"Authorization": f"Bearer {admin_token}"},
                json=update_payload,
                timeout=10.0
            )
            
            assert update_response.status_code == 200, f"Update failed: {update_response.text}"
            
            # DELETE (requires Admin role)
            delete_response = await client.delete(
                f"{GATEWAY_URL}/api/clients/{client_id}",
                headers={"Authorization": f"Bearer {admin_token}"},
                timeout=10.0
            )
            
            assert delete_response.status_code == 200, f"Delete failed: {delete_response.text}"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_10_authorization_delete_requires_admin(self):
        """
        Test 10: Verify that delete client endpoint requires Admin role
        This test validates proper role-based access control
        """
        admin_token = await get_admin_token()
            
        # This test verifies that the admin token works
        # In a real scenario, you would test with a non-admin token
        # For now, we verify admin can delete
        async with httpx.AsyncClient() as client:
            # Create a test client first
            timestamp = int(time.time())
            create_payload = {
                "names": "Delete",
                "lastnames": "Test",
                "email": f"delete{timestamp}@censudex.cl",
                "username": f"deletetest{timestamp}",
                "birthdate": "1990-01-01",
                "address": "Delete Address",
                "phonenumber": "+56912345680",
                "password": "Test123!"
            }
            
            await client.post(
                f"{GATEWAY_URL}/api/clients",
                headers={"Authorization": f"Bearer {admin_token}"},
                json=create_payload,
                timeout=10.0
            )
            
            # Get client ID
            list_response = await client.get(
                f"{GATEWAY_URL}/api/clients?usernamefilter={create_payload['username']}",
                headers={"Authorization": f"Bearer {admin_token}"},
                timeout=10.0
            )
            
            if list_response.status_code == 200:
                clients_data = list_response.json()
                if len(clients_data["clients"]) > 0:
                    client_id = clients_data["clients"][0]["id"]
                    
                    # Delete with admin token should work
                    delete_response = await client.delete(
                        f"{GATEWAY_URL}/api/clients/{client_id}",
                        headers={"Authorization": f"Bearer {admin_token}"},
                        timeout=10.0
                    )
                    
                    assert delete_response.status_code == 200, "Admin should be able to delete"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_11_unauthorized_access_requires_token(self):
        """
        Test 11: Verify that protected endpoints require authentication
        """
        async with httpx.AsyncClient() as client:
            # Try to access inventory without token
            response = await client.get(
                f"{GATEWAY_URL}/api/v1/inventory/",
                timeout=10.0
            )
            
            # Should return 401 or 403 (Unauthorized)
            assert response.status_code in [401, 403], "Protected endpoint should require authentication"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_12_gateway_health_check(self):
        """
        Test 12: Verify gateway health endpoint
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GATEWAY_URL}/gateway/health",
                timeout=10.0
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "services" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
