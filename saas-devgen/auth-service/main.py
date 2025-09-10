"""Authentication Service - JWT auth with Keycloak integration."""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import jwt
from keycloak import KeycloakOpenID
from shared.config import settings
from shared.logging_utils import setup_logger
from shared.database import get_db, create_tables
from shared.models import User, Tenant
from sqlalchemy.orm import Session

# Initialize logger
logger = setup_logger("auth-service", "auth-service.log")

app = FastAPI(title="Authentication Service", version="1.0.0")

# Security
security = HTTPBearer()

# Keycloak configuration
keycloak_openid = KeycloakOpenID(
    server_url=settings.keycloak_url,
    client_id=settings.keycloak_client_id,
    realm_name=settings.keycloak_realm
)


class LoginRequest(BaseModel):
    """Login request model."""
    username: str
    password: str


class LoginResponse(BaseModel):
    """Login response model."""
    access_token: str
    token_type: str = "bearer"
    user_id: int
    tenant_id: int
    roles: list


class UserResponse(BaseModel):
    """User response model."""
    user_id: int
    username: str
    email: str
    tenant_id: int
    roles: list
    is_active: bool


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user."""
    try:
        # Decode JWT token
        payload = jwt.decode(
            credentials.credentials,
            options={"verify_signature": False}  # For development
        )
        username: str = payload.get("preferred_username")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    # Get user from database
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled"
        )
    
    return user


@app.on_event("startup")
async def startup_event():
    """Initialize database tables."""
    logger.info("Starting Auth Service")
    try:
        create_tables()
        logger.info("Database tables initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


@app.post("/login", response_model=LoginResponse)
async def login(login_request: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return JWT token."""
    logger.info(f"Login attempt for user: {login_request.username}")
    
    try:
        # Authenticate with Keycloak
        token = keycloak_openid.token(
            username=login_request.username,
            password=login_request.password
        )
        
        # Get user info from Keycloak
        user_info = keycloak_openid.userinfo(token['access_token'])
        
        # Get or create user in local database
        user = db.query(User).filter(User.username == login_request.username).first()
        if not user:
            # Create default tenant if needed
            tenant = db.query(Tenant).filter(Tenant.org_id == "default").first()
            if not tenant:
                tenant = Tenant(name="Default Organization", org_id="default")
                db.add(tenant)
                db.commit()
                db.refresh(tenant)
            
            # Create user
            user = User(
                username=login_request.username,
                email=user_info.get("email", f"{login_request.username}@example.com"),
                tenant_id=tenant.id,
                roles=["user"]
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"Created new user: {user.username}")
        
        logger.info(f"User {user.username} authenticated successfully")
        
        return LoginResponse(
            access_token=token['access_token'],
            user_id=user.id,
            tenant_id=user.tenant_id,
            roles=user.roles
        )
        
    except Exception as e:
        logger.error(f"Login failed for user {login_request.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )


@app.get("/user", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    logger.info(f"User info requested for: {current_user.username}")
    
    return UserResponse(
        user_id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        tenant_id=current_user.tenant_id,
        roles=current_user.roles,
        is_active=current_user.is_active
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "auth-service",
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Auth Service on port 8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)
