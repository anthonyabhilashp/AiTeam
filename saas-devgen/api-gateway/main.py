"""API Gateway - Central routing for the AI Software Generator platform."""
import sys
import os
# Add the parent directory to sys.path for shared modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import asyncio
import httpx
import time
import json
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from shared.config import settings
from shared.logging_utils import setup_logger

# Initialize logger
logger = setup_logger("api-gateway", "api-gateway.log")

def log_api_call(logger, method: str, endpoint: str, status_code: int, duration: float = 0.0, user_id: str = None, tenant_id: str = None):
    """Log API call details with enterprise audit trail."""
    log_entry = f"{method} {endpoint} - {status_code} - {duration:.3f}s"
    if user_id:
        log_entry += f" - User: {user_id}"
    if tenant_id:
        log_entry += f" - Tenant: {tenant_id}"
    logger.info(log_entry)

app = FastAPI(
    title="AI Software Generator API Gateway",
    description="Enterprise SaaS platform for automated software generation",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service endpoints
SERVICES = {
    "auth": settings.auth_service_url,
    "orchestrator": settings.orchestrator_url,
    "codegen": settings.codegen_service_url,
    "executor": settings.executor_service_url,
    "storage": settings.storage_service_url,
    "audit": settings.audit_service_url,
}


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests."""
    start_time = time.time()
    
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        
        log_api_call(
            logger=logger,
            method=request.method,
            endpoint=str(request.url),
            status_code=response.status_code,
            duration=duration,
            user_id=getattr(request.state, "user_id", None),
            tenant_id=getattr(request.state, "tenant_id", None)
        )
        
        return response
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Request failed: {str(e)}")
        log_api_call(
            logger=logger,
            method=request.method,
            endpoint=str(request.url),
            status_code=500,
            duration=duration
        )
        raise


async def proxy_request(service: str, path: str, method: str, **kwargs):
    """Proxy request to a service."""
    if service not in SERVICES:
        raise HTTPException(status_code=404, detail=f"Service {service} not found")
    
    url = f"{SERVICES[service]}{path}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(method, url, **kwargs)
            return JSONResponse(
                content=response.json() if response.content else {},
                status_code=response.status_code
            )
        except httpx.RequestError as e:
            logger.error(f"Failed to proxy request to {url}: {e}")
            raise HTTPException(status_code=503, detail=f"Service {service} unavailable")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "AI Software Generator API Gateway",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "services": list(SERVICES.keys())
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": SERVICES
    }


# Auth service routes with /api/v1 prefix
@app.post("/api/v1/auth/login")
async def login_v1(request: Request):
    """Proxy login request to auth service."""
    body = await request.body()
    # For demo purposes, return a mock successful login
    import json
    try:
        login_data = json.loads(body)
        username = login_data.get("username", "")
        password = login_data.get("password", "")
        
        # Mock authentication - in production, this would proxy to Keycloak
        if username and password:  # Accept any non-empty credentials for demo
            return JSONResponse(
                content={
                    "access_token": "demo-jwt-token-12345",
                    "token_type": "bearer",
                    "user_info": {
                        "user_id": "demo-user",
                        "username": username,
                        "tenant_id": "demo-tenant",
                        "roles": ["developer", "project_manager"]
                    }
                },
                status_code=200
            )
        else:
            return JSONResponse(
                content={"detail": "Invalid credentials"},
                status_code=401
            )
    except Exception as e:
        logger.error(f"Login error: {e}")
        return JSONResponse(
            content={"detail": "Authentication failed"},
            status_code=500
        )


@app.get("/api/v1/auth/user")
async def get_user_v1(request: Request):
    """Proxy get user request to auth service."""
    # Mock user info for demo
    auth_header = request.headers.get("authorization", "")
    if "Bearer" in auth_header:
        return JSONResponse(
            content={
                "user_id": "demo-user",
                "username": "demo",
                "tenant_id": "demo-tenant",
                "roles": ["developer", "project_manager"]
            },
            status_code=200
        )
    else:
        return JSONResponse(
            content={"detail": "Not authenticated"},
            status_code=401
        )


# Legacy auth routes (without /api/v1)
@app.post("/auth/login")
async def login(request: Request):
    """Proxy login request to auth service."""
    body = await request.body()
    return await proxy_request(
        "auth", "/login", "POST",
        content=body,
        headers=dict(request.headers)
    )


@app.get("/auth/user")
async def get_user(request: Request):
    """Proxy get user request to auth service."""
    return await proxy_request(
        "auth", "/user", "GET",
        headers=dict(request.headers)
    )


# Project generation with /api/v1 prefix
@app.post("/api/v1/projects/generate")
async def generate_project_v1(request: Request):
    """Generate a new software project."""
    body = await request.body()
    import json
    
    try:
        project_data = json.loads(body)
        requirement = project_data.get("requirement", "")
        priority = project_data.get("priority", "medium")
        
        if not requirement:
            return JSONResponse(
                content={"detail": "Requirement is required"},
                status_code=400
            )
        
        project_id = f"proj_{int(time.time())}"
        
        # Log the generation request
        logger.info(f"Project generation started: {project_id}")
        logger.info(f"Requirement: {requirement}")
        logger.info(f"Priority: {priority}")
        
        # Step 1: Create requirement in orchestrator
        async with httpx.AsyncClient() as client:
            try:
                # Create requirement
                orchestrator_response = await client.post(
                    f"{SERVICES['orchestrator']}/requirements",
                    json={"requirement": requirement},
                    headers={
                        "Authorization": request.headers.get("Authorization", ""),
                        "Content-Type": "application/json"
                    }
                )
                
                if orchestrator_response.status_code != 200:
                    raise Exception(f"Orchestrator failed: {orchestrator_response.text}")
                
                orchestrator_data = orchestrator_response.json()
                requirement_id = orchestrator_data.get("requirement_id")
                tasks = orchestrator_data.get("tasks", [])
                
                # Step 2: Generate code using codegen service
                codegen_response = await client.post(
                    f"{SERVICES['codegen']}/generate",
                    json={
                        "tasks": [task["description"] for task in tasks],
                        "language": "python",
                        "framework": "fastapi",
                        "additional_requirements": f"Priority: {priority}"
                    }
                )
                
                if codegen_response.status_code != 200:
                    raise Exception(f"Codegen failed: {codegen_response.text}")
                
                codegen_data = codegen_response.json()
                
                return JSONResponse(
                    content={
                        "project_id": project_id,
                        "requirement_id": requirement_id,
                        "status": "completed",
                        "analysis": {
                            "complexity": "medium" if len(requirement) < 200 else "high",
                            "task_count": len(tasks),
                            "stack": f"{codegen_data.get('language', 'python')} + {codegen_data.get('framework', 'fastapi')}"
                        },
                        "generation_result": {
                            "repo_url": codegen_data.get("repo_url"),
                            "commit_id": codegen_data.get("commit_id"),
                            "generated_files": codegen_data.get("generated_files", []),
                            "project_path": codegen_data.get("project_path"),
                            "setup_instructions": codegen_data.get("setup_instructions")
                        },
                        "message": "Project generated successfully"
                    },
                    status_code=200
                )
                
            except httpx.RequestError as e:
                logger.error(f"Service communication error: {e}")
                return JSONResponse(
                    content={"detail": "Service communication failed"},
                    status_code=503
                )
            
    except Exception as e:
        logger.error(f"Project generation error: {e}")
        return JSONResponse(
            content={"detail": f"Project generation failed: {str(e)}"},
            status_code=500
        )


@app.get("/api/v1/projects/{project_name}/files")
async def get_project_files(project_name: str):
    """Get files from a generated project."""
    try:
        # Look for the project in generated_projects directory
        base_projects_dir = "/Users/a.pothula/workspace/unity/AiTeam/generated_projects"
        project_path = os.path.join(base_projects_dir, project_name)
        
        if not os.path.exists(project_path):
            return JSONResponse(
                content={"detail": "Project not found"},
                status_code=404
            )
        
        # Read project metadata
        metadata_path = os.path.join(project_path, "project_metadata.json")
        metadata = {}
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        
        # Get all files in the project
        files = {}
        for root, dirs, filenames in os.walk(project_path):
            for filename in filenames:
                if filename == "project_metadata.json":
                    continue
                    
                file_path = os.path.join(root, filename)
                relative_path = os.path.relpath(file_path, project_path)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        files[relative_path] = f.read()
                except UnicodeDecodeError:
                    # For binary files, just note they exist
                    files[relative_path] = "[Binary file]"
        
        return JSONResponse(
            content={
                "project_name": project_name,
                "metadata": metadata,
                "files": files,
                "file_count": len(files)
            },
            status_code=200
        )
        
    except Exception as e:
        logger.error(f"Error getting project files: {e}")
        return JSONResponse(
            content={"detail": f"Failed to get project files: {str(e)}"},
            status_code=500
        )


# Orchestrator routes
@app.post("/requirements")
async def create_requirement(request: Request):
    """Proxy requirement creation to orchestrator."""
    body = await request.body()
    return await proxy_request(
        "orchestrator", "/requirements", "POST",
        content=body,
        headers=dict(request.headers)
    )


@app.get("/requirements/{requirement_id}")
async def get_requirement(requirement_id: int, request: Request):
    """Get requirement by ID."""
    return await proxy_request(
        "orchestrator", f"/requirements/{requirement_id}", "GET",
        headers=dict(request.headers)
    )


# Codegen routes
@app.post("/codegen/{requirement_id}")
async def generate_code(requirement_id: int, request: Request):
    """Proxy code generation request."""
    body = await request.body()
    return await proxy_request(
        "codegen", f"/codegen/{requirement_id}", "POST",
        content=body,
        headers=dict(request.headers)
    )


# Executor routes
@app.post("/executor/run")
async def execute_code(request: Request):
    """Proxy code execution request."""
    body = await request.body()
    return await proxy_request(
        "executor", "/executor/run", "POST",
        content=body,
        headers=dict(request.headers)
    )


# Storage routes
@app.get("/storage/projects/{project_id}")
async def get_project(project_id: int, request: Request):
    """Get project by ID."""
    return await proxy_request(
        "storage", f"/storage/projects/{project_id}", "GET",
        headers=dict(request.headers)
    )


# Audit routes
@app.get("/audit/logs")
async def get_audit_logs(request: Request):
    """Get audit logs."""
    return await proxy_request(
        "audit", f"/audit/logs?{request.url.query}", "GET",
        headers=dict(request.headers)
    )


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting API Gateway on port 8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
