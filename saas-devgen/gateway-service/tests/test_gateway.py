"""Test Gateway Service Core Functionality."""
import pytest
from unittest.mock import patch, Mock
from main import GatewayService


class TestGatewayService:
    """Test GatewayService class functionality."""

    def test_init_default_values(self):
        """Test GatewayService initialization with default values."""
        service = GatewayService()

        assert service.kong_admin_url == "http://localhost:8001"
        assert service.kong_proxy_url == "http://localhost:8000"
        assert service.kong_gui_url == "http://localhost:8002"

    def test_init_custom_values(self, mock_env):
        """Test GatewayService initialization with custom environment values."""
        service = GatewayService()

        assert service.kong_admin_url == "http://localhost:8001"
        assert service.kong_proxy_url == "http://localhost:8000"
        assert service.kong_gui_url == "http://localhost:8002"

    @patch('requests.get')
    def test_check_kong_status_success(self, mock_get, gateway_service, mock_kong_response):
        """Test successful Kong status check."""
        mock_get.return_value = mock_kong_response

        result = gateway_service.check_kong_status()

        assert result is True
        mock_get.assert_called_once_with("http://localhost:8001/status", timeout=10)

    @patch('requests.get')
    def test_check_kong_status_failure(self, mock_get, gateway_service):
        """Test failed Kong status check."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        result = gateway_service.check_kong_status()

        assert result is False

    @patch('requests.get')
    def test_check_kong_status_exception(self, mock_get, gateway_service):
        """Test Kong status check with exception."""
        mock_get.side_effect = Exception("Connection error")

        result = gateway_service.check_kong_status()

        assert result is False

    @patch('requests.get')
    def test_get_services_success(self, mock_get, gateway_service, mock_services_response):
        """Test successful services retrieval."""
        mock_get.return_value = mock_services_response

        result = gateway_service.get_services()

        assert result is not None
        assert len(result["data"]) == 1
        assert result["data"][0]["name"] == "auth-service"
        mock_get.assert_called_once_with("http://localhost:8001/services", timeout=10)

    @patch('requests.get')
    def test_get_services_failure(self, mock_get, gateway_service):
        """Test failed services retrieval."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        result = gateway_service.get_services()

        assert result is None

    @patch('requests.get')
    def test_get_routes_success(self, mock_get, gateway_service, mock_routes_response):
        """Test successful routes retrieval."""
        mock_get.return_value = mock_routes_response

        result = gateway_service.get_routes()

        assert result is not None
        assert len(result["data"]) == 1
        assert result["data"][0]["paths"] == ["/auth"]
        mock_get.assert_called_once_with("http://localhost:8001/routes", timeout=10)

    @patch('requests.get')
    def test_get_routes_failure(self, mock_get, gateway_service):
        """Test failed routes retrieval."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        result = gateway_service.get_routes()

        assert result is None


def test_gateway_service_creation():
    """Test GatewayService can be created."""
    service = GatewayService()
    assert service is not None
    assert hasattr(service, 'kong_admin_url')
    assert hasattr(service, 'kong_proxy_url')
    assert hasattr(service, 'kong_gui_url')
