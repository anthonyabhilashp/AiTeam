"""Database initialization script for enterprise AI platform."""
import os
import sys
sys.path.append('/app/shared')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://devgen:devgen_enterprise_2024@postgres:5432/devgen')

def init_database():
    """Initialize database with required tables and demo data."""
    engine = create_engine(DATABASE_URL)
    
    try:
        # Create tables if they don't exist
        with engine.connect() as conn:
            logger.info("Creating database tables...")
            
            # Create aiteam schema
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS aiteam"))
            conn.commit()
            
            # Create tenants table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS aiteam.tenants (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    org_id VARCHAR(255) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Create users table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS aiteam.users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(255) NOT NULL,
                    email VARCHAR(255) NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    tenant_id INTEGER REFERENCES aiteam.tenants(id),
                    roles TEXT[] DEFAULT '{"user"}',
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Create requirements table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS aiteam.requirements (
                    id SERIAL PRIMARY KEY,
                    tenant_id INTEGER REFERENCES aiteam.tenants(id),
                    user_id INTEGER REFERENCES aiteam.users(id),
                    text TEXT NOT NULL,
                    status VARCHAR(50) DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Create tasks table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS aiteam.tasks (
                    id SERIAL PRIMARY KEY,
                    requirement_id INTEGER REFERENCES aiteam.requirements(id),
                    description TEXT NOT NULL,
                    status VARCHAR(50) DEFAULT 'pending',
                    order_index INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Create projects table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS aiteam.projects (
                    id SERIAL PRIMARY KEY,
                    tenant_id INTEGER REFERENCES aiteam.tenants(id),
                    requirement_id INTEGER REFERENCES aiteam.requirements(id),
                    repo_url TEXT NOT NULL,
                    commit_id VARCHAR(255),
                    project_metadata JSONB DEFAULT '{}',
                    status VARCHAR(50) DEFAULT 'created',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Create executions table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS aiteam.executions (
                    id SERIAL PRIMARY KEY,
                    project_id INTEGER REFERENCES aiteam.projects(id),
                    task_id INTEGER REFERENCES aiteam.tasks(id),
                    command TEXT NOT NULL,
                    environment VARCHAR(50) DEFAULT 'sandbox',
                    logs TEXT,
                    output TEXT,
                    error_message TEXT,
                    status VARCHAR(50) DEFAULT 'queued',
                    exit_code INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP
                )
            """))
            
            # Create audit_logs table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS aiteam.audit_logs (
                    id SERIAL PRIMARY KEY,
                    tenant_id INTEGER REFERENCES aiteam.tenants(id),
                    user_id INTEGER REFERENCES aiteam.users(id),
                    action VARCHAR(255) NOT NULL,
                    entity_type VARCHAR(50),
                    entity_id INTEGER,
                    old_values JSONB,
                    new_values JSONB,
                    ip_address INET,
                    user_agent TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Create tenant_settings table (for profile service)
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS aiteam.tenant_settings (
                    id SERIAL PRIMARY KEY,
                    tenant_id INTEGER REFERENCES aiteam.tenants(id),
                    setting_key VARCHAR(100) NOT NULL,
                    setting_value TEXT,
                    api_key TEXT,
                    additional_config JSONB DEFAULT '{}',
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(tenant_id, setting_key)
                )
            """))
            
            conn.commit()
            logger.info("Database tables created successfully")
            
            # Insert demo tenant if not exists
            result = conn.execute(text("SELECT COUNT(*) FROM aiteam.tenants WHERE org_id = 'demo-org'"))
            if result.scalar() == 0:
                logger.info("Creating demo tenant...")
                conn.execute(text("""
                    INSERT INTO aiteam.tenants (name, org_id) 
                    VALUES ('Demo Organization', 'demo-org')
                """))
                conn.commit()
                
            # Get tenant ID
            result = conn.execute(text("SELECT id FROM aiteam.tenants WHERE org_id = 'demo-org'"))
            tenant_id = result.scalar()
            
            # Insert admin user if not exists
            result = conn.execute(text("SELECT COUNT(*) FROM aiteam.users WHERE username = 'admin'"))
            if result.scalar() == 0:
                logger.info("Creating admin user...")
                # Using a simple hash for demo - in production use proper hashing
                admin_password_hash = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPjYfY8Zx9r2'  # 'admin123'
                conn.execute(text("""
                    INSERT INTO aiteam.users (username, email, password_hash, tenant_id, roles, is_active) 
                    VALUES ('admin', 'admin@example.com', :password_hash, :tenant_id, ARRAY['admin', 'user'], true)
                """), {"password_hash": admin_password_hash, "tenant_id": tenant_id})
                conn.commit()
                
            # Initialize tenant settings if not exists
            result = conn.execute(text("SELECT COUNT(*) FROM aiteam.tenant_settings WHERE tenant_id = :tenant_id AND setting_key = 'ai_provider'"))
            if result.scalar() == 0:
                logger.info("Creating demo tenant settings...")
                conn.execute(text("""
                    INSERT INTO aiteam.tenant_settings (tenant_id, setting_key, setting_value, api_key, additional_config) 
                    VALUES (:tenant_id, 'ai_provider', 'openrouter', :api_key, '{"model": "deepseek/deepseek-chat-v3.1:free"}'::jsonb)
                """), {"tenant_id": tenant_id, "api_key": os.getenv('OPENROUTER_API_KEY', '')})
                conn.commit()
                
            logger.info("Database initialization completed successfully")
            
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

if __name__ == "__main__":
    init_database()
