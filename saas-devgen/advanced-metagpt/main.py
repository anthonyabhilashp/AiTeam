"""
Advanced MetaGPT Integration for Enterprise AI Software Generator
Production-ready multi-agent system with specialized roles for complex software architecture
"""

import asyncio
import logging
import os
import json
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import subprocess

import sys
import os
# Add the parent directory to sys.path for shared modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, String, DateTime, Text, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import httpx

# Enterprise configuration
from shared.config import settings
from shared.logging_utils import setup_logger

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.getenv('LOG_DIR', '../../logs') + '/advanced-metagpt.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Database Models
Base = declarative_base()

class AgentExecution(Base):
    __tablename__ = "agent_executions"
    
    id = Column(String, primary_key=True)
    requirement_id = Column(String, nullable=False)
    tenant_id = Column(String, nullable=False)
    agent_type = Column(String, nullable=False)  # PM, Architect, Engineer, QA
    status = Column(String, nullable=False)  # running, completed, failed
    input_data = Column(Text)  # JSON input
    output_data = Column(Text)  # JSON output
    logs = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

class ProjectArchitecture(Base):
    __tablename__ = "project_architectures"
    
    id = Column(String, primary_key=True)
    requirement_id = Column(String, nullable=False)
    tenant_id = Column(String, nullable=False)
    architecture_type = Column(String, nullable=False)  # microservices, monolith, serverless
    components = Column(Text)  # JSON list of components
    technologies = Column(Text)  # JSON list of technologies
    design_doc = Column(Text)  # Architecture document
    created_at = Column(DateTime, default=datetime.utcnow)

# Pydantic Models
class RequirementInput(BaseModel):
    requirement_text: str = Field(..., description="Natural language requirement")
    tenant_id: str = Field(..., description="Tenant ID")
    complexity: str = Field(default="medium", description="Project complexity: simple, medium, complex, enterprise")
    domain: Optional[str] = Field(None, description="Domain/industry context")
    constraints: Optional[List[str]] = Field(None, description="Technical constraints")

class AgentResponse(BaseModel):
    agent_id: str
    agent_type: str
    status: str
    output: Dict[str, Any]
    next_agent: Optional[str] = None

class ProjectPlan(BaseModel):
    requirement_id: str
    breakdown: List[Dict[str, Any]]
    architecture: Dict[str, Any]
    implementation_plan: List[Dict[str, Any]]
    testing_strategy: Dict[str, Any]
    estimated_time: str

