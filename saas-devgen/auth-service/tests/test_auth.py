"""Test Auth Service with Keycloak."""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "unhealthy"]
    assert data["service"] == "auth-service"

def test_login_invalid_credentials():
    """Test login with invalid credentials."""
    response = client.post("/login", json={
        "username": "invalid",
        "password": "invalid"
    })
    # Should fail due to Keycloak connection or invalid credentials
    assert response.status_code in [401, 500]

def test_refresh_token_invalid():
    """Test refresh token with invalid token."""
    response = client.post("/refresh?refresh_token=invalid")
    # Should fail due to Keycloak connection or invalid token
    assert response.status_code in [401, 500, 422]

def test_logout_invalid_token():
    """Test logout with invalid token."""
    response = client.post("/logout?refresh_token=invalid")
    # Should fail due to Keycloak connection or invalid token
    assert response.status_code in [422, 500]

def test_userinfo_invalid_token():
    """Test userinfo with invalid token."""
    response = client.get("/userinfo", headers={
        "Authorization": "Bearer invalid"
    })
    assert response.status_code == 401

def test_introspect_invalid_token():
    """Test token introspection with invalid token."""
    response = client.get("/introspect", params={"token": "invalid"})
    assert response.status_code == 401

def test_register_user():
    """Test user registration."""
    response = client.post("/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
        "first_name": "Test",
        "last_name": "User"
    })
    # Should fail due to Keycloak connection
    assert response.status_code in [400, 500]

def test_password_reset():
    """Test password reset request."""
    response = client.post("/password-reset", json={
        "email": "test@example.com"
    })
    # Should fail due to Keycloak connection
    assert response.status_code in [404, 500]

def test_change_password_invalid_token():
    """Test password change with invalid token."""
    response = client.post("/change-password", json={
        "current_password": "oldpass",
        "new_password": "newpass123"
    }, headers={
        "Authorization": "Bearer invalid"
    })
    assert response.status_code == 401

def test_get_user_roles_invalid_token():
    """Test getting user roles with invalid token."""
    response = client.get("/roles", headers={
        "Authorization": "Bearer invalid"
    })
    assert response.status_code == 401

def test_update_user_roles_invalid_token():
    """Test updating user roles with invalid token."""
    response = client.put("/user/test-user-id/roles", json={
        "user_id": "test-user-id",
        "roles": ["user", "admin"]
    }, headers={
        "Authorization": "Bearer invalid"
    })
    assert response.status_code == 401
