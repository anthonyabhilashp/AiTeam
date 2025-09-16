-- Migration 001: Initial Schema Setup
-- Enterprise AI Platform Database Schema
-- Version: 1.0.0
-- Date: 2025-09-15

-- Create schema for AI Team platform
CREATE SCHEMA IF NOT EXISTS aiteam;

-- Create tenants table (Multi-tenancy support)
CREATE TABLE IF NOT EXISTS aiteam.tenants (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    org_id VARCHAR(50) UNIQUE,
    status VARCHAR(20) DEFAULT 'active',
    subscription_plan VARCHAR(50) DEFAULT 'enterprise',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create users table
CREATE TABLE IF NOT EXISTS aiteam.users (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER REFERENCES aiteam.tenants(id) ON DELETE CASCADE,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255),
    roles TEXT[] DEFAULT ARRAY['user'],
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, username),
    UNIQUE(tenant_id, email)
);

-- Create requirements table
CREATE TABLE IF NOT EXISTS aiteam.requirements (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER REFERENCES aiteam.tenants(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES aiteam.users(id) ON DELETE CASCADE,
    title VARCHAR(200),
    description TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'submitted',
    priority VARCHAR(20) DEFAULT 'medium',
    estimated_complexity VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create projects table
CREATE TABLE IF NOT EXISTS aiteam.projects (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER REFERENCES aiteam.tenants(id) ON DELETE CASCADE,
    requirement_id INTEGER REFERENCES aiteam.requirements(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    repo_url TEXT,
    language VARCHAR(50),
    framework VARCHAR(50),
    status VARCHAR(50) DEFAULT 'initializing',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create tasks table
CREATE TABLE IF NOT EXISTS aiteam.tasks (
    id SERIAL PRIMARY KEY,
    requirement_id INTEGER REFERENCES aiteam.requirements(id) ON DELETE CASCADE,
    project_id INTEGER REFERENCES aiteam.projects(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    agent_type VARCHAR(50),
    assigned_agent VARCHAR(100),
    result JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create executions table
CREATE TABLE IF NOT EXISTS aiteam.executions (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES aiteam.projects(id) ON DELETE CASCADE,
    task_id INTEGER REFERENCES aiteam.tasks(id) ON DELETE SET NULL,
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
);

-- Create audit_logs table
CREATE TABLE IF NOT EXISTS aiteam.audit_logs (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER REFERENCES aiteam.tenants(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES aiteam.users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id INTEGER,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create tenant_settings table
CREATE TABLE IF NOT EXISTS aiteam.tenant_settings (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER REFERENCES aiteam.tenants(id) ON DELETE CASCADE,
    setting_key VARCHAR(100) NOT NULL,
    setting_value TEXT,
    api_key TEXT,
    additional_config JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, setting_key)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_tenant_status ON aiteam.users(tenant_id, is_active);
CREATE INDEX IF NOT EXISTS idx_requirements_tenant_status ON aiteam.requirements(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_projects_tenant_status ON aiteam.projects(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_tasks_requirement_status ON aiteam.tasks(requirement_id, status);
CREATE INDEX IF NOT EXISTS idx_executions_project_status ON aiteam.executions(project_id, status);
CREATE INDEX IF NOT EXISTS idx_audit_logs_tenant_created ON aiteam.audit_logs(tenant_id, created_at);
CREATE INDEX IF NOT EXISTS idx_tenant_settings_tenant_key ON aiteam.tenant_settings(tenant_id, setting_key);