# Enterprise AI Agents
class EnterpriseProductManager:
    """AI Product Manager for requirement analysis and breakdown"""
    
    def __init__(self):
        self.role = "Product Manager"
        self.capabilities = [
            "requirement_analysis",
            "user_story_creation", 
            "feature_prioritization",
            "acceptance_criteria",
            "project_planning"
        ]
    
    async def analyze_requirement(self, requirement: str, domain: Optional[str] = None, 
                                constraints: Optional[List[str]] = None) -> Dict[str, Any]:
        """Analyze requirements and create detailed breakdown"""
        try:
            logger.info(f"PM analyzing requirement: {requirement[:100]}...")
            
            # Simulate advanced requirement analysis
            analysis = {
                "requirement_id": str(uuid.uuid4()),
                "original_requirement": requirement,
                "domain": domain or "general",
                "complexity_score": self._assess_complexity(requirement),
                "user_stories": self._generate_user_stories(requirement),
                "features": self._extract_features(requirement),
                "acceptance_criteria": self._generate_acceptance_criteria(requirement),
                "project_scope": self._define_scope(requirement),
                "constraints": constraints or [],
                "estimated_effort": self._estimate_effort(requirement),
                "risk_assessment": self._assess_risks(requirement),
                "recommendations": self._generate_recommendations(requirement)
            }
            
            logger.info(f"PM completed analysis for requirement {analysis['requirement_id']}")
            return analysis
            
        except Exception as e:
            logger.error(f"PM analysis failed: {e}")
            raise

    def _assess_complexity(self, requirement: str) -> int:
        """Assess requirement complexity (1-10)"""
        complexity_indicators = [
            "microservice", "distributed", "scalable", "enterprise", "integration",
            "authentication", "authorization", "payment", "real-time", "analytics",
            "machine learning", "ai", "blockchain", "mobile", "api"
        ]
        
        score = 3  # Base complexity
        req_lower = requirement.lower()
        
        for indicator in complexity_indicators:
            if indicator in req_lower:
                score += 1
        
        return min(10, score)

    def _generate_user_stories(self, requirement: str) -> List[Dict[str, Any]]:
        """Generate user stories from requirement"""
        # Enhanced user story generation
        stories = []
        
        if "api" in requirement.lower():
            stories.append({
                "id": "US001",
                "title": "API Endpoint Creation",
                "story": "As a developer, I want to create REST API endpoints so that external systems can interact with the application",
                "priority": "high",
                "estimation": "5 story points"
            })
        
        if "user" in requirement.lower() or "login" in requirement.lower():
            stories.append({
                "id": "US002", 
                "title": "User Authentication",
                "story": "As a user, I want to securely log into the system so that I can access my personalized features",
                "priority": "high",
                "estimation": "8 story points"
            })
        
        if "data" in requirement.lower() or "database" in requirement.lower():
            stories.append({
                "id": "US003",
                "title": "Data Management",
                "story": "As a system administrator, I want to manage data efficiently so that the application performs optimally",
                "priority": "medium",
                "estimation": "13 story points"
            })
        
        # Add generic story if none match
        if not stories:
            stories.append({
                "id": "US001",
                "title": "Core Functionality",
                "story": f"As a user, I want {requirement.lower()} so that I can achieve my goals",
                "priority": "high",
                "estimation": "8 story points"
            })
        
        return stories

    def _extract_features(self, requirement: str) -> List[Dict[str, Any]]:
        """Extract key features from requirement"""
        features = []
        req_lower = requirement.lower()
        
        feature_map = {
            "api": {"name": "REST API", "description": "RESTful web services"},
            "auth": {"name": "Authentication", "description": "User authentication system"},
            "database": {"name": "Data Storage", "description": "Database integration"},
            "ui": {"name": "User Interface", "description": "Frontend user interface"},
            "report": {"name": "Reporting", "description": "Data reporting and analytics"},
            "notification": {"name": "Notifications", "description": "User notification system"},
            "search": {"name": "Search", "description": "Search functionality"},
            "payment": {"name": "Payment Processing", "description": "Payment gateway integration"}
        }
        
        for keyword, feature in feature_map.items():
            if keyword in req_lower:
                features.append({
                    "id": f"F{len(features)+1:03d}",
                    "name": feature["name"],
                    "description": feature["description"],
                    "priority": "high" if keyword in ["api", "auth"] else "medium",
                    "complexity": "high" if keyword in ["payment", "auth"] else "medium"
                })
        
        # Ensure at least one feature
        if not features:
            features.append({
                "id": "F001",
                "name": "Core Application",
                "description": "Main application functionality",
                "priority": "high",
                "complexity": "medium"
            })
        
        return features

    def _generate_acceptance_criteria(self, requirement: str) -> List[str]:
        """Generate acceptance criteria"""
        criteria = [
            "Application must be functional and error-free",
            "Code must follow enterprise coding standards",
            "All endpoints must be properly documented",
            "Security best practices must be implemented",
            "Performance requirements must be met"
        ]
        
        if "api" in requirement.lower():
            criteria.extend([
                "API must return appropriate HTTP status codes",
                "API responses must be in JSON format",
                "API must handle error cases gracefully"
            ])
        
        if "auth" in requirement.lower():
            criteria.extend([
                "Authentication must use secure protocols",
                "User sessions must be properly managed",
                "Password policies must be enforced"
            ])
        
        return criteria

    def _define_scope(self, requirement: str) -> Dict[str, Any]:
        """Define project scope"""
        return {
            "in_scope": [
                "Core functionality implementation",
                "Basic error handling",
                "Standard security measures",
                "Documentation"
            ],
            "out_of_scope": [
                "Advanced monitoring and alerting",
                "Custom UI themes",
                "Third-party integrations beyond requirements",
                "Performance optimization beyond basic needs"
            ],
            "assumptions": [
                "Standard deployment environment",
                "Basic infrastructure available",
                "Standard security requirements"
            ]
        }

    def _estimate_effort(self, requirement: str) -> Dict[str, Any]:
        """Estimate development effort"""
        complexity = self._assess_complexity(requirement)
        
        base_hours = {
            1: 8, 2: 16, 3: 24, 4: 40, 5: 60,
            6: 80, 7: 120, 8: 160, 9: 200, 10: 300
        }
        
        estimated_hours = base_hours.get(complexity, 60)
        
        return {
            "total_hours": estimated_hours,
            "development": int(estimated_hours * 0.6),
            "testing": int(estimated_hours * 0.2),
            "documentation": int(estimated_hours * 0.1),
            "deployment": int(estimated_hours * 0.1),
            "estimated_days": estimated_hours // 8,
            "confidence": "medium" if complexity <= 7 else "low"
        }

    def _assess_risks(self, requirement: str) -> List[Dict[str, Any]]:
        """Assess project risks"""
        risks = []
        req_lower = requirement.lower()
        
        if "complex" in req_lower or "enterprise" in req_lower:
            risks.append({
                "type": "complexity",
                "description": "High complexity may lead to extended development time",
                "impact": "high",
                "mitigation": "Break down into smaller phases"
            })
        
        if "integration" in req_lower:
            risks.append({
                "type": "integration",
                "description": "Third-party integration dependencies",
                "impact": "medium",
                "mitigation": "Early API testing and fallback plans"
            })
        
        if "performance" in req_lower or "scalable" in req_lower:
            risks.append({
                "type": "performance",
                "description": "Performance requirements may be challenging",
                "impact": "medium",
                "mitigation": "Early performance testing and optimization"
            })
        
        # Default risk
        risks.append({
            "type": "scope_creep",
            "description": "Requirements may expand during development",
            "impact": "medium",
            "mitigation": "Clear requirement documentation and change control"
        })
        
        return risks

    def _generate_recommendations(self, requirement: str) -> List[str]:
        """Generate PM recommendations"""
        recommendations = [
            "Start with MVP implementation",
            "Implement comprehensive logging",
            "Include health check endpoints",
            "Plan for monitoring and alerting"
        ]
        
        if "api" in requirement.lower():
            recommendations.extend([
                "Use OpenAPI/Swagger for API documentation",
                "Implement API versioning strategy",
                "Add rate limiting for production"
            ])
        
        if "database" in requirement.lower():
            recommendations.extend([
                "Design proper database schema",
                "Implement database migrations",
                "Plan for data backup and recovery"
            ])
        
        return recommendations

