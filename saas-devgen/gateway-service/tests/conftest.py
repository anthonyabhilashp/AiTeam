"""Test Configuration and Fixtures for Gateway Service."""
import pytest
import os
import sys
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
import json

# Add the parent directory to the Python path so we can import main
# Check if we're in Docker (production) or local development
if os.path.exists('/app'):
    sys.path.insert(0, '/app')
else:
    # Local development - add the gateway-service directory
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import app


@pytest.fixture(scope="function")
def client():
    """Create FastAPI test client."""
    return TestClient(app)


@pytest.fixture(scope="function")
def mock_env():
    """Mock environment variables for testing."""
    env_vars = {
        'KEYCLOAK_URL': 'http://keycloak:8080',
        'KEYCLOAK_REALM': 'master',
        'KEYCLOAK_CLIENT_ID': 'admin-cli',
        'KEYCLOAK_CLIENT_SECRET': '',
        'KEYCLOAK_ADMIN_USER': 'admin',
        'KEYCLOAK_ADMIN_PASSWORD': 'admin',
        'KAFKA_BROKER_URL': 'kafka:29092',
        'KAFKA_TOPIC_USER_REGISTRATION': 'user-registration-events',
        'PROFILE_SERVICE_URL': 'http://profile-service:8005'
    }

    with patch.dict(os.environ, env_vars):
        yield env_vars


@pytest.fixture(scope="function")
def mock_keycloak_openid(valid_jwt_token):
    """Mock KeycloakOpenID instance."""
    with patch('main.KeycloakOpenID') as mock_kc:
        mock_instance = Mock()
        mock_instance.token.return_value = {
            "access_token": valid_jwt_token,  # Use the same valid JWT token
            "refresh_token": "test-refresh-token",
            "token_type": "Bearer"
        }
        mock_instance.userinfo.return_value = {
            "sub": "test-user-id",
            "preferred_username": "testuser",
            "email": "test@example.com"
        }
        mock_kc.return_value = mock_instance
        yield mock_instance


@pytest.fixture(scope="function")
def mock_get_keycloak_openid(mock_keycloak_openid):
    """Mock the get_keycloak_openid function."""
    with patch('main.get_keycloak_openid', return_value=mock_keycloak_openid):
        yield mock_keycloak_openid


@pytest.fixture(scope="function")
def mock_keycloak_admin():
    """Mock KeycloakAdmin instance."""
    with patch('main.KeycloakAdmin') as mock_kc_admin:
        mock_instance = Mock()
        mock_instance.create_user.return_value = "test-user-id"
        mock_instance.set_user_password.return_value = None
        mock_instance.get_users.return_value = []  # No existing users by default
        mock_kc_admin.return_value = mock_instance
        yield mock_instance


@pytest.fixture(scope="function")
def mock_get_keycloak_admin(mock_keycloak_admin):
    """Mock the get_keycloak_admin function."""
    with patch('main.get_keycloak_admin', return_value=mock_keycloak_admin):
        yield mock_keycloak_admin


@pytest.fixture(scope="function")
def mock_kafka_producer():
    """Mock Kafka producer."""
    with patch('main.KafkaProducer') as mock_producer:
        mock_instance = Mock()
        mock_producer.return_value = mock_instance
        yield mock_instance


@pytest.fixture(scope="function")
def mock_httpx_client():
    """Mock httpx client for service calls."""
    with patch('httpx.AsyncClient') as mock_client:
        mock_instance = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "healthy"}
        mock_response.content = b'{"status": "healthy"}'
        mock_response.headers = {"content-type": "application/json"}

        # Mock the async context manager properly
        mock_instance.__aenter__ = Mock(return_value=mock_instance)
        mock_instance.__aexit__ = Mock(return_value=None)
        mock_instance.get = Mock(return_value=mock_response)
        mock_instance.post = Mock(return_value=mock_response)

        mock_client.return_value.__aenter__.return_value = mock_instance
        mock_client.return_value.__aexit__.return_value = None

        yield mock_instance


@pytest.fixture(scope="function")
def valid_jwt_token():
    """Valid JWT token for testing."""
    import jwt
    import datetime

    payload = {
        "sub": "test-user-id",
        "preferred_username": "testuser",
        "email": "test@example.com",
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),
        "iat": datetime.datetime.utcnow(),
        "iss": "test-issuer"
    }

    # Create a token without signature verification for testing
    token = jwt.encode(payload, "test-secret", algorithm="HS256")
    return token


@pytest.fixture(scope="function")
def user_registration_data():
    """Sample user registration data."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123",
        "first_name": "John",
        "last_name": "Doe"
    }


@pytest.fixture(scope="function")
def login_data():
    """Sample login data."""
    return {
        "username": "admin",
        "password": "admin"
    }


@pytest.fixture(scope="function")
def gateway_service():
    """Mock GatewayService instance for integration tests."""
    service = Mock()
    service.kong_admin_url = "http://localhost:8001"
    service.kong_proxy_url = "http://localhost:8000"
    service.kong_gui_url = "http://localhost:8002"

    # Mock methods with proper behavior
    def mock_check_kong_status():
        return True

    def mock_get_services():
        # Simulate successful response
        return {"data": []}

    def mock_get_routes():
        return {"data": []}

    service.check_kong_status = mock_check_kong_status
    service.get_services = mock_get_services
    service.get_routes = mock_get_routes

    return service
