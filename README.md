# AI Software Generator Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)](https://docker.com)
[![Keycloak](https://img.shields.io/badge/Keycloak-24.0-000000)](https://www.keycloak.org)
[![Kafka](https://img.shields.io/badge/Apache%20Kafka-7.4-000?style=flat&logo=apachekafka)](https://kafka.apache.org/)

An enterprise-grade SaaS platform that automatically generates production-ready software from natural language requirements using AI-powered agents and microservices architecture.

## 🌟 Features

### Core Capabilities
- **FastAPI Gateway**: High-performance API gateway with authentication, routing, and request proxying
- **Keycloak Authentication**: Complete identity management with JWT tokens and role-based access control
- **Kafka Event Streaming**: Asynchronous event-driven architecture for user registration and profile management
- **PostgreSQL Integration**: Robust database backend with Flyway migrations
- **Docker-based Microservices**: Containerized services with proper isolation and scalability
- **Comprehensive Testing**: Full test coverage with unit, integration, and API tests

### Current Services
- **Gateway Service**: API routing, Keycloak authentication, JWT validation, user registration
- **Profile Service**: User profile management with Kafka event consumption
- **Infrastructure**: PostgreSQL, Keycloak, Kafka, MinIO, Loki

### Enterprise Features
- **Security**: JWT authentication, CORS configuration, secure token management
- **Scalability**: Docker-based deployment with horizontal scaling support
- **Event-Driven**: Kafka integration for asynchronous processing
- **Monitoring**: Health checks, structured logging, and service status monitoring
- **Testing**: Comprehensive test suite with API documentation

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- 8GB RAM minimum

### 1. Clone and Setup
```bash
git clone https://github.com/anthonyabhilashp/AiTeam.git
cd AiTeam

# Environment variables are already configured in .env
# Edit if needed for your setup
nano .env
```

### 2. Start the Platform
```bash
# Start all infrastructure services
docker compose up -d postgres keycloak kafka zookeeper minio loki

# Initialize database
docker compose up db-init

# Start application services
docker compose up -d gateway-service profile-service

# Or start everything at once
make up-all
```

### 3. Access the Services
```bash
# API Gateway (FastAPI)
open http://localhost:8000/docs  # Interactive API documentation

# Keycloak Admin Console
open http://localhost:8080

# MinIO Console
open http://localhost:9001

# Health Check
curl http://localhost:8000/health
```

## 📋 Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Request  │───▶│  API Gateway    │───▶│ Profile Service │
│                 │    │  (FastAPI)      │    │  (FastAPI)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Keycloak      │    │   PostgreSQL    │    │     Kafka       │
│ Authentication  │    │   Database      │    │ Event Streaming │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## �️ Service Components

### Core Services
- **Gateway Service**: FastAPI-based API gateway with Keycloak JWT authentication, user registration, and request routing
- **Profile Service**: User profile management with Kafka consumer for registration events

### Infrastructure
- **PostgreSQL**: Primary database with Flyway migrations
- **Keycloak**: Identity and access management with JWT tokens
- **Kafka**: Event streaming for asynchronous processing
- **MinIO**: Object storage for files and artifacts
- **Loki**: Log aggregation and monitoring

## 🔧 Configuration

### Environment Variables (.env)

```bash
# Database
POSTGRES_USER=devgen
POSTGRES_PASSWORD=devgen
POSTGRES_DB=devgen

# Keycloak
KEYCLOAK_URL=http://keycloak:8080
KEYCLOAK_REALM=master
KEYCLOAK_CLIENT_ID=admin-cli
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=admin

# Kafka
KAFKA_BROKER_URL=kafka:29092
KAFKA_TOPIC_USER_REGISTRATION=user-registration-events

# MinIO
MINIO_ROOT_USER=admin
MINIO_ROOT_PASSWORD=admin123456

# Service URLs
PROFILE_SERVICE_URL=http://profile-service:8005
```

## 📖 API Documentation

### Gateway Service APIs

#### Authentication Endpoints

**POST /auth/login**
- **Description**: Authenticate user with Keycloak
- **Request Body**:
```json
{
  "username": "admin",
  "password": "admin"
}
```
- **Response**:
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzUxMiIs...",
  "token_type": "Bearer"
}
```

**POST /auth/register**
- **Description**: Register new user and send Kafka event
- **Request Body**:
```json
{
  "username": "newuser",
  "email": "user@example.com",
  "password": "securepassword",
  "first_name": "John",
  "last_name": "Doe"
}
```
- **Response**:
```json
{
  "message": "User registered successfully",
  "user_id": "uuid-string"
}
```

**GET /auth/user**
- **Description**: Get current user information
- **Headers**: `Authorization: Bearer <token>`
- **Response**:
```json
{
  "user_id": "uuid-string",
  "username": "admin",
  "email": "admin@example.com",
  "roles": ["admin"]
}
```

#### Proxy Endpoints

**GET /profile/{path}**
- **Description**: Proxy requests to profile service
- **Headers**: `Authorization: Bearer <token>`

**GET /health**
- **Description**: Gateway health check
- **Response**:
```json
{
  "status": "healthy"
}
```

### Profile Service APIs

**GET /health**
- **Description**: Profile service health check
- **Response**:
```json
{
  "status": "healthy",
  "service": "profile-service",
  "database": "connected",
  "kafka": "connected"
}
```

## 🧪 Testing

### Run All Tests
```bash
# Run tests for all services
make test-all

# Run specific service tests
make test-gateway-service
make test-profile-service
```

### API Testing Examples

```bash
# Test gateway health
curl http://localhost:8000/health

# Test user login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}'

# Test user registration
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "password123"}'

# Test profile service through gateway
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/profile/health
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
# Start all services
make up-all

# View logs
make logs

# Stop services
make down-all
```

### Production
```bash
# Build production images
make build-all

# Deploy with Docker Compose
docker compose -f docker-compose.prod.yml up -d
```

## 📊 Monitoring

### Health Checks
```bash
# Gateway health
curl http://localhost:8000/health

# Profile service health
curl http://localhost:8000/profile/health

# Infrastructure health
curl http://localhost:8080/realms/master/.well-known/openid-connect-configuration
```

### Service Logs
```bash
# View all service logs
make logs-all

# View specific service logs
docker compose logs gateway-service
docker compose logs profile-service
```

## � Security

### Authentication & Authorization
- JWT-based authentication with Keycloak integration
- Role-based access control (RBAC)
- Secure token management with expiration
- CORS configuration for cross-origin requests

### Network Security
- HTTPS/TLS encryption (configurable)
- API request validation
- Secure password hashing in Keycloak
- Event-driven security with Kafka

## 🤝 Contributing

### Development Setup
```bash
# Clone repository
git clone https://github.com/anthonyabhilashp/AiTeam.git
cd AiTeam

# Start development environment
make up-all

# Run tests
make test-gateway-service
make test-profile-service
```

### Code Standards
- Follow PEP 8 for Python code
- Write comprehensive unit tests
- Update API documentation for changes
- Use type hints and docstrings

## 📚 Documentation

### Available Documentation
- [API Reference](docs/API_REFERENCE.md) - Complete API documentation
- [Development Setup](docs/DEVELOPMENT_SETUP.md) - Local development guide
- [Gateway Service Guide](saas-devgen/gateway-service/README.md) - API gateway details
- [Profile Service Guide](saas-devgen/profile-service/README.md) - Profile service details

### Interactive API Documentation
- **Gateway Service**: http://localhost:8000/docs (FastAPI Swagger UI)
- **Keycloak Admin Console**: http://localhost:8080
- **MinIO Console**: http://localhost:9001

## 🏢 Current Status

### ✅ Working Services
- **Gateway Service**: FastAPI-based API gateway with Keycloak authentication, JWT validation, user registration, and Kafka events
- **Profile Service**: User profile management with Kafka event consumption and database integration

### 🔄 In Development
- **Orchestrator Service**: AI-powered requirement analysis and task breakdown
- **Codegen Service**: Automated code generation with MetaGPT integration
- **Executor Service**: Secure sandbox execution environment
- **Storage Service**: File and artifact management with MinIO
- **Audit Service**: Comprehensive logging and telemetry with Loki

### 📋 Next Steps
1. Complete orchestrator service for AI requirement analysis
2. Implement codegen service with MetaGPT integration
3. Add executor service for secure code execution
4. Integrate storage service for project management
5. Deploy audit service for comprehensive logging

---

**🚀 Ready for AI software generation! Core authentication and API gateway foundation complete.**

[🚀 Quick Start](#-quick-start) | [📖 API Documentation](#-api-documentation) | [🧪 Testing](#-testing) | [🏗️ Architecture](#-architecture)
curl http://localhost:8001/status
```

### 4. Test Authentication
```bash
# Login to get JWT token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}'

# Use JWT token for API access
curl -X GET http://localhost:8000/auth/user \
  -H "Authorization: Bearer your-jwt-token"

# Register new user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "password123"}'
```

## 📋 Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Request  │───▶│  API Gateway    │───▶│ Profile Service │
│                 │    │  (FastAPI)      │    │  (FastAPI)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Keycloak      │    │   PostgreSQL    │    │     Kafka       │
│ Authentication  │    │   Database      │    │ Event Streaming │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🏗️ Service Components

### Core Services
- **Gateway Service**: FastAPI-based API gateway with Keycloak JWT authentication, user registration, and request routing
- **Profile Service**: User profile management with Kafka event consumption

### Infrastructure
- **PostgreSQL**: Primary database with Flyway migrations
- **Keycloak**: Identity and access management with JWT tokens
- **Kafka**: Event streaming for asynchronous processing
- **MinIO**: Object storage for files and artifacts
- **Loki**: Log aggregation and monitoring

## 🔧 Configuration

### Environment Variables (.env)

```bash
# Database
POSTGRES_USER=devgen
POSTGRES_PASSWORD=devgen
POSTGRES_DB=devgen

# Keycloak
KEYCLOAK_URL=http://keycloak:8080
KEYCLOAK_REALM=master
KEYCLOAK_CLIENT_ID=admin-cli
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=admin

# Kafka
KAFKA_BROKER_URL=kafka:29092
KAFKA_TOPIC_USER_REGISTRATION=user-registration-events

# MinIO
MINIO_ROOT_USER=admin
MINIO_ROOT_PASSWORD=admin123456

# Service URLs
PROFILE_SERVICE_URL=http://profile-service:8005
```

## 📖 API Documentation

### Gateway Service APIs

#### Authentication Endpoints

**POST /auth/login**
- **Description**: Authenticate user with Keycloak
- **Request Body**:
```json
{
  "username": "admin",
  "password": "admin"
}
```
- **Response**:
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzUxMiIs...",
  "token_type": "Bearer"
}
```

**POST /auth/register**
- **Description**: Register new user and send Kafka event
- **Request Body**:
```json
{
  "username": "newuser",
  "email": "user@example.com",
  "password": "securepassword",
  "first_name": "John",
  "last_name": "Doe"
}
```
- **Response**:
```json
{
  "message": "User registered successfully",
  "user_id": "uuid-string"
}
```

**GET /auth/user**
- **Description**: Get current user information
- **Headers**: `Authorization: Bearer <token>`
- **Response**:
```json
{
  "user_id": "uuid-string",
  "username": "admin",
  "email": "admin@example.com",
  "roles": ["admin"]
}
```

#### Proxy Endpoints

**GET /profile/{path}**
- **Description**: Proxy requests to profile service
- **Headers**: `Authorization: Bearer <token>`

**GET /health**
- **Description**: Gateway health check
- **Response**:
```json
{
  "status": "healthy"
}
```

### Profile Service APIs

**GET /health**
- **Description**: Profile service health check
- **Response**:
```json
{
  "status": "healthy",
  "service": "profile-service",
  "database": "connected",
  "kafka": "connected"
}
```

## 🧪 Testing

### Run All Tests
```bash
# Run tests for all services
make test-all

# Run specific service tests
make test-gateway-service
make test-profile-service
```

### API Testing Examples

```bash
# Test gateway health
curl http://localhost:8000/health

# Test user login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}'

# Test user registration
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "password123"}'

