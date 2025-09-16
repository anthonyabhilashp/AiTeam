# Auth Service

A comprehensive authentication service that integrates with Keycloak for enterprise-grade identity management.

## 🚀 Quick Start Guide

### Prerequisites
- **Python 3.11+**
- **Docker & Docker Compose**
- **Keycloak instance** (automatically started with docker-compose)
- **Make** (usually pre-installed on macOS/Linux)

### ⚡ One-Command Setup
```bash
# Clone and setup entire platform
git clone <repository>
cd AiTeam
make setup-dev
```

---

## 🛠️ Development Workflow

### 1. Build the Service
```bash
# Build Docker image
make build auth-service

# Alternative: Build with Docker Compose
docker compose build auth-service
```

### 2. Run the Service
```bash
# Run locally (development)
make run auth-service

# Run with Docker Compose (production-like)
docker compose up -d auth-service

# Run entire platform
make docker-run
```

### 3. Test the Service
```bash
# Run all tests
make test auth-service

# Run specific test file
cd saas-devgen/auth-service && python -m pytest tests/test_auth.py -v

# Run with coverage
cd saas-devgen/auth-service && python -m pytest tests/ --cov=. --cov-report=html
```

### 4. Stop the Service
```bash
# Stop local service (Ctrl+C in terminal)

# Stop Docker containers
docker compose down auth-service

# Stop entire platform
make docker-down
```

---

## 📋 Complete Command Reference

### Make Commands
```bash
# Development
make setup auth-service     # Install dependencies
make build auth-service     # Build Docker image
make run auth-service       # Run locally
make test auth-service      # Run tests
make stop auth-service      # Stop service

# Docker Operations
make docker-build          # Build all services
make docker-run            # Start all services
make docker-down           # Stop all services
make docker-logs           # View all logs
make docker-status         # Check status

# Platform Management
make setup-dev             # Setup development environment
make setup-prod            # Setup production environment
make clean                 # Clean build artifacts
make health                # Check all services health
```

### Docker Commands
```bash
# Service-specific
docker compose up -d auth-service           # Start auth-service only
docker compose logs -f auth-service         # Follow logs
docker compose restart auth-service         # Restart service
docker compose exec auth-service bash       # Access container shell

# Full platform
docker compose up -d                        # Start all services
docker compose down                         # Stop all services
docker compose down -v                      # Stop and remove volumes
docker compose build --no-cache             # Rebuild without cache
```

### Local Development
```bash
# Manual setup
cd saas-devgen/auth-service
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run service
python main.py

# Run tests
python -m pytest tests/ -v
```

---

## 🔍 Testing & Validation

### Automated Testing
```bash
# Run all tests with verbose output
make test auth-service

# Run tests with coverage report
cd saas-devgen/auth-service
python -m pytest tests/ --cov=. --cov-report=html
open htmlcov/index.html  # View coverage report

# Run specific test
python -m pytest tests/test_auth.py::test_login -v
```

### Manual Testing
```bash
# Health check
curl http://localhost:8001/health

# API documentation
open http://localhost:8001/docs

# Test login endpoint
curl -X POST http://localhost:8001/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}'
```

### Integration Testing
```bash
# Test with Keycloak
docker compose up -d keycloak
sleep 30  # Wait for Keycloak to start
make test auth-service
```

---

## 🔧 Troubleshooting

### Common Issues

#### Docker Build Fails
```bash
# Check Docker is running
docker ps

# Clean Docker cache
docker system prune -a

# Rebuild without cache
docker compose build --no-cache auth-service
```

#### Tests Fail
```bash
# Check virtual environment
source .venv/bin/activate

# Install test dependencies
pip install -r requirements.txt

# Run tests with debug info
python -m pytest tests/ -v -s
```

#### Service Won't Start
```bash
# Check logs
docker compose logs auth-service

# Check port availability
lsof -i :8001

# Check environment variables
docker compose exec auth-service env | grep KEYCLOAK
```

#### Keycloak Connection Issues
```bash
# Check Keycloak is running
docker compose ps keycloak

# Check Keycloak logs
docker compose logs keycloak

# Wait for Keycloak to fully start (can take 30-60 seconds)
sleep 60 && docker compose up -d auth-service
```

---

## 📖 API Documentation

### Interactive Documentation
Once running, access:
- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc
- **OpenAPI Schema**: http://localhost:8001/openapi.json

### Health Endpoints
```bash
# Service health
GET /health

# Dependencies health
GET /health/dependencies
```

---

## 🔗 Complete API Reference

### Authentication Endpoints

