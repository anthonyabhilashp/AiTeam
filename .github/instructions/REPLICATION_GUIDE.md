# Microservice Replication Guide

This guide provides step-by-step instructions for replicating the comprehensive Auth Service pattern across all microservices in the AI Software Generator platform.

## Overview

The Auth Service serves as a complete template for building enterprise-grade microservices with:
- UUID-based user identification
- Comprehensive API endpoints
- Enterprise documentation
- Full test coverage
- Security best practices
- Production-ready configuration

## Target Microservices

Apply this pattern to these services in priority order:

1. **Orchestrator Service** - Task breakdown and workflow management
2. **Codegen Service** - Code generation with MetaGPT integration
3. **Executor Service** - Secure code execution in sandboxed environment
4. **Storage Service** - File and data storage management
5. **Audit Service** - Comprehensive audit logging and compliance
6. **Profile Service** - User profile and preference management

## Replication Steps

### Step 1: Service Structure Setup

For each target service, create this directory structure:

```
saas-devgen/{service-name}/
├── main.py                    # Main FastAPI application
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Container configuration
├── start.sh                   # Startup script
├── docs/                      # Documentation
│   ├── README.md             # Service overview and setup
│   ├── FEATURES.md           # Feature documentation
│   └── api.yaml              # OpenAPI specification
├── tests/                     # Test suite
│   ├── conftest.py           # Test configuration
│   ├── test_{service}.py     # Service-specific tests
│   ├── test_security.py      # Security tests
│   ├── test_integration.py   # Integration tests
│   ├── test_runner.py        # Test execution script
│   └── README.md             # Test documentation
└── __pycache__/              # Python cache (auto-generated)
```

### Step 2: Core Implementation

#### 2.1 FastAPI Application Structure

Use this template for `main.py`:

```python
"""Service Name - Description."""
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import jwt
from shared.config import settings
from shared.logging_utils import setup_logger
from shared.database import get_db, create_tables
from shared.models import User, Tenant
from sqlalchemy.orm import Session

# Initialize logger
logger = setup_logger("service-name", "service-name.log")

app = FastAPI(title="Service Name", version="1.0.0")

# Security
security = HTTPBearer()

# Service-specific models and endpoints go here

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "service-name"
    }

# Add service-specific endpoints following the Auth Service pattern
```

#### 2.2 Database Models

Extend shared models in `shared/models.py` as needed:

```python
# Add service-specific models here
class ServiceModel(Base):
    """Base model for service-specific entities."""
    __tablename__ = "service_models"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

#### 2.3 Authentication & Authorization

Implement consistent auth patterns:

```python
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user."""
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=["HS256"])
        user_id = payload.get("user_id")

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### Step 3: API Endpoints Implementation

#### 3.1 CRUD Operations Pattern

Implement standard CRUD operations:

```python
@app.post("/entities")
async def create_entity(
    request: CreateEntityRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new entity."""
    # Implementation here

