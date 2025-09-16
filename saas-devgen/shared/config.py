"""Shared configuration management across all services."""
import os
from typing import Optional


class Settings:
    """Application settings loaded from environment variables."""
    
    def __init__(self):
        # Database
        self.postgres_user = os.getenv("POSTGRES_USER", "devgen")
        self.postgres_password = os.getenv("POSTGRES_PASSWORD", "secret")
        self.postgres_db = os.getenv("POSTGRES_DB", "devgen")
        self.postgres_host = os.getenv("POSTGRES_HOST", "localhost")
        self.postgres_port = int(os.getenv("POSTGRES_PORT", "5432"))
        
        # MinIO
        self.minio_endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
        self.minio_access_key = os.getenv("MINIO_ROOT_USER", "admin")
        self.minio_secret_key = os.getenv("MINIO_ROOT_PASSWORD", "admin123")
        self.minio_secure = os.getenv("MINIO_SECURE", "false").lower() == "true"
        
        # Keycloak
        self.keycloak_url = os.getenv("KEYCLOAK_URL", "http://localhost:8080")
        self.keycloak_realm = os.getenv("KEYCLOAK_REALM", "master")
        self.keycloak_client_id = os.getenv("KEYCLOAK_CLIENT_ID", "admin-cli")
        
        # AI Configuration (from settings page)
        self.ai_provider = os.getenv("AI_PROVIDER", "openai")
        self.ai_model = os.getenv("AI_MODEL", "gpt-4")
        self.ai_api_key = os.getenv("AI_API_KEY")
        
        # Service URLs
        self.auth_service_url = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")
        self.orchestrator_url = os.getenv("ORCHESTRATOR_URL", "http://localhost:8002")
        self.codegen_service_url = os.getenv("CODEGEN_SERVICE_URL", "http://localhost:8003")
        self.executor_service_url = os.getenv("EXECUTOR_SERVICE_URL", "http://localhost:8004")
        self.storage_service_url = os.getenv("STORAGE_SERVICE_URL", "http://localhost:8005")
        self.audit_service_url = os.getenv("AUDIT_SERVICE_URL", "http://localhost:8006")
        self.profile_service_url = os.getenv("PROFILE_SERVICE_URL", "http://localhost:8007")
        
        # Logging
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_dir = os.getenv("LOG_DIR", "../../logs")


settings = Settings()


def get_database_url() -> str:
    """Get PostgreSQL database URL."""
    return f"postgresql://{settings.postgres_user}:{settings.postgres_password}@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"


def get_minio_config() -> dict:
    """Get MinIO configuration."""
    return {
        "endpoint": settings.minio_endpoint,
        "access_key": settings.minio_access_key,
        "secret_key": settings.minio_secret_key,
        "secure": settings.minio_secure
    }
