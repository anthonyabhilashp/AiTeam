"""API Gateway Service - FastAPI-based with Keycloak integration."""
from fastapi import FastAPI, HTTPException, Request, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from keycloak import KeycloakOpenID, KeycloakAdmin
from keycloak.exceptions import KeycloakAuthenticationError, KeycloakGetError, KeycloakPostError, KeycloakPutError, KeycloakDeleteError, KeycloakConnectionError
import requests
import os
import json
import jwt
import time
from kafka import KafkaProducer
import httpx
import asyncio
from typing import Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"

# Keycloak configuration
KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://keycloak:8080")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "master")
KEYCLOAK_AUDIENCE = os.getenv("KEYCLOAK_AUDIENCE", "profile-service")

# Cache for Keycloak public keys
keycloak_public_keys = None
keys_last_updated = None
KEYS_CACHE_DURATION = 3600  # 1 hour
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "admin-cli")
KEYCLOAK_CLIENT_SECRET = os.getenv("KEYCLOAK_CLIENT_SECRET", "")
KEYCLOAK_ADMIN_USER = os.getenv("KEYCLOAK_ADMIN_USER", "admin")
KEYCLOAK_ADMIN_PASSWORD = os.getenv("KEYCLOAK_ADMIN_PASSWORD", "admin")

# Kafka configuration
KAFKA_BROKER_URL = os.getenv("KAFKA_BROKER_URL", "kafka:29092")
KAFKA_TOPIC_USER_REGISTRATION = os.getenv("KAFKA_TOPIC_USER_REGISTRATION", "user-registration-events")

# Service URLs
PROFILE_SERVICE_URL = os.getenv("PROFILE_SERVICE_URL", "http://profile-service:8005")
ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://orchestrator:8002")
CODEGEN_SERVICE_URL = os.getenv("CODEGEN_SERVICE_URL", "http://codegen-service:8003")
EXECUTOR_SERVICE_URL = os.getenv("EXECUTOR_SERVICE_URL", "http://executor-service:8006")
STORAGE_SERVICE_URL = os.getenv("STORAGE_SERVICE_URL", "http://storage-service:8007")
AUDIT_SERVICE_URL = os.getenv("AUDIT_SERVICE_URL", "http://audit-service:8008")

