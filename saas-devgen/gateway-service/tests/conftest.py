"""Test Configuration and Fixtures for Gateway Service."""
import pytest
import os
import requests
from unittest.mock import Mock, patch
from main import GatewayService


@pytest.fixture(scope="function")
def gateway_service():
    """Create GatewayService instance for testing."""
    service = GatewayService()
    return service


@pytest.fixture(scope="function")
def mock_env():
    """Mock environment variables for testing."""
    env_vars = {
        'KONG_ADMIN_URL': 'http://localhost:8001',
        'KONG_PROXY_URL': 'http://localhost:8000',
        'KONG_GUI_URL': 'http://localhost:8002'
    }

    with patch.dict(os.environ, env_vars):
        yield env_vars


@pytest.fixture(scope="function")
def mock_kong_response():
    """Mock Kong API response."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "configuration_hash": "test-hash",
        "server": {
            "connections_accepted": 100,
            "connections_active": 10,
            "connections_handled": 100,
            "connections_reading": 2,
            "connections_writing": 8,
            "connections_waiting": 0,
            "total_requests": 1000
        }
    }
    return mock_response


@pytest.fixture(scope="function")
def mock_services_response():
    """Mock Kong services response."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [
            {
                "id": "service-1",
                "name": "auth-service",
                "url": "http://auth-service:8004",
                "created_at": 1609459200
            }
        ],
        "next": None
    }
    return mock_response


@pytest.fixture(scope="function")
def mock_routes_response():
    """Mock Kong routes response."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [
            {
                "id": "route-1",
                "service": {"id": "service-1"},
                "paths": ["/auth"],
                "methods": ["GET", "POST"],
                "created_at": 1609459200
            }
        ],
        "next": None
    }
    return mock_response


@pytest.fixture(scope="function")
def mock_kong_error():
    """Mock Kong API error response."""
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.json.return_value = {
        "message": "Internal Server Error"
    }
    return mock_response
