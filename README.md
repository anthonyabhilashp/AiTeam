# AI Software Generator Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)](https://docker.com)
[![Kubernetes](https://img.shields.io/badge/kubernetes-%23326ce5.svg?style=flat&logo=kubernetes&logoColor=white)](https://kubernetes.io)

An enterprise-grade SaaS platform that automatically generates production-ready software from natural language requirements using AI-powered agents.

## 🌟 Features

### Core Capabilities
- **AI-Powered Requirements Analysis**: Break down complex software requirements into actionable tasks
- **Automated Code Generation**: Generate production-ready code using MetaGPT and template systems
- **Secure Sandbox Execution**: Run and test generated code in isolated Docker environments
- **Multi-tenant Architecture**: Complete tenant isolation with RBAC and audit logging
- **Enterprise Integrations**: Support for PostgreSQL, MinIO, Keycloak, Redis, and more

### AI Integration
- **Multiple AI Providers**: OpenAI GPT-4, Anthropic Claude, and OpenRouter support
- **Intelligent Task Breakdown**: AI analyzes requirements and creates detailed task lists
- **Code Generation**: Generate complete applications with proper structure and dependencies
- **Fallback Mechanisms**: Graceful degradation when AI services are unavailable

### Enterprise Features
- **Audit Logging**: Complete audit trail with OpenTelemetry and Loki integration
- **Security**: JWT authentication, role-based access control, and secure sandboxing
- **Scalability**: Kubernetes-native deployment with horizontal pod autoscaling
- **Monitoring**: Comprehensive metrics and logging with Prometheus and Grafana
- **Backup & Recovery**: Automated database and file backups

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.10+
- 8GB RAM minimum

### 1. Clone and Setup
```bash
git clone https://github.com/your-org/ai-software-generator.git
cd ai-software-generator

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

### 3. Access the Platform
```bash
# API Gateway
open http://localhost:8000

# API Documentation
open http://localhost:8000/docs

# Health Check
curl http://localhost:8000/health
```

## 📋 Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Request  │───▶│  API Gateway    │───▶│  Orchestrator   │
│                 │    │  (FastAPI)      │    │  (AI Analysis)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
┌─────────────────┐    ┌─────────────────┐             ▼
│   Auth Service  │    │  Codegen        │    ┌─────────────────┐
│   (Keycloak)    │    │  Service        │    │  Task Breakdown │
└─────────────────┘    │  (MetaGPT)      │    │  & AI Planning  │
                       └─────────────────┘    └─────────────────┘
                                │                        │
┌─────────────────┐             ▼               ┌─────────────────┐
│  Storage        │    ┌─────────────────┐     │  Project        │
│  Service        │    │  Code           │     │  Repository     │
│  (MinIO)        │    │  Generation     │     │  Creation       │
└─────────────────┘    └─────────────────┘     └─────────────────┘
                                │                        │
┌─────────────────┐    ┌─────────────────┐             ▼
│  Audit Service  │    │  Executor       │    ┌─────────────────┐
│  (OpenTelemetry)│    │  Service        │    │  Sandbox        │
└─────────────────┘    │  (Docker)       │    │  Execution      │
                       └─────────────────┘    │  & Testing      │
                                │             └─────────────────┘
┌─────────────────┐             ▼                        │
│  Database       │    ┌─────────────────┐             ▼
│  (PostgreSQL)   │    │  Test Results   │    ┌─────────────────┐
└─────────────────┘    │  & Logs         │    │  Deployment     │
                       └─────────────────┘    │  Package        │
                                               └─────────────────┘
```

## 🏗️ Service Components

### Core Services
- **API Gateway**: Unified entry point with routing, authentication, and rate limiting
- **Orchestrator**: AI-powered requirement analysis and task orchestration
- **Codegen Service**: Code generation using MetaGPT and template systems
- **Executor Service**: Secure sandbox execution with Docker isolation
- **Storage Service**: File and project artifact management with MinIO
- **Audit Service**: Comprehensive logging and telemetry

### Supporting Services
- **Auth Service**: Identity management with Keycloak integration
- **Profile Service**: AI provider settings and user preferences
- **Workflow Engine**: Complex process orchestration with Temporal
- **Testing Framework**: Automated testing and quality assurance

### Infrastructure
- **PostgreSQL**: Primary database with multi-tenant support
- **MinIO**: S3-compatible object storage
- **Redis**: Caching and session management
- **Loki**: Log aggregation and analysis
- **Prometheus**: Metrics collection and monitoring

## 🔧 Configuration

### Environment Variables

#### Required
```bash
# Database
POSTGRES_USER=devgen
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=devgen

# AI Providers (choose at least one)
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key

# Storage
MINIO_ROOT_USER=admin
MINIO_ROOT_PASSWORD=your_secure_minio_password

# Authentication
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=your_secure_keycloak_password
```

#### Optional
```bash
# Redis (for caching)
REDIS_URL=redis://localhost:6379

# Logging
LOKI_URL=http://localhost:3100

# Security
JWT_SECRET_KEY=your-256-bit-secret
```

### Docker Compose Override

For development with live reloading:
```yaml
version: '3.8'
services:
  api-gateway:
    volumes:
      - ./saas-devgen/api-gateway:/app
    environment:
      - DEBUG=true
    command: uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 📖 Usage Examples

### 1. Create a Requirement

```bash
curl -X POST http://localhost:8000/api/v1/requirements \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-jwt-token" \
  -d '{
    "requirement": "Build a REST API for task management with user authentication"
  }'
```

**Response:**
```json
{
  "requirement_id": 1,
  "text": "Build a REST API for task management with user authentication",
  "status": "completed",
  "tasks": [
    {
      "id": 1,
      "description": "Design REST API endpoints and data models",
      "status": "pending"
    },
    {
      "id": 2,
      "description": "Set up FastAPI project structure with middleware",
      "status": "pending"
    }
  ]
}
```

### 2. Generate Code

```bash
curl -X POST http://localhost:8000/api/v1/codegen/1 \
  -H "Authorization: Bearer your-jwt-token" \
  -d '{
    "language": "python",
    "framework": "fastapi",
    "additional_requirements": "Add comprehensive error handling"
  }'
