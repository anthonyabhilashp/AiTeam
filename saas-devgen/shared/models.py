"""Shared database models for all services."""
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class Tenant(Base):
    """Tenant model for multi-tenancy."""
    __tablename__ = "tenants"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    org_id = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    users = relationship("User", back_populates="tenant")
    requirements = relationship("Requirement", back_populates="tenant")
    projects = relationship("Project", back_populates="tenant")
    audit_logs = relationship("AuditLog", back_populates="tenant")


class User(Base):
    """User model."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    roles = Column(JSON, default=list)  # Store roles as JSON array
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    requirements = relationship("Requirement", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")


class Requirement(Base):
    """Requirement model."""
    __tablename__ = "requirements"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    text = Column(Text, nullable=False)
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tenant = relationship("Tenant", back_populates="requirements")
    user = relationship("User", back_populates="requirements")
    tasks = relationship("Task", back_populates="requirement", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="requirement", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="requirement")
    projects = relationship("Project", back_populates="requirement")


class Task(Base):
    """Task model for requirement breakdown."""
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    requirement_id = Column(Integer, ForeignKey("requirements.id"), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(50), default="pending")  # pending, in_progress, completed, failed
    order_index = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    requirement = relationship("Requirement", back_populates="tasks")


class Project(Base):
    """Project model for generated code."""
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    requirement_id = Column(Integer, ForeignKey("requirements.id"), nullable=False)
    repo_url = Column(String(500), nullable=False)
    commit_id = Column(String(255))
    project_metadata = Column(JSON, default=dict)
    status = Column(String(50), default="created")  # created, building, ready, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tenant = relationship("Tenant", back_populates="projects")
    requirement = relationship("Requirement", back_populates="projects")
    executions = relationship("Execution", back_populates="project")


class Execution(Base):
    """Execution model for sandbox runs."""
    __tablename__ = "executions"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    command = Column(String(1000), nullable=False)
    logs = Column(Text)
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    exit_code = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    project = relationship("Project", back_populates="executions")


class AuditLog(Base):
    """Audit log model for compliance."""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(255), nullable=False)
    entity = Column(String(255))  # requirement, project, execution, etc.
    entity_id = Column(Integer)
    details = Column(JSON, default=dict)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    tenant = relationship("Tenant", back_populates="audit_logs")
    user = relationship("User", back_populates="audit_logs")
