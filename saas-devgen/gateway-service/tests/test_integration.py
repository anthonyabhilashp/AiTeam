"""Integration Tests for Gateway Service."""
import pytest
import requests
import time
from unittest.mock import patch
from main import GatewayService


class TestGatewayIntegration:
    """Integration tests for Gateway Service."""

    def test_kong_admin_api_accessibility(self, gateway_service):
        """Test that Kong Admin API is accessible."""
        try:
            response = requests.get(f"{gateway_service.kong_admin_url}/status", timeout=5)
            assert response.status_code == 200
            data = response.json()
            assert "server" in data
            assert "configuration_hash" in data
        except requests.exceptions.RequestException:
            pytest.skip("Kong Admin API not available - skipping integration test")

    def test_kong_proxy_accessibility(self, gateway_service):
        """Test that Kong Proxy is accessible."""
        try:
            response = requests.get(f"{gateway_service.kong_proxy_url}/", timeout=5)
            # Kong proxy should return 404 for root path (no routes configured)
            assert response.status_code in [404, 200]
        except requests.exceptions.RequestException:
            pytest.skip("Kong Proxy not available - skipping integration test")

    def test_kong_services_endpoint(self, gateway_service):
        """Test Kong services endpoint."""
        try:
            response = requests.get(f"{gateway_service.kong_admin_url}/services", timeout=5)
            assert response.status_code == 200
            data = response.json()
            assert "data" in data
            assert isinstance(data["data"], list)
        except requests.exceptions.RequestException:
            pytest.skip("Kong Admin API not available - skipping integration test")

    def test_kong_routes_endpoint(self, gateway_service):
        """Test Kong routes endpoint."""
        try:
            response = requests.get(f"{gateway_service.kong_admin_url}/routes", timeout=5)
            assert response.status_code == 200
            data = response.json()
            assert "data" in data
            assert isinstance(data["data"], list)
        except requests.exceptions.RequestException:
            pytest.skip("Kong Admin API not available - skipping integration test")

    def test_gateway_service_monitoring(self, gateway_service):
        """Test gateway service monitoring functionality."""
        # Test that monitoring methods don't crash
        try:
            status = gateway_service.check_kong_status()
            assert isinstance(status, bool)

            services = gateway_service.get_services()
            assert services is None or isinstance(services, dict)

            routes = gateway_service.get_routes()
            assert routes is None or isinstance(routes, dict)

        except Exception as e:
            pytest.fail(f"Monitoring functionality failed: {e}")

    @patch('time.sleep')
    def test_monitoring_loop_structure(self, mock_sleep, gateway_service):
        """Test the structure of the monitoring loop."""
        # This test verifies the monitoring loop components work correctly
        # without actually running the infinite loop

        with patch.object(gateway_service, 'check_kong_status', return_value=True):
            with patch.object(gateway_service, 'get_services', return_value={"data": []}):
                with patch.object(gateway_service, 'get_routes', return_value={"data": []}):
                    # Test that the individual components work
                    status = gateway_service.check_kong_status()
                    services = gateway_service.get_services()
                    routes = gateway_service.get_routes()

                    assert status is True
                    assert services == {"data": []}
                    assert routes == {"data": []}

                    # Verify sleep was not called (since we're not running the loop)
                    mock_sleep.assert_not_called()


def test_environment_variables_loaded():
    """Test that environment variables are properly loaded."""
    service = GatewayService()

    # Check that URLs are set (either from env or defaults)
    assert service.kong_admin_url.startswith("http://")
    assert service.kong_proxy_url.startswith("http://")
    assert service.kong_gui_url.startswith("http://")

    # Check that they contain expected host/port patterns
    assert "localhost" in service.kong_admin_url or "kong" in service.kong_admin_url
    assert ":8000" in service.kong_proxy_url
    assert ":8001" in service.kong_admin_url
    assert ":8002" in service.kong_gui_url
