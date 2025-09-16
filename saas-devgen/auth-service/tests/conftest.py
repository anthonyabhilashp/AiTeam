"""Test Configuration and Fixtures."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os

# Import the app and models
from main import app, get_db, Base, User, Tenant

# Create test database
TEST_DATABASE_URL = "sqlite:///./test_auth.db"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def test_db():
    """Create test database and tables."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    """Create test client."""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def demo_user(test_db):
    """Create a demo user for testing."""
    # Create default tenant
    tenant = Tenant(name="Default Organization", org_id="default")
    test_db.add(tenant)
    test_db.commit()
    test_db.refresh(tenant)

    # Create demo user
    user = User(
        username="demo",
        email="demo@example.com",
        password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6fMhJ4w8K",  # demo123
        tenant_id=tenant.id,
        roles='["admin", "user"]',
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant", back_populates="users")


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_db():
    """Create a test database."""
    # Use SQLite for testing
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create all tables
    TestBase.metadata.create_all(bind=engine)

    # Create a sessionmaker
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    yield TestingSessionLocal

    # Clean up
    TestBase.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(test_db):
    """Create a database session for each test."""
    session = test_db()

    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database session."""
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    # Override the database dependency
    app.dependency_overrides[get_db] = override_get_db

    # Mock the database engine to prevent startup table creation
    from unittest.mock import patch, MagicMock
    mock_engine = MagicMock()
    mock_engine.connect.return_value = MagicMock()

    # Patch the shared models to use our test models
    with patch('main.User', User), \
         patch('main.Tenant', Tenant), \
         patch('shared.database.engine', mock_engine), \
         patch('shared.database.create_tables'):  # Prevent table creation
        with TestClient(app) as test_client:
            yield test_client


@pytest.fixture(scope="function")
def test_tenant(db_session):
    """Create a test tenant."""
    tenant = Tenant(
        name="Test Tenant",
        org_id="test-org",
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    return tenant


@pytest.fixture(scope="function")
def test_user(db_session, test_tenant):
    """Create a test user."""
    from passlib.context import CryptContext
    import json

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    user = User(
        username="demo",
        email="demo@example.com",
        password_hash=pwd_context.hash("demo123"),  # Hash the password properly
        tenant_id=test_tenant.id,
        roles=json.dumps(["admin", "user"]),  # Convert list to JSON string
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_token(client, test_user):
    """Get an authentication token for the test user."""
    response = client.post("/login", json={
        "username": "demo",
        "password": "demo123"
    })
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture(scope="function")
def admin_token(client, test_user):
    """Get an admin authentication token."""
    # Assuming the test user has admin role
    response = client.post("/login", json={
        "username": "demo",
        "password": "demo123"
    })
    assert response.status_code == 200
    return response.json()["access_token"]


# Custom markers
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "security: marks tests as security tests")
    config.addinivalue_line("markers", "performance: marks tests as performance tests")


# Test utilities
class TestUtils:
    """Utility functions for tests."""

    @staticmethod
    def create_test_user(client, username=None, email=None, password=None):
        """Create a test user via API."""
        import time
        if username is None:
            username = f"testuser_{int(time.time())}"
        if email is None:
            email = f"{username}@example.com"
        if password is None:
            password = "SecurePass123!"

        response = client.post("/register", json={
            "username": username,
            "email": email,
            "password": password
        })
        return response, username, email, password

    @staticmethod
    def login_user(client, username, password):
        """Login a user and return token."""
        response = client.post("/login", json={
            "username": username,
            "password": password
        })
        if response.status_code == 200:
            return response.json()["access_token"]
        return None

    @staticmethod
    def make_authenticated_request(client, method, endpoint, token, **kwargs):
        """Make an authenticated request."""
        headers = kwargs.get('headers', {})
        headers['Authorization'] = f"Bearer {token}"
        kwargs['headers'] = headers

        if method.lower() == 'get':
            return client.get(endpoint, **kwargs)
        elif method.lower() == 'post':
            return client.post(endpoint, **kwargs)
        elif method.lower() == 'put':
            return client.put(endpoint, **kwargs)
        elif method.lower() == 'delete':
            return client.delete(endpoint, **kwargs)
        else:
            raise ValueError(f"Unsupported method: {method}")


# Make TestUtils available to all tests
@pytest.fixture(scope="session")
def test_utils():
    """Provide test utilities."""
    return TestUtils()
