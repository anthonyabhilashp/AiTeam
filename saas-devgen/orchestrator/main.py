"""Orchestrator Service - Manages requirement intake and task breakdown."""
import sys
import os
# Add the parent directory to sys.path for shared modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel
from shared.config import settings
from shared.logging_utils import setup_logger
from shared.database import get_db
from shared.models import Requirement, Task, User
from sqlalchemy.orm import Session

# AI imports for intelligent requirement breakdown
import openai
import anthropic
import requests
import json

# Initialize logger
logger = setup_logger("orchestrator", "orchestrator.log")

app = FastAPI(title="Orchestrator Service", version="1.0.0")


class RequirementRequest(BaseModel):
    """Requirement creation request."""
    requirement: str


class TaskResponse(BaseModel):
    """Task response model."""
    id: int
    description: str
    status: str
    order_index: int


class RequirementResponse(BaseModel):
    """Requirement response model."""
    requirement_id: int
    text: str
    status: str
    tasks: List[TaskResponse]
    created_at: datetime


class AIPromptManager:
    """Manages AI prompts for requirement breakdown using enterprise AI providers."""
    
    def __init__(self):
        self.logger = logger
        self.ai_provider = os.getenv("AI_PROVIDER", "openai")
        self.ai_model = os.getenv("AI_MODEL", "gpt-4")
        self.api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENROUTER_API_KEY")
    
    def break_down_requirement(self, requirement_text: str) -> List[str]:
        """
        Break down requirement into tasks using AI.
        Uses enterprise AI providers for intelligent task generation.
        """
        self.logger.info(f"Breaking down requirement using {self.ai_provider}: {requirement_text[:100]}...")
        
        try:
            if self.ai_provider == "openai" and self.api_key:
                return self._break_down_with_openai(requirement_text)
            elif self.ai_provider == "anthropic" and self.api_key:
                return self._break_down_with_anthropic(requirement_text)
            elif self.ai_provider == "openrouter" and self.api_key:
                return self._break_down_with_openrouter(requirement_text)
            else:
                self.logger.warning("No AI provider configured, falling back to rule-based breakdown")
                return self._rule_based_breakdown(requirement_text)
        except Exception as e:
            self.logger.error(f"AI breakdown failed: {e}, falling back to rule-based")
            return self._rule_based_breakdown(requirement_text)
    
    def _break_down_with_openai(self, requirement_text: str) -> List[str]:
        """Break down requirement using OpenAI."""
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            
            prompt = f"""
            You are an expert software project manager. Break down the following software requirement into specific, actionable development tasks.
            
            Requirement: {requirement_text}
            
            Please provide a detailed breakdown of tasks that would be needed to implement this requirement. Each task should be:
            1. Specific and actionable
            2. Appropriately sized (not too large, not too small)
            3. Include technical details where relevant
            4. Consider best practices and industry standards
            
            Return the tasks as a JSON array of strings.
            """
            
            response = client.chat.completions.create(
                model=self.ai_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1000
            )
            
            tasks_json = response.choices[0].message.content.strip()
            tasks = json.loads(tasks_json)
            
            if isinstance(tasks, list):
                self.logger.info(f"OpenAI generated {len(tasks)} tasks")
                return tasks
            else:
                raise ValueError("Invalid response format")
                
        except Exception as e:
            self.logger.error(f"OpenAI breakdown failed: {e}")
            raise
    
    def _break_down_with_anthropic(self, requirement_text: str) -> List[str]:
        """Break down requirement using Anthropic Claude."""
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            
            prompt = f"""
            You are an expert software project manager. Break down the following software requirement into specific, actionable development tasks.
            
            Requirement: {requirement_text}
            
            Please provide a detailed breakdown of tasks that would be needed to implement this requirement. Each task should be:
            1. Specific and actionable
            2. Appropriately sized (not too large, not too small)
            3. Include technical details where relevant
            4. Consider best practices and industry standards
            
            Return ONLY a JSON array of task strings, no other text.
            """
            
            response = client.messages.create(
                model=self.ai_model,
                max_tokens=1000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            
            tasks_json = response.content[0].text.strip()
            tasks = json.loads(tasks_json)
            
            if isinstance(tasks, list):
                self.logger.info(f"Anthropic generated {len(tasks)} tasks")
                return tasks
            else:
                raise ValueError("Invalid response format")
                
        except Exception as e:
            self.logger.error(f"Anthropic breakdown failed: {e}")
            raise
    
    def _break_down_with_openrouter(self, requirement_text: str) -> List[str]:
        """Break down requirement using OpenRouter."""
        try:
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            prompt = f"""
            You are an expert software project manager. Break down the following software requirement into specific, actionable development tasks.
            
            Requirement: {requirement_text}
            
            Please provide a detailed breakdown of tasks that would be needed to implement this requirement. Each task should be:
            1. Specific and actionable
            2. Appropriately sized (not too large, not too small)
            3. Include technical details where relevant
            4. Consider best practices and industry standards
            
            Return ONLY a JSON array of task strings, no other text.
            """
            
            data = {
                "model": self.ai_model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 1000
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            tasks_json = result["choices"][0]["message"]["content"].strip()
            tasks = json.loads(tasks_json)
            
            if isinstance(tasks, list):
                self.logger.info(f"OpenRouter generated {len(tasks)} tasks")
                return tasks
            else:
                raise ValueError("Invalid response format")
                
        except Exception as e:
            self.logger.error(f"OpenRouter breakdown failed: {e}")
            raise
    
    def _rule_based_breakdown(self, requirement_text: str) -> List[str]:
        """
        Fallback rule-based task breakdown when AI is not available.
        """
        self.logger.info("Using rule-based requirement breakdown")
        
        tasks = []
        req_lower = requirement_text.lower()
        
        # API-related tasks
        if "api" in req_lower or "rest" in req_lower or "endpoint" in req_lower:
            tasks.extend([
                "Design REST API endpoints and data models",
                "Set up FastAPI/Express project structure with proper middleware",
                "Implement authentication and authorization middleware",
                "Create database models and migration scripts",
                "Implement CRUD operations for all entities",
                "Add input validation and error handling",
                "Write comprehensive API tests",
                "Create API documentation with OpenAPI/Swagger",
                "Implement rate limiting and security headers",
                "Set up API monitoring and logging"
            ])
        
        # Frontend/UI tasks
        if "frontend" in req_lower or "ui" in req_lower or "user interface" in req_lower or "react" in req_lower or "vue" in req_lower or "angular" in req_lower:
            tasks.extend([
                "Design responsive UI/UX wireframes and mockups",
                "Set up React/Next.js/Vue.js project with TypeScript",
                "Implement responsive layout with CSS Grid/Flexbox",
                "Create reusable component library",
                "Integrate with backend APIs using React Query/SWR",
                "Implement state management (Redux/Zustand/Context)",
                "Add form validation and error handling",
                "Implement responsive design for mobile/tablet/desktop",
                "Write component unit tests",
                "Set up CI/CD pipeline for frontend deployment"
            ])
        
        # Database tasks
        if "database" in req_lower or "data" in req_lower or "storage" in req_lower:
            tasks.extend([
                "Design database schema and entity relationships",
                "Set up database migration system",
                "Implement data access layer with ORM",
                "Add database indexing for performance",
                "Implement database connection pooling",
                "Set up database backup and recovery strategy",
                "Add database monitoring and alerting",
                "Implement data validation and constraints",
                "Set up database testing environment",
                "Document database schema and relationships"
            ])
        
        # Authentication tasks
        if "auth" in req_lower or "login" in req_lower or "user" in req_lower or "security" in req_lower:
            tasks.extend([
                "Implement user registration and login system",
                "Set up JWT token-based authentication",
                "Add password hashing and security measures",
                "Implement role-based access control (RBAC)",
                "Add OAuth integration for social login",
                "Implement password reset functionality",
                "Add session management and security headers",
                "Set up user profile management",
                "Implement account verification system",
                "Add security audit logging"
            ])
        
        # Testing tasks
        if "test" in req_lower or len(tasks) > 5:  # Add testing if complex project
            tasks.extend([
                "Set up testing framework (Jest/Pytest)",
                "Write unit tests for all modules",
                "Implement integration tests",
                "Add end-to-end testing with Cypress/Playwright",
                "Set up test coverage reporting",
                "Implement automated testing in CI/CD",
                "Write API testing with Postman/Newman",
                "Add performance testing",
                "Implement security testing",
                "Set up test data management"
            ])
        
        # DevOps/CI-CD tasks
        if len(tasks) > 10:  # Add DevOps for larger projects
            tasks.extend([
                "Set up Docker containerization",
                "Configure CI/CD pipeline with GitHub Actions",
                "Set up staging and production environments",
                "Implement monitoring and logging (ELK stack)",
                "Configure automated deployment",
                "Set up database migration in production",
                "Implement backup and disaster recovery",
                "Configure SSL certificates and security",
                "Set up performance monitoring",
                "Document deployment and maintenance procedures"
            ])
        
        # Default tasks if no specific patterns found
        if not tasks:
            tasks = [
                "Analyze requirements and create technical specification",
                "Design system architecture and technology stack",
                "Set up project structure and development environment",
                "Implement core business logic and functionality",
                "Add comprehensive error handling and validation",
                "Write unit and integration tests",
                "Create user documentation and API references",
                "Set up deployment and monitoring infrastructure",
                "Perform security audit and penetration testing",
                "Conduct performance optimization and load testing"
            ]
        
        self.logger.info(f"Generated {len(tasks)} tasks using rule-based breakdown")
        return tasks[:15]  # Limit to 15 tasks max


ai_pm = AIPromptManager()


async def get_current_user_from_token(authorization: str) -> dict:
    """Extract user info from authorization header."""
    # For enterprise demo, use the created enterprise user
    # In production, this would validate JWT and extract real user info
    return {
        "user_id": 1,  # Enterprise user ID
        "tenant_id": 1,  # Enterprise tenant ID
        "username": "enterprise_user",
        "roles": ["admin", "developer", "project_manager"]
    }


@app.post("/requirements", response_model=RequirementResponse)
async def create_requirement(
    req: RequirementRequest,
    db: Session = Depends(get_db),
    authorization: str = Depends(lambda: "Bearer mock-token")
):
    """Create a new requirement and break it down into tasks."""
    logger.info(f"Creating requirement: {req.requirement[:100]}...")
    
    try:
        # Get user info (simplified for MVP)
        user_info = await get_current_user_from_token(authorization)
        
        # Create requirement
        requirement = Requirement(
            tenant_id=user_info["tenant_id"],
            user_id=user_info["user_id"],
            text=req.requirement,
            status="processing"
        )
        db.add(requirement)
        db.commit()
        db.refresh(requirement)
        
        # Break down into tasks using AI PM
        task_descriptions = ai_pm.break_down_requirement(req.requirement)
        
        # Create tasks
        tasks = []
        for i, desc in enumerate(task_descriptions):
            task = Task(
                requirement_id=requirement.id,
                description=desc,
                order_index=i,
                status="pending"
            )
            db.add(task)
            tasks.append(task)
        
        db.commit()
        
        # Update requirement status
        requirement.status = "completed"
        db.commit()
        
        logger.info(f"Created requirement {requirement.id} with {len(tasks)} tasks")
        
        return RequirementResponse(
            requirement_id=requirement.id,
            text=requirement.text,
            status=requirement.status,
            tasks=[
                TaskResponse(
                    id=task.id,
                    description=task.description,
                    status=task.status,
                    order_index=task.order_index
                ) for task in tasks
            ],
            created_at=requirement.created_at
        )
        
    except Exception as e:
        logger.error(f"Failed to create requirement: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process requirement"
        )


@app.get("/requirements/{requirement_id}", response_model=RequirementResponse)
async def get_requirement(requirement_id: int, db: Session = Depends(get_db)):
    """Get requirement by ID."""
    logger.info(f"Fetching requirement {requirement_id}")
    
    requirement = db.query(Requirement).filter(Requirement.id == requirement_id).first()
    if not requirement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requirement not found"
        )
    
    tasks = db.query(Task).filter(Task.requirement_id == requirement_id).order_by(Task.order_index).all()
    
    return RequirementResponse(
        requirement_id=requirement.id,
        text=requirement.text,
        status=requirement.status,
        tasks=[
            TaskResponse(
                id=task.id,
                description=task.description,
                status=task.status,
                order_index=task.order_index
            ) for task in tasks
        ],
        created_at=requirement.created_at
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "orchestrator",
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Orchestrator Service on port 8002")
    uvicorn.run(app, host="0.0.0.0", port=8002)