@app.get("/entities")
async def list_entities(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List entities."""
    # Implementation here

@app.get("/entities/{entity_id}")
async def get_entity(
    entity_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific entity."""
    # Implementation here

@app.put("/entities/{entity_id}")
async def update_entity(
    entity_id: UUID,
    request: UpdateEntityRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update entity."""
    # Implementation here

@app.delete("/entities/{entity_id}")
async def delete_entity(
    entity_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete entity."""
    # Implementation here
```

#### 3.2 Service-Specific Endpoints

Add endpoints specific to each service:

**Orchestrator Service:**
- POST `/tasks` - Create task
- GET `/tasks/{task_id}/status` - Get task status
- POST `/workflows` - Create workflow
- GET `/workflows/{workflow_id}/execute` - Execute workflow

**Codegen Service:**
- POST `/generate` - Generate code
- GET `/templates` - List code templates
- POST `/validate` - Validate generated code
- GET `/languages` - Supported languages

**Executor Service:**
- POST `/execute` - Execute code
- GET `/executions/{execution_id}/status` - Get execution status
- POST `/environments` - Create execution environment
- GET `/environments/{env_id}/logs` - Get execution logs

### Step 4: Documentation

#### 4.1 README.md Template

```markdown
# Service Name

Brief description of the service and its purpose.

## Features

- Feature 1
- Feature 2
- Feature 3

## API Endpoints

### Core Endpoints
- GET `/health` - Health check
- GET `/entities` - List entities
- POST `/entities` - Create entity

### Service-Specific Endpoints
- [List service-specific endpoints]

## Authentication

Uses JWT tokens from Auth Service for authentication.

## Configuration

Environment variables:
- `SERVICE_PORT` - Service port (default: 8000)
- `DATABASE_URL` - Database connection string
- `JWT_SECRET` - JWT secret key

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run service
python main.py

# Run tests
python tests/test_runner.py all
```

## Deployment

```bash
# Build Docker image
docker build -t service-name .

# Run container
docker run -p 8000:8000 service-name
```
```

#### 4.2 OpenAPI Specification

Create `docs/api.yaml` with comprehensive API documentation:

```yaml
openapi: 3.0.3
info:
  title: Service Name API
  version: 1.0.0
  description: API documentation for Service Name

servers:
  - url: http://localhost:8000
    description: Development server

security:
  - bearerAuth: []

paths:
  /health:
    get:
      summary: Health check
      responses:
        '200':
          description: Service is healthy

  # Add service-specific endpoints

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

  schemas:
    # Define request/response models
```

### Step 5: Test Suite Implementation

#### 5.1 Test Structure

Create comprehensive tests following the Auth Service pattern:

**test_service.py:**
```python
"""Service-specific unit tests."""
import pytest
from fastapi.testclient import TestClient

class TestService:
    """Test service functionality."""

    def test_create_entity_success(self, client, auth_token):
        """Test successful entity creation."""
        # Test implementation

    def test_get_entity_success(self, client, auth_token):
        """Test successful entity retrieval."""
        # Test implementation

    # Add more tests...
```

**test_security.py:**
```python
"""Security tests."""
import pytest

class TestSecurity:
    """Test security functionality."""

    def test_unauthorized_access_prevention(self, client):
        """Test prevention of unauthorized access."""
        # Test implementation

    def test_input_validation(self, client):
        """Test input validation and sanitization."""
        # Test implementation

    # Add more security tests...
```

**test_integration.py:**
```python
"""Integration tests."""
import pytest

class TestIntegration:
    """Test integration scenarios."""

    def test_full_workflow(self, client):
        """Test complete service workflow."""
        # Test implementation

    def test_concurrent_operations(self, client):
        """Test concurrent operations."""
        # Test implementation

    # Add more integration tests...
```

#### 5.2 Test Configuration

Use the same `conftest.py` pattern with service-specific fixtures:

```python
@pytest.fixture(scope="function")
def test_entity(db_session, test_tenant):
    """Create a test entity."""
    entity = ServiceEntity(
        id=str(uuid4()),
        tenant_id=test_tenant.id,
        # Add service-specific fields
    )
    db_session.add(entity)
    db_session.commit()
    db_session.refresh(entity)
    return entity
```

### Step 6: Docker Configuration

#### 6.1 Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

EXPOSE 8000

CMD ["python", "main.py"]
```

#### 6.2 docker-compose.yml (Service Level)

```yaml
version: '3.8'

services:
  service-name:
    build: .
    ports:
      - "8000:8000"
    environment:
      - SERVICE_PORT=8000
      - DATABASE_URL=postgresql://user:password@db:5432/dbname
      - JWT_SECRET=your-secret-key
    depends_on:
      - db
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=dbname
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

### Step 7: Configuration Management

#### 7.1 Environment Variables

Define service-specific environment variables in `shared/config.py`:

```python
# Service-specific settings
service_port: int = Field(default=8000, env="SERVICE_PORT")
service_timeout: int = Field(default=30, env="SERVICE_TIMEOUT")
service_workers: int = Field(default=4, env="SERVICE_WORKERS")

# Service-specific external service URLs
external_api_url: str = Field(default="http://external-api:8000", env="EXTERNAL_API_URL")
external_api_key: str = Field(default="", env="EXTERNAL_API_KEY")
```

#### 7.2 Logging Configuration

Configure structured logging in `shared/logging_utils.py`:

```python
def setup_logger(service_name: str, log_file: str) -> logging.Logger:
    """Setup structured logging for service."""
    logger = logging.getLogger(service_name)

    # Add service-specific log format
    formatter = logging.Formatter(
        f'%(asctime)s - {service_name} - %(levelname)s - %(message)s'
    )

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler for development
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    logger.setLevel(logging.INFO)
    return logger
```

### Step 8: Deployment Configuration

#### 8.1 Kubernetes Manifests

Create K8s manifests in `k8s/` directory:

**deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: service-name
spec:
  replicas: 3
  selector:
    matchLabels:
      app: service-name
  template:
    metadata:
      labels:
        app: service-name
    spec:
      containers:
      - name: service-name
        image: service-name:latest
        ports:
        - containerPort: 8000
        env:
        - name: SERVICE_PORT
          value: "8000"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: database-url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

**service.yaml:**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: service-name
spec:
  selector:
    app: service-name
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
```

### Step 9: Monitoring and Observability

#### 9.1 Health Checks

Implement comprehensive health checks:

```python
@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Comprehensive health check."""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "service-name",
        "checks": {}
    }

    # Database health check
    try:
        db.execute("SELECT 1")
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = "unhealthy"
        health_status["status"] = "unhealthy"

    # External service health check
    try:
        # Check external dependencies
        health_status["checks"]["external_services"] = "healthy"
    except Exception as e:
        health_status["checks"]["external_services"] = "unhealthy"
        health_status["status"] = "unhealthy"

    # Service-specific health checks
    # Add service-specific checks here

    return health_status
```

#### 9.2 Metrics

Add metrics endpoints for monitoring:

```python
from fastapi import Request
import time

@app.middleware("http")
async def add_metrics(request: Request, call_next):
    """Add request metrics."""
    start_time = time.time()

    response = await call_next(request)

    process_time = time.time() - start_time
    logger.info(
        f"Request: {request.method} {request.url.path} "
        f"Status: {response.status_code} "
        f"Duration: {process_time:.3f}s"
    )

    return response
```

### Step 10: Security Implementation

#### 10.1 Input Validation

Implement comprehensive input validation:

```python
from pydantic import BaseModel, validator
import re

class CreateEntityRequest(BaseModel):
    """Create entity request with validation."""
    name: str
    description: Optional[str] = None

    @validator('name')
    def name_must_be_valid(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Name cannot be empty')
        if len(v) > 100:
            raise ValueError('Name too long')
        # Prevent injection attacks
        if re.search(r'[<>]', v):
            raise ValueError('Invalid characters in name')
        return v.strip()
```

#### 10.2 Rate Limiting

Implement rate limiting:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

limiter = Limiter(key_func=get_remote_address)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

@app.post("/entities")
@limiter.limit("10/minute")
async def create_entity(request: CreateEntityRequest):
    """Create entity with rate limiting."""
    # Implementation
```

### Step 11: Error Handling

#### 11.1 Global Exception Handler

Implement consistent error handling:

```python
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "type": "http_exception"
            }
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Handle validation errors."""
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": 422,
                "message": "Validation error",
                "details": exc.errors(),
                "type": "validation_error"
            }
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": 500,
                "message": "Internal server error",
                "type": "internal_error"
            }
        }
    )
