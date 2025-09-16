"""Test Configuration and Fixtures for Auth Service."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import os

# Import the app
from main import app

# Create test client
@pytest.fixture(scope="function")
def client():
    """Create test client for API testing."""
    return TestClient(app)


@pytest.fixture(scope="function")
def mock_keycloak():
    """Mock Keycloak clients for testing."""
    with patch('main.get_keycloak_openid') as mock_openid, \
         patch('main.get_keycloak_admin') as mock_admin:

        # Mock OpenID client
        mock_openid_instance = MagicMock()
        mock_openid.return_value = mock_openid_instance

        # Mock Admin client
        mock_admin_instance = MagicMock()
        mock_admin.return_value = mock_admin_instance

        # Mock successful token response
        mock_token = {
            "access_token": "mock-access-token",
            "refresh_token": "mock-refresh-token",
            "token_type": "Bearer",
            "expires_in": 300
        }
        mock_openid_instance.token.return_value = mock_token

        # Mock userinfo response
        mock_userinfo = {
            "sub": "test-user-id",
            "preferred_username": "testuser",
            "email": "test@example.com",
            "realm_access": {"roles": ["user"]}
        }
        mock_openid_instance.userinfo.return_value = mock_userinfo

        yield {
            'openid': mock_openid_instance,
            'admin': mock_admin_instance,
            'token': mock_token,
            'userinfo': mock_userinfo
        }


@pytest.fixture(scope="function")
def mock_admin_keycloak():
    """Mock Keycloak clients for admin testing."""
    with patch('main.get_keycloak_openid') as mock_openid, \
         patch('main.get_keycloak_admin') as mock_admin:

        # Mock OpenID client
        mock_openid_instance = MagicMock()
        mock_openid.return_value = mock_openid_instance

        # Mock Admin client
        mock_admin_instance = MagicMock()
        mock_admin.return_value = mock_admin_instance

        # Mock successful admin token response
        mock_token = {
            "access_token": "mock-admin-access-token",
            "refresh_token": "mock-admin-refresh-token",
            "token_type": "Bearer",
            "expires_in": 300
        }
        mock_openid_instance.token.return_value = mock_token

        # Mock admin userinfo response
        mock_userinfo = {
            "sub": "admin-user-id",
            "preferred_username": "admin",
            "email": "admin@example.com",
            "realm_access": {"roles": ["admin", "user"]}
        }
        mock_openid_instance.userinfo.return_value = mock_userinfo

        yield {
            'openid': mock_openid_instance,
            'admin': mock_admin_instance,
            'token': mock_token,
            'userinfo': mock_userinfo
        }


@pytest.fixture(scope="function")
def auth_headers(mock_keycloak):
    """Create authorization headers for authenticated requests."""
    return {"Authorization": f"Bearer {mock_keycloak['token']['access_token']}"}


@pytest.fixture(scope="function")
def admin_auth_headers(mock_admin_keycloak):
    """Create authorization headers for admin requests."""
    return {"Authorization": f"Bearer {mock_admin_keycloak['token']['access_token']}"}


# Test utilities
class TestUtils:
    """Utility functions for tests."""

    @staticmethod
    def create_mock_user(mock_admin, username="testuser", email="test@example.com"):
        """Create a mock user in Keycloak."""
        mock_admin.create_user.return_value = f"{username}-id"
        return f"{username}-id"

    @staticmethod
    def mock_successful_login(mock_openid, user_id="test-user-id", username="testuser", roles=None):
        """Mock a successful login response."""
        if roles is None:
            roles = ["user"]

        mock_token = {
            "access_token": f"mock-access-{user_id}",
            "refresh_token": f"mock-refresh-{user_id}",
            "token_type": "Bearer",
            "expires_in": 300
        }

        mock_userinfo = {
            "sub": user_id,
            "preferred_username": username,
            "email": f"{username}@example.com",
            "realm_access": {"roles": roles}
        }

        mock_openid.token.return_value = mock_token
        mock_openid.userinfo.return_value = mock_userinfo

        return mock_token, mock_userinfo


# Make TestUtils available to all tests
@pytest.fixture(scope="session")
def test_utils():
    """Provide test utilities."""
    return TestUtils()
