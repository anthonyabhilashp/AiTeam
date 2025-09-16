# AI Software Generator Platform - API Documentation

## Overview

The AI Software Generator Platform provides a comprehensive REST API for automated software generation. This document covers all available endpoints, request/response formats, and usage examples.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

All API requests require authentication using JWT tokens:

```bash
Authorization: Bearer <your-jwt-token>
```

### Login

```http
POST /auth/login
Content-Type: application/json

{
  "username": "demo",
  "password": "demo123"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "user_id": 1,
  "tenant_id": 1,
  "roles": ["admin", "developer"]
}
```

## Core Endpoints

### Requirements Management

#### Create Requirement

Break down a software requirement into actionable tasks using AI.

```http
POST /requirements
Authorization: Bearer <token>
Content-Type: application/json

{
  "requirement": "Build a REST API for task management with user authentication"
}
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
      "status": "pending",
      "order_index": 0
    },
    {
      "id": 2,
      "description": "Set up FastAPI project structure with proper middleware",
      "status": "pending",
      "order_index": 1
    }
  ],
  "created_at": "2024-01-01T10:00:00Z"
}
```

#### Get Requirement

Retrieve a specific requirement and its tasks.

```http
GET /requirements/{requirement_id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "requirement_id": 1,
  "text": "Build a REST API for task management with user authentication",
  "status": "completed",
  "tasks": [...],
  "created_at": "2024-01-01T10:00:00Z"
}
```

### Code Generation

#### Generate Code

Generate production-ready code from tasks using AI.

```http
POST /codegen/{requirement_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "tasks": [
    "Design REST API endpoints and data models",
    "Set up FastAPI project structure"
  ],
  "language": "python",
  "framework": "fastapi",
  "additional_requirements": "Add comprehensive error handling and logging"
}
```

**Response:**
```json
{
  "status": "ready",
  "repo_url": "file:///app/generated_projects/project_123",
  "commit_id": "initial",
  "generated_files": [
    "main.py",
    "requirements.txt",
    "models.py",
    "database.py",
    "README.md"
  ],
  "metadata": {
    "language": "python",
    "framework": "fastapi",
    "generation_timestamp": "2024-01-01T10:05:00Z"
  }
}
```

### Project Management

#### List Projects

Get all projects for the current tenant.

```http
GET /projects
Authorization: Bearer <token>
```

**Response:**
```json
[
  {
    "id": 1,
    "tenant_id": 1,
    "requirement_id": 1,
    "repo_url": "file:///app/generated_projects/project_123",
    "commit_id": "v1.0.0",
    "status": "ready",
    "created_at": "2024-01-01T10:05:00Z"
  }
]
```

#### Get Project

Get detailed information about a specific project.

```http
GET /projects/{project_id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "id": 1,
  "tenant_id": 1,
  "requirement_id": 1,
  "repo_url": "file:///app/generated_projects/project_123",
  "files": [
    {
      "filename": "main.py",
      "content_type": "text/plain",
      "size": 2048,
      "uploaded_at": "2024-01-01T10:05:00Z"
    }
  ],
  "metadata": {
    "language": "python",
    "framework": "fastapi",
    "generated_files": 5
  }
}
```

#### Download Project

Download a project as a ZIP archive.

```http
GET /projects/{project_id}/download
Authorization: Bearer <token>
```

**Response:** ZIP file containing the complete project.

#### Execute Project

Run tests or execute the generated project in a secure sandbox.

```http
POST /projects/{project_id}/sandbox
Authorization: Bearer <token>
Content-Type: application/json

{
  "command": "python -m pytest",
  "timeout": 300,
  "environment": {
    "PYTHONPATH": "/app"
  }
}
```

**Response:**
```json
{
  "execution_id": 1,
  "status": "completed",
  "logs": "============================= test session starts ==============================\nplatform linux -- Python 3.11...",
  "exit_code": 0,
  "duration": 45.2
}
```

### Profile Management

#### Get Profile Settings

Get AI provider settings and preferences.

```http
GET /profile
Authorization: Bearer <token>
```

**Response:**
```json
{
  "ai_provider": "openai",
  "ai_model": "gpt-4",
  "api_key": "sk-****-****-****-*****"
}
```