# Test profile service through gateway
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/profile/health
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
# Start all services
make up-all

# View logs
make logs

# Stop services
make down-all
```

### Production
```bash
# Build production images
make build-all

# Deploy with Docker Compose
docker compose -f docker-compose.prod.yml up -d
```

## 📊 Monitoring

### Health Checks
```bash
# Gateway health
curl http://localhost:8000/health

# Profile service health
curl http://localhost:8000/profile/health

# Infrastructure health
curl http://localhost:8080/realms/master/.well-known/openid-connect/configuration
```

### Service Logs
```bash
# View all service logs
make logs-all

# View specific service logs
docker compose logs gateway-service
docker compose logs profile-service
```

## 🔒 Security

### Authentication & Authorization
- JWT-based authentication with Keycloak integration
- Role-based access control (RBAC)
- Secure token management with expiration
- CORS configuration for cross-origin requests

### Network Security
- HTTPS/TLS encryption (configurable)
- API request validation
- Secure password hashing in Keycloak
- Event-driven security with Kafka

## 🤝 Contributing

### Development Setup
```bash
# Clone repository
git clone https://github.com/anthonyabhilashp/AiTeam.git
cd AiTeam

# Start development environment
make up-all

# Run tests
make test-gateway-service
make test-profile-service
```

### Code Standards
- Follow PEP 8 for Python code
- Write comprehensive unit tests
- Update API documentation for changes
- Use type hints and docstrings

## 📚 Documentation

### Available Documentation
- [API Reference](docs/API_REFERENCE.md) - Complete API documentation
- [Development Setup](docs/DEVELOPMENT_SETUP.md) - Local development guide
- [Gateway Service Guide](saas-devgen/gateway-service/README.md) - API gateway details
- [Profile Service Guide](saas-devgen/profile-service/README.md) - Profile service details

### Interactive API Documentation
- **Gateway Service**: http://localhost:8000/docs (FastAPI Swagger UI)
- **Keycloak Admin Console**: http://localhost:8080
- **MinIO Console**: http://localhost:9001

## 🏢 Current Status

### ✅ Working Services
- **Gateway Service**: FastAPI-based API gateway with Keycloak authentication, JWT validation, user registration, and Kafka events
- **Profile Service**: User profile management with Kafka event consumption and database integration

### 🔄 In Development
- **Orchestrator Service**: AI-powered requirement analysis and task breakdown
- **Codegen Service**: Automated code generation with MetaGPT integration
- **Executor Service**: Secure sandbox execution environment
- **Storage Service**: File and artifact management with MinIO
- **Audit Service**: Comprehensive logging and telemetry with Loki

### 📋 Next Steps
1. Complete orchestrator service for AI requirement analysis
2. Implement codegen service with MetaGPT integration
3. Add executor service for secure code execution
4. Integrate storage service for project management
5. Deploy audit service for comprehensive logging

---

**🚀 Ready for AI software generation! Core authentication and API gateway foundation complete.**

[🚀 Quick Start](#-quick-start) | [📖 API Documentation](#-api-documentation) | [🧪 Testing](#-testing) | [🏗️ Architecture](#-architecture)