```

### 3. Execute Tests

```bash
curl -X POST http://localhost:8000/api/v1/projects/1/sandbox \
  -H "Authorization: Bearer your-jwt-token" \
  -d '{
    "command": "python -m pytest",
    "timeout": 300
  }'
```

### 4. Download Project

```bash
curl -X GET http://localhost:8000/api/v1/projects/1/download \
  -H "Authorization: Bearer your-jwt-token" \
  -o generated_project.zip
```

## 🧪 Testing

### Run All Tests
```bash
make test-all
```

### Run Service-Specific Tests
```bash
# Auth Service tests (50 tests covering authentication, security, integration)
make test-auth-service

# Orchestrator tests
make test-orchestrator

# Codegen Service tests
make test-codegen-service

# API Gateway tests
make test-api-gateway

# Storage Service tests
make test-storage-service

# Audit Service tests
make test-audit-service

# Executor Service tests
make test-executor-service

# Profile Service tests
make test-profile-service
```

### Integration Tests
```bash
# Run integration tests across all services
make test-integration
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

# Deploy to Kubernetes
make deploy-k8s

# Or use Docker Compose
docker-compose -f docker-compose.prod.yml up -d
```

### Cloud Platforms

#### AWS
```bash
# Deploy to EKS
make deploy-aws

# Use AWS services (RDS, S3, ElastiCache)
# See docs/PRODUCTION_DEPLOYMENT.md for details
```

#### Google Cloud
```bash
# Deploy to GKE
make deploy-gcp

# Use Cloud SQL, Cloud Storage, Memorystore
```

#### Azure
```bash
# Deploy to AKS
make deploy-azure

# Use Azure Database, Blob Storage, Cache
```

## 📊 Monitoring

### Health Checks
```bash
# Overall health
curl http://localhost:8000/health

# Database health
curl http://localhost:8000/health/database

# AI providers health
curl http://localhost:8000/health/ai
```

### Metrics
```bash
# Prometheus metrics
curl http://localhost:8000/metrics

# Custom metrics
curl http://localhost:8000/metrics/custom
```

### Logging
```bash
# View application logs
docker-compose logs -f

