"""Auth Service - Keycloak Integration."""
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from keycloak import KeycloakOpenID, KeycloakAdmin
from keycloak.exceptions import KeycloakAuthenticationError, KeycloakGetError
import requests
import os
from typing import Optional, List
import json
from kafka import KafkaProducer
import json as json_lib

from contextlib import asynccontextmanager
from fastapi import FastAPI

# Keycloak configuration
KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://localhost:8080")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "master")  # Use master realm for now
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "admin-cli")  # Use admin-cli client for now
KEYCLOAK_CLIENT_SECRET = os.getenv("KEYCLOAK_CLIENT_SECRET", "")
KEYCLOAK_ADMIN_USER = os.getenv("KEYCLOAK_ADMIN_USER", "admin")
KEYCLOAK_ADMIN_PASSWORD = os.getenv("KEYCLOAK_ADMIN_PASSWORD", "admin")

# Kafka configuration
KAFKA_BROKER_URL = os.getenv("KAFKA_BROKER_URL", "localhost:9092")
KAFKA_TOPIC_USER_REGISTRATION = os.getenv("KAFKA_TOPIC_USER_REGISTRATION", "user-registration-events")

# Initialize Kafka producer (lazy initialization)
kafka_producer = None

def get_kafka_producer():
    """Lazy initialization of Kafka producer."""
    global kafka_producer
    if kafka_producer is None:
        try:
            kafka_producer = KafkaProducer(
                bootstrap_servers=[KAFKA_BROKER_URL],
                value_serializer=lambda v: json_lib.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None
            )
            print(f"✅ Kafka producer initialized with broker: {KAFKA_BROKER_URL}")
        except Exception as e:
            print(f"❌ Failed to initialize Kafka producer: {e}")
            kafka_producer = None
    return kafka_producer

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown events."""
    print("🚀 STARTUP EVENT TRIGGERED - Auth service is starting up!")
    try:
        print("👤 Creating default admin user...")
        await create_default_admin_user()
        print("✅ Auth service initialization completed")
    except Exception as e:
        print(f"❌ Warning: Failed to create default admin user: {e}")
        import traceback
        print(f"❌ Full traceback: {traceback.format_exc()}")

    yield

    # Shutdown logic (if needed)
    print("🛑 Auth service is shutting down...")

app = FastAPI(title="Auth Service", version="1.0.0", lifespan=lifespan)

# Initialize Keycloak clients (lazy initialization)
keycloak_openid = None
keycloak_admin = None

def get_keycloak_openid():
    """Lazy initialization of Keycloak OpenID client."""
    global keycloak_openid
    if keycloak_openid is None:
        keycloak_openid = KeycloakOpenID(
            server_url=KEYCLOAK_URL,
            client_id=KEYCLOAK_CLIENT_ID,
            realm_name=KEYCLOAK_REALM,
            client_secret_key=KEYCLOAK_CLIENT_SECRET
        )
    return keycloak_openid

def get_keycloak_admin():
    """Lazy initialization of Keycloak Admin client."""
    global keycloak_admin
    if keycloak_admin is None:
        try:
            print(f"🔗 Connecting to Keycloak admin at {KEYCLOAK_URL}")
            print(f"👤 Using admin user: {KEYCLOAK_ADMIN_USER}")
            print(f"🏰 Using realm: {KEYCLOAK_REALM}")
            print(f"📱 Using client: {KEYCLOAK_CLIENT_ID}")
            keycloak_admin = KeycloakAdmin(
                server_url=KEYCLOAK_URL,
                username=KEYCLOAK_ADMIN_USER,
                password=KEYCLOAK_ADMIN_PASSWORD,
                realm_name=KEYCLOAK_REALM,
                client_id=KEYCLOAK_CLIENT_ID,
                client_secret_key=KEYCLOAK_CLIENT_SECRET,
                verify=True
            )
            print("✅ Keycloak admin client created successfully")
        except Exception as e:
            print(f"❌ Failed to create Keycloak admin client: {e}")
            import traceback
            print(f"❌ Full error: {traceback.format_exc()}")
            # Return None if Keycloak is not available (for testing)
            keycloak_admin = None
    return keycloak_admin

# Security scheme
security = HTTPBearer()

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    user_id: str
    roles: List[str]

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class RegisterResponse(BaseModel):
    user_id: str
    message: str

class PasswordResetRequest(BaseModel):
    email: str

class PasswordResetResponse(BaseModel):
    message: str

class PasswordChangeRequest(BaseModel):
    new_password: str

class PasswordChangeResponse(BaseModel):
    message: str

class UserRoleUpdateRequest(BaseModel):
    user_id: str
    roles: List[str]

class UserRoleResponse(BaseModel):
    user_id: str
    roles: List[str]
    message: str

# OAuth2 scheme for token extraction
oauth2_scheme = HTTPBearer()

@app.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Authenticate user with Keycloak."""
    try:
        kc_openid = get_keycloak_openid()
        token = kc_openid.token(
            username=request.username,
            password=request.password
        )

        # Get user info to extract roles and user_id
        userinfo = kc_openid.userinfo(token["access_token"])
        user_id = userinfo.get("sub", "")
        roles = userinfo.get("realm_access", {}).get("roles", [])

        return LoginResponse(
            access_token=token["access_token"],
            refresh_token=token["refresh_token"],
            token_type="Bearer",
            expires_in=token.get("expires_in", 300),
            user_id=user_id,
            roles=roles
        )
    except KeycloakAuthenticationError:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Authentication failed: {str(e)}"
        )

