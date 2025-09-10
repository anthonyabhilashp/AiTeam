# AI Software Generator Platform

Enterprise SaaS platform for automated software generation using AI agents.

## 🏗️ Architecture

The platform follows a microservices architecture with the following components:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   API Gateway   │    │  Auth Service    │    │  Orchestrator   │
│   Port: 8000    │    │  Port: 8001      │    │  Port: 8002     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ├───────────────────────┼───────────────────────┤
         │                       │                       │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Codegen Service │    │ Executor Service │    │ Storage Service │
│   Port: 8003    │    │   Port: 8004     │    │   Port: 8005    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Audit Service  │
                    │   Port: 8006    │
                    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.10+
- 8GB RAM minimum
- 10GB free disk space

### 1. Start the Platform

```bash
cd saas-devgen
chmod +x start-platform.sh
./start-platform.sh
```

### 2. Verify Installation

Visit http://localhost:8000/docs to see the API documentation.

### 3. Test the Platform

```bash
# Create a requirement
curl -X POST "http://localhost:8000/requirements" \
  -H "Content-Type: application/json" \
  -d '{
    "requirement": "Build a REST API for employee management with FastAPI"
  }'

# Check the generated tasks
curl "http://localhost:8000/requirements/1"

# Generate code
curl -X POST "http://localhost:8000/codegen/1" \
  -H "Content-Type: application/json" \
  -d '{
    "tasks": ["Design API endpoints", "Implement CRUD operations"],
    "language": "python",
    "framework": "fastapi"
  }'
```

## 🏗️ Services Overview

### 🌐 API Gateway (Port 8000)
- Single entry point for all client requests
- Request routing and load balancing
- Authentication and authorization
- Rate limiting and monitoring

### 🔐 Auth Service (Port 8001)
- JWT-based authentication
- Integration with Keycloak
- Multi-tenant user management
- Role-based access control (RBAC)

### 🎯 Orchestrator Service (Port 8002)
- Requirement intake and processing
- Task breakdown using AI PM agent
- Workflow orchestration
- Progress tracking

### 🛠️ Codegen Service (Port 8003)
- AI-powered code generation
- Template-based project scaffolding
- Support for multiple languages/frameworks
- Code quality validation

### ⚡ Executor Service (Port 8004)
- Secure sandbox execution
- Docker-based isolation
- Resource management
- Execution monitoring

### 💾 Storage Service (Port 8005)
- File and object storage using MinIO
- Project artifact management
- Metadata tracking
- Backup and versioning

### 📊 Audit Service (Port 8006)
- Comprehensive audit logging
- Compliance reporting
- Security event tracking
- OpenTelemetry integration

## 🏗️ Infrastructure Components

### Database (PostgreSQL)
- Multi-tenant data isolation
- ACID compliance
- Backup and recovery
- Connection pooling

### Object Storage (MinIO)
- S3-compatible API
- Distributed storage
- Data encryption
- Access policies

### Identity Management (Keycloak)
- Enterprise SSO
- User federation
- OAuth 2.0 / OpenID Connect
- Admin console

### Logging (Loki)
- Centralized log aggregation
- Query and alerting
- Retention policies
- Grafana integration

## 🔧 Configuration

### Environment Variables

```bash
# Database Configuration
POSTGRES_USER=devgen
POSTGRES_PASSWORD=secret
POSTGRES_DB=devgen

# MinIO Configuration
MINIO_ROOT_USER=admin
MINIO_ROOT_PASSWORD=admin123

# Keycloak Configuration
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=admin

# AI Configuration (Set in settings UI)
AI_PROVIDER=openai
AI_MODEL=gpt-4
```

### Service Configuration

Each service has its own configuration file and startup script:
- `auth-service/start.sh`
- `orchestrator/start.sh`
- `codegen-service/start.sh`
- `executor-service/start.sh`
- `storage-service/start.sh`
- `audit-service/start.sh`
- `api-gateway/start.sh`

## 📊 Monitoring and Logging

### Application Logs
- Location: `/logs/`
- Format: Structured JSON
- Rotation: Daily
- Retention: 30 days

### Health Checks
- All services expose `/health` endpoints
- Automatic health monitoring
- Alerting on failures
- Service discovery integration

### Metrics
- Prometheus-compatible metrics
- Performance monitoring
- Resource utilization
- Business metrics

## 🔒 Security

### Authentication
- JWT tokens with expiration
- Refresh token rotation
- Multi-factor authentication support
- Session management

### Authorization
- Role-based access control (RBAC)
- Resource-level permissions
- Tenant isolation
- API rate limiting

### Compliance
- Comprehensive audit logging
- Data encryption at rest and in transit
- GDPR compliance features
- SOC 2 Type II ready

## 🧪 Testing

### Unit Tests
```bash
cd tests
python -m pytest unit/
```

### Integration Tests
```bash
cd tests
python -m pytest integration/
```

### End-to-End Tests
```bash
cd tests
python -m pytest e2e/
```

## 📈 Scaling

### Horizontal Scaling
- Stateless service design
- Load balancer ready
- Database connection pooling
- Caching layer support

### Vertical Scaling
- Resource monitoring
- Auto-scaling policies
- Performance optimization
- Capacity planning

## 🛠️ Development

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export PYTHONPATH="/Users/a.pothula/workspace/unity/AiTeam:$PYTHONPATH"

# Start individual service
cd auth-service
uvicorn main:app --reload --port 8001
```

### Code Quality
- Black code formatting
- isort import sorting
- flake8 linting
- Type hints with mypy

### Database Migrations
```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head
```

## 📋 API Documentation

### Interactive API Docs
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI Spec: http://localhost:8000/openapi.json

### Example API Calls

#### Authentication
```bash
# Login
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}'

# Get user info
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/auth/user"
```

#### Requirements
```bash
# Create requirement
curl -X POST "http://localhost:8000/requirements" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"requirement": "Build a REST API for user management"}'

# Get requirement
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/requirements/1"
```

#### Code Generation
```bash
# Generate code
curl -X POST "http://localhost:8000/codegen/1" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "tasks": ["Design API", "Implement CRUD"],
    "language": "python",
    "framework": "fastapi"
  }'
```

#### Execution
```bash
# Execute code
curl -X POST "http://localhost:8000/executor/run" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "file:///path/to/generated/code",
    "command": "python -m pytest"
  }'
```

## 🚨 Troubleshooting

### Common Issues

#### Services won't start
- Check Docker is running
- Verify port availability
- Check log files in `/logs/`
- Ensure Python dependencies are installed

#### Database connection issues
- Verify PostgreSQL is running
- Check database credentials
- Ensure network connectivity
- Review connection pool settings

#### Authentication errors
- Verify Keycloak is running
- Check user credentials
- Validate JWT tokens
- Review auth service logs

### Log Analysis
```bash
# View all service logs
tail -f /Users/a.pothula/workspace/unity/AiTeam/logs/*.log

# View specific service
tail -f /Users/a.pothula/workspace/unity/AiTeam/logs/api-gateway.log

# Search for errors
grep -i error /Users/a.pothula/workspace/unity/AiTeam/logs/*.log
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the troubleshooting guide
