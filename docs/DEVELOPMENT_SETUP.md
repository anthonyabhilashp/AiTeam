# Development Setup Guide

## Prerequisites

Before setting up the AI Software Generator Platform, ensure you have the following installed:

### System Requirements
- **Operating System**: macOS 12+, Linux (Ubuntu 20.04+), or Windows 10+
- **CPU**: 4+ cores recommended
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 20GB free space

### Required Software
- **Docker**: Version 24.0+ with Docker Compose V2
- **Python**: Version 3.10+ (for local development)
- **Node.js**: Version 18+ (for frontend development)
- **Git**: Version 2.30+
- **Make**: GNU Make (usually pre-installed on macOS/Linux)

### Optional Tools
- **VS Code**: Recommended IDE with Python and Docker extensions
- **kubectl**: For Kubernetes deployment
- **Helm**: For advanced Kubernetes deployments
- **Postman**: For API testing

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/ai-software-generator.git
cd ai-software-generator
```

### 2. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit environment variables
nano .env
```

**Required Environment Variables:**
```bash
# Database
POSTGRES_USER=devgen
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=devgen

# MinIO Storage
MINIO_ROOT_USER=admin
MINIO_ROOT_PASSWORD=your_secure_minio_password

# Keycloak Auth
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=your_secure_keycloak_password

# AI Providers (choose one or more)
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
OPENROUTER_API_KEY=sk-or-your-openrouter-key

# Redis (optional)
REDIS_URL=redis://localhost:6379

# Logging
LOKI_URL=http://localhost:3100
```

### 3. Start the Platform

```bash
# Start all services
make up

# Or use Docker Compose directly
docker-compose up -d
```

### 4. Verify Installation

```bash
# Check service health
curl http://localhost:8000/health

# Access the platform
open http://localhost:8000
```

## Detailed Setup

### Infrastructure Setup

#### PostgreSQL Database

```bash
# Start PostgreSQL
docker run -d \
  --name postgres-devgen \
  -e POSTGRES_USER=devgen \
  -e POSTGRES_PASSWORD=your_password \
  -e POSTGRES_DB=devgen \
  -p 5432:5432 \
  postgres:14
```

#### MinIO Object Storage

```bash
# Start MinIO
docker run -d \
  --name minio-devgen \
  -e MINIO_ROOT_USER=admin \
  -e MINIO_ROOT_PASSWORD=your_password \
  -p 9000:9000 \
  -p 9001:9001 \
  minio/minio server /data
```

#### Keycloak Identity Management

```bash
# Start Keycloak
docker run -d \
  --name keycloak-devgen \
  -e KEYCLOAK_ADMIN=admin \
  -e KEYCLOAK_ADMIN_PASSWORD=your_password \
  -p 8080:8080 \
  quay.io/keycloak/keycloak:24.0 start-dev
```

#### Redis (Optional)

```bash
# Start Redis
docker run -d \
  --name redis-devgen \
  -p 6379:6379 \
  redis:7-alpine
```

### Service Development Setup

#### Python Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

#### Individual Service Setup

```bash
# API Gateway
cd saas-devgen/api-gateway
pip install -r requirements.txt
python main.py

# Orchestrator Service
cd ../orchestrator
pip install -r requirements.txt
python main.py

# Code Generation Service
cd ../codegen-service
pip install -r requirements.txt
python main.py

# And so on for other services...
```

### Frontend Development

```bash
# Install Node.js dependencies
cd saas-devgen/frontend
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

## Configuration

### Environment Variables

#### Core Configuration
```bash
# Application
APP_ENV=development
APP_NAME=AI Software Generator
APP_VERSION=1.0.0

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=true

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

#### Database Configuration
```bash
# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=devgen
POSTGRES_PASSWORD=your_password
POSTGRES_DB=devgen

# Connection pool
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
```

#### AI Provider Configuration
```bash
# OpenAI
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL=gpt-4
OPENAI_MAX_TOKENS=4000

# Anthropic
ANTHROPIC_API_KEY=sk-ant-your-key
ANTHROPIC_MODEL=claude-3-sonnet-20240229

# OpenRouter
OPENROUTER_API_KEY=sk-or-your-key
OPENROUTER_MODEL=openai/gpt-4
```

#### Storage Configuration
```bash
# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=admin
MINIO_SECRET_KEY=your_password
MINIO_SECURE=false
MINIO_BUCKET=devgen-projects
```

