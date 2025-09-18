"""Test Configuration and Fixtures for Profile Service."""
import pytest
import os
import sys
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

# Add the parent directory to the Python path so we can import main
# Check if we're in Docker (production) or local development
if os.path.exists('/app'):
    sys.path.insert(0, '/app')
else:
    # Local development - add the profile-service directory
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
        'DATABASE_URL': 'postgresql://devgen:devgen@postgres:5432/devgen',
        'KEYCLOAK_URL': 'http://keycloak:8080',
        'KEYCLOAK_REALM': 'master',
        'KAFKA_BROKER_URL': 'kafka:29092',
        'KAFKA_TOPIC_USER_REGISTRATION': 'user-registration-events',
        'KAFKA_GROUP_ID': 'profile-service'
    }

    with patch.dict(os.environ, env_vars):
        yield env_vars


@pytest.fixture(scope="function")
def mock_db_connection():
    """Mock database connection."""
    with patch('main.psycopg2.connect') as mock_connect:
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor

        # Track SQL queries to determine appropriate response
        executed_queries = []

        # Track updated values
        updated_values = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'John',
            'last_name': 'Doe'
        }

        def mock_execute(query, params=None):
            executed_queries.append((query.strip(), params))

            # Parse UPDATE queries to track changes
            if query.strip().startswith("UPDATE"):
                # Extract SET clauses
                set_part = query.split("SET")[1].split("WHERE")[0].strip()
                set_clauses = [clause.strip() for clause in set_part.split(",")]

                for clause in set_clauses:
                    if "=" in clause:
                        field, value_placeholder = clause.split("=", 1)
                        field = field.strip()
                        if field in updated_values and params:
                            # Find the corresponding parameter
                            param_index = set_clauses.index(clause)
                            if param_index < len(params):
                                updated_values[field] = params[param_index]

        def mock_fetchone():
            if not executed_queries:
                return None

            last_query, params = executed_queries[-1]

            # Profile existence check
            if "SELECT user_id FROM aiteam.profiles WHERE user_id = %s" in last_query and len(params) == 1:
                return ('test-user-id',)  # Profile exists

            # Uniqueness checks (should return None for no conflicts)
            elif "WHERE username = %s AND user_id != %s" in last_query:
                return None  # Username available
            elif "WHERE email = %s AND user_id != %s" in last_query:
                return None  # Email available

            # Profile data retrieval
            elif "SELECT user_id, username, email, first_name, last_name, created_at, updated_at" in last_query:
                return ('test-user-id', updated_values['username'], updated_values['email'],
                       updated_values['first_name'], updated_values['last_name'],
                       '2024-01-01T00:00:00Z', '2024-01-01T00:00:00Z')

            # Default case
            return None

        mock_cursor.execute.side_effect = mock_execute
        mock_cursor.fetchone.side_effect = mock_fetchone
        mock_cursor.fetchall.return_value = []
        mock_connect.return_value = mock_conn
        yield mock_conn


@pytest.fixture(scope="function")
def mock_kafka_consumer():
    """Mock Kafka consumer."""
    with patch('kafka.KafkaConsumer') as mock_consumer:
        mock_instance = Mock()
        mock_consumer.return_value = mock_instance
        yield mock_instance


@pytest.fixture(scope="function")
def mock_jwt_decode():
    """Mock JWT decode function."""
    with patch('main.jwt.decode') as mock_decode:
        mock_decode.return_value = {
            'sub': 'test-user-id',
            'preferred_username': 'testuser',
            'email': 'test@example.com'
        }
        yield mock_decode


@pytest.fixture(scope="function")
def valid_jwt_token():
    """Valid JWT token for testing."""
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0LXVzZXItaWQiLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiJ0ZXN0dXNlciIsImVtYWlsIjoidGVzdEBleGFtcGxlLmNvbSJ9.test-signature"


@pytest.fixture(scope="function")
def user_profile_data():
    """Sample user profile data."""
    return {
        "username": "testuser",
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com"
    }


@pytest.fixture(scope="function")
def kafka_message():
    """Sample Kafka message for user registration."""
    return {
        "user_id": "test-user-id",
        "username": "testuser",
        "email": "test@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "timestamp": "2024-01-01T00:00:00Z"
    }
