"""Storage Service - File and object storage with metadata management."""
import os
import json
import mimetypes
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from minio import Minio
from minio.error import S3Error
from shared.config import settings, get_minio_config
from shared.logging_utils import setup_logger
from shared.database import get_db
from shared.models import Project, Tenant
from sqlalchemy.orm import Session
import io

# Initialize logger
logger = setup_logger("storage-service", "storage-service.log")

app = FastAPI(title="Storage Service", version="1.0.0")


class FileMetadata(BaseModel):
    """File metadata model."""
    filename: str
    content_type: str
    size: int
    bucket: str
    object_name: str
    uploaded_at: datetime


class ProjectFilesResponse(BaseModel):
    """Project files response."""
    project_id: int
    repo_url: str
    files: List[FileMetadata]
    metadata: Dict[str, Any]


class StorageManager:
    """Manages file storage using MinIO."""
    
    def __init__(self):
        self.logger = logger
        self.minio_client = None
        self._initialize_minio()
    
    def _initialize_minio(self):
        """Initialize MinIO client."""
        try:
            config = get_minio_config()
            self.minio_client = Minio(
                endpoint=config["endpoint"],
                access_key=config["access_key"],
                secret_key=config["secret_key"],
                secure=config["secure"]
            )
            self.logger.info("MinIO client initialized successfully")
            
            # Ensure default bucket exists
            self._ensure_bucket_exists("projects")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize MinIO: {e}")
            self.minio_client = None
    
    def _ensure_bucket_exists(self, bucket_name: str):
        """Ensure bucket exists, create if not."""
        try:
            if not self.minio_client.bucket_exists(bucket_name):
                self.minio_client.make_bucket(bucket_name)
                self.logger.info(f"Created bucket: {bucket_name}")
        except S3Error as e:
            self.logger.error(f"Failed to create bucket {bucket_name}: {e}")
    
    def upload_file(self, tenant_id: int, project_id: int, filename: str, 
                   file_data: bytes, content_type: str = None) -> Dict[str, Any]:
        """Upload file to storage."""
        if not self.minio_client:
            raise Exception("MinIO client not available")
        
        try:
            bucket = "projects"
            object_name = f"{tenant_id}/{project_id}/{filename}"
            
            # Determine content type
            if not content_type:
                content_type, _ = mimetypes.guess_type(filename)
                content_type = content_type or "application/octet-stream"
            
            # Upload file
            file_stream = io.BytesIO(file_data)
            self.minio_client.put_object(
                bucket_name=bucket,
                object_name=object_name,
                data=file_stream,
                length=len(file_data),
                content_type=content_type
            )
            
            self.logger.info(f"Uploaded file: {object_name}")
            
            return {
                "bucket": bucket,
                "object_name": object_name,
                "filename": filename,
                "content_type": content_type,
                "size": len(file_data),
                "uploaded_at": datetime.utcnow()
            }
            
        except S3Error as e:
            self.logger.error(f"Failed to upload file {filename}: {e}")
            raise Exception(f"File upload failed: {e}")
    
    def download_file(self, bucket: str, object_name: str) -> bytes:
        """Download file from storage."""
        if not self.minio_client:
            raise Exception("MinIO client not available")
        
        try:
            response = self.minio_client.get_object(bucket, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            
            self.logger.info(f"Downloaded file: {object_name}")
            return data
            
        except S3Error as e:
            self.logger.error(f"Failed to download file {object_name}: {e}")
            raise Exception(f"File download failed: {e}")
    
    def list_files(self, tenant_id: int, project_id: int) -> List[Dict[str, Any]]:
        """List files for a project."""
        if not self.minio_client:
            return []
        
        try:
            bucket = "projects"
            prefix = f"{tenant_id}/{project_id}/"
            
            objects = self.minio_client.list_objects(bucket, prefix=prefix, recursive=True)
            files = []
            
            for obj in objects:
                # Get object metadata
                stat = self.minio_client.stat_object(bucket, obj.object_name)
                
                files.append({
                    "filename": obj.object_name.split("/")[-1],
                    "content_type": stat.content_type,
                    "size": stat.size,
                    "bucket": bucket,
                    "object_name": obj.object_name,
                    "uploaded_at": stat.last_modified
                })
            
            self.logger.info(f"Listed {len(files)} files for project {project_id}")
            return files
            
        except S3Error as e:
            self.logger.error(f"Failed to list files for project {project_id}: {e}")
            return []
    
    def delete_file(self, bucket: str, object_name: str):
        """Delete file from storage."""
        if not self.minio_client:
            raise Exception("MinIO client not available")
        
        try:
            self.minio_client.remove_object(bucket, object_name)
            self.logger.info(f"Deleted file: {object_name}")
            
        except S3Error as e:
            self.logger.error(f"Failed to delete file {object_name}: {e}")
            raise Exception(f"File deletion failed: {e}")
    
    def upload_project_files(self, tenant_id: int, project_id: int, 
                           project_path: str) -> List[Dict[str, Any]]:
        """Upload entire project directory to storage."""
        uploaded_files = []
        
        if not os.path.exists(project_path):
            raise Exception(f"Project path not found: {project_path}")
        
        for root, dirs, files in os.walk(project_path):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, project_path)
                
                try:
                    with open(file_path, "rb") as f:
                        file_data = f.read()
                    
                    result = self.upload_file(
                        tenant_id=tenant_id,
                        project_id=project_id,
                        filename=relative_path,
                        file_data=file_data
                    )
                    uploaded_files.append(result)
                    
                except Exception as e:
                    self.logger.error(f"Failed to upload file {relative_path}: {e}")
        
        self.logger.info(f"Uploaded {len(uploaded_files)} files for project {project_id}")
        return uploaded_files


