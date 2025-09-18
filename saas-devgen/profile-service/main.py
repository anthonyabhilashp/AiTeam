"""Profile Service - Enterprise user profile management."""
import sys
import os
from datetime import datetime
from typing import Dict, Any, Optional
import threading
import time
import logging
import json as json_lib
import psycopg2
import jwt
import requests

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from kafka import KafkaConsumer

# Initialize logger
logger = logging.getLogger("profile-service")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Environment variables
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://devgen:devgen@postgres:5432/devgen")
SCHEMA = os.getenv("SCHEMA", "aiteam")

# Keycloak configuration
KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://keycloak:8080")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "master")
KEYCLOAK_AUDIENCE = os.getenv("KEYCLOAK_AUDIENCE", "profile-service")  # Expected audience for JWT tokens

# Kafka configuration
KAFKA_BROKER_URL = os.getenv("KAFKA_BROKER_URL", "kafka:29092")
KAFKA_TOPIC_USER_REGISTRATION = os.getenv("KAFKA_TOPIC_USER_REGISTRATION", "user-registration-events")
KAFKA_GROUP_ID = os.getenv("KAFKA_GROUP_ID", "profile-service")

# Cache for Keycloak public keys
keycloak_public_keys = None
keys_last_updated = None
KEYS_CACHE_DURATION = 3600  # 1 hour

# Initialize Kafka consumer (lazy initialization)
kafka_consumer = None
consumer_thread = None

def get_kafka_consumer():
    """Lazy initialization of Kafka consumer."""
    global kafka_consumer
    if kafka_consumer is None:
        try:
            kafka_consumer = KafkaConsumer(
                KAFKA_TOPIC_USER_REGISTRATION,
                bootstrap_servers=[KAFKA_BROKER_URL],
                group_id=KAFKA_GROUP_ID,
                value_deserializer=lambda x: json_lib.loads(x.decode('utf-8')),
                key_deserializer=lambda x: x.decode('utf-8') if x else None,
                auto_offset_reset='earliest',
                enable_auto_commit=True
            )
            logger.info(f"✅ Kafka consumer initialized with broker: {KAFKA_BROKER_URL}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Kafka consumer: {e}")
            kafka_consumer = None
    return kafka_consumer

def start_kafka_consumer():
    """Start Kafka consumer in a background thread."""
    global consumer_thread
    if consumer_thread is None or not consumer_thread.is_alive():
        consumer_thread = threading.Thread(target=consume_user_registration_events, daemon=True)
        consumer_thread.start()
        logger.info("🚀 Kafka consumer thread started")

def consume_user_registration_events():
    """Consume user registration events and create user profiles."""
    consumer = get_kafka_consumer()
    if not consumer:
        logger.error("❌ Kafka consumer not available")
        return

    logger.info("👂 Listening for user registration events...")
    try:
        for message in consumer:
            try:
                event_data = message.value
                logger.info(f"📨 Received event: {event_data}")

                if event_data.get('event_type') == 'user_registered':
                    create_user_profile_from_event(event_data)

            except Exception as e:
                logger.error(f"❌ Error processing message: {e}")
                continue
    except Exception as e:
        logger.error(f"❌ Kafka consumer error: {e}")

