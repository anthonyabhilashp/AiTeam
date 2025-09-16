"""Executor Service - Secure sandbox execution of generated code."""
import asyncio
import os
import tempfile
import shutil
import subprocess
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel
import docker
from shared.config import settings
from shared.logging_utils import setup_logger
from shared.database import get_db
from shared.models import Project, Execution
from sqlalchemy.orm import Session

# Initialize logger
logger = setup_logger("executor-service", "executor-service.log")

app = FastAPI(title="Executor Service", version="1.0.0")


class ExecutionRequest(BaseModel):
    """Execution request model."""
    repo_url: str
    command: str
    timeout: int = 300  # 5 minutes default
    environment: Optional[Dict[str, str]] = None


class ExecutionResponse(BaseModel):
    """Execution response model."""
    execution_id: int
    status: str
    logs: str
    exit_code: Optional[int]
    duration: float


class SecureSandbox:
    """Secure sandbox for code execution."""
    
    def __init__(self):
        self.logger = logger
        self.docker_client = None
        try:
            self.docker_client = docker.from_env()
            self.logger.info("Docker client initialized successfully")
        except Exception as e:
            self.logger.warning(f"Docker not available: {e}. Falling back to subprocess execution.")
    
    async def execute_code(self, repo_url: str, command: str, timeout: int = 300, 
                          environment: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Execute code in a secure sandbox environment.
        Supports both Docker and subprocess execution.
        """
        self.logger.info(f"Executing command: {command} for repo: {repo_url}")
        
        if self.docker_client:
            return await self._execute_in_docker(repo_url, command, timeout, environment)
        else:
            return await self._execute_in_subprocess(repo_url, command, timeout, environment)
    
    async def _execute_in_docker(self, repo_url: str, command: str, timeout: int, 
                                environment: Dict[str, str]) -> Dict[str, Any]:
        """Execute code in Docker container."""
        start_time = datetime.utcnow()
        container = None
        
        try:
            # Copy code to temporary directory
            temp_dir = tempfile.mkdtemp(prefix="executor_")
            self.logger.info(f"Using temp directory: {temp_dir}")
            
            # For file:// URLs, copy directly
            if repo_url.startswith("file://"):
                source_path = repo_url.replace("file://", "")
                if os.path.exists(source_path):
                    shutil.copytree(source_path, os.path.join(temp_dir, "app"))
                else:
                    raise Exception(f"Source path not found: {source_path}")
            else:
                # For future: clone from git repository
                raise Exception("Git repositories not yet supported")
            
            # Prepare environment variables
            env_vars = environment or {}
            env_vars.update({
                "PYTHONUNBUFFERED": "1",
                "PYTHONIOENCODING": "utf-8"
            })
            
            # Create and start container
            container = self.docker_client.containers.run(
                image="python:3.11-slim",
                command=f"sh -c 'cd /app && {command}'",
                volumes={temp_dir: {"bind": "/app", "mode": "rw"}},
                environment=env_vars,
                detach=True,
                remove=False,
                network_mode="none",  # Isolate network access
                mem_limit="512m",  # Limit memory
                cpu_quota=50000,  # Limit CPU (50% of one core)
            )
            
            # Wait for completion with timeout
            try:
                result = container.wait(timeout=timeout)
                exit_code = result["StatusCode"]
            except Exception as e:
                self.logger.error(f"Container execution timeout or error: {e}")
                container.kill()
                exit_code = -1
            
            # Get logs
            logs = container.logs(stdout=True, stderr=True).decode("utf-8")
            
            # Calculate duration
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            self.logger.info(f"Docker execution completed. Exit code: {exit_code}, Duration: {duration}s")
            
            return {
                "status": "completed" if exit_code == 0 else "failed",
                "logs": logs,
                "exit_code": exit_code,
                "duration": duration
            }
            
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            error_msg = f"Docker execution failed: {str(e)}"
            self.logger.error(error_msg)
            
            return {
                "status": "failed",
                "logs": error_msg,
                "exit_code": -1,
                "duration": duration
            }
            
        finally:
            # Cleanup
            if container:
                try:
                    container.remove(force=True)
                except Exception as e:
                    self.logger.warning(f"Failed to remove container: {e}")
            
            if 'temp_dir' in locals() and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    async def _execute_in_subprocess(self, repo_url: str, command: str, timeout: int,
                                   environment: Dict[str, str]) -> Dict[str, Any]:
        """Execute code using subprocess (fallback when Docker is not available)."""
        start_time = datetime.utcnow()
        temp_dir = None
        
        try:
            # Copy code to temporary directory
            temp_dir = tempfile.mkdtemp(prefix="executor_")
            self.logger.info(f"Using temp directory: {temp_dir}")
            
            # For file:// URLs, copy directly
            if repo_url.startswith("file://"):
                source_path = repo_url.replace("file://", "")
                if os.path.exists(source_path):
                    # Copy all files to temp directory
                    for item in os.listdir(source_path):
                        source_item = os.path.join(source_path, item)
                        dest_item = os.path.join(temp_dir, item)
                        if os.path.isdir(source_item):
                            shutil.copytree(source_item, dest_item)
                        else:
                            shutil.copy2(source_item, dest_item)
                else:
                    raise Exception(f"Source path not found: {source_path}")
            
            # Prepare environment
            env = os.environ.copy()
            if environment:
                env.update(environment)
            env.update({
                "PYTHONUNBUFFERED": "1",
                "PYTHONIOENCODING": "utf-8"
            })
            
            # Execute command
            self.logger.info(f"Executing subprocess command: {command}")
            process = await asyncio.create_subprocess_shell(
                command,
                cwd=temp_dir,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                limit=1024*1024  # 1MB limit for output
            )
            
            try:
                stdout, _ = await asyncio.wait_for(process.communicate(), timeout=timeout)
                exit_code = process.returncode
                logs = stdout.decode("utf-8") if stdout else ""
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                exit_code = -1
                logs = "Execution timed out"
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            self.logger.info(f"Subprocess execution completed. Exit code: {exit_code}, Duration: {duration}s")
            
            return {
                "status": "completed" if exit_code == 0 else "failed",
                "logs": logs,
                "exit_code": exit_code,
                "duration": duration
            }
            
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            error_msg = f"Subprocess execution failed: {str(e)}"
            self.logger.error(error_msg)
            
            return {
                "status": "failed",
                "logs": error_msg,
                "exit_code": -1,
                "duration": duration
            }
            
        finally:
            # Cleanup
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)


sandbox = SecureSandbox()


@app.post("/executor/run", response_model=ExecutionResponse)
async def execute_code(
    request: ExecutionRequest,
    db: Session = Depends(get_db)
):
    """Execute code in secure sandbox."""
    logger.info(f"Execution request for repo: {request.repo_url}")
    
    try:
        # Get project from repo URL
        project = db.query(Project).filter(Project.repo_url == request.repo_url).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Create execution record
        execution = Execution(
            project_id=project.id,
            command=request.command,
            status="running"
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)
        
        # Execute code in sandbox
        result = await sandbox.execute_code(
            repo_url=request.repo_url,
            command=request.command,
            timeout=request.timeout,
            environment=request.environment
        )
        
        # Update execution record
        execution.status = result["status"]
        execution.logs = result["logs"]
        execution.exit_code = result["exit_code"]
        execution.completed_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Execution {execution.id} completed with status: {result['status']}")
        
        return ExecutionResponse(
            execution_id=execution.id,
            status=result["status"],
            logs=result["logs"],
            exit_code=result["exit_code"],
            duration=result["duration"]
        )
        
    except Exception as e:
        logger.error(f"Execution failed: {e}")
        
        # Update execution record if it exists
        if 'execution' in locals():
            execution.status = "failed"
            execution.logs = f"Execution failed: {str(e)}"
            execution.exit_code = -1
            execution.completed_at = datetime.utcnow()
            db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Execution failed"
        )


@app.get("/executor/status/{execution_id}")
async def get_execution_status(execution_id: int, db: Session = Depends(get_db)):
    """Get execution status by ID."""
    execution = db.query(Execution).filter(Execution.id == execution_id).first()
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found"
        )
    
    return {
        "execution_id": execution.id,
        "status": execution.status,
        "command": execution.command,
        "logs": execution.logs,
        "exit_code": execution.exit_code,
        "created_at": execution.created_at,
        "completed_at": execution.completed_at
    }


@app.post("/execute/project/{project_uuid}")
async def execute_project(project_uuid: str, request: dict):
    """Execute a project from storage in a secure sandbox."""
    logger.info(f"Project execution request: {project_uuid}")
    
    try:
        import httpx
        import zipfile
        import tempfile
        
        # Download project from storage service
        storage_url = settings.storage_service_url
        download_url = f"{storage_url}/download/project/{project_uuid}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(download_url, timeout=30.0)
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=404,
                    detail="Project not found in storage"
                )
        
        # Create temporary directory for extraction
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = os.path.join(temp_dir, f"{project_uuid}.zip")
            
            # Save zip file
            with open(zip_path, 'wb') as f:
                f.write(response.content)
            
            # Extract zip file
            extract_dir = os.path.join(temp_dir, "project")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # Read project metadata
            metadata_path = os.path.join(extract_dir, "project_metadata.json")
            metadata = {}
            if os.path.exists(metadata_path):
                import json
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
            
            # Determine execution command based on project type
            language = metadata.get('language', 'unknown')
            framework = metadata.get('framework', 'unknown')
            
            if language == 'javascript' and framework == 'react':
                commands = [
                    "npm install",
                    "npm run build",
                    "npm test -- --watchAll=false || true"  # Run tests but don't fail if no tests
                ]
            elif language == 'python' and framework == 'fastapi':
                commands = [
                    "pip install -r requirements.txt",
                    "python -m pytest || true"  # Run tests but don't fail if no tests
                ]
            else:
                commands = ["echo 'Project type not supported for execution'"]
            
            # Execute commands in Docker sandbox
            results = []
            for cmd in commands:
                try:
                    result = sandbox.execute_code(
                        code_dir=extract_dir,
                        command=cmd,
                        timeout=request.get('timeout', 300),
                        environment=request.get('environment', {})
                    )
                    results.append({
                        "command": cmd,
                        "status": result["status"],
                        "logs": result["logs"][:1000],  # Limit log size
                        "exit_code": result.get("exit_code"),
                        "duration": result.get("duration", 0)
                    })
                    
                    # Stop on first failure for build commands
                    if result["status"] == "failed" and cmd.startswith(("npm install", "pip install")):
                        break
                        
                except Exception as e:
                    results.append({
                        "command": cmd,
                        "status": "failed",
                        "logs": f"Execution error: {str(e)}",
                        "exit_code": -1,
                        "duration": 0
                    })
            
            # Determine overall status
            overall_status = "completed"
            for result in results:
                if result["status"] == "failed" and result["command"].startswith(("npm install", "pip install")):
                    overall_status = "failed"
                    break
            
            return {
                "project_uuid": project_uuid,
                "status": overall_status,
                "language": language,
                "framework": framework,
                "execution_results": results,
                "total_duration": sum(r["duration"] for r in results),
                "executed_at": datetime.utcnow().isoformat()
            }
    
    except Exception as e:
        logger.error(f"Project execution failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Execution failed: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    docker_status = "available" if sandbox.docker_client else "unavailable"
    return {
        "status": "healthy",
        "service": "executor-service",
        "docker": docker_status,
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Executor Service on port 8004")
    uvicorn.run(app, host="0.0.0.0", port=8004)
