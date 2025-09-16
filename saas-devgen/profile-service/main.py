"""Profile Service - Enterprise user profiles and AI provider configuration."""
import sys
import os
# Add the parent directory to sys.path for shared modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import json
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, DateTime, create_engine, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from shared.config import get_database_url
from shared.logging_utils import setup_logger
import jwt
from passlib.context import CryptContext

# Initialize logger
logger = setup_logger("profile-service", "profile-service.log")

app = FastAPI(
    title="Profile Service",
    description="Enterprise user profiles and AI provider configuration",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security
security = HTTPBearer()

# Database setup
DATABASE_URL = get_database_url()
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Tenant(Base):
    """Tenant model."""
    __tablename__ = "aiteam.tenants"
    __table_args__ = {"schema": "aiteam"}
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    org_id = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default="now()")
    updated_at = Column(DateTime(timezone=True), onupdate="now()")
    
    # Relationships
    users = relationship("User", back_populates="tenant")

class User(Base):
    """User model."""
    __tablename__ = "aiteam.users"
    __table_args__ = {"schema": "aiteam"}
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    tenant_id = Column(Integer, ForeignKey("aiteam.tenants.id"), nullable=False)
    roles = Column(JSON, default=list)
    is_active = Column(Integer, default=1)  # Using Integer for SQLite compatibility
    created_at = Column(DateTime(timezone=True), server_default="now()")
    updated_at = Column(DateTime(timezone=True), onupdate="now()")
    
    # Relationships
    tenant = relationship("Tenant", back_populates="users")

class TenantSettings(Base):
    __tablename__ = "tenant_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, unique=True, index=True, default="demo-tenant")
    ai_provider = Column(String, default="openai")
    ai_model = Column(String, default="gpt-4")
    api_key = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

class SettingsRequest(BaseModel):
    ai_provider: str
    ai_model: str
    api_key: str

class SettingsResponse(BaseModel):
    ai_provider: str
    ai_model: str
    api_key: str

class OpenRouterModel(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    context_length: Optional[int] = None
    pricing: Optional[Dict[str, Any]] = None

class UserResponse(BaseModel):
    """User response model."""
    user_id: str
    username: str
    email: str
    tenant_id: int
    roles: List[str]
    is_active: bool

class UserRegistrationRequest(BaseModel):
    """User registration request model."""
    username: str
    email: str
    password: str
    tenant_id: Optional[int] = None

class UserRegistrationResponse(BaseModel):
    """User registration response model."""
    user_id: str
    username: str
    email: str
    tenant_id: int
    roles: List[str]
    message: str

class PasswordChangeRequest(BaseModel):
    """Password change request model."""
    current_password: str
    new_password: str

def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user."""
    try:
        # Decode JWT token with signature verification
        payload = jwt.decode(
            credentials.credentials,
            "demo-secret-key",  # Use the same key as login
            algorithms=["HS256"]
        )
        
        # Handle demo token (has 'username' field)
        username = payload.get("username")
        if username is None:
            # Handle Keycloak token (has 'preferred_username' field)
            username = payload.get("preferred_username")
        
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        # Get user from database
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is deactivated"
            )
        
        return user
        
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

def mask_api_key(api_key: str) -> str:
    """Mask API key for security."""
    if not api_key:
        return ""
    if len(api_key) <= 8:
        return "*" * len(api_key)
    return api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:]

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "profile-service"}

# User Management Endpoints

@app.post("/users", response_model=UserRegistrationResponse)
async def register_user(request: UserRegistrationRequest, db: Session = Depends(get_db)):
    """Register a new user."""
    logger.info(f"User registration attempt for: {request.username}")

    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.username == request.username) | (User.email == request.email)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this username or email already exists"
        )

    # Get or create tenant
    if request.tenant_id:
        tenant = db.query(Tenant).filter(Tenant.id == request.tenant_id).first()
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid tenant ID"
            )
    else:
        # Create default tenant if needed
        tenant = db.query(Tenant).filter(Tenant.org_id == "default").first()
        if not tenant:
            tenant = Tenant(name="Default Organization", org_id="default")
            db.add(tenant)
            db.commit()
            db.refresh(tenant)

    # Create new user
    hashed_password = pwd_context.hash(request.password)
    new_user = User(
        username=request.username,
        email=request.email,
        password_hash=hashed_password,
        tenant_id=tenant.id,
        roles=["user"],  # Default role
        is_active=True
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logger.info(f"User registered successfully: {new_user.username}")

    return UserRegistrationResponse(
        user_id=str(new_user.id),  # Convert to string
        username=new_user.username,
        email=new_user.email,
        tenant_id=new_user.tenant_id,
        roles=new_user.roles,
        message="User registered successfully"
    )

@app.get("/users/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    logger.info(f"User info requested for: {current_user.username}")
    
    return UserResponse(
        user_id=str(current_user.id),  # Convert to string
        username=current_user.username,
        email=current_user.email,
        tenant_id=current_user.tenant_id,
        roles=current_user.roles or ["user"],  # Ensure roles is never None
        is_active=bool(current_user.is_active)
    )

@app.delete("/users/{user_id}")
async def delete_user(
    user_id: str,  # Changed from UUID to str to handle integer IDs
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a user account."""
    logger.info(f"User deletion request for: {user_id}")

    try:
        user_id_int = int(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )

    # Check if user exists
    user_to_delete = db.query(User).filter(User.id == user_id_int).first()
    if not user_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check permissions (user can delete themselves, admin can delete anyone)
    if current_user.id != user_id_int and "admin" not in current_user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to delete this user"
        )

    # Prevent deletion of the last admin user
    if "admin" in user_to_delete.roles:
        admin_count = db.query(User).filter(
            User.roles.contains(["admin"]),
            User.is_active == True
        ).count()
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the last admin user"
            )

    # Soft delete by deactivating
    user_to_delete.is_active = False
    db.commit()

    logger.info(f"User deactivated successfully: {user_to_delete.username}")

    return {
        "message": "User account deactivated successfully",
        "user_id": user_id
    }

