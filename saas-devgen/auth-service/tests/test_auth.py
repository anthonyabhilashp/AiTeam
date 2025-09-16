"""Test Auth Service with Keycloak."""
import pytest
from unittest.mock import patch, MagicMock
import asyncio


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "unhealthy"]
    assert data["service"] == "auth-service"


@patch('main.get_keycloak_admin')
def test_create_default_admin_user_new_user(mock_get_admin):
    """Test creating default admin user when user doesn't exist."""
    from main import create_default_admin_user

    # Mock Keycloak admin client
    mock_admin = MagicMock()
    mock_get_admin.return_value = mock_admin

    # Mock that no users exist with username "admin"
    mock_admin.get_users.return_value = []

    # Mock user creation
    mock_admin.create_user.return_value = "admin-user-id"

    # Mock role assignment
    mock_role = {"id": "admin-role-id", "name": "admin"}
    mock_admin.get_realm_role.return_value = mock_role

    # Run the function
    asyncio.run(create_default_admin_user())

    # Verify user was created with correct data
    mock_admin.create_user.assert_called_once()
    call_args = mock_admin.create_user.call_args[0][0]

    assert call_args["username"] == "admin"
    assert call_args["email"] == "admin@example.com"
    assert call_args["firstName"] == "Admin"
    assert call_args["lastName"] == "User"
    assert call_args["enabled"] is True
    assert call_args["emailVerified"] is True
    assert len(call_args["credentials"]) == 1
    assert call_args["credentials"][0]["value"] == "admin"

    # Verify role was assigned
    mock_admin.assign_realm_roles.assert_called_once_with("admin-user-id", [mock_role])

@patch('main.get_keycloak_openid')
@patch('main.get_keycloak_admin')
def test_admin_user_login_functionality(mock_get_admin, mock_get_openid, client):
    """Test that admin user can login and get proper token with admin role."""
    # Mock Keycloak clients
    mock_admin = MagicMock()
    mock_openid = MagicMock()
    mock_get_admin.return_value = mock_admin
    mock_get_openid.return_value = mock_openid

    # Mock that admin user exists
    mock_admin.get_users.return_value = [{"id": "admin-user-id", "username": "admin"}]

    # Mock successful token exchange
    mock_token_response = {
        "access_token": "mock-admin-access-token",
        "refresh_token": "mock-admin-refresh-token",
        "token_type": "Bearer",
        "expires_in": 300,
        "user_id": "admin-user-id",
        "roles": ["admin", "uma_protection"]
    }
    mock_openid.token.return_value = mock_token_response

    # Mock user info
    mock_userinfo = {
        "sub": "admin-user-id",
        "preferred_username": "admin",
        "email": "admin@example.com",
        "realm_access": {"roles": ["admin", "uma_protection"]},
        "name": "Admin User"
    }
    mock_openid.userinfo.return_value = mock_userinfo

    # Test login endpoint
    response = client.post("/login", json={
        "username": "admin",
        "password": "admin"
    })

    # Should succeed with proper token response
    assert response.status_code == 200
    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "Bearer"
    assert data["expires_in"] == 300
    assert data["user_id"] == "admin-user-id"
    assert "admin" in data["roles"]

    # Test userinfo endpoint with the token
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    userinfo_response = client.get("/userinfo", headers=headers)

    assert userinfo_response.status_code == 200
    user_data = userinfo_response.json()

    assert user_data["preferred_username"] == "admin"
    assert user_data["email"] == "admin@example.com"
    assert "admin" in user_data["realm_access"]["roles"]

@patch('main.get_keycloak_admin')
def test_admin_user_already_exists_skip_creation(mock_get_admin):
    """Test that default admin user creation is skipped when user already exists."""
    from main import create_default_admin_user

    # Mock Keycloak admin client
    mock_admin = MagicMock()
    mock_get_admin.return_value = mock_admin

    # Mock that admin user already exists
    mock_admin.get_users.return_value = [{"id": "existing-admin-id", "username": "admin"}]

    # Run the function
    import asyncio
    asyncio.run(create_default_admin_user())

    # Verify user was NOT created (no creation calls made)
    mock_admin.create_user.assert_not_called()
    mock_admin.assign_realm_roles.assert_not_called()

@patch('main.get_keycloak_admin')
def test_create_default_admin_user_keycloak_unavailable(mock_get_admin):
    """Test handling when Keycloak admin is not available."""
    from main import create_default_admin_user

    # Mock that Keycloak admin is not available
    mock_get_admin.return_value = None

    # Run the function (should not raise exception)
    import asyncio
    asyncio.run(create_default_admin_user())

    # Function should complete without error
    assert True

def test_login_invalid_credentials(client):
    """Test login with invalid credentials."""
    response = client.post("/login", json={
        "username": "invalid",
        "password": "invalid"
    })
    # Should fail due to Keycloak connection or invalid credentials
    assert response.status_code in [401, 500]


def test_refresh_token_invalid(client):
    """Test refresh token with invalid token."""
    response = client.post("/refresh?refresh_token=invalid")
    # Should fail due to Keycloak connection or invalid token
    assert response.status_code in [401, 500, 422]


def test_logout_invalid_token(client):
    """Test logout with invalid token."""
    response = client.post("/logout?refresh_token=invalid")
    # Should fail due to Keycloak connection or invalid token
    assert response.status_code in [422, 500]


def test_userinfo_invalid_token(client):
    """Test userinfo with invalid token."""
    response = client.get("/userinfo", headers={
        "Authorization": "Bearer invalid"
    })
    assert response.status_code == 401


def test_introspect_invalid_token(client):
    """Test token introspection with invalid token."""
    response = client.get("/introspect", params={"token": "invalid"})
    assert response.status_code == 401


def test_register_user(client):
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


def test_password_reset(client):
    """Test password reset request."""
    response = client.post("/password-reset", json={
        "email": "test@example.com"
    })
    # Should fail due to Keycloak connection
    assert response.status_code in [404, 500]


def test_change_password_invalid_token(client):
    """Test password change with invalid token."""
    response = client.post("/change-password", json={
        "current_password": "oldpass",
        "new_password": "newpass123"
    }, headers={
        "Authorization": "Bearer invalid"
    })
    assert response.status_code == 401


def test_get_user_roles_invalid_token(client):
    """Test getting user roles with invalid token."""
    response = client.get("/roles", headers={
        "Authorization": "Bearer invalid"
    })
    assert response.status_code == 401


def test_update_user_roles_invalid_token(client):
    """Test updating user roles with invalid token."""
    response = client.put("/user/test-user-id/roles", json={
        "user_id": "test-user-id",
        "roles": ["user", "admin"]
    }, headers={
        "Authorization": "Bearer invalid"
    })
    assert response.status_code == 401
