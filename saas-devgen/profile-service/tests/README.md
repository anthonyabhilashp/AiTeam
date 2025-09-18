# Profile Service Tests

This directory contains comprehensive tests for the Profile Service component of the AI Team SaaS platform.

## Test Structure

```
tests/
├── conftest.py          # Test configuration and fixtures
├── test_profile.py      # Main profile service endpoint tests
└── test_runner.py       # Test runner script
```

## Test Coverage

### Health Endpoints
- ✅ Health check endpoint (`/health`)
- ✅ Database connectivity testing
- ✅ Kafka connectivity testing
- ✅ Error handling for connection failures

### Profile Management
- ✅ Get user profile (`GET /me`)
- ✅ Update user profile (`PUT /me`)
- ✅ Authentication and authorization
- ✅ Input validation
- ✅ Database error handling

### Kafka Integration
- ✅ Consumer creation and configuration
- ✅ Message processing for user registration
- ✅ Consumer thread management
- ✅ Event-driven profile creation

### Authentication
- ✅ JWT token validation
- ✅ Keycloak integration
- ✅ Authorization middleware
- ✅ Token error handling

### Error Handling
- ✅ Invalid JSON payloads
- ✅ Method not allowed
- ✅ Not found endpoints
- ✅ Database connection errors
- ✅ Authentication failures

## Running Tests

### Run All Tests
```bash
# From profile-service directory
python tests/test_runner.py

# Or using pytest directly
pytest tests/ --verbose --cov=main --cov-report=html
```

### Run Specific Test Classes
```bash
# Test only health endpoints
pytest tests/test_profile.py::TestProfileHealth -v

# Test only profile endpoints
pytest tests/test_profile.py::TestProfileEndpoints -v

# Test only Kafka integration
pytest tests/test_profile.py::TestKafkaIntegration -v
```

### Generate Coverage Report
```bash
# Generate HTML coverage report
pytest tests/ --cov=main --cov-report=html

# View coverage report
open htmlcov/index.html
```

## Test Fixtures

### Database Fixtures
- `mock_db_connection`: Mocks PostgreSQL database connection
- `mock_cursor`: Mocks database cursor for queries

### Authentication Fixtures
- `valid_jwt_token`: Valid JWT token for testing
- `mock_jwt_decode`: Mocks JWT token decoding

### Kafka Fixtures
- `mock_kafka_consumer`: Mocks Kafka consumer
- `kafka_message`: Sample user registration message

### API Fixtures
- `client`: FastAPI test client
- `user_profile_data`: Sample profile update data

## Mock Strategy

The tests use comprehensive mocking to:
- Isolate unit tests from external dependencies
- Test error conditions safely
- Ensure fast test execution
- Provide predictable test data

### External Dependencies Mocked
- PostgreSQL database connections
- Kafka message broker
- Keycloak authentication service
- JWT token validation
- HTTP requests for Keycloak keys

## Test Data

### Sample User Profile
```json
{
  "id": "test-user-id",
  "username": "testuser",
  "email": "test@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### Sample JWT Token
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0LXVzZXItaWQiLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiJ0ZXN0dXNlciIsImVtYWlsIjoidGVzdEBleGFtcGxlLmNvbSJ9.test-signature
```

## Integration Testing

The test suite includes integration tests that verify:
- End-to-end API workflows
- Component interaction
- Error propagation
- Health check functionality

## Continuous Integration

These tests are designed to run in CI/CD pipelines and provide:
- Fast feedback on code changes
- Regression testing
- Coverage reporting
- Automated test execution

## Dependencies

Test dependencies are specified in `requirements.txt`:
- pytest: Testing framework
- pytest-cov: Coverage reporting
- fastapi: API framework
- httpx: HTTP client for testing
- kafka-python: Kafka client
- psycopg2: PostgreSQL client

## Best Practices

The test suite follows these best practices:
- ✅ Isolated unit tests
- ✅ Comprehensive mocking
- ✅ Clear test naming
- ✅ Proper fixture usage
- ✅ Error condition testing
- ✅ Code coverage reporting
- ✅ Fast execution
- ✅ Maintainable test code