# Search logs with Loki
logcli query '{service="api-gateway"}' --addr=http://localhost:3100
```

## 🔒 Security

### Authentication & Authorization
- JWT-based authentication with Keycloak integration
- Role-based access control (RBAC)
- Multi-tenant isolation
- API rate limiting

### Data Protection
- Encrypted database connections
- Secure file storage with MinIO
- Audit logging for all operations
- GDPR and SOC2 compliance ready

### Network Security
- HTTPS/TLS encryption
- Network policies in Kubernetes
- Secure sandbox execution
- Input validation and sanitization

## 🤝 Contributing

### Development Setup
```bash
# Fork the repository
git clone https://github.com/your-username/ai-software-generator.git
cd ai-software-generator

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start development services
make dev-up
```

### Code Standards
- Follow PEP 8 for Python code
- Use type hints and docstrings
- Write comprehensive unit tests
- Update documentation for changes

### Pull Request Process
1. Create a feature branch from `main`
2. Make changes with tests
3. Ensure all tests pass
4. Update documentation
5. Submit pull request with description

### Commit Guidelines
```bash
# Use conventional commits
git commit -m "feat: add AI requirement breakdown"
git commit -m "fix: resolve MetaGPT integration issue"
git commit -m "docs: update API reference"
```

## 📚 Documentation

### User Guides
- [API Reference](docs/API_REFERENCE.md) - Complete API documentation
- [Development Setup](docs/DEVELOPMENT_SETUP.md) - Local development guide
- [Production Deployment](docs/PRODUCTION_DEPLOYMENT.md) - Production deployment guide

### Technical Documentation
- [Architecture Overview](docs/ARCHITECTURE.md) - System architecture details
- [Database Schema](docs/DATABASE_SCHEMA.md) - Database design and migrations
- [Security Guide](docs/SECURITY.md) - Security best practices
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues and solutions

### API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Spec**: http://localhost:8000/openapi.json

## 🏢 Enterprise Features

### Multi-tenancy
- Complete tenant isolation
- Per-tenant resource quotas
- Tenant-specific configurations
- Cross-tenant audit logging

### Compliance
- SOC 2 Type II ready
- GDPR compliance
- HIPAA ready (healthcare option)
- Custom compliance frameworks

### Integrations
- **Version Control**: GitHub, GitLab, Bitbucket
- **CI/CD**: Jenkins, GitHub Actions, GitLab CI
- **Monitoring**: Datadog, New Relic, Splunk
- **Security**: Snyk, SonarQube, Checkmarx

### Support
- **Enterprise SLA**: 99.9% uptime guarantee
- **24/7 Support**: Phone and email support
- **Dedicated Success Manager**: For large deployments
- **Custom Development**: Bespoke features and integrations

## 📈 Performance

### Benchmarks
- **Requirement Processing**: < 30 seconds for complex requirements
- **Code Generation**: < 2 minutes for medium projects
- **Sandbox Execution**: < 5 minutes for full test suites
- **API Response Time**: < 100ms for most endpoints

### Scaling
- **Horizontal Scaling**: Kubernetes HPA with custom metrics
- **Database Scaling**: Read replicas and connection pooling
- **Storage Scaling**: MinIO distributed setup
- **Caching**: Redis for session and API caching

## 🛠️ Built With

### Core Technologies
- **FastAPI**: High-performance async web framework
- **PostgreSQL**: Advanced open-source database
- **MinIO**: S3-compatible object storage
- **Keycloak**: Open-source identity management
- **Docker**: Containerization platform
- **Kubernetes**: Container orchestration

### AI & ML
- **MetaGPT**: Multi-agent AI framework
- **OpenAI GPT-4**: Advanced language model
- **Anthropic Claude**: Enterprise AI assistant
- **LangChain**: LLM application framework

### DevOps & Monitoring
- **Prometheus**: Metrics collection
- **Grafana**: Visualization and dashboards
- **Loki**: Log aggregation
- **OpenTelemetry**: Observability framework

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **MetaGPT**: For the multi-agent AI framework
- **FastAPI**: For the excellent web framework
- **OpenAI & Anthropic**: For powerful AI capabilities
- **Kubernetes Community**: For orchestration excellence
- **Open Source Community**: For the amazing tools and libraries

## 📞 Support

### Community Support
- 📧 **Email**: support@ai-devgen.com
- 📚 **Documentation**: https://docs.ai-devgen.com
- 💬 **Discord**: https://discord.gg/ai-devgen
- 🐛 **GitHub Issues**: https://github.com/ai-devgen/platform/issues

### Enterprise Support
- 📞 **Phone**: 1-800-AI-DEVGEN
- 📧 **Enterprise Email**: enterprise@ai-devgen.com
- 👥 **Dedicated Support**: Contact your account manager
- 🚀 **Professional Services**: Custom implementation and training

## 🚀 Roadmap

### Q1 2024
- ✅ AI-powered requirement analysis
- ✅ Multi-tenant architecture
- ✅ Production deployment guides
- 🔄 Frontend dashboard (Next.js)

### Q2 2024
- 🔄 Advanced AI integrations
- 🔄 Git platform integrations
- 🔄 Enterprise security features
- 🔄 Performance optimizations

### Q3 2024
- 🔄 Mobile application
- 🔄 Advanced analytics
- 🔄 Custom AI model training
- 🔄 Multi-cloud deployment

### Future
- 🔄 AI-powered code review
- 🔄 Automated deployment pipelines
- 🔄 Integration with enterprise tools
- 🔄 Advanced compliance features

---

**Ready to build the future of software development?** Get started with AI Software Generator today!

[🚀 Quick Start](#-quick-start) | [📖 Documentation](docs/) | [💬 Community](https://discord.gg/ai-devgen) | [🏢 Enterprise](https://ai-devgen.com/enterprise)
