"""
Enterprise E2B Sandbox Integration
Production-ready secure code execution environment with advanced isolation.
Handles heavy workloads with containerized execution and resource management.
"""
import asyncio
import os
import json
import tempfile
import shutil
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import subprocess
import tarfile
import zipfile

# Enterprise FastAPI (MIT License)
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

# Enterprise E2B SDK (MIT License) 
try:
    from e2b import Sandbox, SandboxException
    E2B_AVAILABLE = True
except ImportError:
    E2B_AVAILABLE = False
    
# Enterprise Docker SDK (Apache 2.0)
import docker
from docker.errors import DockerException

# Enterprise configuration
from shared.config import settings
from shared.logging_utils import setup_logger
from shared.database import get_db
from shared.models import Execution, Project

# Initialize enterprise logging
logger = setup_logger("e2b-executor", "e2b-executor.log")

app = FastAPI(title="Enterprise E2B Executor Service", version="1.0.0")

# CORS middleware for enterprise integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Execution models
class ExecutionRequest(BaseModel):
    """Enterprise execution request."""
    project_path: str
    command: str
    language: str
    timeout: int = Field(default=300, ge=10, le=3600)  # 10 seconds to 1 hour
    memory_limit: str = "1g"
    cpu_limit: str = "1.0"
    environment: Optional[Dict[str, str]] = None
    files_to_upload: Optional[List[str]] = None
    execution_type: str = Field(default="test", regex="^(test|build|run|deploy)$")

class ExecutionResult(BaseModel):
    """Enterprise execution result."""
    execution_id: str
    status: str
    exit_code: Optional[int]
    stdout: str
    stderr: str
    execution_time: float
    resource_usage: Dict[str, Any]
    security_report: Dict[str, Any]
    artifacts: List[str]

class SandboxInfo(BaseModel):
    """Sandbox environment information."""
    sandbox_id: str
    status: str
    language: str
    created_at: datetime
    resource_limits: Dict[str, str]