#### 1. POST `/login`
**Authenticate user with Keycloak**

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 300,
  "user_id": "uuid-string",
  "roles": ["user", "admin"]
}
```

**Error Responses:**
- `401`: Invalid credentials
- `500`: Authentication failed

---

#### 2. POST `/refresh`
**Refresh access token using refresh token**

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 300
}
```

**Error Response:**
- `401`: Invalid refresh token

---

#### 3. POST `/logout`
**Logout user by invalidating refresh token**

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200):**
```json
{
  "message": "Logged out successfully"
}
```

**Error Response:**
- `500`: Logout failed

---

### User Management Endpoints

#### 4. POST `/register`
**Register a new user with Keycloak**

**Request Body:**
```json
{
  "username": "string",
  "email": "user@example.com",
  "password": "string",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Response (200):**
```json
{
  "user_id": "uuid-string",
  "message": "User registered successfully"
}
```

**Error Response:**
- `400`: Registration failed
- `500`: Keycloak admin not available

---

#### 5. POST `/password-reset`
**Request password reset for a user**

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response (200):**
```json
{
  "message": "Password reset email sent successfully"
}
```

**Error Responses:**
- `404`: User not found
- `500`: Password reset failed / Keycloak admin not available

---

#### 6. POST `/change-password`
**Change password for authenticated user**

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "new_password": "new_secure_password123"
}
```

**Response (200):**
```json
{
  "message": "Password changed successfully"
}
```

**Error Responses:**
- `401`: Invalid token
- `500`: Password change failed / Keycloak services not available

---

### Token Management Endpoints

#### 7. GET `/userinfo`
**Get user information from access token**

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "sub": "user-uuid",
  "email_verified": true,
  "name": "John Doe",
  "preferred_username": "johndoe",
  "given_name": "John",
  "family_name": "Doe",
  "email": "john.doe@example.com",
  "realm_access": {
    "roles": ["user", "admin"]
  }
}
```

**Error Response:**
- `401`: Invalid token

---

#### 8. GET `/introspect`
**Introspect token to check validity**

**Query Parameters:**
- `token` (string): The access token to introspect

**Response (200):**
```json
{
  "active": true,
  "client_id": "auth-service",
  "username": "johndoe",
  "token_type": "Bearer",
  "exp": 1640995200,
  "iat": 1640994900,
  "sub": "user-uuid",
  "realm_access": {
    "roles": ["user"]
  }
}
```

**Error Response:**
- `401`: Token introspection failed

---

### Role Management Endpoints

#### 9. GET `/roles`
**Get current user's roles**

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "user_id": "user-uuid",
  "roles": ["user", "admin"]
}
```

**Error Responses:**
- `401`: Invalid token
- `500`: Keycloak OpenID not available

---

#### 10. PUT `/user/{user_id}/roles`
**Update user roles (admin only)**

**Headers:**
```
Authorization: Bearer <admin_access_token>
```

**Path Parameters:**
- `user_id` (string): The UUID of the user to update

**Request Body:**
```json
{
  "user_id": "user-uuid",
  "roles": ["user", "admin", "manager"]
}
```

**Response (200):**
```json
{
  "user_id": "user-uuid",
  "roles": ["user", "admin", "manager"],
  "message": "User roles updated successfully"
}
```

**Error Responses:**
- `401`: Invalid token
- `403`: Admin access required
- `500`: Role update failed / Keycloak services not available

---

### Health & Monitoring Endpoints

#### 11. GET `/health`
**Health check endpoint**

**Response (200 - Healthy):**
```json
{
  "status": "healthy",
  "service": "auth-service",
  "keycloak_status": "connected"
}
```

**Response (200 - Unhealthy):**
```json
{
  "status": "unhealthy",
  "service": "auth-service",
  "keycloak_status": "error: Connection refused"
}
```

---

## 🔐 Authentication & Authorization

### Bearer Token Authentication
All protected endpoints require a Bearer token in the Authorization header:

```
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Role-Based Access Control
- **Admin-only endpoints**: Require `admin` role in the user's realm roles
- **User endpoints**: Require valid authentication (any authenticated user)
- **Public endpoints**: No authentication required (`/health`, `/login`, `/register`, `/password-reset`)

### Token Expiration
- **Access tokens**: Typically expire in 5 minutes (300 seconds)
- **Refresh tokens**: Used to obtain new access tokens without re-authentication
- **Automatic refresh**: Use the `/refresh` endpoint to get new tokens

---

## 📊 Response Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (invalid credentials/token) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not Found (user not found) |
| 500 | Internal Server Error (server error) |

---

## 🧪 Testing Examples

### Login and Get User Info
```bash
# Login
curl -X POST http://localhost:8001/login 
  -H "Content-Type: application/json" 
  -d '{"username":"testuser","password":"testpass"}'

