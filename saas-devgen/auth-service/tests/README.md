# Auth Service Test Suite

This directory contains a comprehensive test suite for the Authentication Service, covering unit tests, integration tests, security tests, and performance tests.

## Test Structure

```
tests/
├── conftest.py           # Test configuration and fixtures
├── test_auth.py          # Authentication endpoint tests
├── test_user.py          # User management endpoint tests
├── test_security.py      # Security-focused tests
├── test_integration.py   # Integration and system tests
└── test_runner.py        # Test execution script
```

## Test Categories

### Unit Tests (`test_auth.py`, `test_user.py`)
- **Authentication Tests**: Login, token validation, error handling
- **User Management Tests**: Registration, profile management, password changes
- **API Validation**: Request/response validation, error codes

### Security Tests (`test_security.py`)
- **Token Security**: Expiration, tampering detection, leakage prevention
- **Input Validation**: SQL injection, XSS, path traversal prevention
- **Authentication Security**: Role validation, session isolation
- **Error Handling**: Safe error messages, no information leakage

### Integration Tests (`test_integration.py`)
- **Full User Lifecycle**: Registration → Login → Profile → Password Change → Deletion
- **Concurrent Operations**: Multi-user scenarios, load testing
- **Cross-Service Data Consistency**: Database integrity, transaction handling
- **System Resilience**: Error recovery, graceful degradation

## Running Tests

### Using the Test Runner

```bash
# Run all tests
python test_runner.py all

# Run with verbose output
python test_runner.py all -v

# Run with coverage report
python test_runner.py all --coverage

# Run specific test categories
python test_runner.py unit
python test_runner.py integration
python test_runner.py security

# Run specific test files
python test_runner.py auth
python test_runner.py user

# Run specific test function
python test_runner.py test tests/test_auth.py test_login_success
```

### Using pytest Directly

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=main.py --cov-report=html tests/

# Run specific test categories
pytest -m "not integration" tests/  # Unit tests only
pytest -m integration tests/       # Integration tests only
pytest -m security tests/          # Security tests only

# Run specific test file
pytest tests/test_auth.py -v

# Run specific test function
pytest tests/test_auth.py::TestAuth::test_login_success -v
```

## Test Configuration

### Fixtures

The test suite uses pytest fixtures defined in `conftest.py`:

- **`client`**: FastAPI test client with database session
- **`test_db`**: In-memory SQLite database for testing
- **`test_user`**: Pre-created test user
- **`auth_token`**: Valid authentication token
- **`admin_token`**: Admin authentication token

### Test Database

Tests use an in-memory SQLite database to ensure:
- Fast test execution
- Isolated test environments
- No interference with production data
- Easy cleanup between tests

## Test Coverage

The test suite covers:

### Authentication Endpoints
- ✅ POST `/login` - User authentication
- ✅ POST `/register` - User registration
- ✅ GET `/user` - Get user profile
- ✅ PUT `/user/{user_id}` - Update user profile
- ✅ DELETE `/user/{user_id}` - Delete user
- ✅ POST `/user/change-password` - Password change
- ✅ GET `/health` - Health check

### Security Features
- ✅ JWT token validation and expiration
- ✅ Role-based access control (RBAC)
- ✅ Input sanitization and validation
- ✅ SQL injection prevention
- ✅ XSS prevention
- ✅ Path traversal prevention
- ✅ Error message safety

### Integration Scenarios
- ✅ Complete user lifecycle
- ✅ Concurrent user operations
- ✅ Database connection persistence
- ✅ Cross-service data consistency
- ✅ Error recovery and resilience
- ✅ Load distribution simulation

## Test Data

### Default Test User
- **Username**: `demo`
- **Password**: `demo123`
- **Email**: `demo@example.com`
- **Roles**: `["admin", "user"]`

### Test Utilities

The `TestUtils` class provides helper methods:
- `create_test_user()`: Create a test user via API
- `login_user()`: Login and return authentication token
- `make_authenticated_request()`: Make authenticated API calls

## Performance Testing

Performance tests are marked with `@pytest.mark.performance`:

```bash
# Run performance tests
python test_runner.py performance

# Or with pytest
pytest -m performance tests/
```

Performance tests measure:
- Response times under load
- Concurrent request handling
- Memory usage patterns
- Database connection efficiency

## Security Testing

Security tests focus on:
- **Authentication Bypass**: Attempting unauthorized access
- **Token Manipulation**: Testing token integrity
- **Input Validation**: Preventing injection attacks
- **Information Disclosure**: Ensuring error messages don't leak data
- **Session Management**: Proper session isolation

## Continuous Integration

For CI/CD pipelines, use:

```bash
# Run all tests with coverage
python test_runner.py all --coverage

# Exit with proper status codes
echo $?  # 0 for success, 1 for failure
```

## Test Reports

### Coverage Reports
Coverage reports are generated in HTML format:
```
htmlcov/
├── index.html      # Main coverage report
├── main_py.html    # File-specific coverage
└── ...            # Additional report files
```

### Test Output
Verbose test output includes:
- Test execution time
- Pass/fail status per test
- Error messages and stack traces
- Coverage statistics

## Best Practices

### Writing New Tests
1. Use descriptive test names: `test_user_registration_success`
2. Group related tests in classes: `class TestAuth`
3. Use fixtures for common setup: `@pytest.fixture`
4. Mark slow tests: `@pytest.mark.slow`
5. Test both success and failure scenarios
6. Verify edge cases and error conditions

### Test Organization
- Keep test files focused on specific functionality
- Use clear naming conventions
- Document complex test scenarios
- Maintain test independence (no shared state)

### Maintenance
- Update tests when API changes
- Keep test data realistic but minimal
- Regularly review and refactor tests
- Monitor test execution time

## Troubleshooting

### Common Issues

**Import Errors**
```bash
# Ensure proper Python path
export PYTHONPATH=/path/to/auth-service:$PYTHONPATH
```

**Database Connection Issues**
```bash
# Check if test database is properly initialized
pytest tests/conftest.py::test_db -v
```

**Test Failures**
```bash
# Run with detailed output
pytest tests/ -v -s

# Run specific failing test
pytest tests/test_auth.py::TestAuth::test_login_success -v -s
```

### Debug Mode
```bash
# Run tests with debug output
pytest tests/ -v -s --log-cli-level=DEBUG
```

## Contributing

When adding new tests:
1. Follow the existing naming conventions
2. Add appropriate markers for categorization
3. Include docstrings explaining test purpose
4. Update this README if adding new test categories
5. Ensure tests pass in CI/CD pipeline

## Dependencies

Test dependencies are listed in `requirements.txt`:
- pytest: Testing framework
- pytest-cov: Coverage reporting
- fastapi: API framework
- sqlalchemy: Database ORM
- httpx: HTTP client for testing

Install dependencies:
```bash
pip install -r requirements.txt
```
