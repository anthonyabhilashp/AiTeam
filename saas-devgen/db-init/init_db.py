#!/usr/bin/env python3
"""
Enterprise Database Initialization Service
Handles schema migrations and initial data seeding with proper timeout handling.
"""
import os
import sys
import time
import signal
import logging
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from typing import List

# Add the parent directory to sys.path for shared modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from shared.logging_utils import setup_logger

# Timeout settings
DB_CONNECTION_TIMEOUT = 30
MIGRATION_TIMEOUT = 60
OVERALL_TIMEOUT = 300  # 5 minutes max

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Operation timed out")

def with_timeout(timeout_seconds: int):
    def decorator(func):
        def wrapper(*args, **kwargs):
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout_seconds)
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
        return wrapper
    return decorator

@with_timeout(DB_CONNECTION_TIMEOUT)
def wait_for_database(host: str, port: int, database: str, user: str, password: str, logger) -> bool:
    max_retries = 10
    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(host=host, port=port, database=database, 
                                  user=user, password=password, connect_timeout=5)
            conn.close()
            logger.info("Database is ready")
            return True
        except psycopg2.OperationalError as e:
            if attempt < max_retries - 1:
                logger.info(f"Database not ready (attempt {attempt + 1}/{max_retries})")
                time.sleep(2)
            else:
                logger.error(f"Database connection failed after {max_retries} attempts")
                raise
    return False

def fix_seed_data(migration_content: str) -> str:
    """Fix the seed data to match actual schema"""
    return migration_content.replace(
        """INSERT INTO tenant_settings (tenant_id, ai_provider, ai_model, api_key, additional_config)""",
        """INSERT INTO tenant_settings (tenant_id, setting_key, setting_value, api_key, additional_config)"""
    ).replace(
        """VALUES (1, 'openrouter', 'deepseek/deepseek-chat-v3.1:free', '',""",
        """VALUES (1, 'ai_provider', 'openrouter', '',"""
    )

@with_timeout(MIGRATION_TIMEOUT)
def apply_migration(conn, migration_file: str, migration_content: str, logger) -> bool:
    try:
        cursor = conn.cursor()
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        logger.info(f"Applying migration: {migration_file}")
        
        if "002_seed_data.sql" in migration_file:
            migration_content = fix_seed_data(migration_content)
        
        statements = [stmt.strip() for stmt in migration_content.split(';') if stmt.strip()]
        
        for i, statement in enumerate(statements):
            if statement:
                try:
                    cursor.execute(statement)
                except psycopg2.Error as e:
                    logger.error(f"Failed statement {i+1}: {e}")
                    raise
        
        cursor.execute("""
            INSERT INTO schema_migrations (version, applied_at)
            VALUES (%s, CURRENT_TIMESTAMP)
            ON CONFLICT (version) DO NOTHING
        """, (migration_file,))
        
        cursor.close()
        logger.info(f"Successfully applied migration: {migration_file}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to apply migration {migration_file}: {e}")
        return False

def get_applied_migrations(conn, logger) -> List[str]:
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(255) PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("SELECT version FROM schema_migrations ORDER BY version")
        applied = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return applied
    except Exception as e:
        logger.error(f"Failed to get applied migrations: {e}")
        return []

@with_timeout(OVERALL_TIMEOUT - 60)
def run_migrations(conn, migrations_dir: str, logger) -> bool:
    try:
        logger.info("Starting database migration process")
        
        applied_migrations = get_applied_migrations(conn, logger)
        logger.info(f"Found {len(applied_migrations)} applied migrations")
        
        migration_files = sorted([f for f in os.listdir(migrations_dir) if f.endswith('.sql')])
        logger.info(f"Found {len(migration_files)} migration files")
        
        success_count = 0
        for migration_file in migration_files:
            if migration_file in applied_migrations:
                logger.info(f"Skipping already applied migration: {migration_file}")
                success_count += 1
                continue
                
            migration_path = os.path.join(migrations_dir, migration_file)
            with open(migration_path, 'r') as f:
                migration_content = f.read()
            
            if apply_migration(conn, migration_file, migration_content, logger):
                success_count += 1
            else:
                logger.error(f"Migration failed: {migration_file}")
                return False
        
        logger.info(f"Successfully applied {success_count}/{len(migration_files)} migrations")
        return success_count == len(migration_files)
        
    except TimeoutError:
        logger.error("Migration process timed out")
        return False
    except Exception as e:
        logger.error(f"Migration process failed: {e}")
        return False

@with_timeout(OVERALL_TIMEOUT)
def main():
    logger = setup_logger("db-init", "db-init.log")
    logger.info("Starting enterprise database initialization with timeouts")
    
    try:
        db_config = {
            'host': os.getenv('POSTGRES_HOST', 'postgres'),
            'port': int(os.getenv('POSTGRES_PORT', 5432)),
            'database': os.getenv('POSTGRES_DB', 'devgen'),
            'user': os.getenv('POSTGRES_USER', 'devgen'),
            'password': os.getenv('POSTGRES_PASSWORD', 'devgen_enterprise_2024')
        }
        
        logger.info(f"Database URL: {db_config['host']}:{db_config['port']}/{db_config['database']}")
        
        if not wait_for_database(**db_config, logger=logger):
            logger.error("Database is not ready")
            sys.exit(1)
        
        conn = psycopg2.connect(**db_config)
        
        migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')
        if run_migrations(conn, migrations_dir, logger):
            logger.info("Database initialization completed successfully")
            conn.close()
            sys.exit(0)
        else:
            logger.error("Database initialization failed")
            conn.close()
            sys.exit(1)
            
    except TimeoutError:
        logger.error("Database initialization timed out after 5 minutes")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