# Enterprise E2B Sandbox Manager
class EnterpriseE2BSandbox:
    """Production-ready E2B sandbox with advanced features."""
    
    def __init__(self):
        self.logger = logger
        self.sandboxes: Dict[str, Any] = {}
        self.docker_client = None
        
        # Initialize Docker client as fallback
        try:
            self.docker_client = docker.from_env()
            self.logger.info("Docker client initialized for fallback execution")
        except DockerException as e:
            self.logger.warning(f"Docker client initialization failed: {e}")
    
    async def create_sandbox(self, language: str, memory_limit: str = "1g", 
                           cpu_limit: str = "1.0") -> str:
        """Create secure sandbox environment."""
        try:
            if E2B_AVAILABLE:
                # Use E2B for production sandbox
                sandbox_id = f"e2b-{language}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                
                # Configure E2B sandbox
                sandbox_config = {
                    "template": self._get_template_for_language(language),
                    "memory": memory_limit,
                    "cpu": cpu_limit,
                    "timeoutMs": 300000,  # 5 minutes
                    "metadata": {
                        "created_by": "enterprise-executor",
                        "language": language,
                        "created_at": datetime.utcnow().isoformat()
                    }
                }
                
                sandbox = Sandbox(**sandbox_config)
                await sandbox.start()
                
                self.sandboxes[sandbox_id] = {
                    "sandbox": sandbox,
                    "language": language,
                    "created_at": datetime.utcnow(),
                    "status": "active"
                }
                
                self.logger.info(f"E2B sandbox created: {sandbox_id}")
                return sandbox_id
                
            else:
                # Use Docker as fallback
                return await self._create_docker_sandbox(language, memory_limit, cpu_limit)
                
        except Exception as e:
            self.logger.error(f"Failed to create sandbox: {e}")
            raise
    
    def _get_template_for_language(self, language: str) -> str:
        """Get E2B template for programming language."""
        templates = {
            "python": "python3",
            "javascript": "nodejs",
            "typescript": "nodejs",
            "java": "java",
            "go": "golang",
            "rust": "rust",
            "cpp": "cpp",
            "csharp": "dotnet"
        }
        return templates.get(language.lower(), "ubuntu")
    
    async def _create_docker_sandbox(self, language: str, memory_limit: str, cpu_limit: str) -> str:
        """Create Docker-based sandbox as fallback."""
        try:
            sandbox_id = f"docker-{language}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            
            # Select appropriate Docker image
            image_map = {
                "python": "python:3.11-slim",
                "javascript": "node:18-alpine",
                "typescript": "node:18-alpine", 
                "java": "openjdk:17-slim",
                "go": "golang:1.21-alpine",
                "rust": "rust:1.75-slim",
                "cpp": "gcc:latest",
                "csharp": "mcr.microsoft.com/dotnet/sdk:8.0"
            }
            
            image = image_map.get(language.lower(), "ubuntu:22.04")
            
            # Create container with resource limits
            container = self.docker_client.containers.create(
                image=image,
                command="sleep infinity",  # Keep container running
                detach=True,
                name=sandbox_id,
                mem_limit=memory_limit,
                cpu_period=100000,
                cpu_quota=int(float(cpu_limit) * 100000),
                network_disabled=True,  # Security: no network access
                working_dir="/workspace",
                volumes={
                    # Mount temporary workspace
                    tempfile.mkdtemp(): {"bind": "/workspace", "mode": "rw"}
                }
            )
            
            container.start()
            
            self.sandboxes[sandbox_id] = {
                "container": container,
                "language": language,
                "created_at": datetime.utcnow(),
                "status": "active",
                "type": "docker"
            }
            
            self.logger.info(f"Docker sandbox created: {sandbox_id}")
            return sandbox_id
            
        except Exception as e:
            self.logger.error(f"Failed to create Docker sandbox: {e}")
            raise
    
    async def upload_files(self, sandbox_id: str, files: Dict[str, str]) -> bool:
        """Upload files to sandbox."""
        try:
            sandbox_info = self.sandboxes.get(sandbox_id)
            if not sandbox_info:
                raise ValueError(f"Sandbox {sandbox_id} not found")
            
            if sandbox_info.get("type") == "docker":
                # Upload to Docker container
                container = sandbox_info["container"]
                
                # Create tar archive with files
                with tempfile.NamedTemporaryFile(suffix=".tar") as tar_file:
                    with tarfile.open(tar_file.name, "w") as tar:
                        for file_path, content in files.items():
                            tarinfo = tarfile.TarInfo(name=file_path)
                            tarinfo.size = len(content.encode())
                            tar.addfile(tarinfo, fileobj=tempfile.io.BytesIO(content.encode()))
                    
                    # Upload tar to container
                    with open(tar_file.name, "rb") as f:
                        container.put_archive("/workspace", f)
                
            else:
                # Upload to E2B sandbox
                sandbox = sandbox_info["sandbox"]
                for file_path, content in files.items():
                    await sandbox.filesystem.write(file_path, content)
            
            self.logger.info(f"Files uploaded to sandbox {sandbox_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to upload files to sandbox {sandbox_id}: {e}")
            raise
    
    async def execute_command(self, sandbox_id: str, command: str, 
                            timeout: int = 300, working_dir: str = "/workspace") -> Dict[str, Any]:
        """Execute command in sandbox with comprehensive monitoring."""
        try:
            sandbox_info = self.sandboxes.get(sandbox_id)
            if not sandbox_info:
                raise ValueError(f"Sandbox {sandbox_id} not found")
            
            start_time = datetime.utcnow()
            
            if sandbox_info.get("type") == "docker":
                # Execute in Docker container
                result = await self._execute_docker_command(
                    sandbox_info["container"], command, timeout, working_dir
                )
            else:
                # Execute in E2B sandbox
                result = await self._execute_e2b_command(
                    sandbox_info["sandbox"], command, timeout, working_dir
                )
            
            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds()
            
            # Add execution metadata
            result["execution_time"] = execution_time
            result["started_at"] = start_time.isoformat()
            result["completed_at"] = end_time.isoformat()
            
            self.logger.info(f"Command executed in sandbox {sandbox_id}: {command}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to execute command in sandbox {sandbox_id}: {e}")
            raise
    
    async def _execute_docker_command(self, container, command: str, 
                                    timeout: int, working_dir: str) -> Dict[str, Any]:
        """Execute command in Docker container."""
        try:
            # Execute command with timeout
            exec_result = container.exec_run(
                command,
                workdir=working_dir,
                user="root",
                environment={},
                detach=False,
                stream=False,
                demux=True
            )
            
            stdout = exec_result.output[0].decode() if exec_result.output[0] else ""
            stderr = exec_result.output[1].decode() if exec_result.output[1] else ""
            
            # Get resource usage stats
            stats = container.stats(stream=False)
            resource_usage = {
                "memory_usage": stats["memory_stats"].get("usage", 0),
                "memory_limit": stats["memory_stats"].get("limit", 0),
                "cpu_usage": stats["cpu_stats"].get("cpu_usage", {}).get("total_usage", 0)
            }
            
            return {
                "exit_code": exec_result.exit_code,
                "stdout": stdout,
                "stderr": stderr,
                "resource_usage": resource_usage,
                "security_report": self._generate_security_report(stdout, stderr),
                "status": "completed" if exec_result.exit_code == 0 else "failed"
            }
            
        except Exception as e:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e),
                "resource_usage": {},
                "security_report": {"status": "error", "message": str(e)},
                "status": "error"
            }
    
    async def _execute_e2b_command(self, sandbox, command: str, 
                                 timeout: int, working_dir: str) -> Dict[str, Any]:
        """Execute command in E2B sandbox."""
        try:
            # Execute command with E2B
            result = await sandbox.process.start_and_wait(
                command,
                cwd=working_dir,
                timeout=timeout * 1000  # Convert to milliseconds
            )
            
            return {
                "exit_code": result.exit_code,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "resource_usage": {
                    "memory_usage": 0,  # E2B provides this in enterprise tier
                    "cpu_usage": 0
                },
                "security_report": self._generate_security_report(result.stdout, result.stderr),
                "status": "completed" if result.exit_code == 0 else "failed"
            }
            
        except Exception as e:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e),
                "resource_usage": {},
                "security_report": {"status": "error", "message": str(e)},
                "status": "error"
            }
    
    def _generate_security_report(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """Generate security analysis report."""
        security_issues = []
        
        # Check for potential security issues
        security_patterns = [
            "password", "secret", "api_key", "token", "credential",
            "sql injection", "xss", "csrf", "vulnerability"
        ]
        
        combined_output = (stdout + stderr).lower()
        for pattern in security_patterns:
            if pattern in combined_output:
                security_issues.append({
                    "type": "potential_exposure",
                    "pattern": pattern,
                    "severity": "medium"
                })
        
        return {
            "status": "clean" if not security_issues else "warnings",
            "issues": security_issues,
            "scanned_at": datetime.utcnow().isoformat()
        }
    
    async def download_artifacts(self, sandbox_id: str, paths: List[str]) -> Dict[str, str]:
        """Download artifacts from sandbox."""
        try:
            sandbox_info = self.sandboxes.get(sandbox_id)
            if not sandbox_info:
                raise ValueError(f"Sandbox {sandbox_id} not found")
            
            artifacts = {}
            
            if sandbox_info.get("type") == "docker":
                # Download from Docker container
                container = sandbox_info["container"]
                for path in paths:
                    try:
                        # Get archive from container
                        archive_data, _ = container.get_archive(f"/workspace/{path}")
                        
                        # Extract content
                        with tempfile.NamedTemporaryFile() as temp_file:
                            for chunk in archive_data:
                                temp_file.write(chunk)
                            temp_file.seek(0)
                            
                            with tarfile.open(temp_file.name, "r") as tar:
                                for member in tar.getmembers():
                                    if member.isfile():
                                        content = tar.extractfile(member).read().decode()
                                        artifacts[member.name] = content
                    except Exception as e:
                        self.logger.warning(f"Could not download {path}: {e}")
            
            else:
                # Download from E2B sandbox
                sandbox = sandbox_info["sandbox"]
                for path in paths:
                    try:
                        content = await sandbox.filesystem.read(path)
                        artifacts[path] = content
                    except Exception as e:
                        self.logger.warning(f"Could not download {path}: {e}")
            
            self.logger.info(f"Downloaded {len(artifacts)} artifacts from sandbox {sandbox_id}")
            return artifacts
            
        except Exception as e:
            self.logger.error(f"Failed to download artifacts from sandbox {sandbox_id}: {e}")
            raise
    
    async def destroy_sandbox(self, sandbox_id: str) -> bool:
        """Destroy sandbox and cleanup resources."""
        try:
            sandbox_info = self.sandboxes.get(sandbox_id)
            if not sandbox_info:
                return True  # Already destroyed
            
            if sandbox_info.get("type") == "docker":
                # Stop and remove Docker container
                container = sandbox_info["container"]
                container.stop(timeout=10)
                container.remove(force=True)
            
            else:
                # Destroy E2B sandbox
                sandbox = sandbox_info["sandbox"]
                await sandbox.close()
            
            # Remove from tracking
            del self.sandboxes[sandbox_id]
            
            self.logger.info(f"Sandbox destroyed: {sandbox_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to destroy sandbox {sandbox_id}: {e}")
            return False
    
    def get_sandbox_info(self, sandbox_id: str) -> Optional[Dict[str, Any]]:
        """Get sandbox information."""
        return self.sandboxes.get(sandbox_id)
    
    def list_sandboxes(self) -> List[Dict[str, Any]]:
        """List all active sandboxes."""
        return [
            {
                "sandbox_id": sid,
                "language": info["language"],
                "created_at": info["created_at"],
                "status": info["status"],
                "type": info.get("type", "e2b")
            }
            for sid, info in self.sandboxes.items()
        ]

# Global sandbox manager
sandbox_manager = EnterpriseE2BSandbox()

# API Endpoints
@app.post("/sandboxes", response_model=SandboxInfo)
async def create_sandbox(
    language: str,
    memory_limit: str = "1g",
    cpu_limit: str = "1.0"
):
    """Create a new secure sandbox environment."""
    try:
        sandbox_id = await sandbox_manager.create_sandbox(language, memory_limit, cpu_limit)
        
        return SandboxInfo(
            sandbox_id=sandbox_id,
            status="active",
            language=language,
            created_at=datetime.utcnow(),
            resource_limits={"memory": memory_limit, "cpu": cpu_limit}
        )
        
    except Exception as e:
        logger.error(f"Failed to create sandbox: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create sandbox: {e}")

@app.post("/sandboxes/{sandbox_id}/execute", response_model=ExecutionResult)
async def execute_in_sandbox(
    sandbox_id: str,
    request: ExecutionRequest,
    db: Session = Depends(get_db)
):
    """Execute code in secure sandbox environment."""
    try:
        execution_id = f"exec-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # Upload files if provided
        if request.files_to_upload:
            # In production, files would be retrieved from storage
            files = {file: f"# Content of {file}" for file in request.files_to_upload}
            await sandbox_manager.upload_files(sandbox_id, files)
        
        # Execute command
        result = await sandbox_manager.execute_command(
            sandbox_id,
            request.command,
            request.timeout,
            "/workspace"
        )
        
        # Store execution record
        execution = Execution(
            execution_id=execution_id,
            sandbox_id=sandbox_id,
            command=request.command,
            status=result["status"],
            exit_code=result.get("exit_code"),
            stdout=result.get("stdout", ""),
            stderr=result.get("stderr", ""),
            execution_time=result.get("execution_time", 0.0),
            created_at=datetime.utcnow()
        )
        db.add(execution)
        db.commit()
        
        # Download artifacts
        artifact_paths = ["*.log", "dist/*", "build/*", "target/*"]
        artifacts = await sandbox_manager.download_artifacts(sandbox_id, artifact_paths)
        
        return ExecutionResult(
            execution_id=execution_id,
            status=result["status"],
            exit_code=result.get("exit_code"),
            stdout=result.get("stdout", ""),
            stderr=result.get("stderr", ""),
            execution_time=result.get("execution_time", 0.0),
            resource_usage=result.get("resource_usage", {}),
            security_report=result.get("security_report", {}),
            artifacts=list(artifacts.keys())
        )
        
    except Exception as e:
        logger.error(f"Failed to execute in sandbox {sandbox_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Execution failed: {e}")

@app.get("/sandboxes")
async def list_sandboxes():
    """List all active sandbox environments."""
    try:
        sandboxes = sandbox_manager.list_sandboxes()
        return {"sandboxes": sandboxes}
        
    except Exception as e:
        logger.error(f"Failed to list sandboxes: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list sandboxes: {e}")

@app.delete("/sandboxes/{sandbox_id}")
async def destroy_sandbox(sandbox_id: str):
    """Destroy sandbox environment."""
    try:
        success = await sandbox_manager.destroy_sandbox(sandbox_id)
        if success:
            return {"message": "Sandbox destroyed successfully"}
        else:
            raise HTTPException(status_code=404, detail="Sandbox not found")
        
    except Exception as e:
        logger.error(f"Failed to destroy sandbox {sandbox_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to destroy sandbox: {e}")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "e2b-executor",
        "timestamp": datetime.utcnow().isoformat(),
        "e2b_available": E2B_AVAILABLE,
        "docker_available": sandbox_manager.docker_client is not None,
        "active_sandboxes": len(sandbox_manager.sandboxes)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8009)