@app.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str):
    """Refresh access token using refresh token."""
    try:
        kc_openid = get_keycloak_openid()
        token = kc_openid.refresh_token(refresh_token)
        return TokenResponse(
            access_token=token["access_token"],
            refresh_token=token["refresh_token"],
            token_type="Bearer",
            expires_in=token.get("expires_in", 300)
        )
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token"
        )

@app.post("/logout")
async def logout(refresh_token: str):
    """Logout user by invalidating refresh token."""
    try:
        kc_openid = get_keycloak_openid()
        kc_openid.logout(refresh_token)
        return {"message": "Logged out successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Logout failed: {str(e)}"
        )

@app.get("/userinfo")
async def get_userinfo(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get user information from access token."""
    try:
        kc_openid = get_keycloak_openid()
        userinfo = kc_openid.userinfo(credentials.credentials)
        return userinfo
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

@app.get("/introspect")
async def introspect_token(token: str):
    """Introspect token to check validity."""
    try:
        kc_openid = get_keycloak_openid()
        introspection = kc_openid.introspect(token)
        return introspection
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail="Token introspection failed"
        )

@app.post("/register", response_model=RegisterResponse)
async def register_user(request: RegisterRequest):
    """Register a new user with Keycloak."""
    try:
        kc_admin = get_keycloak_admin()
        if kc_admin is None:
            raise HTTPException(
                status_code=500,
                detail="Keycloak admin not available"
            )

        # Create user in Keycloak
        user_data = {
            "username": request.username,
            "email": request.email,
            "firstName": request.first_name,
            "lastName": request.last_name,
            "enabled": True,
            "credentials": [{
                "type": "password",
                "value": request.password,
                "temporary": False
            }]
        }

        user_id = kc_admin.create_user(user_data)

        # Publish user registration event to Kafka
        try:
            producer = get_kafka_producer()
            if producer:
                event_data = {
                    "event_type": "user_registered",
                    "user_id": user_id,
                    "username": request.username,
                    "email": request.email,
                    "first_name": request.first_name,
                    "last_name": request.last_name,
                    "timestamp": json_lib.dumps(None)  # Will be set by consumer or use current time
                }
                producer.send(KAFKA_TOPIC_USER_REGISTRATION, key=user_id, value=event_data)
                producer.flush()
                print(f"📤 Published user registration event for user: {user_id}")
            else:
                print("⚠️  Kafka producer not available, skipping event publication")
        except Exception as e:
            print(f"⚠️  Failed to publish user registration event: {e}")
            # Don't fail registration if Kafka publishing fails

        return RegisterResponse(
            user_id=user_id,
            message="User registered successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Registration failed: {str(e)}"
        )

@app.post("/password-reset", response_model=PasswordResetResponse)
async def request_password_reset(request: PasswordResetRequest):
    """Request password reset for a user."""
    try:
        kc_admin = get_keycloak_admin()
        if kc_admin is None:
            raise HTTPException(
                status_code=500,
                detail="Keycloak admin not available"
            )

        # Find user by email
        users = kc_admin.get_users({"email": request.email})
        if not users:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        user_id = users[0]["id"]

        # Send password reset email
        kc_admin.send_reset_email(
            user_id=user_id,
            redirect_uri=os.getenv("RESET_PASSWORD_REDIRECT_URI", "http://localhost:3000/reset-password")
        )

        return PasswordResetResponse(
            message="Password reset email sent successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Password reset failed: {str(e)}"
        )

@app.post("/change-password", response_model=PasswordChangeResponse)
async def change_password(request: PasswordChangeRequest, token: str = Depends(oauth2_scheme)):
    """Change password for authenticated user."""
    try:
        kc_admin = get_keycloak_admin()
        kc_openid = get_keycloak_openid()
        if kc_openid is None:
            raise HTTPException(
                status_code=500,
                detail="Keycloak OpenID not available"
            )

        # Verify token and get user info
        try:
            userinfo = kc_openid.userinfo(token)
            user_id = userinfo["sub"]
        except Exception:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )

        if kc_admin is None:
            raise HTTPException(
                status_code=500,
                detail="Keycloak admin not available"
            )

        # Set new password
        kc_admin.set_user_password(
            user_id=user_id,
            password=request.new_password,
            temporary=False
        )

        return PasswordChangeResponse(
            message="Password changed successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Password change failed: {str(e)}"
        )

@app.get("/roles")
async def get_user_roles(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user's roles."""
    try:
        kc_openid = get_keycloak_openid()
        if kc_openid is None:
            raise HTTPException(
                status_code=500,
                detail="Keycloak OpenID not available"
            )

        userinfo = kc_openid.userinfo(credentials.credentials)
        roles = userinfo.get("realm_access", {}).get("roles", [])
        return {"user_id": userinfo.get("sub"), "roles": roles}
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

@app.put("/user/{user_id}/roles", response_model=UserRoleResponse)
async def update_user_roles(
    user_id: str,
    request: UserRoleUpdateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update user roles (admin only)."""
    try:
        kc_openid = get_keycloak_openid()
        kc_admin = get_keycloak_admin()
        if kc_openid is None:
            raise HTTPException(
                status_code=500,
                detail="Keycloak OpenID not available"
            )

        # Verify token and admin role
        try:
            userinfo = kc_openid.userinfo(credentials.credentials)
            user_roles = userinfo.get("realm_access", {}).get("roles", [])
        except Exception:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )

        if "admin" not in user_roles:
            raise HTTPException(
                status_code=403,
                detail="Admin access required"
            )

        if kc_admin is None:
            raise HTTPException(
                status_code=500,
                detail="Keycloak admin not available"
            )

        # Get available roles
        realm_roles = kc_admin.get_realm_roles()

        # Map role names to role objects
        roles_to_assign = []
        for role in realm_roles:
            if role["name"] in request.roles:
                roles_to_assign.append(role)

        # Update user roles
        kc_admin.assign_realm_roles(user_id=user_id, roles=roles_to_assign)

        return UserRoleResponse(
            user_id=user_id,
            roles=request.roles,
            message="User roles updated successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Role update failed: {str(e)}"
        )

async def create_default_admin_user():
    """Create default admin user if it doesn't exist."""
    print("🔧 Starting admin user creation process...")
    try:
        print("🔗 Getting Keycloak admin client...")
        keycloak_admin = get_keycloak_admin()
        if not keycloak_admin:
            print("❌ Keycloak admin client not available, skipping default user creation")
            return

        print("✅ Keycloak admin client obtained successfully")

        # Check if admin user already exists
        try:
            users = keycloak_admin.get_users({"username": "admin"})
            if users and len(users) > 0:
                print("Default admin user already exists, skipping creation")
                return
        except Exception as e:
            print(f"Error checking for existing admin user: {e}")
            # Continue with creation if we can't check

        # Create default admin user
        user_data = {
            "username": "admin",
            "email": "admin@example.com",
            "firstName": "Admin",
            "lastName": "User",
            "enabled": True,
            "emailVerified": True,
            "credentials": [
                {
                    "type": "password",
                    "value": "admin",
                    "temporary": False
                }
            ],
            "realmRoles": ["admin"],
            "clientRoles": {}
        }

        # Create the user
        try:
            user_id = keycloak_admin.create_user(user_data)
            print(f"Created default admin user with ID: {user_id}")

            # Assign admin role
            try:
                admin_role = keycloak_admin.get_realm_role("admin")
                keycloak_admin.assign_realm_roles(user_id, [admin_role])
                print("Assigned admin role to default user")
            except Exception as e:
                print(f"Warning: Could not assign admin role: {e}")

        except Exception as e:
            if "already exists" in str(e).lower() or "409" in str(e):
                print("Admin user already exists, skipping creation")
            else:
                print(f"Error creating default admin user: {e}")
                raise

    except Exception as e:
        print(f"Error in create_default_admin_user: {e}")
        # Don't raise exception to prevent service startup failure

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Test Keycloak connection
        keycloak_client = get_keycloak_openid()
        if keycloak_client:
            keycloak_client.well_known()
            keycloak_status = "connected"
        else:
            keycloak_status = "not initialized"

        return {
            "status": "healthy",
            "service": "auth-service",
            "keycloak_status": keycloak_status
        }
    except Exception as e:
        return {
            "status": "healthy",  # Service is healthy even if Keycloak is down
            "service": "auth-service",
            "keycloak_status": f"error: {str(e)}"
        }

if __name__ == "__main__":
    import uvicorn
    import os

    # Get port from environment variable, default to 8004 for backward compatibility
    port = int(os.getenv("AUTH_SERVICE_PORT", "8004"))
    uvicorn.run(app, host="0.0.0.0", port=port)