@app.post("/users/change-password")
async def change_password(
    request: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password."""
    logger.info(f"Password change request for: {current_user.username}")

    # Verify current password for non-demo users
    if current_user.username != "demo" and not pwd_context.verify(request.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    if len(request.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )

    # Hash and update the new password
    hashed_password = pwd_context.hash(request.new_password)
    current_user.password_hash = hashed_password
    db.commit()

    logger.info(f"Password changed successfully for: {current_user.username}")

    return {
        "message": "Password changed successfully",
        "user_id": str(current_user.id)
    }

@app.get("/openrouter/models")
async def get_openrouter_models() -> List[OpenRouterModel]:
    """Get available OpenRouter models from API."""
    try:
        logger.info("Fetching OpenRouter models...")
        response = requests.get("https://openrouter.ai/api/v1/models", timeout=10)
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch OpenRouter models: {response.status_code}")
            raise HTTPException(status_code=503, detail="Failed to fetch OpenRouter models")
        
        data = response.json()
        models = []
        
        # Filter for enterprise-ready models
        preferred_providers = [
            "anthropic/", "openai/", "meta-llama/", "google/", "mistralai/", 
            "deepseek/", "qwen/", "cohere/", "nvidia/", "microsoft/"
        ]
        
        skip_keywords = [
            "preview", "test", "experimental", "alpha", "beta", "free",
            "uncensored", "venice", "router", "auto"
        ]
        
        for model_data in data.get("data", []):
            model_id = model_data.get("id", "")
            model_name = model_data.get("name", "")
            
            if not model_id or not model_name:
                continue
                
            # Filter for enterprise models
            is_preferred = any(model_id.startswith(provider) for provider in preferred_providers)
            has_skip_keyword = any(keyword in model_id.lower() or keyword in model_name.lower() 
                                 for keyword in skip_keywords)
            
            if is_preferred and not has_skip_keyword:
                models.append(OpenRouterModel(
                    id=model_id,
                    name=model_name,
                    description=model_data.get("description", "")[:200] + "..." if len(model_data.get("description", "")) > 200 else model_data.get("description"),
                    context_length=model_data.get("context_length"),
                    pricing=model_data.get("pricing")
                ))
        
        # Sort by provider and name
        models.sort(key=lambda x: (x.id.split('/')[0], x.name))
        
        logger.info(f"Successfully fetched {len(models)} OpenRouter models")
        return models
        
    except requests.RequestException as e:
        logger.error(f"Network error fetching OpenRouter models: {e}")
        raise HTTPException(status_code=503, detail="Network error fetching OpenRouter models")
    except Exception as e:
        logger.error(f"Error fetching OpenRouter models: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/settings")
async def get_settings(db: Session = Depends(get_db)) -> SettingsResponse:
    """Get AI settings for tenant."""
    try:
        tenant_id = "demo-tenant"
        
        settings = db.query(TenantSettings).filter(TenantSettings.tenant_id == tenant_id).first()
        
        if not settings:
            settings = TenantSettings(
                tenant_id=tenant_id,
                ai_provider="openai",
                ai_model="gpt-4",
                api_key=""
            )
            db.add(settings)
            db.commit()
            db.refresh(settings)
            logger.info(f"Created default settings for tenant {tenant_id}")
        
        return SettingsResponse(
            ai_provider=settings.ai_provider,
            ai_model=settings.ai_model,
            api_key=mask_api_key(settings.api_key)
        )
        
    except Exception as e:
        logger.error(f"Error getting settings: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/settings")
async def save_settings(request: SettingsRequest, db: Session = Depends(get_db)) -> Dict[str, str]:
    """Save AI settings for tenant."""
    try:
        tenant_id = "demo-tenant"
        
        settings = db.query(TenantSettings).filter(TenantSettings.tenant_id == tenant_id).first()
        
        if settings:
            settings.ai_provider = request.ai_provider
            settings.ai_model = request.ai_model
            settings.api_key = request.api_key
            settings.updated_at = datetime.utcnow()
        else:
            settings = TenantSettings(
                tenant_id=tenant_id,
                ai_provider=request.ai_provider,
                ai_model=request.ai_model,
                api_key=request.api_key
            )
            db.add(settings)
        
        db.commit()
        logger.info(f"Saved settings for tenant {tenant_id}: provider={request.ai_provider}, model={request.ai_model}")
        
        return {"message": "Settings saved successfully"}
        
    except Exception as e:
        logger.error(f"Error saving settings: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Profile Service on port 8007")
    uvicorn.run(app, host="0.0.0.0", port=8007)
