"""Test Profile Service FastAPI."""
import pytest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from main import app


class TestProfileHealth:
    """Test Profile Service Health Endpoints."""

    def test_health_endpoint(self, client, mock_db_connection, mock_kafka_consumer):
        """Test health endpoint returns healthy status."""
        # Mock the global kafka_consumer to be initialized
        with patch('main.kafka_consumer', mock_kafka_consumer):
            response = client.get("/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "profile-service"
            assert data["database"] == "connected"
            assert data["kafka"] == "connected"

    def test_health_database_error(self, client, mock_kafka_consumer):
        """Test health endpoint with database error."""
        with patch('main.psycopg2.connect', side_effect=Exception("DB connection failed")):
            response = client.get("/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "unhealthy"
            assert data["database"] == "disconnected"

    def test_health_kafka_error(self, client, mock_db_connection):
        """Test health endpoint with Kafka error."""
        # Mock Kafka consumer to be None (failed initialization)
        with patch('main.kafka_consumer', None):
            response = client.get("/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"  # Status is healthy if DB is connected
            assert data["kafka"] == "disconnected"


class TestProfileEndpoints:
    """Test Profile Management Endpoints."""

    def test_get_profile_success(self, client, mock_db_connection):
        """Test successful profile retrieval."""
        # Send headers as they would come from the gateway service
        headers = {
            "X-User-ID": "test-user-id",
            "X-User-Username": "testuser",
            "X-User-Email": "test@example.com",
            "X-User-Roles": "user"
        }
        response = client.get("/me", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "test-user-id"
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert data["first_name"] == "John"
        assert data["last_name"] == "Doe"

    def test_get_profile_no_token(self, client):
        """Test profile retrieval without authorization token."""
        response = client.get("/me")

        assert response.status_code == 401

    def test_get_profile_invalid_token(self, client):
        """Test profile retrieval with invalid token."""
        response = client.get("/me", headers={"Authorization": "Bearer invalid-token"})

        assert response.status_code == 401
        assert "User authentication required" in response.json()["detail"]

    def test_get_profile_database_error(self, client):
        """Test profile retrieval with database error."""
        headers = {
            "X-User-ID": "test-user-id",
            "X-User-Username": "testuser",
            "X-User-Email": "test@example.com"
        }
        with patch('main.psycopg2.connect', side_effect=Exception("DB error")):
            response = client.get("/me", headers=headers)

            assert response.status_code == 500
            assert "Internal server error" in response.json()["detail"]

    def test_update_profile_success(self, client, mock_db_connection, user_profile_data):
        """Test successful profile update."""
        headers = {
            "X-User-ID": "test-user-id",
            "X-User-Username": "testuser",
            "X-User-Email": "test@example.com"
        }
        response = client.put("/me", json=user_profile_data, headers=headers)

        assert response.status_code == 200

    def test_update_profile_partial_data(self, client, mock_db_connection):
        """Test profile update with partial data."""
        headers = {
            "X-User-ID": "test-user-id",
            "X-User-Username": "testuser",
            "X-User-Email": "test@example.com"
        }
        partial_data = {"first_name": "Jane"}
        response = client.put("/me", json=partial_data, headers=headers)

        assert response.status_code == 200

    def test_update_profile_invalid_data(self, client, mock_db_connection):
        """Test profile update with invalid data."""
        headers = {
            "X-User-ID": "test-user-id",
            "X-User-Username": "testuser",
            "X-User-Email": "test@example.com"
        }
        invalid_data = {"invalid_field": "value"}
        response = client.put("/me", json=invalid_data, headers=headers)

        assert response.status_code == 200  # Should still work, just ignore invalid fields

    def test_update_profile_database_error(self, client, user_profile_data):
        """Test profile update with database error."""
        headers = {
            "X-User-ID": "test-user-id",
            "X-User-Username": "testuser",
            "X-User-Email": "test@example.com"
        }
        with patch('main.psycopg2.connect', side_effect=Exception("DB error")):
            response = client.put("/me", json=user_profile_data, headers=headers)

            assert response.status_code == 500
            assert "Internal server error" in response.json()["detail"]


class TestKafkaIntegration:
    """Test Kafka Integration."""

    def test_kafka_consumer_creation(self, mock_env):
        """Test Kafka consumer is created properly."""
        from main import get_kafka_consumer

        # Ensure the global consumer is None to force creation
        import main
        original_consumer = main.kafka_consumer
        main.kafka_consumer = None

        try:
            with patch('main.KafkaConsumer') as mock_consumer:
                mock_instance = Mock()
                mock_consumer.return_value = mock_instance

                consumer = get_kafka_consumer()

                assert consumer is not None
                # Verify consumer was created with correct parameters
                mock_consumer.assert_called_once()
        finally:
            # Restore original consumer
            main.kafka_consumer = original_consumer

    def test_kafka_message_processing(self, mock_db_connection, kafka_message):
        """Test processing of Kafka user registration message."""
        from main import create_user_profile_from_event

        # Test the message processing function
        result = create_user_profile_from_event(kafka_message)

        # The function doesn't return anything, but we can check if it was called without errors
        assert result is None


class TestIntegration:
    """Test Integration Scenarios."""

    def test_full_profile_workflow(self, client, mock_db_connection, user_profile_data):
        """Test complete profile management workflow."""
        headers = {
            "X-User-ID": "test-user-id",
            "X-User-Username": "testuser",
            "X-User-Email": "test@example.com"
        }
        # Get initial profile
        get_response = client.get("/me", headers=headers)
        assert get_response.status_code == 200

        # Update profile
        update_response = client.put("/me", json=user_profile_data, headers=headers)
        assert update_response.status_code == 200

        # Verify update
        get_updated_response = client.get("/me", headers=headers)
        assert get_updated_response.status_code == 200

    def test_health_check_integration(self, client, mock_db_connection):
        """Test health check with all components."""
        with patch('main.kafka_consumer', Mock()):
            response = client.get("/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["database"] == "connected"
            assert data["kafka"] == "connected"


class TestErrorHandling:
    """Test Error Handling."""

    def test_invalid_json(self, client):
        """Test handling of invalid JSON."""
        headers = {
            "X-User-ID": "test-user-id",
            "X-User-Username": "testuser",
            "X-User-Email": "test@example.com"
        }
        response = client.put("/me", data="invalid json", headers=headers)

        assert response.status_code == 422

    def test_method_not_allowed(self, client):
        """Test method not allowed."""
        headers = {
            "X-User-ID": "test-user-id",
            "X-User-Username": "testuser",
            "X-User-Email": "test@example.com"
        }
        response = client.patch("/me", headers=headers)

        assert response.status_code == 405

    def test_not_found(self, client):
        """Test not found endpoint."""
        headers = {
            "X-User-ID": "test-user-id",
            "X-User-Username": "testuser",
            "X-User-Email": "test@example.com"
        }
        response = client.get("/nonexistent", headers=headers)

        assert response.status_code == 404