```

### Step 12: Performance Optimization

#### 12.1 Database Optimization

Implement efficient database queries:

```python
from sqlalchemy.orm import selectinload, joinedload

@app.get("/entities")
async def list_entities(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """List entities with pagination and eager loading."""
    query = db.query(Entity).options(
        selectinload(Entity.related_entities)
    ).offset(skip).limit(limit)

    entities = query.all()
    return {"entities": entities, "skip": skip, "limit": limit}
```

#### 12.2 Caching

Implement caching for frequently accessed data:

```python
from cachetools import TTLCache
import asyncio

cache = TTLCache(maxsize=1000, ttl=300)  # 5 minute TTL

@app.get("/entities/{entity_id}")
async def get_entity(entity_id: UUID, db: Session = Depends(get_db)):
    """Get entity with caching."""
    # Check cache first
    cache_key = f"entity:{entity_id}"
    if cache_key in cache:
        return cache[cache_key]

    # Fetch from database
    entity = db.query(Entity).filter(Entity.id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    # Cache the result
    cache[cache_key] = entity

    return entity
```

## Service-Specific Implementation Notes

### Orchestrator Service
- Implement task queue management
- Add workflow execution engine
- Include task status tracking
- Support for parallel task execution

### Codegen Service
- Integrate with MetaGPT framework
- Support multiple programming languages
- Implement code validation
- Add template management

### Executor Service
- Implement sandboxed execution
- Add resource limits and monitoring
- Support multiple runtimes
- Include execution result caching

### Storage Service
- Implement file upload/download
- Add metadata management
- Support for different storage backends
- Include access control

### Audit Service
- Implement comprehensive logging
- Add compliance reporting
- Support for different audit levels
- Include data retention policies

### Profile Service
- Implement user preferences
- Add profile customization
- Support for user avatars
- Include notification settings

## Quality Assurance

### Testing Checklist
- [ ] Unit tests for all endpoints
- [ ] Integration tests for workflows
- [ ] Security tests for vulnerabilities
- [ ] Performance tests under load
- [ ] Documentation completeness
- [ ] API specification accuracy

### Code Review Checklist
- [ ] Consistent error handling
- [ ] Input validation on all endpoints
- [ ] Authentication on protected routes
- [ ] Database query optimization
- [ ] Logging of important operations
- [ ] Comprehensive test coverage

### Deployment Checklist
- [ ] Docker image builds successfully
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] Health checks passing
- [ ] Monitoring configured
- [ ] Logs accessible

## Next Steps

1. Start with the Orchestrator Service as the next priority
2. Follow this guide step-by-step for each service
3. Update shared components as needed
4. Maintain consistency across all services
5. Regularly review and update the template based on lessons learned

This replication guide ensures all microservices follow the same high-quality standards established by the Auth Service, creating a cohesive and maintainable platform architecture.