def create_user_profile_from_event(event_data: Dict[str, Any]):
    """Create user profile from registration event using raw SQL."""
    try:
        user_id = event_data.get('user_id')
        username = event_data.get('username')
        email = event_data.get('email')
        first_name = event_data.get('first_name')
        last_name = event_data.get('last_name')

        if not all([user_id, username, email]):
            logger.error(f"❌ Missing required fields in event: {event_data}")
            return

        # Get database connection
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        try:
            # Check if profile already exists
            cursor.execute(f"SELECT user_id FROM {SCHEMA}.profiles WHERE user_id = %s", (user_id,))
            existing_profile = cursor.fetchone()

            if existing_profile:
                logger.info(f"ℹ️  User profile already exists for user_id: {user_id}")
                return

            # Create new user profile
            cursor.execute(f"""
                INSERT INTO {SCHEMA}.profiles (user_id, username, email, first_name, last_name)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, username, email, first_name, last_name))

            conn.commit()
            logger.info(f"✅ Created user profile for user_id: {user_id}, username: {username}")

        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        logger.error(f"❌ Failed to create user profile from event: {e}")
        import traceback
        logger.error(f"❌ Full traceback: {traceback.format_exc()}")

# Pydantic models
class ProfileResponse(BaseModel):
    user_id: str
    username: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

class ProfileUpdateRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    service: str
    database: str
    kafka: str

# FastAPI app
app = FastAPI(
    title="Profile Service",
    description="Enterprise user profile management",
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

# Removed JWT validation functions - authentication handled by gateway service

def get_current_user(request: Request):
    """Extract user information from gateway headers (trusted source)."""
    # Get user info from headers set by gateway service
    user_id = request.headers.get("X-User-ID")
    username = request.headers.get("X-User-Username")
    email = request.headers.get("X-User-Email")
    roles = request.headers.get("X-User-Roles", "").split(",") if request.headers.get("X-User-Roles") else []

    if not user_id:
        raise HTTPException(status_code=401, detail="User authentication required")

    return {
        "user_id": user_id,
        "username": username,
        "email": email,
        "roles": roles
    }

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("🚀 Profile service is starting up...")
    start_kafka_consumer()
    logger.info("✅ Profile service initialization completed")

@app.get("/me", response_model=ProfileResponse)
async def get_my_profile(user_info: dict = Depends(get_current_user)):
    """Get current user's profile information."""
    try:
        # Get database connection
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        try:
            # Get profile by user_id from gateway headers
            user_id = user_info.get("user_id")
            if not user_id:
                raise HTTPException(status_code=400, detail="User ID not found")

            cursor.execute(f"""
                SELECT user_id, username, email, first_name, last_name, created_at, updated_at
                FROM {SCHEMA}.profiles
                WHERE user_id = %s
            """, (user_id,))

            profile_row = cursor.fetchone()

            if not profile_row:
                raise HTTPException(status_code=404, detail="User profile not found")

            return ProfileResponse(
                user_id=profile_row[0],
                username=profile_row[1],
                email=profile_row[2],
                first_name=profile_row[3],
                last_name=profile_row[4],
                created_at=profile_row[5],
                updated_at=profile_row[6]
            )

        finally:
            cursor.close()
            conn.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get profile: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/me", response_model=ProfileResponse)
async def update_my_profile(
    profile_update: ProfileUpdateRequest,
    user_info: dict = Depends(get_current_user)
):
    """Update current user's profile information."""
    try:
        # Get database connection
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        try:
            # Get profile by user_id from gateway headers
            user_id = user_info.get("user_id")
            if not user_id:
                raise HTTPException(status_code=400, detail="User ID not found")

            # Check if profile exists
            cursor.execute(f"SELECT user_id FROM {SCHEMA}.profiles WHERE user_id = %s", (user_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="User profile not found")

            # Update fields if provided
            update_fields = []
            update_values = []

            if profile_update.username:
                # Check if username is already taken
                cursor.execute(f"""
                    SELECT user_id FROM {SCHEMA}.profiles
                    WHERE username = %s AND user_id != %s
                """, (profile_update.username, user_id))
                if cursor.fetchone():
                    raise HTTPException(status_code=400, detail="Username already taken")

                update_fields.append("username = %s")
                update_values.append(profile_update.username)

            if profile_update.email:
                # Check if email is already taken
                cursor.execute(f"""
                    SELECT user_id FROM {SCHEMA}.profiles
                    WHERE email = %s AND user_id != %s
                """, (profile_update.email, user_id))
                if cursor.fetchone():
                    raise HTTPException(status_code=400, detail="Email already taken")

                update_fields.append("email = %s")
                update_values.append(profile_update.email)

            if profile_update.first_name is not None:
                update_fields.append("first_name = %s")
                update_values.append(profile_update.first_name)

            if profile_update.last_name is not None:
                update_fields.append("last_name = %s")
                update_values.append(profile_update.last_name)

            if update_fields:
                update_values.append(user_id)
                cursor.execute(f"""
                    UPDATE {SCHEMA}.profiles
                    SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = %s
                """, update_values)

                conn.commit()

            # Get updated profile data
            cursor.execute(f"""
                SELECT user_id, username, email, first_name, last_name, created_at, updated_at
                FROM {SCHEMA}.profiles WHERE user_id = %s
            """, (user_id,))

            updated_profile = cursor.fetchone()

            logger.info(f"Profile updated for user: {updated_profile[1]}")

            return ProfileResponse(
                user_id=updated_profile[0],
                username=updated_profile[1],
                email=updated_profile[2],
                first_name=updated_profile[3],
                last_name=updated_profile[4],
                created_at=updated_profile[5],
                updated_at=updated_profile[6]
            )

        finally:
            cursor.close()
            conn.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to update profile: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        # Check database connection
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    # Check Kafka connection
    kafka_status = "connected" if kafka_consumer else "disconnected"

    return HealthResponse(
        status="healthy" if db_status == "connected" else "unhealthy",
        service="profile-service",
        database=db_status,
        kafka=kafka_status
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PROFILE_SERVICE_PORT", "8005"))
    uvicorn.run(app, host="0.0.0.0", port=port)
