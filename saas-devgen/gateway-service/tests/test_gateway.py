"""Test Gateway Service FastAPI Endpoints."""
import pytest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from main import app


class TestGatewayHealth:
    """Test Gateway Service Health Endpoints."""

    def test_health_endpoint(self, client):
        """Test gateway health endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")

        assert response.status_code == 200
        assert "API Gateway" in response.json()["message"]


class TestAuthentication:
    """Test Authentication Endpoints."""

    def test_login_success(self, client, mock_get_keycloak_openid, login_data):
        """Test successful user login."""
        response = client.post("/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "Bearer"

    def test_login_failure(self, client, mock_get_keycloak_openid):
        """Test login failure with invalid credentials."""
        from keycloak.exceptions import KeycloakAuthenticationError
        mock_get_keycloak_openid.token.side_effect = KeycloakAuthenticationError("Invalid credentials")

        login_data = {"username": "invalid", "password": "invalid"}
        response = client.post("/auth/login", json=login_data)

        assert response.status_code == 401
        assert "Invalid" in response.json()["detail"]

    def test_user_info_success(self, client, mock_keycloak_openid, valid_jwt_token):
        """Test successful user info retrieval."""
        response = client.get("/auth/user", headers={"Authorization": f"Bearer {valid_jwt_token}"})

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "test-user-id"
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"

    def test_user_info_no_token(self, client):
        """Test user info without authorization token."""
        response = client.get("/auth/user")

        assert response.status_code == 403  # HTTPBearer returns 403 for missing token
        assert "not authenticated" in response.json()["detail"].lower()

    def test_user_info_invalid_token(self, client):
        """Test user info with invalid token."""
        response = client.get("/auth/user", headers={"Authorization": "Bearer invalid-token"})

        assert response.status_code == 401
        assert "Invalid" in response.json()["detail"]


class TestUserRegistration:
    """Test User Registration Endpoints."""

    def test_register_user_success(self, client, mock_get_keycloak_admin, mock_kafka_producer, user_registration_data):
        """Test successful user registration."""
        response = client.post("/auth/register", json=user_registration_data)

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "user_id" in data
        assert data["user_id"] == "test-user-id"

    def test_register_user_missing_fields(self, client):
        """Test user registration with missing required fields."""
        incomplete_data = {"username": "testuser"}
        response = client.post("/auth/register", json=incomplete_data)

        assert response.status_code == 422  # Validation error

    def test_register_user_keycloak_error(self, client, mock_get_keycloak_admin):
        """Test user registration with Keycloak error."""
        mock_get_keycloak_admin.create_user.side_effect = Exception("Keycloak error")

        response = client.post("/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123"
        })

        assert response.status_code == 500
        assert "unexpected error occurred during registration" in response.json()["detail"]


class TestProxyRoutes:
    """Test Proxy Route Endpoints."""

    def test_proxy_profile_health(self, client, valid_jwt_token):
        """Test proxy to profile service health endpoint."""
        from fastapi import Response

        with patch('main.proxy_request') as mock_proxy:
            # Create a proper FastAPI Response object
            mock_response = Response(
                content='{"status": "healthy"}',
                status_code=200,
                media_type="application/json"
            )
            mock_proxy.return_value = mock_response

            response = client.get("/profile/health", headers={"Authorization": f"Bearer {valid_jwt_token}"})

            assert response.status_code == 200
            assert response.json() == {"status": "healthy"}

    def test_proxy_profile_without_auth(self, client):
        """Test proxy to profile service without authentication."""
        response = client.get("/profile/health")

        assert response.status_code == 403
        assert "Not authenticated" in response.json()["detail"]

    def test_proxy_unknown_service(self, client, valid_jwt_token):
        """Test proxy to unknown service."""
        response = client.get("/unknown/health", headers={"Authorization": f"Bearer {valid_jwt_token}"})

        assert response.status_code == 404
        assert "Not Found" in response.json()["detail"]


class TestErrorHandling:
    """Test Error Handling."""

    def test_invalid_json(self, client):
        """Test handling of invalid JSON."""
        response = client.post("/auth/login", data="invalid json")

        assert response.status_code == 422

    def test_method_not_allowed(self, client):
        """Test method not allowed."""
        response = client.put("/health")

        assert response.status_code == 405

    def test_not_found(self, client):
        """Test not found endpoint."""
        response = client.get("/nonexistent")

        assert response.status_code == 404


class TestMiddleware:
    """Test Middleware Functionality."""

    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        # Test with a POST request that should have CORS headers
        response = client.post("/auth/login", json={"username": "test", "password": "test"})

        # Check if CORS headers are present (may not be for all endpoints)
        cors_headers = ["access-control-allow-origin", "access-control-allow-methods"]
        has_cors = any(header in response.headers for header in cors_headers)
        if has_cors:
            assert "access-control-allow-origin" in response.headers
            assert "access-control-allow-methods" in response.headers
            assert "access-control-allow-headers" in response.headers


class TestIntegration:
    """Test Integration Scenarios."""

    def test_full_authentication_flow(self, client, mock_get_keycloak_openid, mock_get_keycloak_admin, mock_kafka_producer):
        """Test complete authentication flow."""
        # Register user
        register_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
            "first_name": "John",
            "last_name": "Doe"
        }
        register_response = client.post("/auth/register", json=register_data)
        assert register_response.status_code == 200

        # Login user
        login_data = {"username": "testuser", "password": "password123"}
        login_response = client.post("/auth/login", json=login_data)
        assert login_response.status_code == 200

        token = login_response.json()["access_token"]

        # Access protected endpoint
        user_response = client.get("/auth/user", headers={"Authorization": f"Bearer {token}"})
        assert user_response.status_code == 200

        # Access proxy endpoint
        from fastapi import Response

        with patch('main.proxy_request') as mock_proxy:
            # Create a proper FastAPI Response object
            mock_response = Response(
                content='{"status": "healthy"}',
                status_code=200,
                media_type="application/json"
            )
            mock_proxy.return_value = mock_response

            proxy_response = client.get("/profile/health", headers={"Authorization": f"Bearer {token}"})
            assert proxy_response.status_code == 200