#### Security Configuration
```bash
# JWT
JWT_SECRET_KEY=your-256-bit-secret
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Keycloak
KEYCLOAK_URL=http://localhost:8080
KEYCLOAK_REALM=master
KEYCLOAK_CLIENT_ID=devgen
```

### Configuration Files

#### Docker Compose Override

Create `docker-compose.override.yml` for development:

```yaml
version: '3.8'
services:
  api-gateway:
    environment:
      - DEBUG=true
    volumes:
      - ./saas-devgen/api-gateway:/app
    command: uvicorn main:app --reload --host 0.0.0.0 --port 8000

  orchestrator:
    environment:
      - DEBUG=true
    volumes:
      - ./saas-devgen/orchestrator:/app
```

#### VS Code Configuration

`.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true
}
```

## Development Workflow

### 1. Code Changes

```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes
# ...

# Run tests
make test

# Commit changes
git add .
git commit -m "Add new feature"
```

### 2. Testing

```bash
# Run all tests
make test

# Run specific service tests
cd saas-devgen/orchestrator
python -m pytest tests/

# Run integration tests
make test-integration
```

### 3. Code Quality

```bash
# Format code
make format

# Lint code
make lint

# Type checking
make type-check
```

### 4. Database Migrations

```bash
# Create migration
cd saas-devgen/shared
alembic revision --autogenerate -m "Add new table"

# Run migrations
alembic upgrade head
```

## Debugging

### Logs

```bash
# View all service logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f orchestrator

# View application logs
tail -f logs/app.log
```

### Health Checks

```bash
# Check all services
curl http://localhost:8000/health

# Check database
curl http://localhost:8000/health/database

# Check AI providers
curl http://localhost:8000/health/ai
```

### Debugging Tools

#### Python Debugger

```python
import pdb; pdb.set_trace()
```

#### VS Code Debugging

`.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug API Gateway",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
      "cwd": "${workspaceFolder}/saas-devgen/api-gateway"
    }
  ]
}
```

## Deployment

### Local Deployment

```bash
# Build and start all services
make deploy-local

# Or manually
docker-compose up --build -d
```

### Production Deployment

```bash
# Build production images
make build-prod

# Deploy to Kubernetes
make deploy-k8s

# Or use Docker Compose for production
docker-compose -f docker-compose.prod.yml up -d
```

## Troubleshooting

### Common Issues

#### Port Conflicts
```bash
# Check what's using ports
lsof -i :8000

# Kill process
kill -9 <PID>
```

#### Database Connection Issues
```bash
# Check PostgreSQL logs
docker-compose logs postgres

# Reset database
make db-reset
```

#### AI Provider Issues
```bash
# Test OpenAI connection
curl -X POST http://localhost:8000/health/ai/openai

# Check API key
echo $OPENAI_API_KEY
```

#### Memory Issues
```bash
# Check Docker memory usage
docker stats

# Increase Docker memory limit
# Docker Desktop > Settings > Resources > Memory
```

### Getting Help

1. **Check Logs**: Always check service logs first
2. **Health Endpoints**: Use `/health` endpoints for diagnostics
3. **Documentation**: Refer to API docs and this guide
4. **Community**: Join our Discord for community support
5. **Issues**: Create GitHub issues for bugs and feature requests

## Contributing

### Code Standards

- Follow PEP 8 for Python code
- Use type hints
- Write comprehensive tests
- Update documentation

### Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Ensure all tests pass
5. Update documentation
6. Submit pull request

### Commit Guidelines

```bash
# Good commit messages
git commit -m "feat: add AI requirement breakdown"
git commit -m "fix: resolve MetaGPT integration issue"
git commit -m "docs: update API reference"
```

## Security

### Development Security

- Never commit secrets to version control
- Use environment variables for sensitive data
- Rotate API keys regularly
- Enable 2FA on all accounts

### Code Security

- Validate all inputs
- Use parameterized queries
- Implement proper authentication
- Follow OWASP guidelines

## Performance

### Optimization Tips

- Use connection pooling
- Implement caching (Redis)
- Optimize database queries
- Use async/await for I/O operations

### Monitoring

```bash
# Enable metrics
export METRICS_ENABLED=true

# View metrics
curl http://localhost:8000/metrics
```

## Next Steps

1. **Complete Setup**: Follow this guide to get the platform running
2. **Explore Features**: Try creating your first requirement
3. **Customize**: Modify configurations for your needs
4. **Contribute**: Join the community and contribute improvements
5. **Deploy**: Move to production when ready

For more information, visit our [documentation site](https://docs.ai-devgen.com) or join our [Discord community](https://discord.gg/ai-devgen).
