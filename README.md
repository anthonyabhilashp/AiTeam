# AI Software Generator Platform

# AI Software Generator Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)](https://docker.com)
[![Kong](https://img.shields.io/badge/Kong-3.4-000000)](https://konghq.com)
[![Keycloak](https://img.shields.io/badge/Keycloak-24.0-000000)](https://www.keycloak.org)

An enterprise-grade SaaS platform foundation with Kong API Gateway and Keycloak authentication. Currently implementing core authentication and API management services, with AI-powered software generation capabilities planned for future releases.

**Currently focusing on authentication and API gateway foundation. Full AI software generation platform coming soon!**

## 🛠️ Built With

### Core Technologies
- **Kong**: Enterprise API gateway and microservices management
- **Keycloak**: Open-source identity and access management
- **PostgreSQL**: Advanced open-source database
- **Docker**: Containerization platform
- **Python**: Backend services with FastAPI framework
- **pytest**: Comprehensive testing framework

### Infrastructure
- **Docker Compose**: Multi-container application management
- **Makefile**: Build automation and development workflows
- **Git**: Version control and collaboration

### Security & Authentication
- **JWT**: JSON Web Tokens for secure API authentication
- **OAuth 2.0**: Authorization framework with Keycloak
- **CORS**: Cross-origin resource sharing configuration

[🚀 Quick Start](#-quick-start) | [📖 Documentation](docs/) | [🔧 Auth Service](saas-devgen/auth-service/) | [🌐 Gateway Service](saas-devgen/gateway-service/)tps://docker.com)
[![Kubernetes](https://img.shields.io/badge/kubernetes-%23326ce5.svg?style=flat&logo=kubernetes&logoColor=white)](https://kubernetes.io)

An enterprise-grade SaaS platform that automatically generates production-ready software from natural language requirements using AI-powered agents.

## 🌟 Features

### Core Capabilities
- **Kong API Gateway**: Enterprise-grade API management with authentication, routing, and rate limiting
- **Keycloak Authentication**: Complete identity management with JWT tokens and role-based access control
- **Docker-based Architecture**: Containerized microservices with proper isolation
- **PostgreSQL Integration**: Robust database backend for user and session management
- **Comprehensive Testing**: Full test coverage with unit, integration, and security tests

### Current Services
- **Auth Service**: User authentication, registration, JWT token management
- **Gateway Service**: API routing, request transformation, security plugins
- **Database Layer**: PostgreSQL with connection pooling and migrations
- **Monitoring**: Health checks and service discovery

### Enterprise Features
- **Security**: JWT authentication, rate limiting, CORS configuration
- **Scalability**: Docker-based deployment with horizontal scaling support
- **Monitoring**: Health endpoints and service status monitoring
- **Testing**: Comprehensive test suite with 50+ tests across services

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.10+
- 8GB RAM minimum

### 1. Clone and Setup
```bash
git clone https://github.com/anthonyabhilashp/AiTeam.git
cd AiTeam

# Copy environment template
cp .env.example .env

# Edit environment variables
nano .env
```

### 2. Start the Platform
```bash
# Start all services
make up

# Or use Docker Compose
docker-compose up -d
```

### 3. Access the Services
```bash
# Kong API Gateway
open http://localhost:8000

# Kong Admin Interface
open http://localhost:8002

# Keycloak Admin Console
open http://localhost:8080

# Health Check
curl http://localhost:8001/status
```

### 4. Test Authentication
```bash
# Login to Keycloak
curl -X POST http://localhost:8080/realms/master/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password&client_id=admin-cli&username=admin&password=admin"

# Use JWT token with API Gateway
curl -X GET http://localhost:8000/auth/user \
  -H "Authorization: Bearer your-jwt-token"
```

## 📋 Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Request  │───▶│  API Gateway    │───▶│  Auth Service   │
│                 │    │  (Kong)         │    │  (Keycloak)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                               ┌─────────────────┐
                                               │  JWT            │
                                               │  Authentication │
                                               │  & Authorization│
                                               └─────────────────┘
```

## 🏗️ Service Components

### Core Services
- **API Gateway**: Kong-based API gateway with routing, authentication, and rate limiting
- **Auth Service**: Identity management with Keycloak integration and JWT tokens

### Infrastructure
- **PostgreSQL**: Primary database for user and session data
- **Kong**: API gateway and reverse proxy
- **Keycloak**: Identity and access management

## 🔧 Configuration

### Environment Variables

#### Required
```bash
# Database
POSTGRES_USER=devgen
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=devgen

# Kong Configuration
KONG_DATABASE=postgres
KONG_PG_HOST=postgres
KONG_PG_PORT=5432
KONG_PG_USER=devgen
KONG_PG_PASSWORD=your_secure_password

# Keycloak Configuration
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=your_secure_keycloak_password
```

### Docker Compose Setup

```yaml
version: '3.8'
services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}

  kong:
    image: kong:3.4
    environment:
      KONG_DATABASE: postgres
      KONG_PG_HOST: postgres
      KONG_PG_PORT: 5432
      KONG_PG_USER: ${KONG_PG_USER}
      KONG_PG_PASSWORD: ${KONG_PG_PASSWORD}
    ports:
      - "8000:8000"  # Proxy
      - "8001:8001"  # Admin API
      - "8002:8002"  # Admin GUI

  keycloak:
    image: quay.io/keycloak/keycloak:24.0
    environment:
      KEYCLOAK_ADMIN: ${KEYCLOAK_ADMIN}
      KEYCLOAK_ADMIN_PASSWORD: ${KEYCLOAK_ADMIN_PASSWORD}
    command: start-dev
    ports:
      - "8080:8080"
```

## 📖 Usage Examples

### 1. Authentication Flow

```bash
# Login to get JWT token
curl -X POST http://localhost:8080/realms/master/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password&client_id=admin-cli&username=admin&password=admin"

# Use JWT token for API access
curl -X GET http://localhost:8000/auth/user \
  -H "Authorization: Bearer your-jwt-token"
```

### 2. Gateway Health Check

```bash
# Check Kong status
curl http://localhost:8001/status

# Check gateway health
curl http://localhost:8000/health
```

### 3. API Routing

```bash
# Access auth service through gateway
curl -X GET http://localhost:8000/auth/user \
  -H "Authorization: Bearer your-jwt-token"

# Kong admin interface
open http://localhost:8002
```

## 🧪 Testing

### Run All Tests
```bash
make test-all
```

### Run Service-Specific Tests
```bash
# Auth Service tests (comprehensive authentication and security testing)
make test-auth-service

# Gateway Service tests (Kong API gateway testing)
make test-gateway-service
```

### Test Coverage
```bash
# Generate coverage report
make coverage

# View HTML report
open htmlcov/index.html
```

## 🚀 Deployment

### Development
```bash
# Start services
make up

# View logs
make logs

# Stop services
make down
```

### Production
```bash
# Build production images
make build-prod

# Deploy with Docker Compose
docker-compose -f docker-compose.prod.yml up -d
```

## 📊 Monitoring

### Health Checks
```bash
# Kong health
curl http://localhost:8001/status

# Auth service health
curl http://localhost:8000/auth/health

# Overall system health
curl http://localhost:8000/health
```

### Kong Admin Interface
```bash
# Access Kong Manager
open http://localhost:8002

# Kong Admin API
curl http://localhost:8001/services
curl http://localhost:8001/routes
```

## 🔒 Security

### Authentication & Authorization
- JWT-based authentication with Keycloak integration
- Kong JWT plugin for API gateway authentication
- Role-based access control (RBAC)
- Secure token management

### Network Security
- HTTPS/TLS encryption (configurable)
- API rate limiting with Kong
- Request/response transformation
- CORS configuration

## 🤝 Contributing

### Development Setup
```bash
# Clone repository
git clone https://github.com/anthonyabhilashp/AiTeam.git
cd AiTeam

# Start development environment
make dev-up

# Run tests
make test-auth-service
make test-gateway-service
```

### Code Standards
- Follow PEP 8 for Python code
- Write comprehensive unit tests
- Update documentation for changes
- Use type hints and docstrings

## 📚 Documentation

### Available Documentation
- [API Reference](docs/API_REFERENCE.md) - Complete API documentation
- [Development Setup](docs/DEVELOPMENT_SETUP.md) - Local development guide
- [Auth Service Guide](saas-devgen/auth-service/README.md) - Authentication service details
- [Gateway Service Guide](saas-devgen/gateway-service/README.md) - API gateway details

### API Documentation
- **Kong Admin API**: http://localhost:8001/docs
- **Keycloak Admin Console**: http://localhost:8080
- **Kong Manager**: http://localhost:8002

## 🏢 Current Status

### ✅ Working Services
- **Auth Service**: Complete authentication with Keycloak, JWT tokens, user management
- **Gateway Service**: Kong-based API gateway with routing, authentication, rate limiting

### 🔄 In Development
- **Orchestrator Service**: AI-powered requirement analysis (planned)
- **Codegen Service**: Automated code generation (planned)
- **Executor Service**: Sandbox execution environment (planned)
- **Storage Service**: File and artifact management (planned)
- **Audit Service**: Logging and telemetry (planned)

### 📋 Next Steps
1. Complete orchestrator service for AI requirement analysis
2. Implement codegen service with MetaGPT integration
3. Add executor service for secure code execution
4. Integrate storage service for project management
5. Deploy audit service for comprehensive logging

---

**Currently focusing on authentication and API gateway foundation. Full AI software generation platform coming soon!**

[🚀 Quick Start](#-quick-start) | [📖 Documentation](docs/) | [� Auth Service](saas-devgen/auth-service/) | [� Gateway Service](saas-devgen/gateway-service/)
