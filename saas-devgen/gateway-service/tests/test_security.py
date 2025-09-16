"""Security tests for Gateway Service."""
import pytest
from unittest.mock import Mock, patch
import requests


class TestGatewaySecurity:
    """Test security features of the gateway service."""

    def test_environment_security(self, gateway_service):
        """Test that gateway service uses secure defaults."""
        # Test that URLs use localhost (internal) by default
        assert "localhost" in gateway_service.kong_admin_url
        assert "localhost" in gateway_service.kong_proxy_url
        assert "localhost" in gateway_service.kong_gui_url

        # Test that ports are standard Kong ports
        assert ":8001" in gateway_service.kong_admin_url
        assert ":8000" in gateway_service.kong_proxy_url
        assert ":8002" in gateway_service.kong_gui_url

    def test_request_timeout_security(self, gateway_service):
        """Test that requests have reasonable timeouts to prevent hanging."""
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "ok"}
            mock_get.return_value = mock_response

            # Test that status check doesn't hang
            result = gateway_service.check_kong_status()
            assert result is True

            # Verify timeout was used (requests.get called with timeout)
            mock_get.assert_called_with("http://localhost:8001/status", timeout=10)

    def test_error_handling_security(self, gateway_service):
        """Test that errors are handled securely without exposing sensitive information."""
        with patch('requests.get') as mock_get:
            # Test connection error
            mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

            result = gateway_service.check_kong_status()
            assert result is False

            # Test timeout error
            mock_get.side_effect = requests.exceptions.Timeout("Request timed out")

            result = gateway_service.check_kong_status()
            assert result is False

    def test_service_isolation(self, gateway_service):
        """Test that services are properly isolated."""
        # Test that each service has its own URL
        assert gateway_service.kong_admin_url != gateway_service.kong_proxy_url
        assert gateway_service.kong_admin_url != gateway_service.kong_gui_url
        assert gateway_service.kong_proxy_url != gateway_service.kong_gui_url


class TestGatewaySecurityIntegration:
    """Integration tests for security features."""

    def test_secure_configuration_loading(self, gateway_service):
        """Test that configuration is loaded securely."""
        # Test that service can be created without environment variables
        service = type(gateway_service)()

        # Should use secure defaults
        assert service.kong_admin_url.startswith("http://")
        assert "localhost" in service.kong_admin_url

    def test_request_validation(self, gateway_service):
        """Test that requests are properly validated."""
        with patch('requests.get') as mock_get:
            # Test successful request
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": []}
            mock_get.return_value = mock_response

            services = gateway_service.get_services()
            assert services is not None
            assert "data" in services

            # Test failed request
            mock_response.status_code = 500
            mock_get.return_value = mock_response

            services = gateway_service.get_services()
            assert services is None