storage_manager = StorageManager()


@app.post("/storage/upload/{project_id}")
async def upload_file(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a file to project storage."""
    logger.info(f"File upload request for project {project_id}: {file.filename}")
    
    try:
        # Verify project exists
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Read file data
        file_data = await file.read()
        
        # Upload to storage
        result = storage_manager.upload_file(
            tenant_id=project.tenant_id,
            project_id=project_id,
            filename=file.filename,
            file_data=file_data,
            content_type=file.content_type
        )
        
        logger.info(f"File uploaded successfully: {file.filename}")
        return result
        
    except Exception as e:
        logger.error(f"File upload failed for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="File upload failed"
        )


@app.get("/storage/download/{project_id}/{filename}")
async def download_file(
    project_id: int,
    filename: str,
    db: Session = Depends(get_db)
):
    """Download a file from project storage."""
    logger.info(f"File download request for project {project_id}: {filename}")
    
    try:
        # Verify project exists
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Download from storage
        bucket = "projects"
        object_name = f"{project.tenant_id}/{project_id}/{filename}"
        
        file_data = storage_manager.download_file(bucket, object_name)
        
        # Determine content type
        content_type, _ = mimetypes.guess_type(filename)
        content_type = content_type or "application/octet-stream"
        
        # Return file as streaming response
        return StreamingResponse(
            io.BytesIO(file_data),
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"File download failed for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )


@app.get("/storage/projects/{project_id}", response_model=ProjectFilesResponse)
async def get_project_files(project_id: int, db: Session = Depends(get_db)):
    """Get all files for a project."""
    logger.info(f"Project files request for project {project_id}")
    
    try:
        # Verify project exists
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # List files
        files = storage_manager.list_files(project.tenant_id, project_id)
        
        return ProjectFilesResponse(
            project_id=project_id,
            repo_url=project.repo_url,
            files=[FileMetadata(**file) for file in files],
            metadata=project.project_metadata or {}
        )
        
    except Exception as e:
        logger.error(f"Failed to get project files for {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve project files"
        )


@app.delete("/storage/projects/{project_id}/{filename}")
async def delete_file(
    project_id: int,
    filename: str,
    db: Session = Depends(get_db)
):
    """Delete a file from project storage."""
    logger.info(f"File deletion request for project {project_id}: {filename}")
    
    try:
        # Verify project exists
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Delete from storage
        bucket = "projects"
        object_name = f"{project.tenant_id}/{project_id}/{filename}"
        
        storage_manager.delete_file(bucket, object_name)
        
        return {"message": f"File {filename} deleted successfully"}
        
    except Exception as e:
        logger.error(f"File deletion failed for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="File deletion failed"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    minio_status = "available" if storage_manager.minio_client else "unavailable"
    return {
        "status": "healthy",
        "service": "storage-service",
        "minio": minio_status,
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Storage Service on port 8005")
    uvicorn.run(app, host="0.0.0.0", port=8005)