# Extract token from response and use it
curl -X GET http://localhost:8001/userinfo 
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Register New User
```bash
curl -X POST http://localhost:8001/register 
  -H "Content-Type: application/json" 
  -d '{
    "username":"newuser",
    "email":"newuser@example.com",
    "password":"securepass123",
    "first_name":"John",
    "last_name":"Doe"
  }'
```

### Password Reset
```bash
curl -X POST http://localhost:8001/password-reset 
  -H "Content-Type: application/json" 
  -d '{"email":"user@example.com"}'
```

### Change Password (Authenticated)
```bash
curl -X POST http://localhost:8001/change-password 
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" 
  -H "Content-Type: application/json" 
  -d '{"new_password":"new_secure_password123"}'
```

### Admin: Update User Roles
```bash
curl -X PUT http://localhost:8001/user/user-uuid/roles 
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" 
  -H "Content-Type: application/json" 
  -d '{"user_id":"user-uuid","roles":["user","admin"]}'
```

---

## 🔗 Integration Examples

### Frontend Integration (JavaScript)
```javascript
// Login
const login = async (username, password) => {
  const response = await fetch('/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });
  const data = await response.json();
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);
  return data;
};

// Authenticated request
const getUserInfo = async () => {
  const token = localStorage.getItem('access_token');
  const response = await fetch('/userinfo', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return response.json();
};
```

### Backend Integration (Python)
```python
import requests

def authenticate_user(username: str, password: str):
    response = requests.post('http://localhost:8001/login', json={
        'username': username,
        'password': password
    })
    return response.json()

def get_user_info(token: str):
    response = requests.get('http://localhost:8001/userinfo', headers={
        'Authorization': f'Bearer {token}'
    })
    return response.json()
```

---

## 📋 API Summary Table

| Endpoint | Method | Auth Required | Admin Required | Description |
|----------|--------|---------------|----------------|-------------|
| `/login` | POST | ❌ | ❌ | User authentication |
| `/refresh` | POST | ❌ | ❌ | Token refresh |
| `/logout` | POST | ❌ | ❌ | User logout |
| `/register` | POST | ❌ | ❌ | User registration |
| `/password-reset` | POST | ❌ | ❌ | Password reset request |
| `/change-password` | POST | ✅ | ❌ | Change password |
| `/userinfo` | GET | ✅ | ❌ | Get user information |
| `/introspect` | GET | ❌ | ❌ | Token introspection |
| `/roles` | GET | ✅ | ❌ | Get user roles |
| `/user/{id}/roles` | PUT | ✅ | ✅ | Update user roles |
| `/health` | GET | ❌ | ❌ | Health check |

**Legend:**
- ✅ Required
- ❌ Not required

---

*This comprehensive API documentation serves as a complete reference for integrating with the Auth Service.*

---

## 🔐 Environment Configuration

### Required Environment Variables
```bash
# Keycloak Configuration
KEYCLOAK_URL=http://keycloak:8080
KEYCLOAK_REALM=master
KEYCLOAK_CLIENT_ID=auth-service
KEYCLOAK_CLIENT_SECRET=your-client-secret
KEYCLOAK_ADMIN_USER=admin
KEYCLOAK_ADMIN_PASSWORD=admin

# Optional
RESET_PASSWORD_REDIRECT_URI=http://localhost:3000/reset-password
```

### Environment Files
```bash
# Development
cp .env.example .env

# Production
cp .env.example .env.prod
```

---

## 🏗️ Architecture & Dependencies

### Core Libraries
- **FastAPI** (MIT) - Web framework with automatic OpenAPI docs
- **python-keycloak** (Apache 2.0) - Official Keycloak client
- **python-jose** (MIT) - JWT handling and validation
- **pydantic** (MIT) - Data validation and serialization
- **uvicorn** (Apache 2.0) - ASGI server

### Development Dependencies
- **pytest** - Testing framework
- **pytest-asyncio** - Async testing support
- **httpx** - HTTP client for testing
- **black** - Code formatting
- **isort** - Import sorting
- **flake8** - Linting

---

## 🚀 Deployment

### Development Deployment
```bash
make setup-dev
make docker-run
```

### Production Deployment
```bash
make setup-prod
docker compose -f docker-compose.prod.yml up -d
```

### Kubernetes Deployment
```bash
kubectl apply -f k8s/auth-service.yaml
kubectl apply -f k8s/keycloak.yaml
```

---

