# Gateway Service

A Kong-based API Gateway service for the Enterprise SaaS platform, providing centralized API management, routing, authentication, and monitoring capabilities.

## Overview

The Gateway Service acts as the single entry point for all API requests in the platform, providing:

- **API Routing**: Centralized routing to microservices
- **Authentication**: JWT-based authentication via Kong plugins
- **Security**: CORS, rate limiting, and request transformation
- **Monitoring**: Health checks and service discovery
- **Load Balancing**: Distribution of requests across service instances

## Architecture

```
[Client] → [Kong Gateway (Port 8000)]
                ↓
        [Admin API (Port 8001)]
                ↓
        [Admin GUI (Port 8002)]
                ↓
        [Microservices]
```

## Prerequisites

- Docker & Docker Compose
- Python 3.10+
- Kong Gateway 3.4+
- PostgreSQL (for Kong configuration storage)

## Quick Start

### 1. Environment Setup

Create a `.env` file in the gateway-service directory:

```bash
# Kong Configuration
KONG_DATABASE=postgres
KONG_PG_HOST=postgres
KONG_PG_PORT=5432
KONG_PG_USER=devgen
KONG_PG_PASSWORD=secret
KONG_PG_DATABASE=kong

# Service Ports
KONG_PROXY_PORT=8000
KONG_ADMIN_PORT=8001
KONG_ADMIN_GUI_PORT=8002

# Gateway Configuration
GATEWAY_SERVICE_PORT=8000
AUTH_SERVICE_URL=http://auth-service:8004
```

### 2. Build and Run

Using Docker Compose (from project root):

```bash
# Build the gateway service
make build-gateway

# Start the gateway service
make run-gateway

# View logs
make logs-gateway
```

Using Docker directly:

```bash
# Build the image
docker build -t gateway-service .

# Run the container
docker run -d \
  --name gateway-service \
  --env-file .env \
  -p 8000:8000 \
  -p 8001:8001 \
  -p 8002:8002 \
  --network saas-devgen_default \
  gateway-service
```

### 3. Health Check

```bash
# Check Kong status
curl http://localhost:8001/status

# Check gateway health
curl http://localhost:8000/health

# Access Kong Admin GUI
open http://localhost:8002
```

## Configuration

### Kong Configuration (kong.yml)

The service uses declarative configuration for Kong:

```yaml
_format_version: "3.0"

services:
  - name: auth-service
    url: http://auth-service:8004
    routes:
      - name: auth-route
        paths:
          - /auth
        methods:
          - GET
          - POST
        plugins:
          - name: cors
          - name: request-transformer
            config:
              add:
                headers:
                  - "X-Service:auth-service"

plugins:
  - name: jwt
  - name: cors
  - name: rate-limiting
    config:
      minute: 100
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `KONG_DATABASE` | Database backend | postgres |
| `KONG_PG_HOST` | PostgreSQL host | postgres |
| `KONG_PG_PORT` | PostgreSQL port | 5432 |
| `KONG_PG_USER` | PostgreSQL user | devgen |
| `KONG_PG_PASSWORD` | PostgreSQL password | secret |
| `KONG_PG_DATABASE` | PostgreSQL database | kong |
| `KONG_PROXY_PORT` | Kong proxy port | 8000 |
| `KONG_ADMIN_PORT` | Kong admin port | 8001 |
| `KONG_ADMIN_GUI_PORT` | Kong admin GUI port | 8002 |

## API Endpoints

### Gateway Endpoints

- `GET /health` - Gateway health check
- `GET /status` - Kong status
- `GET /services` - List Kong services
- `GET /routes` - List Kong routes

### Kong Admin API

All Kong Admin API endpoints are available at `http://localhost:8001`:

- `GET /status` - Kong status
- `GET /services` - List services
- `GET /routes` - List routes
- `POST /services` - Create service
- `POST /routes` - Create route

## Development

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the service locally
python main.py

# Run with auto-reload
uvicorn main:app --reload --port 8000
```

### Testing

```bash
# Run all tests
python tests/test_runner.py

# Run tests with coverage
python tests/test_runner.py coverage

# Run specific test file
python tests/test_runner.py specific test_gateway.py

# Run using pytest directly
pytest tests/ -v
```

### Test Structure

```
tests/
├── conftest.py          # Test fixtures and configuration
├── test_gateway.py      # Unit tests for GatewayService
├── test_integration.py  # Integration tests
└── test_runner.py       # Test runner script
```

## Docker Commands

### Build Commands

```bash
# Build gateway service
make build-gateway

# Build all services
make build

# Clean build artifacts
make clean
```

### Run Commands

```bash
# Start gateway service
make run-gateway

# Start all services
make run

# Stop gateway service
make stop-gateway

# Stop all services
make stop
```

### Log Commands

```bash
# View gateway logs
make logs-gateway

# View all logs
make logs

# Follow gateway logs
make logs-gateway-follow
```

## Monitoring

### Health Checks

The service provides several health check endpoints:

```bash
# Gateway health
curl http://localhost:8000/health

# Kong status
curl http://localhost:8001/status

# Service discovery
curl http://localhost:8000/services
```

### Metrics

Kong exposes metrics through the Admin API:

```bash
# Get Kong metrics
curl http://localhost:8001/metrics
```

### Logging

Logs are stored in the `logs/` directory:

- `gateway-service.log` - Application logs
- Kong logs are available via Docker logs

## Security

### Authentication

The gateway uses Kong JWT plugin for authentication:

```yaml
plugins:
  - name: jwt
    config:
      claims_to_verify:
        - exp
        - nbf
```

### CORS Configuration

CORS is configured globally:

```yaml
plugins:
  - name: cors
    config:
      origins:
        - http://localhost:3000
      methods:
        - GET
        - POST
        - PUT
        - DELETE
      headers:
        - Authorization
        - Content-Type
```

### Rate Limiting

Rate limiting is configured per service:

```yaml
plugins:
  - name: rate-limiting
    config:
      minute: 100
      hour: 1000
```

## Troubleshooting

### Common Issues

1. **Kong fails to start**
   - Check PostgreSQL connection
   - Verify environment variables
   - Check Kong logs: `docker logs kong`

2. **Services not accessible**
   - Verify service URLs in kong.yml
   - Check Docker network connectivity
   - Ensure services are running

3. **Authentication failures**
   - Verify JWT tokens
   - Check Kong JWT plugin configuration
   - Validate token claims

### Debug Commands

```bash
# Check Kong configuration
curl http://localhost:8001/config

# List all services
curl http://localhost:8001/services

# List all routes
curl http://localhost:8001/routes

# Check Kong logs
docker logs kong
```

## Contributing

1. Follow the existing code style
2. Add tests for new features
3. Update documentation
4. Create pull requests with detailed descriptions

## License

This service is part of the Enterprise SaaS platform and follows the same licensing terms.