# Initialize FastAPI
app = FastAPI(title="API Gateway", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Keycloak clients
keycloak_openid = None
keycloak_admin = None
kafka_producer = None

def get_keycloak_openid():
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
    global keycloak_admin
    if keycloak_admin is None:
        try:
            keycloak_admin = KeycloakAdmin(
                server_url=KEYCLOAK_URL,
                username=KEYCLOAK_ADMIN_USER,
                password=KEYCLOAK_ADMIN_PASSWORD,
                realm_name=KEYCLOAK_REALM,
                client_id=KEYCLOAK_CLIENT_ID,
                client_secret_key=KEYCLOAK_CLIENT_SECRET,
                verify=True
            )
        except Exception as e:
            logger.error(f"Failed to initialize Keycloak admin: {e}")
            keycloak_admin = None
    return keycloak_admin

def get_kafka_producer():
    global kafka_producer
    if kafka_producer is None:
        try:
            kafka_producer = KafkaProducer(
                bootstrap_servers=[KAFKA_BROKER_URL],
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None
            )
            logger.info(f"Kafka producer initialized with broker: {KAFKA_BROKER_URL}")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            kafka_producer = None
    return kafka_producer

# Pydantic models
class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"

# Security
security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token with Keycloak."""
    try:
        if not credentials.credentials:
            raise HTTPException(status_code=401, detail="Authorization token is required")

        # Validate JWT token with Keycloak
        payload = validate_jwt_token(credentials.credentials)

        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        # Validate required claims
        if not payload.get('sub'):
            raise HTTPException(status_code=401, detail="Invalid token: missing user ID")

        return payload
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed. Please log in again.")

def get_keycloak_public_keys():
    """Fetch and cache Keycloak public keys."""
    global keycloak_public_keys, keys_last_updated

    current_time = time.time()
    if (keycloak_public_keys is None or
        keys_last_updated is None or
        current_time - keys_last_updated > KEYS_CACHE_DURATION):

        try:
            # Fetch Keycloak's JWKS (JSON Web Key Set)
            jwks_url = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/certs"
            response = requests.get(jwks_url, timeout=10)

            if response.status_code == 200:
                jwks = response.json()
                keycloak_public_keys = {}
                for key in jwks.get('keys', []):
                    kid = key.get('kid')
                    if kid:
                        keycloak_public_keys[kid] = key
                keys_last_updated = current_time
                logger.info(f"✅ Fetched {len(keycloak_public_keys)} Keycloak public keys")
            else:
                logger.error(f"❌ Failed to fetch Keycloak public keys: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"❌ Error fetching Keycloak public keys: {e}")
            return None

    return keycloak_public_keys

def validate_jwt_token(token: str):
    """Validate JWT token using Keycloak public keys or test mode."""
    try:
        # Test mode: validate test tokens without Keycloak
        if TEST_MODE:
            try:
                # Decode test token with test secret
                payload = jwt.decode(token, "test-secret", algorithms=["HS256"])
                logger.info("✅ Test token validated successfully")
                return payload
            except jwt.ExpiredSignatureError:
                logger.error("❌ Test token has expired")
                return None
            except Exception as e:
                logger.error(f"❌ Test token validation failed: {e}")
                return None

        # Production mode: validate with Keycloak public keys
        # Decode header to get key ID
        header = jwt.get_unverified_header(token)
        kid = header.get('kid')

        if not kid:
            logger.error("❌ No key ID found in JWT header")
            return None

        # Get public keys
        public_keys = get_keycloak_public_keys()
        if not public_keys or kid not in public_keys:
            logger.error(f"❌ Public key not found for kid: {kid}")
            return None

        # Get the public key
        key_data = public_keys[kid]

        # Convert JWK to PEM format
        if key_data.get('kty') == 'RSA':
            # Use PyJWT's built-in JWK support
            from jwt import PyJWK
            public_key = PyJWK(key_data).key
        else:
            logger.error(f"❌ Unsupported key type: {key_data.get('kty')}")
            return None

        # Decode and validate token with flexible audience validation
        valid_audiences = [
            KEYCLOAK_AUDIENCE,  # Expected service audience
            "admin-cli",        # Keycloak admin client
            "account",          # Keycloak account service
        ]

        payload = None
        last_error = None

        # Try each valid audience
        for audience in valid_audiences:
            try:
                payload = jwt.decode(
                    token,
                    public_key,
                    algorithms=['RS256'],
                    audience=audience,
                    issuer=f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}"
                )
                break  # Success, exit loop
            except (jwt.InvalidAudienceError, jwt.MissingRequiredClaimError) as e:
                last_error = e
                continue  # Try next audience
            except Exception as e:
                last_error = e
                break  # Other error, stop trying

        if payload is None:
            # If audience validation failed, try without audience validation
            # This handles tokens that don't have audience claims (common in development)
            if isinstance(last_error, (jwt.InvalidAudienceError, jwt.MissingRequiredClaimError)):
                try:
                    payload = jwt.decode(
                        token,
                        public_key,
                        algorithms=['RS256'],
                        audience=None,  # Skip audience validation
                        issuer=f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}"
                    )
                    logger.info("✅ Token validated without audience claim (development mode)")
                except Exception as e:
                    logger.error(f"❌ Token validation failed even without audience: {e}")
                    return None
            else:
                logger.error(f"❌ Token validation failed: {last_error}")
                return None

        return payload

    except jwt.ExpiredSignatureError:
        logger.error("❌ Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.error(f"❌ Invalid token: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Error validating token: {e}")
        return None

# Auth endpoints
@app.post("/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Login user with Keycloak."""
    try:
        if not request.username or not request.password:
            raise HTTPException(status_code=400, detail="Username and password are required")

        keycloak = get_keycloak_openid()
        if not keycloak:
            logger.error("Keycloak client not available")
            raise HTTPException(status_code=503, detail="Authentication service temporarily unavailable. Please try again later.")

        token = keycloak.token(request.username, request.password)
        return TokenResponse(
            access_token=token['access_token'],
            refresh_token=token['refresh_token']
        )
    except KeycloakAuthenticationError:
        raise HTTPException(status_code=401, detail="Invalid username or password. Please check your credentials and try again.")
    except KeycloakConnectionError:
        logger.error("Keycloak connection error during login")
        raise HTTPException(status_code=503, detail="Authentication service is temporarily unavailable. Please try again in a few minutes.")
    except Exception as e:
        logger.error(f"Unexpected login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed due to an unexpected error. Please try again.")

@app.post("/auth/register")
async def register(request: RegisterRequest):
    """Register new user with Keycloak and send Kafka event."""
    try:
        # Validate input data
        if not request.username or len(request.username.strip()) == 0:
            raise HTTPException(status_code=400, detail="Username is required and cannot be empty")

        if not request.email or len(request.email.strip()) == 0:
            raise HTTPException(status_code=400, detail="Email is required and cannot be empty")

        if not request.password or len(request.password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters long")

        # Validate email format
        if "@" not in request.email or "." not in request.email:
            raise HTTPException(status_code=400, detail="Please provide a valid email address")

        admin = get_keycloak_admin()
        if not admin:
            logger.error("Keycloak admin client not available")
            raise HTTPException(status_code=500, detail="Authentication service temporarily unavailable. Please try again later.")

        # Check if user already exists
        try:
            existing_users = admin.get_users({"username": request.username})
            if existing_users:
                raise HTTPException(status_code=409, detail="Username already exists. Please choose a different username.")

            existing_emails = admin.get_users({"email": request.email})
            if existing_emails:
                raise HTTPException(status_code=409, detail="Email address already registered. Please use a different email or try logging in.")
        except KeycloakGetError as e:
            logger.warning(f"Error checking existing users: {e}")
            # Continue with registration if we can't check existing users

        # Create user in Keycloak
        user_data = {
            "username": request.username.strip(),
            "email": request.email.strip().lower(),
            "firstName": request.first_name.strip() if request.first_name else "",
            "lastName": request.last_name.strip() if request.last_name else "",
            "enabled": True,
            "emailVerified": False,
            "credentials": [{
                "type": "password",
                "value": request.password,
                "temporary": False
            }]
        }

        try:
            user_id = admin.create_user(user_data)
            logger.info(f"User created in Keycloak: {user_id}")
        except KeycloakPostError as e:
            logger.error(f"Keycloak user creation failed: {e}")
            if "already exists" in str(e).lower():
                raise HTTPException(status_code=409, detail="User with this username or email already exists")
            elif "password" in str(e).lower():
                raise HTTPException(status_code=400, detail="Password does not meet security requirements")
            else:
                raise HTTPException(status_code=400, detail="Failed to create user account. Please check your information and try again.")
        except KeycloakConnectionError as e:
            logger.error(f"Keycloak connection error: {e}")
            raise HTTPException(status_code=503, detail="Authentication service is temporarily unavailable. Please try again in a few minutes.")
        except Exception as e:
            logger.error(f"Unexpected error during user creation: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred during registration. Please try again.")

        # Send Kafka event
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
                    "timestamp": str(asyncio.get_event_loop().time())
                }
                producer.send(KAFKA_TOPIC_USER_REGISTRATION, value=event_data, key=request.username)
                producer.flush()
                logger.info(f"Kafka event sent for user: {request.username}")
            else:
                logger.warning("Kafka producer not available, skipping event publishing")
        except Exception as e:
            logger.error(f"Failed to send Kafka event: {e}")
            # Don't fail registration if Kafka is down, just log it

        return {"message": "User registered successfully", "user_id": user_id}

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed due to an unexpected error. Please try again.")

@app.get("/auth/user")
async def get_user(token_info: dict = Depends(verify_token)):
    """Get current user info."""
    return {
        "user_id": token_info.get('sub'),
        "username": token_info.get('preferred_username'),
        "email": token_info.get('email'),
        "roles": token_info.get('realm_access', {}).get('roles', [])
    }

# Proxy endpoints
async def proxy_request(service_url: str, path: str, request: Request, method: str = None, custom_headers: dict = None):
    """Proxy request to downstream service."""
    if not method:
        method = request.method

    url = f"{service_url}{path}"
    headers = dict(request.headers)

    # Add custom headers if provided
    if custom_headers:
        headers.update(custom_headers)

    # Remove host header and content-length (will be recalculated by httpx)
    headers.pop('host', None)
    headers.pop('content-length', None)

    async with httpx.AsyncClient() as client:
        try:
            if method == "GET":
                response = await client.get(url, headers=headers, params=request.query_params)
            elif method == "POST":
                body = await request.body()
                response = await client.post(url, headers=headers, content=body)
            elif method == "PUT":
                body = await request.body()
                response = await client.put(url, headers=headers, content=body)
            elif method == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                raise HTTPException(status_code=405, detail="Method not allowed")

            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
        except httpx.RequestError as e:
            logger.error(f"Proxy request failed: {e}")
            raise HTTPException(status_code=502, detail="Service unavailable")

@app.api_route("/profile/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_profile(path: str, request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Proxy requests to profile service with JWT validation."""
    # Validate JWT token
    user_payload = await verify_token(credentials)

    # Extract user information
    user_id = user_payload.get("sub")
    username = user_payload.get("preferred_username", user_payload.get("username", ""))
    email = user_payload.get("email", "")
    roles = user_payload.get("realm_access", {}).get("roles", [])

    # Add user information headers
    headers = dict(request.headers)
    headers.update({
        "X-User-ID": user_id,
        "X-User-Username": username,
        "X-User-Email": email,
        "X-User-Roles": ",".join(roles) if roles else ""
    })

    # Remove host header
    headers.pop('host', None)

    return await proxy_request(PROFILE_SERVICE_URL, f"/{path}", request, custom_headers=headers)

@app.api_route("/orchestrator/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_orchestrator(path: str, request: Request):
    """Proxy requests to orchestrator service."""
    return await proxy_request(ORCHESTRATOR_URL, f"/{path}", request)

@app.api_route("/codegen/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_codegen(path: str, request: Request):
    """Proxy requests to codegen service."""
    return await proxy_request(CODEGEN_SERVICE_URL, f"/{path}", request)

@app.api_route("/executor/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_executor(path: str, request: Request):
    """Proxy requests to executor service."""
    return await proxy_request(EXECUTOR_SERVICE_URL, f"/{path}", request)

@app.api_route("/storage/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_storage(path: str, request: Request):
    """Proxy requests to storage service."""
    return await proxy_request(STORAGE_SERVICE_URL, f"/{path}", request)

@app.api_route("/audit/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_audit(path: str, request: Request):
    """Proxy requests to audit service."""
    return await proxy_request(AUDIT_SERVICE_URL, f"/{path}", request)

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "AI Team SaaS - API Gateway", "version": "1.0.0", "status": "running"}

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

import os
import sys
import time
import logging
import requests
from datetime import datetime

# Configure logging (console only)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class GatewayService:
    """Kong-based Gateway Service"""

    def __init__(self):
        self.kong_admin_url = os.getenv('KONG_ADMIN_URL', 'http://localhost:8001')
        self.kong_proxy_url = os.getenv('KONG_PROXY_URL', 'http://localhost:8000')
        self.kong_gui_url = os.getenv('KONG_GUI_URL', 'http://localhost:8002')

    def check_kong_status(self):
        """Check Kong gateway status"""
        try:
            response = requests.get(f"{self.kong_admin_url}/status", timeout=10)
            if response.status_code == 200:
                status = response.json()
                logger.info(f"Kong status: {status}")
                return True
            else:
                logger.error(f"Kong status check failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error checking Kong status: {e}")
            return False

    def get_services(self):
        """Get registered services from Kong"""
        try:
            response = requests.get(f"{self.kong_admin_url}/services", timeout=10)
            if response.status_code == 200:
                services = response.json()
                logger.info(f"Registered services: {len(services.get('data', []))}")
                return services
            else:
                logger.error(f"Failed to get services: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error getting services: {e}")
            return None

    def get_routes(self):
        """Get registered routes from Kong"""
        try:
            response = requests.get(f"{self.kong_admin_url}/routes", timeout=10)
            if response.status_code == 200:
                routes = response.json()
                logger.info(f"Registered routes: {len(routes.get('data', []))}")
                return routes
            else:
                logger.error(f"Failed to get routes: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error getting routes: {e}")
            return None

    def monitor_services(self):
        """Monitor gateway services and routes"""
        logger.info("Starting Gateway Service monitoring...")

        while True:
            try:
                # Check Kong status
                if self.check_kong_status():
                    logger.info("Kong gateway is healthy")

                    # Get services and routes
                    services = self.get_services()
                    routes = self.get_routes()

                    if services and routes:
                        logger.info("Gateway configuration is valid")
                    else:
                        logger.warning("Issues detected with gateway configuration")

                else:
                    logger.error("Kong gateway is not responding")

                # Wait before next check
                time.sleep(30)

            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(30)

def main():
    """Main entry point"""
    logger.info("Starting Gateway Service (Kong-based)")

    # Initialize service
    gateway = GatewayService()

    # Log service information
    logger.info("Kong URLs:")
    logger.info(f"  Proxy: {gateway.kong_proxy_url}")
    logger.info(f"  Admin API: {gateway.kong_admin_url}")
    logger.info(f"  Admin GUI: {gateway.kong_gui_url}")

    # Start monitoring
    try:
        gateway.monitor_services()
    except Exception as e:
        logger.error(f"Gateway service error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