#### Update Profile Settings

Update AI provider configuration.

```http
POST /profile
Authorization: Bearer <token>
Content-Type: application/json

{
  "ai_provider": "anthropic",
  "ai_model": "claude-3-sonnet-20240229",
  "api_key": "sk-ant-****-****-****-*****"
}
```

#### Get Available Models

Get available AI models from configured providers.

```http
GET /profile/openrouter/models
Authorization: Bearer <token>
```

**Response:**
```json
[
  {
    "id": "openai/gpt-4",
    "name": "GPT-4",
    "description": "Most capable GPT-4 model",
    "context_length": 8192,
    "pricing": {
      "prompt": 0.03,
      "completion": 0.06
    }
  }
]
```

### Audit and Monitoring

#### Get Audit Logs

Retrieve audit logs for compliance and monitoring.

```http
GET /audit/logs?tenant_id=1&start_date=2024-01-01&end_date=2024-01-31
Authorization: Bearer <token>
```

**Response:**
```json
{
  "logs": [
    {
      "id": 1,
      "tenant_id": 1,
      "user_id": 1,
      "action": "requirement_created",
      "entity": "requirement",
      "entity_id": 1,
      "details": {
        "requirement_text": "Build a REST API..."
      },
      "timestamp": "2024-01-01T10:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 50,
  "has_next": false,
  "has_prev": false
}
```

## Error Handling

All endpoints return appropriate HTTP status codes and error messages:

### Common Error Responses

**400 Bad Request:**
```json
{
  "detail": "Invalid request data"
}
```

**401 Unauthorized:**
```json
{
  "detail": "Authentication required"
}
```

**403 Forbidden:**
```json
{
  "detail": "Insufficient permissions"
}
```

**404 Not Found:**
```json
{
  "detail": "Resource not found"
}
```

**422 Validation Error:**
```json
{
  "detail": [
    {
      "loc": ["body", "requirement"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Internal server error"
}
```

## Rate Limiting

- API requests are rate-limited to prevent abuse
- Default limits: 100 requests per minute per IP
- Enterprise plans have higher limits

## WebSocket Support

Real-time updates for long-running operations:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/codegen/{generation_id}');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Progress:', data.progress, data.status);
};
```

## SDKs and Libraries

### Python SDK

```python
from ai_devgen_client import AIDevGenClient

client = AIDevGenClient(
    base_url="http://localhost:8000",
    api_key="your-jwt-token"
)

# Create requirement
requirement = client.create_requirement(
    "Build a FastAPI application with user authentication"
)

# Generate code
project = client.generate_code(
    requirement_id=requirement.id,
    language="python",
    framework="fastapi"
)

# Download project
client.download_project(project.id, "my_project.zip")
```

### JavaScript SDK

```javascript
import { AIDevGenClient } from 'ai-devgen-sdk';

const client = new AIDevGenClient({
  baseURL: 'http://localhost:8000',
  apiKey: 'your-jwt-token'
});

// Create requirement
const requirement = await client.requirements.create({
  requirement: 'Build a React dashboard'
});

// Generate code
const project = await client.codegen.generate(requirement.id, {
  language: 'javascript',
  framework: 'react'
});
```

## Best Practices

### 1. Requirement Writing
- Be specific and detailed in requirements
- Include technical constraints and preferences
- Mention target platforms and integrations

### 2. Error Handling
- Always check response status codes
- Implement retry logic for transient errors
- Log errors for debugging

### 3. Rate Limiting
- Implement client-side rate limiting
- Use exponential backoff for retries
- Monitor API usage

### 4. Security
- Store API keys securely
- Use HTTPS in production
- Rotate tokens regularly
- Validate input data

## Support

For API support and questions:
- 📧 Email: support@ai-devgen.com
- 📚 Documentation: https://docs.ai-devgen.com
- 💬 Discord: https://discord.gg/ai-devgen
- 🐛 GitHub Issues: https://github.com/ai-devgen/platform/issues</content>
<parameter name="filePath">/Users/a.pothula/workspace/unity/AiTeam/docs/API_REFERENCE.md