## 📊 Monitoring & Logging

### Logs
```bash
# Service logs
docker compose logs -f auth-service

# All platform logs
make docker-logs

# Structured logging
docker compose exec auth-service tail -f /app/logs/auth-service.log
```

### Health Checks
```bash
# Individual service
curl http://localhost:8001/health

# All services
make health
```

---

## 🤝 Contributing

### Development Setup
```bash
# Fork and clone
git clone <your-fork>
cd AiTeam

# Setup development environment
make setup-dev

# Create feature branch
git checkout -b feature/your-feature

# Make changes and test
make test auth-service

# Submit PR
git push origin feature/your-feature
```

### Code Quality
```bash
# Format code
black saas-devgen/auth-service/
isort saas-devgen/auth-service/

# Lint code
flake8 saas-devgen/auth-service/

# Run tests
make test auth-service
```

---

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Keycloak Documentation](https://www.keycloak.org/documentation)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Python Keycloak Library](https://python-keycloak.readthedocs.io/)

---

## 🆘 Support

For issues and questions:
1. Check this README
2. Review [troubleshooting section](#troubleshooting)
3. Check existing GitHub issues
4. Create a new issue with:
   - Error logs
   - Environment details
   - Steps to reproduce

---

*This README serves as a comprehensive guide and benchmark for other services in the platform.*

## Environment Variables

```bash
KEYCLOAK_URL=http://localhost:8080
KEYCLOAK_REALM=master
KEYCLOAK_CLIENT_ID=auth-service
KEYCLOAK_CLIENT_SECRET=your-client-secret
KEYCLOAK_ADMIN_USER=admin
KEYCLOAK_ADMIN_PASSWORD=admin
RESET_PASSWORD_REDIRECT_URI=http://localhost:3000/reset-password
```

## API Endpoints

### Authentication
```bash
POST /login                    # Authenticate with username/password
POST /refresh?refresh_token=   # Refresh access tokens
POST /logout?refresh_token=    # Logout and invalidate tokens
```

### User Management
```bash
POST /register                 # Register new user
POST /password-reset           # Request password reset
POST /change-password          # Change user password
GET  /userinfo                 # Get user information
GET  /roles                    # Get current user roles
PUT  /user/{user_id}/roles     # Update user roles (admin only)
```

### Token Management
```bash
GET  /introspect?token=        # Check token validity
GET  /health                   # Service health check
```

### POST /login
Authenticate user with Keycloak.

**Request:**
```json
{
  "username": "user",
  "password": "password"
}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "Bearer",
  "expires_in": 300,
  "user_id": "user-uuid",
  "roles": ["user", "admin"]
}
```

### POST /register
Register a new user.

**Request:**
```json
{
  "username": "newuser",
  "email": "user@example.com",
  "password": "securepass123",
  "first_name": "John",
  "last_name": "Doe"
}
```

### POST /password-reset
Request password reset.

**Request:**
```json
{
  "email": "user@example.com"
}
```

### POST /change-password
Change user password (requires authentication).

**Request:**
```json
{
  "current_password": "oldpassword",
  "new_password": "newpassword123"
}
```

### PUT /user/{user_id}/roles
Update user roles (admin only).

**Request:**
```json
{
  "user_id": "user-uuid",
  "roles": ["user", "admin"]
}
```

## Running with Docker

```bash
docker build -t auth-service .
docker run -p 8001:8001 \
  -e KEYCLOAK_URL=http://your-keycloak:8080 \
  -e KEYCLOAK_REALM=your-realm \
  -e KEYCLOAK_CLIENT_ID=your-client \
  -e KEYCLOAK_CLIENT_SECRET=your-secret \
  -e KEYCLOAK_ADMIN_USER=admin \
  -e KEYCLOAK_ADMIN_PASSWORD=admin \
  auth-service
```

## Running Locally

```bash
pip install -r requirements.txt
python main.py
```

## Testing

```bash
pytest tests/
```

## Keycloak Setup

1. **Create a realm** in Keycloak
2. **Create a client** with confidential access type
3. **Configure client credentials**
4. **Create realm roles** (user, admin, etc.)
5. **Set environment variables**
6. **Enable user registration** in realm settings
7. **Configure SMTP** for password reset emails

## Security Features

- **JWT Token Validation** - All endpoints validate tokens
- **Role-Based Access Control** - Admin-only endpoints
- **Password Policies** - Enforced by Keycloak
- **Token Expiration** - Automatic token refresh
- **Secure Logout** - Token invalidation

This service provides enterprise-grade authentication with minimal custom code, leveraging Keycloak's proven security features.
