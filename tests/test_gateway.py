"""
Comprehensive test suite for Censudx API Gateway
Tests gateway routing, authentication, and service integration
"""

import pytest
import httpx
import asyncio
from fastapi.testclient import TestClient
import json

# Import the gateway app
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from gateway.main import app

@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)

class TestGatewayHealth:
    """Test gateway health and status endpoints"""
    
    def test_gateway_health(self, client):
        """Test gateway health check"""
        response = client.get("/gateway/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "api-gateway"
        assert "services" in data

    def test_detailed_health(self, client):
        """Test detailed health check"""
        response = client.get("/gateway/health-detailed")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "components" in data

class TestAuthentication:
    """Test authentication endpoints and JWT handling"""
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        response = client.post("/gateway/auth/login", json={
            "username": "nonexistent",
            "password": "wrong"
        })
        # Should get error from auth service (may be 503 if service unavailable)
        assert response.status_code in [401, 503]

    def test_login_missing_credentials(self, client):
        """Test login with missing credentials"""
        response = client.post("/gateway/auth/login", json={})
        assert response.status_code == 400
        data = response.json()
        assert "Username and password required" in data["detail"]

    def test_validate_without_token(self, client):
        """Test token validation without token"""
        response = client.post("/gateway/auth/validate")
        assert response.status_code == 403  # No authorization header

class TestServiceDiscovery:
    """Test service discovery and routing"""
    
    def test_list_services(self, client):
        """Test service discovery endpoint"""
        response = client.get("/gateway/services")
        assert response.status_code == 200
        data = response.json()
        assert "services" in data
        assert "total_services" in data
        
        # Check that all expected services are listed
        expected_services = ["inventory", "auth", "users", "orders", "products"]
        for service in expected_services:
            assert service in data["services"]

class TestProxyRouting:
    """Test service proxy routing"""
    
    def test_proxy_nonexistent_service(self, client):
        """Test proxy to nonexistent service"""
        response = client.get("/gateway/proxy/nonexistent/test")
        assert response.status_code == 404
        data = response.json()
        assert "Service 'nonexistent' not found" in data["detail"]

    def test_proxy_without_auth_required_service(self, client):
        """Test proxy to service that requires auth without token"""
        response = client.get("/gateway/proxy/inventory/")
        assert response.status_code == 401
        data = response.json()
        assert "Authentication required" in data["detail"]

    def test_proxy_public_service(self, client):
        """Test proxy to public service (products)"""
        # Products service doesn't require auth
        response = client.get("/gateway/proxy/products/")
        # May get 503 if service is not running, which is expected
        assert response.status_code in [200, 503]

class TestRateLimiting:
    """Test rate limiting functionality"""
    
    def test_rate_limiting_headers(self, client):
        """Test that rate limiting headers are present"""
        response = client.get("/gateway/health")
        assert response.status_code == 200
        
        # Check for rate limiting headers
        assert "x-ratelimit-limit" in response.headers
        assert "x-ratelimit-remaining" in response.headers
        assert "x-ratelimit-reset" in response.headers

class TestRequestTracing:
    """Test request ID and tracing"""
    
    def test_request_id_generation(self, client):
        """Test that request ID is generated"""
        response = client.get("/gateway/health")
        assert response.status_code == 200
        assert "x-request-id" in response.headers

    def test_existing_request_id_preserved(self, client):
        """Test that existing request ID is preserved"""
        custom_request_id = "test-request-123"
        response = client.get(
            "/gateway/health",
            headers={"x-request-id": custom_request_id}
        )
        assert response.status_code == 200
        assert response.headers["x-request-id"] == custom_request_id

class TestErrorHandling:
    """Test error handling and responses"""
    
    def test_404_error_format(self, client):
        """Test 404 error response format"""
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert "status_code" in data
        assert "timestamp" in data
        assert "path" in data

class TestCORSAndSecurity:
    """Test CORS and security headers"""
    
    def test_cors_preflight(self, client):
        """Test CORS preflight request"""
        response = client.options(
            "/gateway/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
        )
        # FastAPI handles CORS automatically
        assert response.status_code in [200, 405]

# Integration tests (require running services)
class TestServiceIntegration:
    """Integration tests with actual services"""
    
    @pytest.mark.integration
    def test_auth_service_integration(self, client):
        """Test integration with auth service"""
        # This test requires auth-stub service to be running
        response = client.post("/gateway/auth/login", json={
            "username": "test",
            "password": "test123"
        })
        
        if response.status_code == 200:
            # Auth service is running and returned token
            data = response.json()
            assert "access_token" in data
            assert "user" in data
        elif response.status_code == 503:
            # Auth service is not available - expected in unit tests
            pytest.skip("Auth service not available for integration test")
        else:
            # Unexpected response
            assert False, f"Unexpected response: {response.status_code}"

    @pytest.mark.integration  
    def test_inventory_service_integration(self, client):
        """Test integration with inventory service through proxy"""
        # Try to access inventory service without auth (should fail)
        response = client.get("/gateway/proxy/inventory/")
        assert response.status_code == 401  # Requires authentication

if __name__ == "__main__":
    pytest.main([__file__, "-v"])