class EnterpriseArchitect:
    """AI Solutions Architect for system design"""
    
    def __init__(self):
        self.role = "Solutions Architect"
        self.capabilities = [
            "system_design",
            "technology_selection",
            "architecture_patterns",
            "scalability_planning",
            "security_design"
        ]
    
    async def design_architecture(self, pm_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Design system architecture based on PM analysis"""
        try:
            logger.info(f"Architect designing system for requirement {pm_analysis.get('requirement_id')}")
            
            complexity = pm_analysis.get('complexity_score', 5)
            features = pm_analysis.get('features', [])
            
            architecture = {
                "architecture_id": str(uuid.uuid4()),
                "requirement_id": pm_analysis.get('requirement_id'),
                "pattern": self._select_architecture_pattern(complexity, features),
                "technologies": self._select_technologies(features),
                "components": self._design_components(features),
                "data_architecture": self._design_data_architecture(features),
                "security_architecture": self._design_security(features),
                "deployment_architecture": self._design_deployment(complexity),
                "scalability_plan": self._plan_scalability(complexity),
                "integration_points": self._identify_integrations(features)
            }
            
            logger.info(f"Architect completed design for {architecture['architecture_id']}")
            return architecture
            
        except Exception as e:
            logger.error(f"Architecture design failed: {e}")
            raise

    def _select_architecture_pattern(self, complexity: int, features: List[Dict]) -> Dict[str, Any]:
        """Select appropriate architecture pattern"""
        if complexity >= 8:
            return {
                "pattern": "microservices",
                "description": "Microservices architecture for high scalability",
                "services": ["api-gateway", "auth-service", "business-service", "data-service"],
                "communication": "REST APIs with message queues"
            }
        elif complexity >= 6:
            return {
                "pattern": "modular_monolith", 
                "description": "Modular monolith with clear service boundaries",
                "modules": ["auth", "business_logic", "data_access", "api"],
                "communication": "Internal module interfaces"
            }
        else:
            return {
                "pattern": "layered",
                "description": "Traditional layered architecture",
                "layers": ["presentation", "business", "data", "infrastructure"],
                "communication": "Direct method calls"
            }

    def _select_technologies(self, features: List[Dict]) -> Dict[str, Any]:
        """Select appropriate technologies"""
        tech_stack = {
            "backend": {
                "framework": "FastAPI",
                "language": "Python 3.10+",
                "rationale": "Fast development, excellent documentation, async support"
            },
            "database": {
                "primary": "PostgreSQL",
                "rationale": "ACID compliance, excellent performance, JSON support"
            },
            "caching": {
                "technology": "Redis",
                "rationale": "High performance, versatile data structures"
            },
            "api": {
                "style": "REST",
                "documentation": "OpenAPI/Swagger",
                "rationale": "Industry standard, excellent tooling"
            }
        }
        
        # Add specific technologies based on features
        feature_names = [f.get('name', '').lower() for f in features]
        
        if any("auth" in name for name in feature_names):
            tech_stack["authentication"] = {
                "technology": "JWT with FastAPI Security",
                "rationale": "Stateless, scalable, standard"
            }
        
        if any("ui" in name for name in feature_names):
            tech_stack["frontend"] = {
                "framework": "React with TypeScript",
                "rationale": "Component-based, type safety, excellent ecosystem"
            }
        
        if any("payment" in name for name in feature_names):
            tech_stack["payment"] = {
                "integration": "Stripe API",
                "rationale": "Secure, well-documented, reliable"
            }
        
        return tech_stack

    def _design_components(self, features: List[Dict]) -> List[Dict[str, Any]]:
        """Design system components"""
        components = [
            {
                "name": "API Gateway",
                "type": "service",
                "responsibility": "Request routing, authentication, rate limiting",
                "interfaces": ["HTTP REST"],
                "dependencies": ["auth-service"]
            },
            {
                "name": "Business Logic Service",
                "type": "service", 
                "responsibility": "Core business logic implementation",
                "interfaces": ["HTTP REST", "Internal APIs"],
                "dependencies": ["database", "cache"]
            },
            {
                "name": "Data Access Layer",
                "type": "layer",
                "responsibility": "Database operations, data mapping",
                "interfaces": ["Internal APIs"],
                "dependencies": ["database"]
            }
        ]
        
        # Add feature-specific components
        feature_names = [f.get('name', '').lower() for f in features]
        
        if any("auth" in name for name in feature_names):
            components.append({
                "name": "Authentication Service",
                "type": "service",
                "responsibility": "User authentication, token management",
                "interfaces": ["HTTP REST"],
                "dependencies": ["database", "cache"]
            })
        
        if any("notification" in name for name in feature_names):
            components.append({
                "name": "Notification Service",
                "type": "service",
                "responsibility": "Send notifications via multiple channels",
                "interfaces": ["HTTP REST", "Message Queue"],
                "dependencies": ["external-apis"]
            })
        
        return components

    def _design_data_architecture(self, features: List[Dict]) -> Dict[str, Any]:
        """Design data architecture"""
        return {
            "primary_database": {
                "type": "PostgreSQL",
                "purpose": "Transactional data",
                "schema_design": "Normalized relational schema",
                "backup_strategy": "Daily full backup, hourly incremental"
            },
            "caching_layer": {
                "type": "Redis",
                "purpose": "Session data, frequently accessed data",
                "expiration_policy": "TTL-based with LRU eviction"
            },
            "data_flow": {
                "read_pattern": "Cache-first with database fallback",
                "write_pattern": "Write-through to database with cache invalidation",
                "consistency": "Eventual consistency for cached data"
            },
            "migrations": {
                "tool": "Alembic",
                "strategy": "Version-controlled database migrations",
                "rollback_plan": "Automated rollback for failed migrations"
            }
        }

    def _design_security(self, features: List[Dict]) -> Dict[str, Any]:
        """Design security architecture"""
        return {
            "authentication": {
                "method": "JWT tokens",
                "storage": "HTTP-only cookies for web, localStorage for mobile",
                "expiration": "15 minutes access token, 7 days refresh token"
            },
            "authorization": {
                "model": "Role-Based Access Control (RBAC)",
                "enforcement": "Middleware at API gateway level"
            },
            "data_protection": {
                "encryption": "TLS 1.3 for data in transit, AES-256 for data at rest",
                "sensitive_data": "Hashed passwords with bcrypt, encrypted PII"
            },
            "api_security": {
                "rate_limiting": "Per-user and per-IP rate limits",
                "input_validation": "Pydantic models with strict validation",
                "cors": "Configured for specific allowed origins"
            },
            "monitoring": {
                "logging": "Structured logging with correlation IDs",
                "alerts": "Security event monitoring and alerting"
            }
        }

    def _design_deployment(self, complexity: int) -> Dict[str, Any]:
        """Design deployment architecture"""
        if complexity >= 8:
            return {
                "platform": "Kubernetes",
                "container_strategy": "Multi-service containers",
                "scaling": "Horizontal pod autoscaling",
                "service_mesh": "Istio for service communication",
                "monitoring": "Prometheus + Grafana",
                "logging": "ELK stack"
            }
        elif complexity >= 6:
            return {
                "platform": "Docker Compose + Load Balancer",
                "container_strategy": "Service per container",
                "scaling": "Manual scaling with multiple instances",
                "monitoring": "Basic Prometheus setup",
                "logging": "Centralized logging with Loki"
            }
        else:
            return {
                "platform": "Single server deployment",
                "container_strategy": "Single application container",
                "scaling": "Vertical scaling",
                "monitoring": "Application-level monitoring",
                "logging": "File-based logging"
            }

    def _plan_scalability(self, complexity: int) -> Dict[str, Any]:
        """Plan scalability approach"""
        return {
            "horizontal_scaling": {
                "stateless_services": "All services designed to be stateless",
                "load_balancing": "Round-robin with health checks",
                "session_management": "Redis-based session store"
            },
            "database_scaling": {
                "read_replicas": "Read replicas for read-heavy operations",
                "connection_pooling": "PgBouncer for connection management",
                "query_optimization": "Database indexing and query analysis"
            },
            "caching_strategy": {
                "levels": ["Application cache", "Database query cache", "CDN"],
                "invalidation": "Event-based cache invalidation"
            },
            "performance_targets": {
                "response_time": "< 200ms for 95th percentile",
                "throughput": "1000+ requests per second",
                "availability": "99.9% uptime"
            }
        }

    def _identify_integrations(self, features: List[Dict]) -> List[Dict[str, Any]]:
        """Identify integration points"""
        integrations = []
        feature_names = [f.get('name', '').lower() for f in features]
        
        if any("payment" in name for name in feature_names):
            integrations.append({
                "name": "Payment Gateway",
                "type": "External API",
                "provider": "Stripe",
                "protocol": "HTTPS REST",
                "fallback": "Queue failed payments for retry"
            })
        
        if any("notification" in name for name in feature_names):
            integrations.append({
                "name": "Email Service",
                "type": "External API", 
                "provider": "SendGrid",
                "protocol": "HTTPS REST",
                "fallback": "Local SMTP server"
            })
        
        # Always include monitoring
        integrations.append({
            "name": "Monitoring Service",
            "type": "Internal",
            "provider": "Prometheus",
            "protocol": "HTTP metrics endpoint",
            "fallback": "File-based metrics"
        })
        
        return integrations

class EnterpriseEngineer:
    """AI Software Engineer for code implementation"""
    
    def __init__(self):
        self.role = "Software Engineer"
        self.capabilities = [
            "code_generation",
            "api_implementation", 
            "database_design",
            "testing",
            "documentation"
        ]
    
    async def implement_solution(self, architecture: Dict[str, Any], pm_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Implement the solution based on architecture"""
        try:
            logger.info(f"Engineer implementing solution for {architecture.get('architecture_id')}")
            
            implementation = {
                "implementation_id": str(uuid.uuid4()),
                "architecture_id": architecture.get('architecture_id'),
                "requirement_id": pm_analysis.get('requirement_id'),
                "code_structure": self._generate_code_structure(architecture),
                "api_endpoints": self._generate_api_endpoints(pm_analysis, architecture),
                "database_schema": self._generate_database_schema(pm_analysis, architecture),
                "business_logic": self._generate_business_logic(pm_analysis),
                "tests": self._generate_tests(pm_analysis),
                "documentation": self._generate_documentation(pm_analysis, architecture),
                "deployment_config": self._generate_deployment_config(architecture)
            }
            
            logger.info(f"Engineer completed implementation {implementation['implementation_id']}")
            return implementation
            
        except Exception as e:
            logger.error(f"Implementation failed: {e}")
            raise

    def _generate_code_structure(self, architecture: Dict[str, Any]) -> Dict[str, Any]:
        """Generate code structure based on architecture"""
        pattern = architecture.get('pattern', {}).get('pattern', 'layered')
        
        if pattern == "microservices":
            return {
                "structure_type": "microservices",
                "directories": [
                    "api-gateway/", "auth-service/", "business-service/",
                    "data-service/", "shared/", "tests/", "docs/", "k8s/"
                ],
                "shared_components": ["models", "utils", "config", "logging"]
            }
        elif pattern == "modular_monolith":
            return {
                "structure_type": "modular_monolith",
                "directories": [
                    "app/", "app/auth/", "app/business/", "app/data/",
                    "app/api/", "tests/", "docs/", "migrations/"
                ],
                "shared_components": ["models", "config", "utils"]
            }
        else:
            return {
                "structure_type": "layered",
                "directories": [
                    "app/", "app/models/", "app/services/", "app/controllers/",
                    "app/utils/", "tests/", "docs/", "migrations/"
                ],
                "shared_components": ["config", "utils", "exceptions"]
            }

    def _generate_api_endpoints(self, pm_analysis: Dict[str, Any], architecture: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate API endpoint specifications"""
        endpoints = []
        features = pm_analysis.get('features', [])
        
        # Always include health check
        endpoints.append({
            "path": "/health",
            "method": "GET",
            "description": "Service health check",
            "responses": {"200": {"status": "healthy"}},
            "authentication": False
        })
        
        # Generate endpoints based on features
        for feature in features:
            feature_name = feature.get('name', '').lower()
            
            if "api" in feature_name or "rest" in feature_name:
                endpoints.extend([
                    {
                        "path": "/api/v1/items",
                        "method": "GET",
                        "description": "List all items",
                        "responses": {"200": {"items": "array"}},
                        "authentication": True
                    },
                    {
                        "path": "/api/v1/items",
                        "method": "POST", 
                        "description": "Create new item",
                        "request_body": {"name": "string", "description": "string"},
                        "responses": {"201": {"id": "string"}},
                        "authentication": True
                    },
                    {
                        "path": "/api/v1/items/{item_id}",
                        "method": "GET",
                        "description": "Get specific item",
                        "parameters": {"item_id": "string"},
                        "responses": {"200": {"item": "object"}},
                        "authentication": True
                    }
                ])
            
            if "auth" in feature_name:
                endpoints.extend([
                    {
                        "path": "/auth/login",
                        "method": "POST",
                        "description": "User login",
                        "request_body": {"username": "string", "password": "string"},
                        "responses": {"200": {"access_token": "string"}},
                        "authentication": False
                    },
                    {
                        "path": "/auth/logout",
                        "method": "POST",
                        "description": "User logout",
                        "responses": {"200": {"message": "success"}},
                        "authentication": True
                    },
                    {
                        "path": "/auth/profile",
                        "method": "GET",
                        "description": "Get user profile",
                        "responses": {"200": {"user": "object"}},
                        "authentication": True
                    }
                ])
        
        return endpoints

    def _generate_database_schema(self, pm_analysis: Dict[str, Any], architecture: Dict[str, Any]) -> Dict[str, Any]:
        """Generate database schema"""
        features = pm_analysis.get('features', [])
        tables = []
        
        # Always include basic tables
        tables.extend([
            {
                "name": "users",
                "columns": [
                    {"name": "id", "type": "UUID", "primary_key": True},
                    {"name": "username", "type": "VARCHAR(50)", "unique": True},
                    {"name": "email", "type": "VARCHAR(100)", "unique": True},
                    {"name": "password_hash", "type": "VARCHAR(255)"},
                    {"name": "created_at", "type": "TIMESTAMP", "default": "NOW()"},
                    {"name": "updated_at", "type": "TIMESTAMP", "default": "NOW()"}
                ],
                "indexes": ["email", "username"]
            },
            {
                "name": "items",
                "columns": [
                    {"name": "id", "type": "UUID", "primary_key": True},
                    {"name": "name", "type": "VARCHAR(100)"},
                    {"name": "description", "type": "TEXT"},
                    {"name": "user_id", "type": "UUID", "foreign_key": "users.id"},
                    {"name": "created_at", "type": "TIMESTAMP", "default": "NOW()"},
                    {"name": "updated_at", "type": "TIMESTAMP", "default": "NOW()"}
                ],
                "indexes": ["user_id", "created_at"]
            }
        ])
        
        # Add feature-specific tables
        feature_names = [f.get('name', '').lower() for f in features]
        
        if any("notification" in name for name in feature_names):
            tables.append({
                "name": "notifications",
                "columns": [
                    {"name": "id", "type": "UUID", "primary_key": True},
                    {"name": "user_id", "type": "UUID", "foreign_key": "users.id"},
                    {"name": "title", "type": "VARCHAR(200)"},
                    {"name": "message", "type": "TEXT"},
                    {"name": "read", "type": "BOOLEAN", "default": False},
                    {"name": "created_at", "type": "TIMESTAMP", "default": "NOW()"}
                ],
                "indexes": ["user_id", "read", "created_at"]
            })
        
        return {
            "database": "PostgreSQL",
            "tables": tables,
            "migrations": {
                "tool": "Alembic",
                "strategy": "Version-controlled migrations"
            },
            "connection": {
                "pool_size": 20,
                "max_overflow": 30,
                "pool_timeout": 30
            }
        }

    def _generate_business_logic(self, pm_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate business logic specifications"""
        features = pm_analysis.get('features', [])
        
        business_logic = {
            "services": [],
            "validation_rules": [],
            "business_rules": []
        }
        
        # Generate services based on features
        for feature in features:
            feature_name = feature.get('name', '').lower()
            
            if "api" in feature_name:
                business_logic["services"].append({
                    "name": "ItemService",
                    "methods": [
                        "create_item", "get_item", "update_item", 
                        "delete_item", "list_items"
                    ],
                    "validation": ["item_exists", "user_ownership", "input_validation"]
                })
            
            if "auth" in feature_name:
                business_logic["services"].append({
                    "name": "AuthService", 
                    "methods": [
                        "authenticate_user", "create_user", "validate_token",
                        "refresh_token", "logout_user"
                    ],
                    "validation": ["password_strength", "email_format", "unique_credentials"]
                })
        
        # Add validation rules
        business_logic["validation_rules"] = [
            "All input data must be validated",
            "Email addresses must be in valid format",
            "Passwords must meet complexity requirements",
            "User ownership must be verified for data access"
        ]
        
        # Add business rules
        business_logic["business_rules"] = [
            "Users can only access their own data",
            "All operations must be logged for audit",
            "Failed authentication attempts must be rate limited",
            "Data integrity must be maintained across operations"
        ]
        
        return business_logic

    def _generate_tests(self, pm_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate test specifications"""
        return {
            "test_types": [
                "unit_tests", "integration_tests", "api_tests", "security_tests"
            ],
            "coverage_target": "85%",
            "test_framework": "pytest",
            "test_structure": {
                "unit_tests": ["test_services", "test_models", "test_utils"],
                "integration_tests": ["test_database", "test_api_integration"],
                "api_tests": ["test_endpoints", "test_authentication", "test_authorization"],
                "security_tests": ["test_input_validation", "test_auth_bypass", "test_data_exposure"]
            },
            "mock_strategy": "Mock external dependencies, test internal logic",
            "test_data": "Use factory pattern for test data generation"
        }

    def _generate_documentation(self, pm_analysis: Dict[str, Any], architecture: Dict[str, Any]) -> Dict[str, Any]:
        """Generate documentation specifications"""
        return {
            "api_documentation": {
                "tool": "OpenAPI/Swagger",
                "auto_generation": True,
                "includes": ["endpoints", "models", "authentication", "examples"]
            },
            "code_documentation": {
                "style": "Google docstring format",
                "coverage": "All public methods and classes",
                "includes": ["parameters", "return_values", "exceptions", "examples"]
            },
            "deployment_documentation": {
                "includes": ["setup_instructions", "environment_variables", "dependencies", "troubleshooting"]
            },
            "user_documentation": {
                "includes": ["getting_started", "api_guide", "examples", "faq"]
            }
        }

    def _generate_deployment_config(self, architecture: Dict[str, Any]) -> Dict[str, Any]:
        """Generate deployment configuration"""
        deployment = architecture.get('deployment_architecture', {})
        
        return {
            "containerization": {
                "dockerfile": "Multi-stage build for optimization",
                "base_image": "python:3.10-slim",
                "security": "Non-root user, minimal packages"
            },
            "environment_config": {
                "development": {"debug": True, "log_level": "DEBUG"},
                "staging": {"debug": False, "log_level": "INFO"},
                "production": {"debug": False, "log_level": "WARNING"}
            },
            "health_checks": {
                "liveness": "/health",
                "readiness": "/ready",
                "startup": "/startup"
            },
            "scaling": {
                "min_replicas": 2,
                "max_replicas": 10,
                "cpu_threshold": "70%",
                "memory_threshold": "80%"
            }
        }

class EnterpriseQA:
    """AI QA Engineer for testing strategy"""
    
    def __init__(self):
        self.role = "QA Engineer"
        self.capabilities = [
            "test_planning",
            "test_automation",
            "quality_metrics",
            "performance_testing",
            "security_testing"
        ]
    
    async def create_test_strategy(self, pm_analysis: Dict[str, Any], 
                                 architecture: Dict[str, Any], 
                                 implementation: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive test strategy"""
        try:
            logger.info(f"QA creating test strategy for {pm_analysis.get('requirement_id')}")
            
            strategy = {
                "strategy_id": str(uuid.uuid4()),
                "test_levels": self._define_test_levels(architecture),
                "test_types": self._define_test_types(pm_analysis),
                "automation_strategy": self._define_automation_strategy(),
                "performance_testing": self._define_performance_testing(architecture),
                "security_testing": self._define_security_testing(pm_analysis),
                "quality_gates": self._define_quality_gates(),
                "test_data_strategy": self._define_test_data_strategy(),
                "risk_based_testing": self._identify_testing_risks(pm_analysis)
            }
            
            logger.info(f"QA completed test strategy {strategy['strategy_id']}")
            return strategy
            
        except Exception as e:
            logger.error(f"Test strategy creation failed: {e}")
            raise

    def _define_test_levels(self, architecture: Dict[str, Any]) -> Dict[str, Any]:
        """Define testing levels based on architecture"""
        return {
            "unit_testing": {
                "scope": "Individual functions and methods",
                "tools": ["pytest", "unittest.mock"],
                "coverage_target": "90%",
                "responsibility": "Developers"
            },
            "integration_testing": {
                "scope": "Component interactions",
                "tools": ["pytest", "testcontainers"],
                "coverage_target": "80%",
                "responsibility": "Developers + QA"
            },
            "api_testing": {
                "scope": "API contract validation",
                "tools": ["pytest", "httpx", "Postman"],
                "coverage_target": "100% of endpoints",
                "responsibility": "QA"
            },
            "system_testing": {
                "scope": "End-to-end workflows", 
                "tools": ["pytest", "selenium", "playwright"],
                "coverage_target": "Critical user journeys",
                "responsibility": "QA"
            }
        }

    def _define_test_types(self, pm_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Define test types based on requirements"""
        features = pm_analysis.get('features', [])
        
        test_types = {
            "functional_testing": {
                "description": "Validate business requirements",
                "test_cases": self._generate_functional_test_cases(features),
                "priority": "high"
            },
            "api_contract_testing": {
                "description": "Validate API contracts",
                "test_cases": ["Request/response validation", "Error handling", "Status codes"],
                "priority": "high"
            },
            "database_testing": {
                "description": "Validate data operations",
                "test_cases": ["CRUD operations", "Data integrity", "Transaction handling"],
                "priority": "medium"
            },
            "security_testing": {
                "description": "Validate security controls",
                "test_cases": ["Authentication", "Authorization", "Input validation", "Data protection"],
                "priority": "high"
            },
            "performance_testing": {
                "description": "Validate performance requirements",
                "test_cases": ["Load testing", "Stress testing", "Response times"],
                "priority": "medium"
            }
        }
        
        return test_types

    def _generate_functional_test_cases(self, features: List[Dict[str, Any]]) -> List[str]:
        """Generate functional test cases based on features"""
        test_cases = []
        
        for feature in features:
            feature_name = feature.get('name', '').lower()
            
            if "api" in feature_name:
                test_cases.extend([
                    "Create item with valid data",
                    "Create item with invalid data",
                    "Retrieve existing item",
                    "Retrieve non-existent item", 
                    "Update item with valid data",
                    "Delete existing item"
                ])
            
            if "auth" in feature_name:
                test_cases.extend([
                    "Login with valid credentials",
                    "Login with invalid credentials",
                    "Access protected resource with valid token",
                    "Access protected resource without token",
                    "Token expiration handling"
                ])
        
        return test_cases

    def _define_automation_strategy(self) -> Dict[str, Any]:
        """Define test automation strategy"""
        return {
            "automation_pyramid": {
                "unit_tests": "70% - Fast, isolated, developer-driven",
                "integration_tests": "20% - Medium speed, component interactions",
                "e2e_tests": "10% - Slow, critical user journeys"
            },
            "ci_cd_integration": {
                "trigger": "Every code commit",
                "stages": ["Unit tests", "Integration tests", "Security scans"],
                "quality_gates": ["Test coverage > 85%", "No critical vulnerabilities"]
            },
            "test_environments": {
                "development": "Local testing with mocks",
                "staging": "Full integration testing",
                "production": "Smoke tests and monitoring"
            }
        }

    def _define_performance_testing(self, architecture: Dict[str, Any]) -> Dict[str, Any]:
        """Define performance testing strategy"""
        return {
            "load_testing": {
                "tool": "Locust",
                "scenarios": [
                    "Normal load - 100 concurrent users",
                    "Peak load - 500 concurrent users",
                    "Stress test - 1000+ concurrent users"
                ],
                "success_criteria": {
                    "response_time": "< 200ms for 95th percentile",
                    "throughput": "> 1000 requests/second",
                    "error_rate": "< 1%"
                }
            },
            "performance_monitoring": {
                "metrics": ["Response time", "Throughput", "Error rate", "Resource utilization"],
                "alerts": ["Response time > 500ms", "Error rate > 5%", "CPU > 80%"]
            }
        }

    def _define_security_testing(self, pm_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Define security testing strategy"""
        return {
            "static_analysis": {
                "tools": ["Bandit", "Safety", "Semgrep"],
                "scope": "Source code vulnerability scanning",
                "frequency": "Every commit"
            },
            "dynamic_analysis": {
                "tools": ["OWASP ZAP", "Custom scripts"],
                "scope": "Runtime vulnerability testing",
                "frequency": "Weekly"
            },
            "penetration_testing": {
                "scope": ["Authentication bypass", "SQL injection", "XSS", "CSRF"],
                "frequency": "Before each release",
                "tools": ["Manual testing", "Automated scanners"]
            }
        }

    def _define_quality_gates(self) -> Dict[str, Any]:
        """Define quality gates for releases"""
        return {
            "code_quality": {
                "test_coverage": "> 85%",
                "code_duplication": "< 5%",
                "complexity": "< 10 cyclomatic complexity"
            },
            "security": {
                "vulnerabilities": "0 critical, 0 high severity",
                "dependency_check": "No known vulnerable dependencies"
            },
            "performance": {
                "response_time": "< 200ms for 95th percentile",
                "error_rate": "< 1%",
                "availability": "> 99.9%"
            },
            "functional": {
                "critical_tests": "100% pass rate",
                "regression_tests": "100% pass rate",
                "api_tests": "100% pass rate"
            }
        }

    def _define_test_data_strategy(self) -> Dict[str, Any]:
        """Define test data management strategy"""
        return {
            "test_data_types": {
                "synthetic": "Generated test data for automation",
                "anonymized": "Production-like data with PII removed",
                "minimal": "Minimal viable data for unit tests"
            },
            "data_management": {
                "creation": "Factory pattern for consistent data",
                "cleanup": "Automatic cleanup after test execution",
                "isolation": "Each test uses independent data"
            },
            "data_privacy": {
                "pii_handling": "No real PII in test environments",
                "data_retention": "Test data purged after 30 days",
                "access_control": "Restricted access to test data"
            }
        }

    def _identify_testing_risks(self, pm_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify testing risks and mitigation strategies"""
        risks = []
        complexity = pm_analysis.get('complexity_score', 5)
        
        if complexity >= 8:
            risks.append({
                "risk": "High complexity may lead to inadequate test coverage",
                "impact": "high",
                "mitigation": "Risk-based testing focusing on critical paths",
                "monitoring": "Track test coverage metrics"
            })
        
        features = pm_analysis.get('features', [])
        if any("auth" in f.get('name', '').lower() for f in features):
            risks.append({
                "risk": "Authentication vulnerabilities",
                "impact": "critical",
                "mitigation": "Dedicated security testing for auth flows", 
                "monitoring": "Automated security scans"
            })
        
        if any("payment" in f.get('name', '').lower() for f in features):
            risks.append({
                "risk": "Payment processing errors",
                "impact": "high",
                "mitigation": "Comprehensive payment flow testing",
                "monitoring": "Transaction monitoring and alerting"
            })
        
        return risks

# Advanced MetaGPT Integration Service
class AdvancedMetaGPTService:
    """Enterprise MetaGPT orchestration service"""
    
    def __init__(self):
        self.app = FastAPI(title="Advanced MetaGPT Service", version="1.0.0")
        self.setup_database()
        self.setup_routes()
        
        # Initialize AI agents
        self.pm = EnterpriseProductManager()
        self.architect = EnterpriseArchitect()
        self.engineer = EnterpriseEngineer()
        self.qa = EnterpriseQA()
        
        logger.info("Advanced MetaGPT Service initialized")

    def setup_database(self):
        """Setup database connection"""
        try:
            database_url = settings.database_url or f"postgresql://{settings.postgres_user}:{settings.postgres_password}@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"
            self.engine = create_engine(database_url)
            Base.metadata.create_all(self.engine)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Database setup failed: {e}")
            raise

    def setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy", "service": "advanced-metagpt"}
        
        @self.app.post("/generate", response_model=dict)
        async def generate_software(request: RequirementInput, background_tasks: BackgroundTasks):
            """Generate complete software solution using AI agents"""
            requirement_id = str(uuid.uuid4())
            
            # Start generation in background
            background_tasks.add_task(
                self.orchestrate_agents,
                requirement_id,
                request.requirement_text,
                request.tenant_id,
                request.complexity,
                request.domain,
                request.constraints
            )
            
            return {
                "requirement_id": requirement_id,
                "status": "started",
                "message": "AI agent orchestration initiated"
            }
        
        @self.app.get("/status/{requirement_id}")
        async def get_generation_status(requirement_id: str):
            """Get software generation status"""
            db = self.SessionLocal()
            try:
                executions = db.query(AgentExecution).filter(
                    AgentExecution.requirement_id == requirement_id
                ).all()
                
                status = {
                    "requirement_id": requirement_id,
                    "agents": {}
                }
                
                for execution in executions:
                    status["agents"][execution.agent_type] = {
                        "status": execution.status,
                        "completed_at": execution.completed_at.isoformat() if execution.completed_at else None
                    }
                
                return status
            finally:
                db.close()
        
        @self.app.get("/result/{requirement_id}")
        async def get_generation_result(requirement_id: str):
            """Get final generation result"""
            db = self.SessionLocal()
            try:
                # Get all completed agent executions
                executions = db.query(AgentExecution).filter(
                    AgentExecution.requirement_id == requirement_id,
                    AgentExecution.status == "completed"
                ).all()
                
                result = {
                    "requirement_id": requirement_id,
                    "agent_outputs": {}
                }
                
                for execution in executions:
                    result["agent_outputs"][execution.agent_type] = json.loads(execution.output_data or "{}")
                
                return result
            finally:
                db.close()

    async def orchestrate_agents(self, requirement_id: str, requirement_text: str,
                                tenant_id: str, complexity: str, domain: Optional[str],
                                constraints: Optional[List[str]]):
        """Orchestrate AI agents for software generation"""
        try:
            logger.info(f"Starting agent orchestration for requirement {requirement_id}")
            
            # Step 1: Product Manager Analysis
            pm_execution = await self.execute_agent(
                "PM", requirement_id, tenant_id,
                {"requirement": requirement_text, "domain": domain, "constraints": constraints}
            )
            
            if pm_execution["status"] != "completed":
                logger.error("PM analysis failed, stopping orchestration")
                return
            
            pm_output = json.loads(pm_execution["output_data"])
            
            # Step 2: Architecture Design
            arch_execution = await self.execute_agent(
                "Architect", requirement_id, tenant_id,
                {"pm_analysis": pm_output}
            )
            
            if arch_execution["status"] != "completed":
                logger.error("Architecture design failed, stopping orchestration")
                return
            
            arch_output = json.loads(arch_execution["output_data"])
            
            # Step 3: Software Implementation
            impl_execution = await self.execute_agent(
                "Engineer", requirement_id, tenant_id,
                {"pm_analysis": pm_output, "architecture": arch_output}
            )
            
            if impl_execution["status"] != "completed":
                logger.error("Implementation failed, stopping orchestration")
                return
            
            impl_output = json.loads(impl_execution["output_data"])
            
            # Step 4: QA Strategy
            qa_execution = await self.execute_agent(
                "QA", requirement_id, tenant_id,
                {"pm_analysis": pm_output, "architecture": arch_output, "implementation": impl_output}
            )
            
            logger.info(f"Agent orchestration completed for requirement {requirement_id}")
            
        except Exception as e:
            logger.error(f"Agent orchestration failed: {e}")

    async def execute_agent(self, agent_type: str, requirement_id: str, 
                          tenant_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute individual AI agent"""
        db = self.SessionLocal()
        execution_id = str(uuid.uuid4())
        
        try:
            # Record agent execution start
            execution = AgentExecution(
                id=execution_id,
                requirement_id=requirement_id,
                tenant_id=tenant_id,
                agent_type=agent_type,
                status="running",
                input_data=json.dumps(input_data)
            )
            db.add(execution)
            db.commit()
            
            # Execute agent based on type
            if agent_type == "PM":
                output = await self.pm.analyze_requirement(
                    input_data["requirement"],
                    input_data.get("domain"),
                    input_data.get("constraints")
                )
            elif agent_type == "Architect":
                output = await self.architect.design_architecture(input_data["pm_analysis"])
            elif agent_type == "Engineer":
                output = await self.engineer.implement_solution(
                    input_data["architecture"],
                    input_data["pm_analysis"]
                )
            elif agent_type == "QA":
                output = await self.qa.create_test_strategy(
                    input_data["pm_analysis"],
                    input_data["architecture"],
                    input_data["implementation"]
                )
            else:
                raise ValueError(f"Unknown agent type: {agent_type}")
            
            # Update execution record
            execution.status = "completed"
            execution.output_data = json.dumps(output)
            execution.completed_at = datetime.utcnow()
            db.commit()
            
            return {
                "execution_id": execution_id,
                "status": "completed",
                "output_data": json.dumps(output)
            }
            
        except Exception as e:
            logger.error(f"Agent {agent_type} execution failed: {e}")
            
            execution.status = "failed"
            execution.logs = str(e)
            db.commit()
            
            return {
                "execution_id": execution_id,
                "status": "failed",
                "error": str(e)
            }
        finally:
            db.close()

# Initialize the service
service = AdvancedMetaGPTService()
app = service.app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8009)
